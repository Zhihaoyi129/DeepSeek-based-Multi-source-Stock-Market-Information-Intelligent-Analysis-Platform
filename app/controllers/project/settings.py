from flask import Blueprint, request

from app.models.stock_analysis import (
    AIChatRecord,
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    ScheduledTask,
    SentimentAnalysisRecord,
    StockNewsRecord,
    StockSymbol,
)
from app.services.setting_service import get_public_settings, save_setting
from app.services.setting_service import get_setting
from utils.api import error_api, get_json_payload, success_api

bp = Blueprint('project_settings_api', __name__, url_prefix='/api')


@bp.route('/settings')
def get_settings():
    return success_api(data=get_public_settings())


@bp.route('/settings/deepseek', methods=['PUT'])
def update_deepseek_settings():
    data = get_json_payload()
    current = get_setting('deepseek')
    api_key = (data.get('api_key') or '').strip()
    timeout_raw = data.get('timeout', 30)
    try:
        timeout = int(timeout_raw)
    except (TypeError, ValueError):
        return error_api('Bad Request', error='请求超时时间必须是正整数', status_code=400)
    if timeout <= 0:
        return error_api('Bad Request', error='请求超时时间必须是正整数', status_code=400)

    if data.get('clear_api_key'):
        saved_api_key = ''
    else:
        saved_api_key = api_key or current.get('apiKey', '')

    payload = {
        'enabled': bool(data.get('enabled')),
        'baseUrl': (data.get('base_url') or '').strip() or 'https://api.deepseek.com',
        'apiKey': saved_api_key,
        'modelName': (data.get('model_name') or '').strip() or 'deepseek-chat',
        'timeout': timeout,
        'remark': (data.get('remark') or 'DeepSeek Chat 接口已接入').strip(),
    }
    save_setting('deepseek', payload)
    return success_api(msg='DeepSeek 配置已保存', data=get_public_settings()['deepseek'])


@bp.route('/settings/market-source', methods=['PUT'])
def update_market_source_settings():
    data = get_json_payload()
    current = get_setting('market_source')
    token = (data.get('token') or '').strip()
    payload = {
        'provider': 'tushare',
        'token': token or current.get('token', ''),
        'remark': (data.get('remark') or '固定使用 Tushare 获取真实行情数据').strip(),
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
            'aiChatRecords': AIChatRecord.query.count(),
            'newsRecords': StockNewsRecord.query.count(),
            'tasks': ScheduledTask.query.count(),
        },
    })
