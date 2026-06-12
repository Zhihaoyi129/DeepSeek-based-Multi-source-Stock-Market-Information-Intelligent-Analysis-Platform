from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from app import db

LOCAL_TIMEZONE = timezone(timedelta(hours=8))


def _dump_json(value):
    return json.dumps(value, ensure_ascii=False)


def _load_json(value, fallback):
    if not value:
        return deepcopy(fallback)
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return deepcopy(fallback)


def _format_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def _current_local_datetime():
    return datetime.now(LOCAL_TIMEZONE).replace(tzinfo=None)


class StockSymbol(db.Model):
    __tablename__ = 'stock_symbol'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    market = db.Column(db.String(20), nullable=False, default='A股')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'market': self.market,
            'createdAt': _format_datetime(self.created_at),
        }


class SentimentAnalysisRecord(db.Model):
    __tablename__ = 'sentiment_analysis_record'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    sentiment = db.Column(db.String(20), nullable=False, default='neutral')
    summary = db.Column(db.Text, nullable=True)
    keywords_json = db.Column(db.Text, nullable=False, default='[]')
    risk_notes = db.Column(db.Text, nullable=True)
    raw_response = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='completed')
    analysis_mode = db.Column(db.String(20), nullable=False, default='local-demo')
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_keywords(self, value):
        self.keywords_json = _dump_json(value or [])

    def get_keywords(self):
        return _load_json(self.keywords_json, [])

    def to_dict(self, include_content=True):
        payload = {
            'id': self.id,
            'title': self.title,
            'sourceType': self.source_type,
            'symbol': self.symbol,
            'publishedAt': _format_datetime(self.published_at),
            'sentiment': self.sentiment,
            'summary': self.summary,
            'keywords': self.get_keywords(),
            'riskNotes': self.risk_notes,
            'rawResponse': self.raw_response,
            'status': self.status,
            'analysisMode': self.analysis_mode,
            'confidence': self.confidence,
            'createdAt': _format_datetime(self.created_at),
        }
        if include_content:
            payload['content'] = self.content
        return payload


class MarketAnalysisRecord(db.Model):
    __tablename__ = 'market_analysis_record'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    range_type = db.Column(db.String(20), nullable=False, default='3m')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    indicator_config_json = db.Column(db.Text, nullable=False, default='[]')
    source_name = db.Column(db.String(50), nullable=False, default='mock')
    price_series_json = db.Column(db.Text, nullable=False)
    indicator_result_json = db.Column(db.Text, nullable=False)
    summary_json = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='completed')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_indicator_config(self, value):
        self.indicator_config_json = _dump_json(value or [])

    def get_indicator_config(self):
        return _load_json(self.indicator_config_json, [])

    def set_price_series(self, value):
        self.price_series_json = _dump_json(value or [])

    def get_price_series(self):
        return _load_json(self.price_series_json, [])

    def set_indicator_result(self, value):
        self.indicator_result_json = _dump_json(value or {})

    def get_indicator_result(self):
        return _load_json(self.indicator_result_json, {})

    def set_summary(self, value):
        self.summary_json = _dump_json(value or {})

    def get_summary(self):
        return _load_json(self.summary_json, {})

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'rangeType': self.range_type,
            'startDate': self.start_date.isoformat() if self.start_date else None,
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'indicatorConfig': self.get_indicator_config(),
            'sourceName': self.source_name,
            'priceSeries': self.get_price_series(),
            'indicatorResult': self.get_indicator_result(),
            'summary': self.get_summary(),
            'status': self.status,
            'createdAt': _format_datetime(self.created_at),
        }


class DecisionSuggestionRecord(db.Model):
    __tablename__ = 'decision_suggestion_record'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    sentiment_record_id = db.Column(db.Integer, db.ForeignKey('sentiment_analysis_record.id'), nullable=True)
    market_record_id = db.Column(db.Integer, db.ForeignKey('market_analysis_record.id'), nullable=True)
    sentiment = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ma5 = db.Column(db.Float, nullable=False)
    rsi = db.Column(db.Float, nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    matched_rules_json = db.Column(db.Text, nullable=False, default='[]')
    reason_text = db.Column(db.Text, nullable=False)
    deepseek_placeholder = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='completed')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sentiment_record = db.relationship('SentimentAnalysisRecord', lazy='joined', foreign_keys=[sentiment_record_id])
    market_record = db.relationship('MarketAnalysisRecord', lazy='joined', foreign_keys=[market_record_id])

    def set_matched_rules(self, value):
        self.matched_rules_json = _dump_json(value or [])

    def get_matched_rules(self):
        return _load_json(self.matched_rules_json, [])

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'sentimentRecordId': self.sentiment_record_id,
            'marketRecordId': self.market_record_id,
            'sentiment': self.sentiment,
            'price': self.price,
            'ma5': self.ma5,
            'rsi': self.rsi,
            'decision': self.decision,
            'matchedRules': self.get_matched_rules(),
            'reasonText': self.reason_text,
            'deepseekPlaceholder': self.deepseek_placeholder,
            'status': self.status,
            'createdAt': _format_datetime(self.created_at),
        }


