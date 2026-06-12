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
        container.innerHTML = [
            {
                title: 'DeepSeek 配置',
                detail: systemStatus.deepseek.enabled
                    ? '已启用，占位接入'
                    : '未启用，当前为占位模式',
            },
            {
                title: '行情数据源',
                detail: '当前配置: ' + (systemStatus.marketSource.provider || 'mock'),
            },
            {
                title: '数据库状态',
                detail: systemStatus.database,
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
            renderRecent(data.recentRecords || []);
            renderSystemStatus(data.systemStatus || {});
        } catch (error) {
            StockPlatform.notice(error.message || '加载总览失败', true);
        }
    }

    load();
});
