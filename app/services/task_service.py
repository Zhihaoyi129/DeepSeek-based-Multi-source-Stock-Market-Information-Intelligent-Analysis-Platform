from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app import db
from app.models.stock_analysis import (
    ScheduledTask,
    SentimentAnalysisRecord,
    StockNewsRecord,
    TaskRunLog,
)
from app.services.deepseek_service import (
    analyze_sentiment_with_deepseek,
    generate_news_with_deepseek,
)
from app.services.market_service import normalize_symbol
from app.services.symbol_service import ensure_symbol

TASK_PRESETS = {
    'post_market_news': '盘后自动获取新闻',
}

DEFAULT_TASK_SYMBOLS = ['600519.SH', '000001.SZ', '300750.SZ']
LOCAL_TIMEZONE = timezone(timedelta(hours=8))


def current_local_datetime():
    return datetime.now(LOCAL_TIMEZONE).replace(tzinfo=None)


def parse_symbols(value):
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = str(value or '').replace('\n', ',').split(',')
    symbols = []
    for item in raw_items:
        symbol = normalize_symbol(item)
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def validate_run_time(value):
    text = str(value or '').strip()
    try:
        hour_text, minute_text = text.split(':', 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (ValueError, AttributeError):
        raise ValueError('执行时间格式应为 HH:MM')
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError('执行时间格式应为 HH:MM')
    return f'{hour:02d}:{minute:02d}'


def calculate_next_run(run_time, now=None):
    now = now or current_local_datetime()
    hour, minute = [int(part) for part in validate_run_time(run_time).split(':')]
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def list_tasks():
    return [item.to_dict() for item in ScheduledTask.query.order_by(ScheduledTask.id.asc()).all()]


def get_task(task_id):
    return ScheduledTask.query.get(task_id)


def delete_task(task):
    TaskRunLog.query.filter_by(task_id=task.id).delete()
    db.session.delete(task)
    db.session.commit()


def save_task(data, task=None):
    task = task or ScheduledTask()
    name = (data.get('name') or '').strip()
    if not name:
        raise ValueError('任务名称不能为空')
    run_time = validate_run_time(data.get('run_time') or data.get('runTime') or '15:30')
    symbols = parse_symbols(data.get('symbols') or DEFAULT_TASK_SYMBOLS)
    if not symbols:
        raise ValueError('至少配置一个股票代码')

    task.name = name
    task.task_type = (data.get('task_type') or data.get('taskType') or 'auto_news').strip() or 'auto_news'
    task.enabled = _parse_bool(data.get('enabled'))
    task.frequency = 'daily'
    task.run_time = run_time
    task.content_preset = (data.get('content_preset') or data.get('contentPreset') or 'post_market_news').strip()
    task.remark = (data.get('remark') or '').strip()
    task.next_run_at = calculate_next_run(run_time) if task.enabled else None
    task.set_symbols(symbols)
    db.session.add(task)
    db.session.commit()
    return task


def ensure_default_tasks():
    existing = ScheduledTask.query.filter_by(task_type='auto_news').first()
    if existing:
        return
    task = ScheduledTask(
        name='每日盘后自动获取新闻',
        task_type='auto_news',
        enabled=True,
        frequency='daily',
        run_time='15:30',
        content_preset='post_market_news',
        remark='收盘后生成新闻、入库并调用 DeepSeek 做情感分析。',
        next_run_at=calculate_next_run('15:30'),
    )
    task.set_symbols(DEFAULT_TASK_SYMBOLS)
    db.session.add(task)
    db.session.commit()


def get_task_logs(task_id, limit=20):
    rows = (
        TaskRunLog.query
        .filter_by(task_id=task_id)
        .order_by(TaskRunLog.started_at.desc())
        .limit(limit)
        .all()
    )
    return [row.to_dict() for row in rows]


def run_task(task_id):
    task = get_task(task_id)
    if task is None:
        raise ValueError('定时任务不存在')
    if task.task_type != 'auto_news':
        raise ValueError('暂不支持该任务类型')
    return run_auto_news_task(task)


def run_auto_news_task(task):
    started_at = current_local_datetime()
    log = TaskRunLog(
        task_id=task.id,
        status='running',
        message='任务执行中',
        started_at=started_at,
    )
    log.set_detail({'steps': ['任务启动']})
    db.session.add(log)
    db.session.commit()

    detail = {
        'symbols': task.get_symbols(),
        'createdNews': 0,
        'createdSentiments': 0,
        'errors': [],
    }
    try:
        target_date = started_at.date()
        for symbol in task.get_symbols():
            _ensure_symbol(symbol)
            news_items = generate_news_with_deepseek(symbol, target_date.isoformat(), count=3)
            for news in news_items:
                record = _save_news_record(symbol, target_date, news, log.id)
                detail['createdNews'] += 1
                try:
                    _save_sentiment_record(record)
                    detail['createdSentiments'] += 1
                except Exception as exc:  # noqa: BLE001
                    detail['errors'].append(f'{record.title}: {exc}')

        log.status = 'success' if not detail['errors'] else 'partial_success'
        log.message = (
            f"已生成新闻 {detail['createdNews']} 条，"
            f"情感分析 {detail['createdSentiments']} 条。"
        )
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        log = TaskRunLog.query.get(log.id) or log
        log.status = 'failed'
        log.message = str(exc)
        detail['errors'].append(str(exc))
    finally:
        log.finished_at = current_local_datetime()
        log.set_detail(detail)
        task.last_run_at = log.finished_at
        task.next_run_at = calculate_next_run(task.run_time) if task.enabled else None
        db.session.commit()
    return log


def _ensure_symbol(symbol):
    ensure_symbol(symbol)
    db.session.commit()


def _save_news_record(symbol, target_date, news, task_run_id):
    record = StockNewsRecord(
        title=news['title'],
        content=news['content'],
        source_type=_normalize_source_type(news.get('sourceType')),
        symbol=symbol,
        industry=news.get('industry') or '',
        news_date=target_date,
        raw_response=news.get('rawResponse'),
        task_run_id=task_run_id,
    )
    related = news.get('relatedStocks') or [symbol]
    if symbol not in related:
        related.append(symbol)
    record.set_related_stocks(related)
    db.session.add(record)
    db.session.commit()
    return record


def _save_sentiment_record(news_record):
    result = analyze_sentiment_with_deepseek({
        'title': news_record.title,
        'content': news_record.content,
        'source_type': news_record.source_type,
        'symbol': news_record.symbol,
    })
    sentiment_record = SentimentAnalysisRecord(
        title=news_record.title,
        content=news_record.content,
        source_type=news_record.source_type,
        symbol=news_record.symbol,
        published_at=datetime.combine(news_record.news_date, datetime.min.time()),
        sentiment=result['sentiment'],
        summary=result['summary'],
        risk_notes=result['riskNotes'],
        raw_response=result['rawResponse'],
        confidence=result['confidence'],
        analysis_mode='deepseek',
    )
    sentiment_record.set_keywords(result['keywords'])
    db.session.add(sentiment_record)

    news_record.sentiment = result['sentiment']
    news_record.sentiment_score = _score_sentiment(result['sentiment'], result['confidence'])
    news_record.summary = result['summary']
    db.session.commit()
    return sentiment_record


def _normalize_source_type(value):
    source_type = (value or 'financial_news').strip()
    if source_type not in {'financial_news', 'policy_document', 'company_announcement'}:
        return 'financial_news'
    return source_type


def _score_sentiment(sentiment, confidence):
    try:
        value = float(confidence or 0)
    except (TypeError, ValueError):
        value = 0
    value = max(0, min(value, 1))
    if sentiment == 'positive':
        return round(value, 3)
    if sentiment == 'negative':
        return round(-value, 3)
    return 0


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}
