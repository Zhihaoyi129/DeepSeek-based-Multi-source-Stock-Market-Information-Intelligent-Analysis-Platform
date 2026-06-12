from flask import Blueprint, make_response, request

from utils.api import error_api, success_api
from utils.mock_api import (
    ALL_METHODS,
    build_login_payload,
    get_current_mock_user,
    get_mock_user,
    get_mock_user_from_refresh_token,
    require_mock_auth,
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_api(
            'BadRequestException',
            error='Username and password are required',
            status_code=400,
        )

    user = get_mock_user(username)
    if user and user['password'] == password:
        response = make_response(success_api(data=build_login_payload(user))[0])
        response.set_cookie('jwt', user['refreshToken'])
        return response

    return error_api(
        'Username or password is incorrect.',
        error='Username or password is incorrect.',
        status_code=403,
    )


@bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(success_api(data='')[0])
    response.delete_cookie('jwt')
    return response


@bp.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.cookies.get('jwt')
    user = get_mock_user_from_refresh_token(refresh_token)
    if user is None:
        return error_api(
            'Forbidden Exception',
            error='Forbidden Exception',
            status_code=403,
        )

    response = make_response(user['accessToken'])
    response.mimetype = 'text/plain'
    response.delete_cookie('jwt')
    response.set_cookie('jwt', user['refreshToken'])
    return response


@bp.route('/codes', methods=ALL_METHODS)
@require_mock_auth
def get_codes():
    user = get_current_mock_user()
    return success_api(data=user['codes'])
