from __future__ import annotations

from datetime import datetime

from app import db
from app.models.stock_analysis import MarketAnalysisRecord, SentimentAnalysisRecord, StockNewsRecord
from app.services.deepseek_service import generate_causal_report_with_deepseek
from app.services.market_service import build_tushare_quote, normalize_symbol


def analyze_past(symbol, range_type='3m', start_date=None, end_date=None):
    symbol = normalize_symbol(symbol)
    if not symbol:
        raise ValueError('股票代码不能为空')

    market = _build_and_save_market(symbol, range_type, start_date, end_date)
    news = _find_related_news(symbol, market.start_date, market.end_date)
    sentiments = _find_sentiments(symbol, market.start_date, market.end_date)
    market_payload = market.to_dict()
    report = generate_causal_report_with_deepseek({
        'symbol': symbol,
        'range': {
            'startDate': market_payload['startDate'],
            'endDate': market_payload['endDate'],
        },
        'summary': market_payload['summary'],
        'latestSeries': (market_payload['priceSeries'] or [])[-12:],
        'news': [item.to_dict() for item in news[:8]],
        'sentiments': [item.to_dict(include_content=False) for item in sentiments[:8]],
    })
    return {
        'market': market_payload,
        'news': [item.to_dict() for item in news],
        'sentiments': [item.to_dict(include_content=False) for item in sentiments],
        'sentimentStats': _sentiment_stats(news, sentiments),
        'aiReport': report['report'],
        'model': report['model'],
    }


def _build_and_save_market(symbol, range_type, start_date, end_date):
    payload = build_tushare_quote(
        symbol=symbol,
        range_type=range_type,
        start_date=start_date,
        end_date=end_date,
        indicators=['ma5', 'ma10', 'ma20', 'rsi', 'macd', 'volume'],
    )
    record = MarketAnalysisRecord(
        symbol=payload['symbol'],
        range_type=payload['rangeType'],
        start_date=datetime.strptime(payload['startDate'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(payload['endDate'], '%Y-%m-%d').date(),
        source_name=payload['sourceName'],
    )
    record.set_indicator_config(payload['indicators'])
    record.set_price_series(payload['priceSeries'])
    record.set_indicator_result(payload['indicatorResult'])
    record.set_summary(payload['summary'])
    db.session.add(record)
    db.session.commit()
    return record


def _find_related_news(symbol, start_date, end_date):
    rows = (
        StockNewsRecord.query
        .filter(StockNewsRecord.news_date >= start_date)
        .filter(StockNewsRecord.news_date <= end_date)
        .order_by(StockNewsRecord.news_date.desc(), StockNewsRecord.id.desc())
        .all()
    )
    matched = []
    for row in rows:
        related = row.get_related_stocks()
        if row.symbol == symbol or symbol in related:
            matched.append(row)
    return matched


def _find_sentiments(symbol, start_date, end_date):
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    return (
        SentimentAnalysisRecord.query
        .filter_by(symbol=symbol)
        .filter(SentimentAnalysisRecord.published_at >= start_dt)
        .filter(SentimentAnalysisRecord.published_at <= end_dt)
        .order_by(SentimentAnalysisRecord.published_at.desc(), SentimentAnalysisRecord.id.desc())
        .limit(20)
        .all()
    )


def _sentiment_stats(news, sentiments):
    stats = {
        'positive': 0,
        'neutral': 0,
        'negative': 0,
        'averageScore': 0,
    }
    scores = []
    for item in news:
        if item.sentiment in stats:
            stats[item.sentiment] += 1
        scores.append(item.sentiment_score)
    for item in sentiments:
        if item.sentiment in stats:
            stats[item.sentiment] += 1
    if scores:
        stats['averageScore'] = round(sum(scores) / len(scores), 3)
    return stats
