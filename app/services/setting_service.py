from __future__ import annotations

from app import db
from app.models.stock_analysis import SystemSetting

DEFAULT_SETTINGS = {
    'deepseek': {
        'enabled': False,
        'baseUrl': 'https://api.deepseek.com',
        'apiKey': '',
        'modelName': 'deepseek-chat',
        'timeout': 30,
        'remark': 'DeepSeek Chat 接口待启用',
    },
    'market_source': {
        'provider': 'tushare',
        'token': '',
        'remark': '固定使用 Tushare 获取真实行情数据',
    },
}


def get_setting(key):
    record = SystemSetting.query.filter_by(setting_key=key).first()
    if record is None:
        return dict(DEFAULT_SETTINGS.get(key, {}))
    return record.get_value()


def save_setting(key, value):
    record = SystemSetting.query.filter_by(setting_key=key).first()
    if record is None:
        record = SystemSetting(setting_key=key)
        db.session.add(record)
    record.set_value(value)
    db.session.commit()
    return record.get_value()


def get_public_settings():
    deepseek = get_setting('deepseek')
    market_source = get_setting('market_source')
    api_key = (deepseek.get('apiKey') or '').strip()
    api_key_source = '数据库' if api_key else '未配置'
    return {
        'deepseek': {
            'enabled': bool(deepseek.get('enabled')),
            'baseUrl': deepseek.get('baseUrl', ''),
            'modelName': deepseek.get('modelName', ''),
            'timeout': _parse_positive_int(deepseek.get('timeout'), 30),
            'remark': deepseek.get('remark', ''),
            'hasApiKey': bool(api_key),
            'apiKeyPreview': _mask_secret(api_key) or '未配置',
            'apiKeySource': api_key_source,
        },
        'marketSource': {
            'provider': 'tushare',
            'remark': market_source.get('remark', ''),
            'hasToken': bool(market_source.get('token')),
            'tokenPreview': _mask_secret(market_source.get('token', '')),
        },
    }


def _mask_secret(value):
    value = value or ''
    if len(value) <= 6:
        return '*' * len(value)
    return f'{value[:3]}***{value[-3:]}'


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
