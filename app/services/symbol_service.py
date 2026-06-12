from __future__ import annotations

from sqlalchemy import or_

from app import db
from app.models.stock_analysis import StockSymbol
from app.services.market_service import normalize_symbol

DEFAULT_STOCK_SYMBOLS = [
    ('600519.SH', '贵州茅台', 'A股'),
    ('000001.SZ', '平安银行', 'A股'),
    ('300750.SZ', '宁德时代', 'A股'),
    ('601318.SH', '中国平安', 'A股'),
    ('600036.SH', '招商银行', 'A股'),
    ('000858.SZ', '五粮液', 'A股'),
    ('600900.SH', '长江电力', 'A股'),
    ('601899.SH', '紫金矿业', 'A股'),
    ('002594.SZ', '比亚迪', 'A股'),
    ('300059.SZ', '东方财富', 'A股'),
    ('600276.SH', '恒瑞医药', 'A股'),
    ('601888.SH', '中国中免', 'A股'),
    ('688981.SH', '中芯国际', 'A股'),
    ('000333.SZ', '美的集团', 'A股'),
    ('600030.SH', '中信证券', 'A股'),
]


def ensure_default_symbols():
    for symbol, name, market in DEFAULT_STOCK_SYMBOLS:
        ensure_symbol(symbol, name=name, market=market)
    db.session.commit()


def ensure_symbol(symbol, name=None, market='A股'):
    normalized = normalize_symbol(symbol)
    if not normalized:
        raise ValueError('股票代码不能为空')
    with db.session.no_autoflush:
        record = StockSymbol.query.filter_by(symbol=normalized).first()
    if record is None:
        record = StockSymbol(
            symbol=normalized,
            name=(name or normalized).strip() or normalized,
            market=(market or 'A股').strip() or 'A股',
        )
        db.session.add(record)
    return record


def list_symbols(keyword=None):
    query = StockSymbol.query
    keyword = (keyword or '').strip()
    if keyword:
        pattern = f'%{keyword}%'
        query = query.filter(
            or_(
                StockSymbol.symbol.ilike(pattern),
                StockSymbol.name.ilike(pattern),
                StockSymbol.market.ilike(pattern),
            )
        )
    return query.order_by(StockSymbol.symbol.asc()).all()


def save_symbol(data, record=None):
    symbol = normalize_symbol(data.get('symbol'))
    name = (data.get('name') or '').strip()
    market = (data.get('market') or 'A股').strip() or 'A股'
    if not symbol:
        raise ValueError('股票代码不能为空')
    if not name:
        raise ValueError('股票名称不能为空')

    exists = StockSymbol.query.filter_by(symbol=symbol).first()
    if exists is not None and (record is None or exists.id != record.id):
        raise ValueError('股票代码已存在')

    record = record or StockSymbol()
    record.symbol = symbol
    record.name = name
    record.market = market
    db.session.add(record)
    db.session.commit()
    return record


def delete_symbol(record):
    db.session.delete(record)
    db.session.commit()
