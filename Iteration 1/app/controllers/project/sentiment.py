from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from app import db
from app.models.stock_analysis import SentimentAnalysisRecord, StockSymbol
from app.services.deepseek_service import analyze_sentiment_with_deepseek
from app.services.sentiment_service import run_demo_sentiment_analysis
from utils.api import error_api, success_api, table_api

bp = Blueprint('project_sentiment_api', __name__, url_prefix='/api/sentiment')

SOURCE_TYPES = {
    'financial_news': '财经新闻',
    'policy_document': '政策文件',
    'company_announcement': '公司公告',
}


def _parse_datetime(value):
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError('发布时间格式无效')


def _ensure_symbol(symbol):
    symbol = (symbol or '').strip().upper()
    if not symbol:
        raise ValueError('股票代码不能为空')
    existing = StockSymbol.query.filter_by(symbol=symbol).first()
    if existing is None:
        db.session.add(StockSymbol(symbol=symbol, name=symbol))
    return symbol


@bp.route('/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    source_type = (data.get('source_type') or '').strip()

    try:
        symbol = _ensure_symbol(data.get('symbol'))
        published_at = _parse_datetime((data.get('published_at') or '').strip())
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)

    if not title:
        return error_api('Bad Request', error='标题不能为空', status_code=400)
    if not content:
        return error_api('Bad Request', error='正文不能为空', status_code=400)
    if source_type not in SOURCE_TYPES:
        return error_api('Bad Request', error='来源类型无效', status_code=400)

    demo_result = run_demo_sentiment_analysis(title, content, source_type)
    deepseek_placeholder = analyze_sentiment_with_deepseek(data)

    record = SentimentAnalysisRecord(
        title=title,
        content=content,
        source_type=source_type,
        symbol=symbol,
        published_at=published_at,
        sentiment=demo_result['sentiment'],
        summary=demo_result['summary'],
        risk_notes=demo_result['riskNotes'],
        raw_response=demo_result['rawResponse'],
        confidence=demo_result['confidence'],
    )
    record.set_keywords(demo_result['keywords'])
    db.session.add(record)
    db.session.commit()

    payload = record.to_dict()
    payload['deepseek'] = deepseek_placeholder
    payload['sourceTypeLabel'] = SOURCE_TYPES[source_type]
    return success_api(msg='情感分析已完成', data=payload)


@bp.route('/history')
def sentiment_history():
    page = max(request.args.get('page', default=1, type=int), 1)
    page_size = max(request.args.get('page_size', default=10, type=int), 1)
    symbol = (request.args.get('symbol') or '').strip().upper()

    query = SentimentAnalysisRecord.query.order_by(SentimentAnalysisRecord.created_at.desc())
    if symbol:
        query = query.filter_by(symbol=symbol)
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    items = [record.to_dict(include_content=False) for record in pagination.items]
    return table_api(items, total=pagination.total)


@bp.route('/<int:record_id>')
def sentiment_detail(record_id):
    record = SentimentAnalysisRecord.query.get(record_id)
    if record is None:
        return error_api('Not Found', error='情感分析记录不存在', status_code=404)
    payload = record.to_dict()
    payload['deepseek'] = analyze_sentiment_with_deepseek({'record_id': record_id})
    return success_api(data=payload)
