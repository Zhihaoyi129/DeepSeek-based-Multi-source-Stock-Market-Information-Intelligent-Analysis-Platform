from functools import wraps

from flask import Response, g, request

from utils.api import error_api

ALL_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

MOCK_USERS = {
    'vben': {
        'id': 0,
        'username': 'vben',
        'password': '123456',
        'realName': 'Vben',
        'roles': ['super'],
        'homePath': '/workspace',
        'accessToken': 'access-token-vben',
        'refreshToken': 'refresh-token-vben',
        'codes': ['AC_100100', 'AC_100110', 'AC_100120', 'AC_100010'],
    },
    'admin': {
        'id': 1,
        'username': 'admin',
        'password': '123456',
        'realName': 'Admin',
        'roles': ['admin'],
        'homePath': '/workspace',
        'accessToken': 'access-token-admin',
        'refreshToken': 'refresh-token-admin',
        'codes': ['AC_100010', 'AC_100020', 'AC_100030'],
    },
    'jack': {
        'id': 2,
        'username': 'jack',
        'password': '123456',
        'realName': 'Jack',
        'roles': ['user'],
        'homePath': '/dashboard',
        'accessToken': 'access-token-jack',
        'refreshToken': 'refresh-token-jack',
        'codes': ['AC_1000001', 'AC_1000002'],
    },
}

TOKEN_TO_USER = {user['accessToken']: user for user in MOCK_USERS.values()}
REFRESH_TOKEN_TO_USER = {user['refreshToken']: user for user in MOCK_USERS.values()}

MOCK_MENUS = {
    'vben': [
        {'name': 'Dashboard', 'path': '/dashboard', 'redirect': '/analytics', 'children': []},
        {'name': 'Access', 'path': '/demos/access', 'redirect': '/demos/access/frontend-visible', 'children': []},
    ],
    'admin': [
        {'name': 'Workspace', 'path': '/workspace', 'redirect': '/workspace', 'children': []},
    ],
    'jack': [
        {'name': 'Dashboard', 'path': '/dashboard', 'redirect': '/overview', 'children': []},
    ],
}

MOCK_MENU_LIST = [
    {
        'id': 1,
        'pid': 0,
        'name': 'Workspace',
        'path': '/workspace',
        'type': 'menu',
        'status': 1,
        'component': '/workspace/index',
        'authCode': 'AC_100010',
        'meta': {'title': 'Workspace'},
        'children': [
            {
                'id': 2,
                'pid': 1,
                'name': 'Analytics',
                'path': '/analytics',
                'type': 'menu',
                'status': 1,
            }
        ],
    },
    {
        'id': 201,
        'pid': 0,
        'name': 'System',
        'path': '/system',
        'type': 'menu',
        'status': 1,
    },
]

MOCK_DEPTS = [
    {
        'id': 'dept-root',
        'pid': 0,
        'name': 'Books',
        'status': 1,
        'createTime': '2023/01/01 12:00:00',
        'remark': 'root dept',
        'children': [
            {
                'id': 'dept-child',
                'pid': 'dept-root',
                'name': 'Tech',
                'status': 1,
                'createTime': '2023/01/02 12:00:00',
                'remark': 'child dept',
            }
        ],
    }
]

MOCK_ROLE_ITEMS = [
    {
        'id': 'role-admin',
        'name': 'Product',
        'status': 1,
        'createTime': '2024/01/01 12:00:00',
        'permissions': [1, 2, 201],
        'remark': 'mock role',
    },
    {
        'id': 'role-user',
        'name': 'Support',
        'status': 0,
        'createTime': '2024/01/02 12:00:00',
        'permissions': [1],
        'remark': 'mock role 2',
    },
]

TIMEZONE_OPTIONS = [
    {'label': 'America/New_York (GMT-5)', 'value': 'America/New_York'},
    {'label': 'Europe/London (GMT+0)', 'value': 'Europe/London'},
    {'label': 'Asia/Shanghai (GMT+8)', 'value': 'Asia/Shanghai'},
    {'label': 'Asia/Tokyo (GMT+9)', 'value': 'Asia/Tokyo'},
    {'label': 'Asia/Seoul (GMT+9)', 'value': 'Asia/Seoul'},
]

ALLOWED_TIMEZONES = [item['value'] for item in TIMEZONE_OPTIONS]

MOCK_TABLE_ITEMS = [
    {
        'id': 'table-1',
        'imageUrl': 'https://example.com/image-1.webp',
        'imageUrl2': 'https://example.com/image-2.webp',
        'open': True,
        'status': 'success',
        'productName': 'Product A',
        'price': '123.00',
        'currency': 'USD',
        'quantity': 10,
        'available': True,
        'category': 'Books',
        'releaseDate': '2024-01-01T00:00:00.000Z',
        'rating': 4.5,
        'description': 'mock item',
        'weight': 1.2,
        'color': 'red',
        'inProduction': False,
        'tags': ['Small', 'Practical', 'Modern'],
    },
    {
        'id': 'table-2',
        'imageUrl': 'https://example.com/image-3.webp',
        'imageUrl2': 'https://example.com/image-4.webp',
        'open': False,
        'status': 'warning',
        'productName': 'Product B',
        'price': '456.00',
        'currency': 'CNY',
        'quantity': 20,
        'available': True,
        'category': 'Tech',
        'releaseDate': '2024-02-01T00:00:00.000Z',
        'rating': 4.8,
        'description': 'mock item 2',
        'weight': 2.2,
        'color': 'blue',
        'inProduction': True,
        'tags': ['Large', 'Durable'],
    },
]


def get_mock_user(username):
    return MOCK_USERS.get(username)


def get_mock_user_from_token(token):
    return TOKEN_TO_USER.get(token)


def get_mock_user_from_refresh_token(refresh_token):
    return REFRESH_TOKEN_TO_USER.get(refresh_token)


def build_login_payload(user):
    return {
        'id': user['id'],
        'password': user['password'],
        'realName': user['realName'],
        'roles': user['roles'],
        'username': user['username'],
        'homePath': user['homePath'],
        'accessToken': user['accessToken'],
    }


def build_user_info(user):
    return {
        'id': user['id'],
        'realName': user['realName'],
        'roles': user['roles'],
        'username': user['username'],
        'homePath': user['homePath'],
    }


def parse_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    prefix = 'Bearer '
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix):].strip()


def require_mock_auth(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = parse_bearer_token()
        user = get_mock_user_from_token(token)
        if user is None:
            return error_api(
                'Unauthorized Exception',
                error='Unauthorized Exception',
                status_code=401,
            )
        g.current_mock_user = user
        return view_func(*args, **kwargs)

    return wrapper


def get_current_mock_user():
    return getattr(g, 'current_mock_user', None)


def system_write_guard():
    if request.method in {'DELETE', 'PATCH', 'POST', 'PUT'}:
        return error_api(
            '演示环境，禁止修改',
            error='演示环境，禁止修改',
            status_code=403,
        )
    return None


def bigint_response():
    payload = (
        '{"code":0,"message":"success","data":['
        '{"id":123456789012345678901234567890123456789012345678901234567890,'
        '"name":"John Doe","age":30,"email":"john-doe@demo.com"},'
        '{"id":987654321098765432109876543210987654321098765432109876543210,'
        '"name":"Jane Smith","age":25,"email":"jane@demo.com"}'
        ']}'
    )
    return Response(payload, mimetype='application/json')

