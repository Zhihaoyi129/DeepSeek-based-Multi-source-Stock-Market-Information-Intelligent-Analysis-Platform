from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.setting_service import get_setting


class AIServiceError(Exception):
    """中文注释：统一封装 DeepSeek 调用过程中的可展示错误。"""


def _build_api_url(base_url):
    base = (base_url or 'https://api.deepseek.com').strip().rstrip('/')
    if not base:
        base = 'https://api.deepseek.com'
    if base.endswith('/chat/completions'):
        return base
    return f'{base}/chat/completions'


def _load_deepseek_config():
    setting = get_setting('deepseek')
    if not setting.get('enabled'):
        raise AIServiceError('请先在系统设置中启用 DeepSeek。')

    api_key = (setting.get('apiKey') or '').strip()
    if not api_key:
        raise AIServiceError('请先在系统设置中填写 DeepSeek API Key。')

    try:
        timeout = int(setting.get('timeout') or 30)
    except (TypeError, ValueError):
        timeout = 30
    if timeout <= 0:
        timeout = 30

    return {
        'apiKey': api_key,
        'baseUrl': (setting.get('baseUrl') or 'https://api.deepseek.com').strip(),
        'modelName': (setting.get('modelName') or 'deepseek-chat').strip(),
        'timeout': timeout,
    }


def _extract_reply(response_payload):
    try:
        return str(response_payload['choices'][0]['message']['content']).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError('DeepSeek 响应格式异常。') from exc


def _parse_json_reply(reply):
    text = reply.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()
    try:
        return json.loads(text)
    except (TypeError, ValueError) as exc:
        raise AIServiceError('DeepSeek 返回内容不是有效 JSON。') from exc


def call_deepseek_chat(messages, temperature=0.3, response_format=None):
    config = _load_deepseek_config()
    payload = {
        'model': config['modelName'],
        'messages': messages,
        'temperature': temperature,
        'stream': False,
    }
    if response_format:
        payload['response_format'] = response_format

    request = Request(
        _build_api_url(config['baseUrl']),
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config['apiKey']}",
        },
        method='POST',
    )

    try:
        with urlopen(request, timeout=config['timeout']) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise AIServiceError(f'DeepSeek 请求失败，状态码 {exc.code}。{detail[:120]}') from exc
    except URLError as exc:
        raise AIServiceError(f'DeepSeek 连接失败：{exc.reason}') from exc
    except TimeoutError as exc:
        raise AIServiceError('DeepSeek 请求超时。') from exc
    except json.JSONDecodeError as exc:
        raise AIServiceError('DeepSeek 响应格式异常。') from exc

    return {
        'reply': _extract_reply(result),
        'model': config['modelName'],
        'raw': result,
    }


def open_deepseek_chat_stream(messages, temperature=0.5):
    config = _load_deepseek_config()
    payload = {
        'model': config['modelName'],
        'messages': messages,
        'temperature': temperature,
        'stream': True,
    }
    request = Request(
        _build_api_url(config['baseUrl']),
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config['apiKey']}",
        },
        method='POST',
    )

    try:
        response = urlopen(request, timeout=config['timeout'])
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise AIServiceError(f'DeepSeek 请求失败，状态码 {exc.code}。{detail[:120]}') from exc
    except URLError as exc:
        raise AIServiceError(f'DeepSeek 连接失败：{exc.reason}') from exc
    except TimeoutError as exc:
        raise AIServiceError('DeepSeek 请求超时。') from exc

    def generate_chunks():
        try:
            while True:
                line = response.readline()
                if not line:
                    break
                text = line.decode('utf-8', errors='ignore').strip()
                if not text or not text.startswith('data:'):
                    continue
                data = text[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    payload = json.loads(data)
                    delta = payload['choices'][0].get('delta', {}).get('content', '')
                except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                    raise AIServiceError('DeepSeek 流式响应格式异常。') from exc
                if delta:
                    yield str(delta)
        finally:
            response.close()

    return generate_chunks(), config['modelName']


def analyze_sentiment_with_deepseek(payload):
    title = (payload.get('title') or '').strip()
    content = (payload.get('content') or '').strip()
    source_type = (payload.get('source_type') or '').strip()
    symbol = (payload.get('symbol') or '').strip().upper()

    result = call_deepseek_chat(
        [
            {
                'role': 'system',
                'content': (
                    '你是专业的中文财经文本情感分析助手。'
                    '请只返回 JSON，不要返回 Markdown。'
                    '字段必须包含 sentiment、summary、keywords、riskNotes、confidence。'
                    'sentiment 只能是 positive、neutral、negative。'
                    'confidence 为 0 到 1 的数字。'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'股票代码：{symbol}\n'
                    f'文本类型：{source_type}\n'
                    f'标题：{title}\n'
                    f'正文：{content}\n'
                    '请判断该文本对相关股票或板块的市场情绪影响。'
                ),
            },
        ],
        temperature=0.2,
        response_format={'type': 'json_object'},
    )
    data = _parse_json_reply(result['reply'])
    sentiment = data.get('sentiment')
    if sentiment not in {'positive', 'neutral', 'negative'}:
        raise AIServiceError('DeepSeek 情感字段无效。')

    keywords = data.get('keywords') or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]

    try:
        confidence = float(data.get('confidence') or 0)
    except (TypeError, ValueError):
        confidence = 0

    return {
        'sentiment': sentiment,
        'summary': str(data.get('summary') or '').strip(),
        'keywords': [str(item).strip() for item in keywords if str(item).strip()],
        'riskNotes': str(data.get('riskNotes') or '').strip(),
        'confidence': confidence,
        'rawResponse': json.dumps(result['raw'], ensure_ascii=False),
        'model': result['model'],
    }


