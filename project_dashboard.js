StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;

    function renderRecent(items) {
        const container = document.getElementById('recentRecords');
        if (!items.length) {
            container.innerHTML = '<div class="empty-state" style="text-align: center; padding: 40px 20px; color: var(--text-soft);">' +
                   '<svg style="width: 40px; height: 40px; margin-bottom: 10px; opacity: 0.3; display: inline-block;" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                   '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>' +
                   '</svg>' +
                   '<br><span style="font-size: 14px;">系统空空如也，快去跑一次分析吧</span>' +
                   '</div>';
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
