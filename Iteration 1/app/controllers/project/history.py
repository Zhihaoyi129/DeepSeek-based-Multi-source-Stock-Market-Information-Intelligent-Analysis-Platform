from flask import Blueprint, request

from app.services.history_service import collect_history_items, get_history_detail
from utils.api import error_api, success_api, table_api

bp = Blueprint('project_history_api', __name__, url_prefix='/api/history')


@bp.route('/list')
def history_list():
    page = max(request.args.get('page', default=1, type=int), 1)
    page_size = max(request.args.get('page_size', default=10, type=int), 1)

    try:
        items = collect_history_items(
            module=request.args.get('module'),
            symbol=request.args.get('symbol'),
            status=request.args.get('status'),
            start_date=request.args.get('start_date'),
            end_date=request.args.get('end_date'),
        )
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)

    start_index = (page - 1) * page_size
    paged_items = items[start_index:start_index + page_size]
    return table_api(paged_items, total=len(items))


@bp.route('/detail')
def history_detail():
    module = request.args.get('module')
    record_id = request.args.get('id', type=int)
    if not module or not record_id:
        return error_api('Bad Request', error='module 和 id 不能为空', status_code=400)

    payload = get_history_detail(module, record_id)
    if payload is None:
        return error_api('Not Found', error='记录不存在', status_code=404)
    return success_api(data=payload)
