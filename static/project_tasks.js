StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('taskForm');
    const submitButton = document.getElementById('taskSubmit');
    const taskList = document.getElementById('taskList');
    const taskLogs = document.getElementById('taskLogs');

    function startOverlay() {
        return StockPlatform.showProgressOverlay('taskRunLoading', 'taskRunLoadingText', 'taskRunLoadingBar', [
            '正在读取任务配置...',
            '正在调用 DeepSeek 生成盘后新闻...',
            '正在写入新闻库并打硬标签...',
            '正在调用 DeepSeek 执行情感分析...',
            '正在保存任务运行日志...',
        ]);
    }

    function payloadFromForm() {
        return {
            name: document.getElementById('taskName').value.trim(),
            enabled: document.getElementById('taskEnabled').value === 'true',
            run_time: document.getElementById('taskRunTime').value,
            content_preset: document.getElementById('taskPreset').value,
            symbols: document.getElementById('taskSymbols').value,
            remark: document.getElementById('taskRemark').value.trim(),
        };
    }

    function fillForm(task) {
        StockPlatform.setValue('taskId', task.id || '');
        StockPlatform.setValue('taskName', task.name || '');
        StockPlatform.setValue('taskEnabled', String(Boolean(task.enabled)));
        StockPlatform.setValue('taskRunTime', task.runTime || '15:30');
        StockPlatform.setValue('taskPreset', task.contentPreset || 'post_market_news');
        StockPlatform.setValue('taskSymbols', (task.symbols || []).join(', '));
        StockPlatform.setValue('taskRemark', task.remark || '');
    }

    function resetForm() {
        fillForm({
            name: '每日盘后自动获取新闻',
            enabled: true,
            runTime: '15:30',
            contentPreset: 'post_market_news',
            symbols: ['600519.SH', '000001.SZ', '300750.SZ'],
            remark: '',
        });
        taskLogs.innerHTML = '<div class="empty-state">请选择任务查看日志</div>';
    }

    function renderTasks(items) {
        taskList.innerHTML = StockPlatform.renderTable([
            { title: '任务', render: function (row) { return StockPlatform.escapeHtml(row.name); } },
            { title: '状态', render: function (row) { return StockPlatform.renderBadge(row.enabled ? '启用' : '停用', row.enabled ? 'success' : 'default'); } },
            { title: '执行时间', render: function (row) { return StockPlatform.escapeHtml(row.runTime); } },
            { title: '股票', render: function (row) { return StockPlatform.escapeHtml((row.symbols || []).join(', ')); } },
            {
                title: '操作',
                render: function (row) {
                    return '<div class="table-actions">' + [
                        '<a href="#" class="link-btn" data-edit-task="' + row.id + '">编辑</a>',
                        '<a href="#" class="link-btn" data-run-task="' + row.id + '">立即执行</a>',
                        '<a href="#" class="link-btn" data-log-task="' + row.id + '">日志</a>',
                        '<a href="#" class="link-btn" data-delete-task="' + row.id + '">删除</a>',
                    ].join('') + '</div>';
                },
            },
        ], items);
    }

    function renderLogs(items) {
        taskLogs.innerHTML = StockPlatform.renderTable([
            { title: 'ID', key: 'id' },
            { title: '状态', render: function (row) { return StockPlatform.renderBadge(row.status, row.status === 'success' ? 'success' : (row.status === 'failed' ? 'danger' : 'warning')); } },
            { title: '说明', render: function (row) { return StockPlatform.escapeHtml(row.message || '-'); } },
            { title: '开始时间', render: function (row) { return StockPlatform.escapeHtml(row.startedAt || '-'); } },
            { title: '结束时间', render: function (row) { return StockPlatform.escapeHtml(row.finishedAt || '-'); } },
        ], items);
    }

    async function loadTasks(selectFirst) {
        const items = await StockPlatform.request($, { url: endpoints.tasks });
        renderTasks(items || []);
        if (selectFirst && items && items.length) {
            fillForm(items[0]);
            await loadLogs(items[0].id);
        }
        return items || [];
    }

    async function loadLogs(taskId) {
        const items = await StockPlatform.request($, { url: endpoints.taskBase + taskId + '/logs' });
        renderLogs(items || []);
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            await StockPlatform.withButtonLoading(submitButton, '保存中...', async function () {
                const taskId = document.getElementById('taskId').value;
                const url = taskId ? endpoints.taskBase + taskId : endpoints.tasks;
                const method = taskId ? 'PUT' : 'POST';
                const task = await StockPlatform.request($, {
                    url: url,
                    method: method,
                    data: payloadFromForm(),
                    contentType: 'application/json',
                });
                resetForm();
                await loadTasks(false);
                await loadLogs(task.id);
                StockPlatform.notice('定时任务已保存');
            });
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '保存定时任务失败', true);
        }
    });

    taskList.addEventListener('click', async function (event) {
        const editTarget = event.target.closest('[data-edit-task]');
        const runTarget = event.target.closest('[data-run-task]');
        const logTarget = event.target.closest('[data-log-task]');
        const deleteTarget = event.target.closest('[data-delete-task]');
        if (!editTarget && !runTarget && !logTarget && !deleteTarget) {
            return;
        }
        event.preventDefault();
        const items = await loadTasks(false);
        if (editTarget) {
            const task = items.find(function (item) { return String(item.id) === editTarget.getAttribute('data-edit-task'); });
            if (task) {
                fillForm(task);
                await loadLogs(task.id);
            }
        }
        if (logTarget) {
            await loadLogs(logTarget.getAttribute('data-log-task'));
        }
        if (deleteTarget) {
            if (!window.confirm('确定删除这个定时任务吗？对应运行日志也会一起删除。')) {
                return;
            }
            try {
                await StockPlatform.request($, {
                    url: endpoints.taskBase + deleteTarget.getAttribute('data-delete-task'),
                    method: 'DELETE',
                });
                resetForm();
                await loadTasks(false);
                taskLogs.innerHTML = '<div class="empty-state">请选择任务查看日志</div>';
                StockPlatform.notice('定时任务已删除');
            } catch (error) {
                StockPlatform.notice(error.error || error.message || '删除定时任务失败', true);
            }
        }
        if (runTarget) {
            const stopOverlay = startOverlay();
            try {
                const log = await StockPlatform.request($, {
                    url: endpoints.taskBase + runTarget.getAttribute('data-run-task') + '/run',
                    method: 'POST',
                    contentType: 'application/json',
                    data: {},
                });
                await loadTasks(false);
                await loadLogs(log.taskId);
                StockPlatform.notice(log.message || '任务执行完成');
            } catch (error) {
                StockPlatform.notice(error.error || error.message || '任务执行失败', true);
            } finally {
                stopOverlay();
            }
        }
    });

    (async function init() {
        StockPlatform.initStockAppendSelector($, 'taskSymbolPicker', 'taskAddSymbol', 'taskSymbols');
        resetForm();
        try {
            await loadTasks(false);
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '加载定时任务失败', true);
            resetForm();
        }
    })();
});
