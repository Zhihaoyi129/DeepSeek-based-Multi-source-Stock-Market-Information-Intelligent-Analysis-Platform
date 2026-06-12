from flask import Blueprint, request

from app.models.stock_analysis import (
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    SentimentAnalysisRecord,
    StockSymbol,
)
from app.services.setting_service import get_public_settings, save_setting
from utils.api import error_api, success_api

bp = Blueprint('project_settings_api', __name__, url_prefix='/api')


@bp.route('/settings')
def get_settings():
    return success_api(data=get_public_settings())


@bp.route('/settings/deepseek', methods=['PUT'])
def update_deepseek_settings():
    data = request.get_json(silent=True) or {}
    payload = {
        'enabled': bool(data.get('enabled')),
        'baseUrl': (data.get('base_url') or '').strip(),
        'apiKey': (data.get('api_key') or '').strip(),
        'modelName': (data.get('model_name') or '').strip(),
        'remark': (data.get('remark') or 'DeepSeek integration pending').strip(),
    }
    save_setting('deepseek', payload)
    return success_api(msg='DeepSeek 配置已保存', data=get_public_settings()['deepseek'])


@bp.route('/settings/market-source', methods=['PUT'])
def update_market_source_settings():
    data = request.get_json(silent=True) or {}
    provider = (data.get('provider') or '').strip() or 'mock'
    if provider not in {'mock', 'akshare', 'tushare'}:
        return error_api('Bad Request', error='行情数据源无效', status_code=400)
    payload = {
        'provider': provider,
        'token': (data.get('token') or '').strip(),
        'remark': (data.get('remark') or '').strip(),
    }
    save_setting('market_source', payload)
    return success_api(msg='行情数据源配置已保存', data=get_public_settings()['marketSource'])


@bp.route('/system/status')
def system_status():
    settings = get_public_settings()
    return success_api(data={
        'database': 'ready',
        'deepseek': settings['deepseek'],
        'marketSource': settings['marketSource'],
        'statistics': {
            'symbols': StockSymbol.query.count(),
            'sentimentRecords': SentimentAnalysisRecord.query.count(),
            'marketRecords': MarketAnalysisRecord.query.count(),
            'decisionRecords': DecisionSuggestionRecord.query.count(),
        },
    })
