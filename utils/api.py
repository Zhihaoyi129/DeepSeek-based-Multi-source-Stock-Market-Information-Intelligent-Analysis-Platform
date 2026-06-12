import json

from flask import jsonify, request


def get_json_payload():
    payload = request.get_json(silent=True) or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return {}
    return payload if isinstance(payload, dict) else {}


def success_api(msg='ok', data=None, status_code=200):
    return jsonify({
        'code': 0,
        'data': data,
        'error': None,
        'message': msg,
    }), status_code


def error_api(msg='操作失败', error=None, status_code=400, code=-1):
    return jsonify({
        'code': code,
        'data': None,
        'error': error if error is not None else msg,
        'message': msg,
    }), status_code


def table_api(data, total, msg='ok', status_code=200):
    return jsonify({
        'code': 0,
        'data': {
            'items': data,
            'total': total,
        },
        'error': None,
        'message': msg,
    }), status_code
