from flask import Blueprint, request

from utils.api import success_api, table_api
from utils.mock_api import (
    ALL_METHODS,
    MOCK_DEPTS,
    MOCK_MENU_LIST,
    MOCK_ROLE_ITEMS,
    require_mock_auth,
    system_write_guard,
)

bp = Blueprint('system', __name__, url_prefix='/system')


@bp.before_request
def block_write_methods():
    return system_write_guard()


@bp.route('/menu/list', methods=ALL_METHODS)
@require_mock_auth
def menu_list():
    return success_api(data=MOCK_MENU_LIST)


@bp.route('/menu/name-exists', methods=ALL_METHODS)
@require_mock_auth
def menu_name_exists():
    name = request.args.get('name', '')
    current_id = str(request.args.get('id', ''))
    matched = next((item for item in MOCK_MENU_LIST if item['name'] == name), None)
    exists = matched is not None and (not current_id or str(matched['id']) != current_id)
    return success_api(data=exists)


@bp.route('/menu/path-exists', methods=ALL_METHODS)
@require_mock_auth
def menu_path_exists():
    path = request.args.get('path', '')
    current_id = str(request.args.get('id', ''))
    matched = next((item for item in MOCK_MENU_LIST if item['path'] == path), None)
    exists = matched is not None and (not current_id or str(matched['id']) != current_id)
    return success_api(data=exists)


@bp.route('/dept/list', methods=ALL_METHODS)
@require_mock_auth
def dept_list():
    return success_api(data=MOCK_DEPTS)


@bp.route('/dept/<dept_id>', methods=['PUT'])
@require_mock_auth
def update_dept(dept_id):
    _ = dept_id
    _ = request.get_json(silent=True) or {}
    return success_api(data=None)


@bp.route('/dept/<dept_id>', methods=['DELETE'])
@require_mock_auth
def delete_dept(dept_id):
    _ = dept_id
    return success_api(data=None)


@bp.route('/role/list', methods=ALL_METHODS)
@require_mock_auth
def role_list():
    _ = request.args.to_dict()
    return table_api(MOCK_ROLE_ITEMS, total=len(MOCK_ROLE_ITEMS))
