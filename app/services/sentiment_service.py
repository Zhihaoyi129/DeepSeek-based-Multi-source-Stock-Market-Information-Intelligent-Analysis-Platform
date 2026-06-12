from __future__ import annotations

import json
import re

POSITIVE_TERMS = [
    '上涨', '走强', '回暖', '增长', '利好', '突破', '增持', '盈利', '签约',
    '新高', '看多', '提振', 'improve', 'growth', 'surge', 'bullish', 'beat',
]
NEGATIVE_TERMS = [
    '下跌', '走弱', '利空', '风险', '亏损', '减持', '处罚', '下滑', '暴跌',
    '承压', '违约', '降级', 'loss', 'drop', 'bearish', 'warning', 'miss',
]


def _count_terms(text, terms):
    matched = []
    lowered = text.lower()
    for term in terms:
        if term.lower() in lowered:
            matched.append(term)
    return matched


def _extract_keywords(text):
    tokens = re.findall(r'[\u4e00-\u9fa5A-Za-z0-9\.]{2,}', text)
    keywords = []
    for token in tokens:
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= 8:
            break
    return keywords


def run_demo_sentiment_analysis(title, content, source_type):
    text = f'{title}\n{content}'
    positive_hits = _count_terms(text, POSITIVE_TERMS)
    negative_hits = _count_terms(text, NEGATIVE_TERMS)
    score = len(positive_hits) - len(negative_hits)

    if score >= 2:
        sentiment = 'positive'
    elif score <= -1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    keywords = list(dict.fromkeys(positive_hits + negative_hits + _extract_keywords(text)))
    confidence = min(0.95, 0.58 + abs(score) * 0.09)
    summary = (
        f'基于本地演示规则对{source_type}文本进行分析，'
        f'识别到 {len(positive_hits)} 个正向信号、{len(negative_hits)} 个负向信号，'
        f'当前结论为{_sentiment_label(sentiment)}。'
    )
    if negative_hits:
        risk_notes = f'文本中出现的风险关键词: {", ".join(negative_hits[:4])}'
    else:
        risk_notes = '未识别到明显风险关键词，后续可接入 DeepSeek 生成更细粒度解释。'

    raw_response = json.dumps(
        {
            'positiveHits': positive_hits,
            'negativeHits': negative_hits,
            'score': score,
            'engine': 'local-demo',
        },
        ensure_ascii=False,
    )
    return {
        'sentiment': sentiment,
        'summary': summary,
        'keywords': keywords[:8],
        'riskNotes': risk_notes,
        'confidence': round(confidence, 2),
        'rawResponse': raw_response,
    }


def _sentiment_label(sentiment):
    return {
        'positive': '正面',
        'neutral': '中性',
        'negative': '负面',
    }.get(sentiment, sentiment)