def generate_decision_with_deepseek(payload):
    result = call_deepseek_chat(
        [
            {
                'role': 'system',
                'content': (
                    '你是股票交易辅助分析助手。'
                    '请基于给定情感、价格、MA5、RSI 和规则化建议，'
                    '输出简洁中文综合说明，包含依据、风险和下一步观察点。'
                    '不要承诺收益，不要给绝对化投资结论。'
                ),
            },
            {
                'role': 'user',
                'content': json.dumps(payload, ensure_ascii=False),
            },
        ],
        temperature=0.4,
    )
    return {
        'message': result['reply'],
        'model': result['model'],
    }


def generate_news_with_deepseek(symbol, news_date, count=3):
    result = call_deepseek_chat(
        [
            {
                'role': 'system',
                'content': (
                    '你是财经新闻演示数据生成助手。请只返回 JSON，不要返回 Markdown。'
                    'JSON 字段必须包含 news，news 是数组。'
                    '每条新闻必须包含 title、content、sourceType、industry、relatedStocks。'
                    'sourceType 只能是 financial_news、policy_document、company_announcement。'
                    '内容用于教学演示，不要包含真实未证实内幕信息。'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'股票代码：{symbol}\n'
                    f'新闻日期：{news_date}\n'
                    f'生成数量：{count}\n'
                    '请生成与该股票或行业相关的盘后新闻、政策或公司公告摘要。'
                ),
            },
        ],
        temperature=0.6,
        response_format={'type': 'json_object'},
    )
    data = _parse_json_reply(result['reply'])
    items = data.get('news') or []
    if not isinstance(items, list):
        raise AIServiceError('DeepSeek 新闻字段无效。')
    normalized = []
    for item in items[:count]:
        if not isinstance(item, dict):
            continue
        related = item.get('relatedStocks') or [symbol]
        if not isinstance(related, list):
            related = [str(related)]
        normalized.append({
            'title': str(item.get('title') or '').strip(),
            'content': str(item.get('content') or '').strip(),
            'sourceType': str(item.get('sourceType') or 'financial_news').strip(),
            'industry': str(item.get('industry') or '').strip(),
            'relatedStocks': [str(value).strip().upper() for value in related if str(value).strip()],
            'model': result['model'],
            'rawResponse': json.dumps(result['raw'], ensure_ascii=False),
        })
    return [item for item in normalized if item['title'] and item['content']]


def generate_causal_report_with_deepseek(payload):
    result = call_deepseek_chat(
        [
            {
                'role': 'system',
                'content': (
                    '你是股票涨跌归因分析助手。请基于给定 K 线指标、涨跌幅、相关新闻和情感结果，'
                    '判断哪些新闻可能解释价格变化，忽略逻辑不相关的噪音。'
                    '输出中文报告，包含：走势概览、核心原因、传导逻辑、技术指标印证、风险提示。'
                    '不要承诺收益，不要给绝对化投资结论。'
                ),
            },
            {
                'role': 'user',
                'content': json.dumps(payload, ensure_ascii=False),
            },
        ],
        temperature=0.35,
    )
    return {
        'report': result['reply'],
        'model': result['model'],
    }


def chat_with_deepseek(message):
    user_message = str(message or '').strip()
    if not user_message:
        raise AIServiceError('请输入要咨询的问题。')

    result = call_deepseek_chat(
        [
            {
                'role': 'system',
                'content': (
                    '你是基于 DeepSeek 的多源股市信息智能分析平台助手。'
                    '你可以回答财经新闻情绪分析、技术指标、RSI、MA、MACD、'
                    '多源数据融合和系统使用相关问题。'
                    '回答应清晰、谨慎，并提示股市分析不构成投资承诺。'
                ),
            },
            {'role': 'user', 'content': user_message},
        ],
        temperature=0.5,
    )
    return {
        'reply': result['reply'],
        'model': result['model'],
    }


def stream_chat_with_deepseek(message):
    user_message = str(message or '').strip()
    if not user_message:
        raise AIServiceError('请输入要咨询的问题。')

    return open_deepseek_chat_stream(
        [
            {
                'role': 'system',
                'content': (
                    '你是基于 DeepSeek 的多源股市信息智能分析平台助手。'
                    '你可以回答财经新闻情绪分析、技术指标、RSI、MA、MACD、'
                    '多源数据融合和系统使用相关问题。'
                    '回答应清晰、谨慎，并提示股市分析不构成投资承诺。'
                ),
            },
            {'role': 'user', 'content': user_message},
        ],
        temperature=0.5,
    )
