from __future__ import annotations

from app import db
from app.models.stock_analysis import SystemSetting

DEFAULT_SETTINGS = {
    'deepseek': {
        'enabled': False,
        'baseUrl': '',
        'apiKey': '',
        'modelName': '',
        'remark': 'DeepSeek integration pending',
    },
    'market_source': {
        'provider': 'mock',
        'token': '',
        'remark': '行情接口待接入，可后续切换为 AKShare 或 Tushare',
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
    return {
        'deepseek': {
            'enabled': bool(deepseek.get('enabled')),
            'baseUrl': deepseek.get('baseUrl', ''),
            'modelName': deepseek.get('modelName', ''),
            'remark': deepseek.get('remark', ''),
            'hasApiKey': bool(deepseek.get('apiKey')),
            'apiKeyPreview': _mask_secret(deepseek.get('apiKey', '')),
        },
        'marketSource': {
            'provider': market_source.get('provider', 'mock'),
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
