StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('historyForm');
    const tableContainer = document.getElementById('historyTable');

    function renderHistory(items) {
        tableContainer.innerHTML = StockPlatform.renderTable([
            { title: '模块', render: function (row) { return StockPlatform.renderBadge(row.moduleLabel, 'primary'); } },
            { title: '标题', render: function (row) { return StockPlatform.escapeHtml(row.title); } },
            { title: '股票', render: function (row) { return '<span class="mono">' + StockPlatform.escapeHtml(row.symbol) + '</span>'; } },
            { title: '结果', render: function (row) { return StockPlatform.escapeHtml(row.resultLabel); } },
            { title: '状态', render: function (row) { return StockPlatform.renderBadge(row.status, 'default'); } },
            { title: '时间', render: function (row) { return StockPlatform.escapeHtml(row.createdAt); } },
            { title: '跳转', render: function (row) { return '<a class="link-btn" href="' + StockPlatform.escapeHtml(row.detailRoute) + '">打开</a>'; } },
        ], items);
    }

    async function load() {
        const data = await StockPlatform.request($, {
            url: endpoints.list,
            data: {
                page: 1,
                page_size: 20,
                module: document.getElementById('historyModule').value,
                symbol: document.getElementById('historySymbol').value.trim(),
                status: document.getElementById('historyStatus').value,
                start_date: document.getElementById('historyStartDate').value,
                end_date: document.getElementById('historyEndDate').value,
            },
        });
        renderHistory(data.items || []);
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        load().then(function () {
            StockPlatform.notice('历史记录已更新');
        }).catch(function (error) {
            StockPlatform.notice(error.error || error.message || '查询历史失败', true);
        });
    });

    load().catch(function (error) {
        StockPlatform.notice(error.message || '初始化失败', true);
    });
});
