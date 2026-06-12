from __future__ import annotations

from flask import Blueprint, current_app

from app.services.scheduler_service import reload_scheduler_jobs
from app.services.task_service import delete_task, get_task, get_task_logs, list_tasks, run_task, save_task
from utils.api import error_api, get_json_payload, success_api

bp = Blueprint('project_tasks_api', __name__, url_prefix='/api/tasks')


@bp.route('')
def tasks_list():
    return success_api(data=list_tasks())


@bp.route('', methods=['POST'])
def tasks_create():
    data = get_json_payload()
    try:
        task = save_task(data)
        reload_scheduler_jobs(current_app._get_current_object())
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    return success_api(msg='定时任务已创建', data=task.to_dict())


@bp.route('/<int:task_id>', methods=['PUT'])
def tasks_update(task_id):
    task = get_task(task_id)
    if task is None:
        return error_api('Not Found', error='定时任务不存在', status_code=404)
    try:
        task = save_task(get_json_payload(), task=task)
        reload_scheduler_jobs(current_app._get_current_object())
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    return success_api(msg='定时任务已保存', data=task.to_dict())


@bp.route('/<int:task_id>', methods=['DELETE'])
def tasks_delete(task_id):
    task = get_task(task_id)
    if task is None:
        return error_api('Not Found', error='定时任务不存在', status_code=404)
    delete_task(task)
    reload_scheduler_jobs(current_app._get_current_object())
    return success_api(msg='定时任务已删除')


@bp.route('/<int:task_id>/run', methods=['POST'])
def tasks_run(task_id):
    try:
        log = run_task(task_id)
        reload_scheduler_jobs(current_app._get_current_object())
    except ValueError as exc:
        return error_api('Bad Request', error=str(exc), status_code=400)
    return success_api(msg='任务执行完成', data=log.to_dict())


@bp.route('/<int:task_id>/logs')
def tasks_logs(task_id):
    task = get_task(task_id)
    if task is None:
        return error_api('Not Found', error='定时任务不存在', status_code=404)
    return success_api(data=get_task_logs(task_id))
