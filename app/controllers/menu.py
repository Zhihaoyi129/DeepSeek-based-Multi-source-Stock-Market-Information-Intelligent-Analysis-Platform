from flask import Blueprint

from utils.api import success_api
from utils.mock_api import ALL_METHODS, MOCK_MENUS, get_current_mock_user, require_mock_auth

bp = Blueprint('menu', __name__, url_prefix='/menu')


@bp.route('/all', methods=ALL_METHODS)
@require_mock_auth
def all_menu():
    user = get_current_mock_user()
    return success_api(data=MOCK_MENUS.get(user['username'], []))
