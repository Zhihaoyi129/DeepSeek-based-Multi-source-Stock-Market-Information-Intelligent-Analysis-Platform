import json

from flask import Blueprint, Response, request, stream_with_context

from app import db
from app.models.stock_analysis import AIChatRecord
from app.services.deepseek_service import AIServiceError, chat_with_deepseek, stream_chat_with_deepseek
from utils.api import error_api, get_json_payload, success_api

bp = Blueprint('project_ai_api', __name__, url_prefix='/api/ai')


@bp.route('/chat', methods=['POST'])
def ai_chat():
    data = get_json_payload()
    message = (data.get('message') or '').strip()
    try:
        result = chat_with_deepseek(message)
    except AIServiceError as exc:
        return error_api('AI 对话失败', error=str(exc), status_code=400)

    record = AIChatRecord(
        question=message,
        answer=result['reply'],
        model_name=result['model'],
    )
    db.session.add(record)
    db.session.commit()
    payload = record.to_dict()
    payload['reply'] = record.answer
    return success_api(msg='AI 回复成功', data=payload)


@bp.route('/chat/stream', methods=['POST'])
def ai_chat_stream():
    data = get_json_payload()
    message = (data.get('message') or '').strip()

    def sse_event(event, payload):
        packet = json.dumps(payload, ensure_ascii=False)
        return f'event: {event}\ndata: {packet}\n\n'

    @stream_with_context
    def generate():
        reply_parts = []
        model = ''
        try:
            chunks, model = stream_chat_with_deepseek(message)
            for chunk in chunks:
                reply_parts.append(chunk)
                yield sse_event('delta', {'content': chunk})

            reply = ''.join(reply_parts).strip()
            saved = False
            if reply:
                record = AIChatRecord(question=message, answer=reply, model_name=model)
                db.session.add(record)
                db.session.commit()
                saved = True
            yield sse_event('done', {'model': model, 'saved': saved})
        except AIServiceError as exc:
            db.session.rollback()
            yield sse_event('error', {'message': str(exc)})

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


@bp.route('/history', methods=['GET', 'DELETE'])
def ai_history():
    if request.method == 'DELETE':
        AIChatRecord.query.delete()
        db.session.commit()
        return success_api(msg='AI 对话记录已清空')

    records = AIChatRecord.query.order_by(AIChatRecord.created_at.asc()).all()
    return success_api(data=[record.to_dict() for record in records])
