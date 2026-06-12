from flask import Blueprint

from app.models.stock_analysis import (
    AIChatRecord,
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    ScheduledTask,
    SentimentAnalysisRecord,
    StockNewsRecord,
    StockSymbol,
)
from app.services.history_service import collect_history_items
from app.services.setting_service import get_public_settings
from utils.api import success_api

bp = Blueprint('project_dashboard_api', __name__, url_prefix='/api/dashboard')


@bp.route('/state')
def dashboard_state():
    recent_records = collect_history_items()[:8]
    return success_api(data={
        'stats': {
            'sentimentCount': SentimentAnalysisRecord.query.count(),
            'marketCount': MarketAnalysisRecord.query.count(),
            'decisionCount': DecisionSuggestionRecord.query.count(),
            'symbolCount': StockSymbol.query.count(),
            'aiChatCount': AIChatRecord.query.count(),
            'newsCount': StockNewsRecord.query.count(),
            'taskCount': ScheduledTask.query.count(),
        },
        'recentRecords': recent_records,
        'systemStatus': {
            **get_public_settings(),
            'database': 'ready',
        },
    })
