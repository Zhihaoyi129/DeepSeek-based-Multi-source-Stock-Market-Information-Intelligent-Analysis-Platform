from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from app import db
from app.models.stock_analysis import MarketAnalysisRecord
from app.services.market_service import build_tushare_quote, normalize_indicators, normalize_symbol
from app.services.symbol_service import ensure_symbol
from utils.api import error_api, success_api, table_api

bp = Blueprint('project_market_api', __name__, url_prefix='/api/market')


def _ensure_symbol(symbol):
    normalized = normalize_symbol(symbol)
    if not normalized:
        raise ValueError('股票代码不能为空')
    ensure_symbol(normalized)
    return normalized


def _resolve_indicators():
    values = request.args.getlist('indicators')
    if not values:
        raw = (request.args.get('indicators') or '').strip()
        if raw:
            values = [item.strip() for item in raw.split(',') if item.strip()]
    return normalize_indicators(values)


def _find_existing_record(symbol, range_type, start_date, end_date, indicators, source):
    record = (
        MarketAnalysisRecord.query
        .filter_by(symbol=symbol, range_type=range_type, source_name=source)
        .order_by(MarketAnalysisRecord.created_at.desc())
        .first()
    )
    if record is None:
        return None
    if record.start_date.isoformat() != start_date or record.end_date.isoformat() != end_date:
        return None
    if record.get_indicator_config() != indicators:
        return None
    return record


@bp.route('/quote')
def market_quote():
    try:
        symbol = _ensure_symbol(request.args.get('symbol'))
        payload = build_tushare_quote(
            symbol=symbol,
            range_type=request.args.get('range', default='3m', type=str),
            start_date=request.args.get('start_date'),
            end_date=request.args.get('end_date'),
            indicators=_resolve_indicators(),
        )
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)

    existing = _find_existing_record(
        symbol=payload['symbol'],
        range_type=payload['rangeType'],
        start_date=payload['startDate'],
        end_date=payload['endDate'],
        indicators=payload['indicators'],
        source=payload['sourceName'],
    )
    if existing is None:
        existing = MarketAnalysisRecord(
            symbol=payload['symbol'],
            range_type=payload['rangeType'],
            start_date=datetime.strptime(payload['startDate'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(payload['endDate'], '%Y-%m-%d').date(),
            source_name=payload['sourceName'],
        )
        existing.set_indicator_config(payload['indicators'])
        existing.set_price_series(payload['priceSeries'])
        existing.set_indicator_result(payload['indicatorResult'])
        existing.set_summary(payload['summary'])
        db.session.add(existing)
        db.session.commit()

    return success_api(data=existing.to_dict())


@bp.route('/history')
def market_history():
    page = max(request.args.get('page', default=1, type=int), 1)
    page_size = max(request.args.get('page_size', default=10, type=int), 1)
    symbol = normalize_symbol(request.args.get('symbol'))

    query = MarketAnalysisRecord.query.order_by(MarketAnalysisRecord.created_at.desc())
    if symbol:
        query = query.filter_by(symbol=symbol)
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    items = [record.to_dict() for record in pagination.items]
    return table_api(items, total=pagination.total)


@bp.route('/<int:record_id>')
def market_detail(record_id):
    record = MarketAnalysisRecord.query.get(record_id)
    if record is None:
        return error_api('Not Found', error='技术分析记录不存在', status_code=404)
    return success_api(data=record.to_dict())
