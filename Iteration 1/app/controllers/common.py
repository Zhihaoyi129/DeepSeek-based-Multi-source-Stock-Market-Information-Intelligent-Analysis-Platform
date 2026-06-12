from flask import Blueprint, Response, request

from utils.api import error_api, success_api, table_api
from utils.mock_api import ALL_METHODS, MOCK_TABLE_ITEMS, bigint_response, require_mock_auth

bp = Blueprint('common', __name__, url_prefix='/')


@bp.route('/upload', methods=ALL_METHODS)
@require_mock_auth
def upload():
    _ = request.files
    _ = request.form.to_dict()
    return success_api(data={
        'url': 'https://unpkg.com/@vbenjs/static-source@0.1.7/source/logo-v1.webp'
    })


@bp.route('/table/list', methods=ALL_METHODS)
@require_mock_auth
def table_list():
    _ = request.args.to_dict(flat=False)
    return table_api(MOCK_TABLE_ITEMS, total=100)


@bp.route('/demo/bigint', methods=ALL_METHODS)
@require_mock_auth
def demo_bigint():
    return bigint_response()


@bp.route('/status', methods=ALL_METHODS)
def status():
    status_value = request.args.get('status')
    try:
        status_code = int(status_value)
    except (TypeError, ValueError):
        status_code = 400
    return error_api(str(status_value), error=None, status_code=status_code)


@bp.route('/test', methods=['GET'])
def test_get():
    return Response('"Test get handler"', mimetype='application/json')


@bp.route('/test', methods=['POST'])
def test_post():
    return Response('"Test post handler"', mimetype='application/json')
