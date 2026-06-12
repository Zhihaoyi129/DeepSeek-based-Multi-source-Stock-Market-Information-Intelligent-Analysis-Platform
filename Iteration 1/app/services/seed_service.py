from __future__ import annotations

from datetime import datetime

from app import db
from app.models.stock_analysis import (
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    SentimentAnalysisRecord,
    StockSymbol,
    SystemSetting,
)
from app.services.decision_service import evaluate_decision
from app.services.market_service import build_mock_quote
from app.services.sentiment_service import run_demo_sentiment_analysis
from app.services.setting_service import DEFAULT_SETTINGS


def _ensure_symbol(symbol, name):
    with db.session.no_autoflush:
        existing = StockSymbol.query.filter_by(symbol=symbol).first()
    if existing is None:
        db.session.add(StockSymbol(symbol=symbol, name=name))


def seed_project_data():
    _ensure_symbol('000001.SZ', '平安银行')
    _ensure_symbol('600519.SH', '贵州茅台')
    _ensure_symbol('300750.SZ', '宁德时代')
    _ensure_symbol('601318.SH', '中国平安')

    for key, value in DEFAULT_SETTINGS.items():
        with db.session.no_autoflush:
            exists = SystemSetting.query.filter_by(setting_key=key).first()
        if exists is None:
            setting = SystemSetting(setting_key=key)
            setting.set_value(value)
            db.session.add(setting)

    seed_sentiments = [
        {
            'title': '贵州茅台发布年报，利润同比增长',
            'content': '公司披露年报显示盈利继续增长，机构看多情绪回暖，市场普遍认为属于利好消息。',
            'source_type': 'company_announcement',
            'symbol': '600519.SH',
            'published_at': datetime(2026, 3, 20, 9, 30, 0),
        },
        {
            'title': '新能源板块承压，部分龙头股出现回调',
            'content': '行业短期走势承压，市场担忧需求下滑和估值风险，投资者情绪偏谨慎。',
            'source_type': 'financial_news',
            'symbol': '300750.SZ',
            'published_at': datetime(2026, 3, 21, 14, 0, 0),
        },
        {
            'title': '政策文件强调稳增长，银行板块获提振',
            'content': '最新政策提出稳增长目标，银行信贷环境改善，被视为板块利好。',
            'source_type': 'policy_document',
            'symbol': '000001.SZ',
            'published_at': datetime(2026, 3, 22, 10, 15, 0),
        },
    ]
    for item in seed_sentiments:
        with db.session.no_autoflush:
            exists = SentimentAnalysisRecord.query.filter_by(title=item['title'], symbol=item['symbol']).first()
        if exists is not None:
            continue
        demo = run_demo_sentiment_analysis(item['title'], item['content'], item['source_type'])
        record = SentimentAnalysisRecord(
            title=item['title'],
            content=item['content'],
            source_type=item['source_type'],
            symbol=item['symbol'],
            published_at=item['published_at'],
            sentiment=demo['sentiment'],
            summary=demo['summary'],
            risk_notes=demo['riskNotes'],
            raw_response=demo['rawResponse'],
            confidence=demo['confidence'],
        )
        record.set_keywords(demo['keywords'])
        db.session.add(record)

    for symbol in ('600519.SH', '300750.SZ', '000001.SZ'):
        with db.session.no_autoflush:
            exists = MarketAnalysisRecord.query.filter_by(symbol=symbol, range_type='3m').first()
        if exists is not None:
            continue
        payload = build_mock_quote(symbol, range_type='3m', indicators=['ma5', 'ma10', 'rsi', 'macd', 'volume'])
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

    sentiment_record = SentimentAnalysisRecord.query.order_by(SentimentAnalysisRecord.id.asc()).first()
    market_record = MarketAnalysisRecord.query.filter_by(symbol=sentiment_record.symbol).first() if sentiment_record else None
    with db.session.no_autoflush:
        exists = DecisionSuggestionRecord.query.first()
    if exists is None and sentiment_record and market_record:
        summary = market_record.get_summary()
        result = evaluate_decision(
            sentiment=sentiment_record.sentiment,
            price=summary.get('price') or 0,
            ma5=summary.get('ma5') or 0,
            rsi=summary.get('rsi') or 50,
        )
        decision_record = DecisionSuggestionRecord(
            symbol=sentiment_record.symbol,
            sentiment_record_id=sentiment_record.id,
            market_record_id=market_record.id,
            sentiment=sentiment_record.sentiment,
            price=summary.get('price') or 0,
            ma5=summary.get('ma5') or 0,
            rsi=summary.get('rsi') or 50,
            decision=result['decision'],
            reason_text=result['reasonText'],
            deepseek_placeholder=result['deepseekPlaceholder']['message'],
        )
        decision_record.set_matched_rules(result['matchedRules'])
        db.session.add(decision_record)
        db.session.commit()
