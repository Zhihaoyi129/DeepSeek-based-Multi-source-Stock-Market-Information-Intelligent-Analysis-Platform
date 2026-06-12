from __future__ import annotations

import os

from app.models.stock_analysis import ScheduledTask

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:  # pragma: no cover - 依赖未安装时仍允许页面和手动执行可用。
    BackgroundScheduler = None
    CronTrigger = None

_scheduler = None


def init_scheduler(app):
    if BackgroundScheduler is None:
        app.logger.warning('APScheduler 未安装，定时任务后台调度未启用。')
        return
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return

    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    _scheduler.start()
    reload_scheduler_jobs(app)


def reload_scheduler_jobs(app):
    if _scheduler is None:
        return
    for job in _scheduler.get_jobs():
        job.remove()

    with app.app_context():
        tasks = ScheduledTask.query.filter_by(enabled=True).all()
        for task in tasks:
            add_task_job(app, task)


def add_task_job(app, task):
    if _scheduler is None or CronTrigger is None:
        return
    hour, minute = [int(part) for part in task.run_time.split(':')]
    _scheduler.add_job(
        func=_run_task_in_context,
        trigger=CronTrigger(hour=hour, minute=minute),
        args=[app, task.id],
        id=f'stock_task_{task.id}',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def _run_task_in_context(app, task_id):
    with app.app_context():
        from app.services.task_service import run_task

        run_task(task_id)
