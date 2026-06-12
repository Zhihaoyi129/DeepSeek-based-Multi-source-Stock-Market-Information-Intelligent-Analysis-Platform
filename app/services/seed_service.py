from __future__ import annotations

from datetime import datetime

from app import db
from app.models.stock_analysis import (
    SentimentAnalysisRecord,
    SystemSetting,
)
from app.services.sentiment_service import run_demo_sentiment_analysis
from app.services.setting_service import DEFAULT_SETTINGS
from app.services.symbol_service import ensure_default_symbols


def seed_project_data():
    ensure_default_symbols()

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

    db.session.commit()

    from app.services.task_service import ensure_default_tasks
    ensure_default_tasks()
