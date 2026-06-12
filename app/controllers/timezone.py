from flask import Blueprint, current_app, request

from utils.api import error_api, success_api
from utils.mock_api import ALL_METHODS, ALLOWED_TIMEZONES, TIMEZONE_OPTIONS, require_mock_auth

bp = Blueprint('timezone', __name__, url_prefix='/timezone')


@bp.route('/getTimezone', methods=ALL_METHODS)
@require_mock_auth
def get_timezone():
    return success_api(data=current_app.config.get('CURRENT_TIMEZONE'))


@bp.route('/setTimezone', methods=ALL_METHODS)
@require_mock_auth
def set_timezone():
    data = request.get_json(silent=True) or {}
    timezone = data.get('timezone')
    if timezone not in ALLOWED_TIMEZONES:
        return error_api('Bad Request', error='Invalid timezone', status_code=400)

    current_app.config['CURRENT_TIMEZONE'] = timezone
    return success_api(data={})


@bp.route('/getTimezoneOptions', methods=ALL_METHODS)
def get_timezone_options():
    return success_api(data=TIMEZONE_OPTIONS)
