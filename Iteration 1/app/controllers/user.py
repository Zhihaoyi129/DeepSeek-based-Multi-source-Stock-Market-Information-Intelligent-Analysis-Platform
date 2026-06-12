from flask import Blueprint

from utils.api import success_api
from utils.mock_api import ALL_METHODS, build_user_info, get_current_mock_user, require_mock_auth

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/info', methods=ALL_METHODS)
@require_mock_auth
def info():
    return success_api(data=build_user_info(get_current_mock_user()))
