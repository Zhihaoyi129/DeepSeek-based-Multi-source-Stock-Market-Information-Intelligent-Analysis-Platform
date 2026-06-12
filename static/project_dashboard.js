StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;

    function renderRecent(items) {
        const container = document.getElementById('recentRecords');
        if (!items.length) {
            container.innerHTML = '<div class="empty-state">暂无记录</div>';
            return;
        }
        container.innerHTML = items.map(function (item) {
            return (
                '<div class="stack-item">' +
                '<h4>' + StockPlatform.escapeHtml(item.title) + '</h4>' +
                '<div class="stack-meta">' +
                StockPlatform.renderBadge(item.moduleLabel, 'primary') +
                StockPlatform.renderBadge(item.resultLabel, item.module === 'decision' ? 'warning' : 'success') +
                '</div>' +
                '<p>' + StockPlatform.escapeHtml(item.symbol + ' · ' + item.createdAt) + '</p>' +
                '<p><a class="link-btn" href="' + StockPlatform.escapeHtml(item.detailRoute) + '">查看详情</a></p>' +
                '</div>'
            );
        }).join('');
    }

    function renderSystemStatus(systemStatus) {
        const container = document.getElementById('systemStatus');
        const stats = systemStatus.statistics || {};
        const deepseek = systemStatus.deepseek || {};
        const marketSource = systemStatus.marketSource || {};
        container.innerHTML = [
            {
                title: 'DeepSeek 配置',
                detail: deepseek.enabled
                    ? '已启用，模型: ' + (deepseek.modelName || 'deepseek-chat')
                    : '未启用，请在系统设置中配置',
            },
            {
                title: 'AI 对话',
                detail: '历史记录 ' + (stats.aiChatCount || 0) + ' 条',
            },
            {
                title: '行情数据源',
                detail: '固定使用 Tushare' + (marketSource.hasToken ? '，Token 已配置' : '，请在系统设置中配置 Token'),
            },
            {
                title: '数据库状态',
                detail: systemStatus.database || 'unknown',
            },
        ].map(function (item) {
            return '<div class="stack-item"><h4>' + StockPlatform.escapeHtml(item.title) + '</h4><p>' + StockPlatform.escapeHtml(item.detail) + '</p></div>';
        }).join('');
    }

    async function load() {
        try {
            StockPlatform.clearNotice();
            const data = await StockPlatform.request($, { url: endpoints.dashboardState });
            StockPlatform.setText('sentimentCount', data.stats.sentimentCount);
            StockPlatform.setText('marketCount', data.stats.marketCount);
            StockPlatform.setText('decisionCount', data.stats.decisionCount);
            StockPlatform.setText('symbolCount', data.stats.symbolCount);
            data.systemStatus = data.systemStatus || {};
            data.systemStatus.statistics = data.stats || {};
            renderRecent(data.recentRecords || []);
            renderSystemStatus(data.systemStatus || {});
        } catch (error) {
            StockPlatform.notice(error.message || '加载总览失败', true);
        }
    }

    load();
});
