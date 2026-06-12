from __future__ import annotations

from flask import Blueprint, request

from app.models.stock_analysis import StockSymbol
from app.services.symbol_service import delete_symbol, list_symbols, save_symbol
from utils.api import error_api, get_json_payload, success_api, table_api

bp = Blueprint('project_symbols_api', __name__, url_prefix='/api/symbols')


@bp.route('')
def symbols_list():
    keyword = request.args.get('keyword')
    rows = list_symbols(keyword)
    return table_api([row.to_dict() for row in rows], total=len(rows))


@bp.route('/options')
def symbol_options():
    keyword = request.args.get('keyword')
    limit = max(request.args.get('limit', default=80, type=int), 1)
    rows = list_symbols(keyword)[:limit]
    return success_api(data=[row.to_dict() for row in rows])


@bp.route('', methods=['POST'])
def symbols_create():
    try:
        record = save_symbol(get_json_payload())
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    return success_api(msg='常用股票已新增', data=record.to_dict())


@bp.route('/<int:symbol_id>', methods=['PUT'])
def symbols_update(symbol_id):
    record = StockSymbol.query.get(symbol_id)
    if record is None:
        return error_api('Not Found', error='常用股票不存在', status_code=404)
    try:
        record = save_symbol(get_json_payload(), record=record)
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    return success_api(msg='常用股票已保存', data=record.to_dict())


@bp.route('/<int:symbol_id>', methods=['DELETE'])
def symbols_delete(symbol_id):
    record = StockSymbol.query.get(symbol_id)
    if record is None:
        return error_api('Not Found', error='常用股票不存在', status_code=404)
    delete_symbol(record)
    return success_api(msg='常用股票已删除')
