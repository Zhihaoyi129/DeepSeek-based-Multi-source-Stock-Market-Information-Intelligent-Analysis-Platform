from __future__ import annotations

import json

from flask import Blueprint, request

from app import db
from app.models.stock_analysis import DecisionSuggestionRecord
from app.services.deepseek_service import AIServiceError
from app.services.decision_service import evaluate_decision, resolve_market_metrics, resolve_sentiment
from app.services.market_service import normalize_symbol
from utils.api import error_api, get_json_payload, success_api, table_api

bp = Blueprint('project_decision_api', __name__, url_prefix='/api/decision')


@bp.route('/generate', methods=['POST'])
def generate_decision():
    data = get_json_payload()
    symbol = normalize_symbol(data.get('symbol'))
    if not symbol:
        return error_api('Bad Request', error='股票代码不能为空', status_code=400)

    try:
        sentiment, sentiment_record = resolve_sentiment(
            sentiment_record_id=data.get('sentiment_record_id'),
            manual_sentiment=(data.get('sentiment') or '').strip().lower() or None,
        )
        market_metrics = resolve_market_metrics(
            market_record_id=data.get('market_record_id'),
            price=data.get('price'),
            ma5=data.get('ma5'),
            rsi=data.get('rsi'),
        )
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)

    try:
        result = evaluate_decision(
            sentiment=sentiment,
            price=market_metrics['price'],
            ma5=market_metrics['ma5'],
            rsi=market_metrics['rsi'],
        )
    except AIServiceError as exc:
        return error_api('DeepSeek 决策建议失败', error=str(exc), status_code=400)
    record = DecisionSuggestionRecord(
        symbol=symbol,
        sentiment_record_id=sentiment_record.id if sentiment_record else None,
        market_record_id=market_metrics['marketRecord'].id if market_metrics['marketRecord'] else None,
        sentiment=sentiment,
        price=market_metrics['price'],
        ma5=market_metrics['ma5'],
        rsi=market_metrics['rsi'],
        decision=result['decision'],
        reason_text=result['reasonText'],
        deepseek_placeholder=json.dumps(result['deepseekPlaceholder'], ensure_ascii=False),
    )
    record.set_matched_rules(result['matchedRules'])
    db.session.add(record)
    db.session.commit()
    return success_api(msg='决策建议已生成', data=record.to_dict())


@bp.route('/history')
def decision_history():
    page = max(request.args.get('page', default=1, type=int), 1)
    page_size = max(request.args.get('page_size', default=10, type=int), 1)
    symbol = normalize_symbol(request.args.get('symbol'))

    query = DecisionSuggestionRecord.query.order_by(DecisionSuggestionRecord.created_at.desc())
    if symbol:
        query = query.filter_by(symbol=symbol)
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    items = [record.to_dict() for record in pagination.items]
    return table_api(items, total=pagination.total)


@bp.route('/<int:record_id>')
def decision_detail(record_id):
    record = DecisionSuggestionRecord.query.get(record_id)
    if record is None:
        return error_api('Not Found', error='决策记录不存在', status_code=404)
    return success_api(data=record.to_dict())
