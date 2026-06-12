from __future__ import annotations

from flask import Blueprint

from app.services.deepseek_service import AIServiceError
from app.services.past_analysis_service import analyze_past
from utils.api import error_api, get_json_payload, success_api

bp = Blueprint('project_past_analysis_api', __name__, url_prefix='/api/past-analysis')


@bp.route('/analyze', methods=['POST'])
def past_analysis_analyze():
    data = get_json_payload()
    try:
        payload = analyze_past(
            symbol=data.get('symbol'),
            range_type=data.get('range') or data.get('range_type') or '3m',
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
        )
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    except AIServiceError as exc:
        return error_api('DeepSeek 归因分析失败', error=str(exc), status_code=400)
    return success_api(msg='过往分析已生成', data=payload)
