from __future__ import annotations

from datetime import datetime

from app.models.stock_analysis import (
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    SentimentAnalysisRecord,
)
from app.services.market_service import parse_date_input


def _parse_datetime_boundary(value, is_end=False):
    if not value:
        return None
    try:
        parsed_date = parse_date_input(value)
        if is_end:
            return datetime.combine(parsed_date, datetime.max.time()).replace(microsecond=0)
        return datetime.combine(parsed_date, datetime.min.time())
    except ValueError:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S'):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
    raise ValueError('日期筛选格式无效')


def _detail_route(module, record_id):
    mapping = {
        'sentiment': f'/project/sentiment?record_id={record_id}',
        'market': f'/project/market?record_id={record_id}',
        'decision': f'/project/decision?record_id={record_id}',
    }
    return mapping[module]


def _build_sentiment_item(record):
    return {
        'module': 'sentiment',
        'moduleLabel': '情感分析',
        'id': record.id,
        'symbol': record.symbol,
        'title': record.title,
        'status': record.status,
        'resultLabel': {
            'positive': '正面',
            'neutral': '中性',
            'negative': '负面',
        }.get(record.sentiment, record.sentiment),
        'createdAt': record.to_dict(include_content=False)['createdAt'],
        'detailRoute': _detail_route('sentiment', record.id),
    }


def _build_market_item(record):
    summary = record.get_summary()
    return {
        'module': 'market',
        'moduleLabel': '技术分析',
        'id': record.id,
        'symbol': record.symbol,
        'title': f'{record.symbol} {record.range_type} 技术指标分析',
        'status': record.status,
        'resultLabel': f"最新价 {summary.get('latestPrice', '-')}",
        'createdAt': record.to_dict()['createdAt'],
        'detailRoute': _detail_route('market', record.id),
    }


def _build_decision_item(record):
    return {
        'module': 'decision',
        'moduleLabel': '决策建议',
        'id': record.id,
        'symbol': record.symbol,
        'title': f'{record.symbol} 综合决策建议',
        'status': record.status,
        'resultLabel': {
            'buy': '买入',
            'sell': '卖出',
            'hold': '观望',
        }.get(record.decision, record.decision),
        'createdAt': record.to_dict()['createdAt'],
        'detailRoute': _detail_route('decision', record.id),
    }


def _passes_filter(item, module=None, symbol=None, status=None, start_at=None, end_at=None):
    if module and item['module'] != module:
        return False
    if symbol and item['symbol'] != symbol:
        return False
    if status and item['status'] != status:
        return False
    created_at = datetime.strptime(item['createdAt'], '%Y-%m-%d %H:%M:%S')
    if start_at and created_at < start_at:
        return False
    if end_at and created_at > end_at:
        return False
    return True


def collect_history_items(module=None, symbol=None, status=None, start_date=None, end_date=None):
    normalized_module = (module or '').strip().lower() or None
    normalized_symbol = (symbol or '').strip().upper() or None
    normalized_status = (status or '').strip().lower() or None
    start_at = _parse_datetime_boundary(start_date)
    end_at = _parse_datetime_boundary(end_date, is_end=True)

    items = []
    if normalized_module in (None, 'sentiment'):
        items.extend(_build_sentiment_item(record) for record in SentimentAnalysisRecord.query.all())
    if normalized_module in (None, 'market'):
        items.extend(_build_market_item(record) for record in MarketAnalysisRecord.query.all())
    if normalized_module in (None, 'decision'):
        items.extend(_build_decision_item(record) for record in DecisionSuggestionRecord.query.all())

    items = [
        item for item in items
        if _passes_filter(
            item,
            module=normalized_module,
            symbol=normalized_symbol,
            status=normalized_status,
            start_at=start_at,
            end_at=end_at,
        )
    ]
    items.sort(key=lambda item: item['createdAt'], reverse=True)
    return items


def get_history_detail(module, record_id):
    module = (module or '').strip().lower()
    if module == 'sentiment':
        record = SentimentAnalysisRecord.query.get(record_id)
        return None if record is None else {'module': module, 'detail': record.to_dict()}
    if module == 'market':
        record = MarketAnalysisRecord.query.get(record_id)
        return None if record is None else {'module': module, 'detail': record.to_dict()}
    if module == 'decision':
        record = DecisionSuggestionRecord.query.get(record_id)
        return None if record is None else {'module': module, 'detail': record.to_dict()}
    return None