class StockNewsRecord(db.Model):
    __tablename__ = 'stock_news_record'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(50), nullable=False, default='financial_news')
    symbol = db.Column(db.String(20), nullable=False, index=True)
    industry = db.Column(db.String(80), nullable=True)
    news_date = db.Column(db.Date, nullable=False, index=True)
    sentiment = db.Column(db.String(20), nullable=False, default='neutral')
    sentiment_score = db.Column(db.Float, nullable=False, default=0)
    summary = db.Column(db.Text, nullable=True)
    related_stocks_json = db.Column(db.Text, nullable=False, default='[]')
    raw_response = db.Column(db.Text, nullable=True)
    task_run_id = db.Column(db.Integer, db.ForeignKey('task_run_log.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_related_stocks(self, value):
        self.related_stocks_json = _dump_json(value or [])

    def get_related_stocks(self):
        return _load_json(self.related_stocks_json, [])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'sourceType': self.source_type,
            'symbol': self.symbol,
            'industry': self.industry,
            'newsDate': self.news_date.isoformat() if self.news_date else None,
            'sentiment': self.sentiment,
            'sentimentScore': self.sentiment_score,
            'summary': self.summary,
            'relatedStocks': self.get_related_stocks(),
            'createdAt': _format_datetime(self.created_at),
        }


class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_task'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    task_type = db.Column(db.String(50), nullable=False, default='auto_news')
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    frequency = db.Column(db.String(20), nullable=False, default='daily')
    run_time = db.Column(db.String(5), nullable=False, default='15:30')
    symbols_json = db.Column(db.Text, nullable=False, default='[]')
    content_preset = db.Column(db.String(80), nullable=False, default='post_market_news')
    remark = db.Column(db.Text, nullable=True)
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_symbols(self, value):
        self.symbols_json = _dump_json(value or [])

    def get_symbols(self):
        return _load_json(self.symbols_json, [])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'taskType': self.task_type,
            'enabled': self.enabled,
            'frequency': self.frequency,
            'runTime': self.run_time,
            'symbols': self.get_symbols(),
            'contentPreset': self.content_preset,
            'remark': self.remark,
            'lastRunAt': _format_datetime(self.last_run_at),
            'nextRunAt': _format_datetime(self.next_run_at),
            'createdAt': _format_datetime(self.created_at),
            'updatedAt': _format_datetime(self.updated_at),
        }


class TaskRunLog(db.Model):
    __tablename__ = 'task_run_log'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('scheduled_task.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='running')
    message = db.Column(db.Text, nullable=True)
    detail_json = db.Column(db.Text, nullable=False, default='{}')
    started_at = db.Column(db.DateTime, nullable=False, default=_current_local_datetime)
    finished_at = db.Column(db.DateTime, nullable=True)

    task = db.relationship('ScheduledTask', lazy='joined', foreign_keys=[task_id])

    def set_detail(self, value):
        self.detail_json = _dump_json(value or {})

    def get_detail(self):
        return _load_json(self.detail_json, {})

    def to_dict(self):
        return {
            'id': self.id,
            'taskId': self.task_id,
            'taskName': self.task.name if self.task else '',
            'status': self.status,
            'message': self.message,
            'detail': self.get_detail(),
            'startedAt': _format_datetime(self.started_at),
            'finishedAt': _format_datetime(self.finished_at),
        }


class AIChatRecord(db.Model):
    __tablename__ = 'ai_chat_record'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(80), nullable=False, default='deepseek-chat')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'modelName': self.model_name,
            'createdAt': _format_datetime(self.created_at),
        }


class SystemSetting(db.Model):
    __tablename__ = 'system_setting'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(120), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False, default='{}')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_value(self, value):
        self.setting_value = _dump_json(value or {})

    def get_value(self):
        return _load_json(self.setting_value, {})

    def to_dict(self):
        return {
            'id': self.id,
            'settingKey': self.setting_key,
            'settingValue': self.get_value(),
            'updatedAt': _format_datetime(self.updated_at),
        }
