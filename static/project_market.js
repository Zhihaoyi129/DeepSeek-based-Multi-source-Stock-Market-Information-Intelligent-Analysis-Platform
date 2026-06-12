StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('marketForm');
    const submitButton = document.getElementById('marketSubmit');
    const summaryContainer = document.getElementById('marketSummary');
    const indicatorsContainer = document.getElementById('marketIndicators');
    const historyContainer = document.getElementById('marketHistory');

    function renderSummary(data) {
        const summary = data.summary || {};
        summaryContainer.innerHTML = [
            { label: '最新价', value: summary.latestPrice },
            { label: '涨跌幅', value: (summary.changePercent || 0) + '%' },
            { label: '最高价', value: summary.highestPrice },
            { label: '最低价', value: summary.lowestPrice },
            { label: '平均成交量', value: summary.averageVolume },
            { label: '最新日期', value: summary.latestDate },
        ].map(function (item) {
            return '<div class="mini-metric"><span class="label-text">' + StockPlatform.escapeHtml(item.label) + '</span><strong>' + StockPlatform.escapeHtml(item.value) + '</strong></div>';
        }).join('');
        StockPlatform.candlestickChart('marketChart', data.priceSeries || []);
    }

    function renderIndicators(data) {
        indicatorsContainer.innerHTML = StockPlatform.renderTable([
            { title: '日期', render: function (row) { return StockPlatform.escapeHtml(row.date); } },
            { title: '收盘价', render: function (row) { return StockPlatform.escapeHtml(row.close); } },
            { title: 'MA5', render: function (row) { return StockPlatform.escapeHtml(row.ma5 == null ? '-' : row.ma5); } },
            { title: 'MA10', render: function (row) { return StockPlatform.escapeHtml(row.ma10 == null ? '-' : row.ma10); } },
            { title: 'RSI', render: function (row) { return StockPlatform.escapeHtml(row.rsi == null ? '-' : row.rsi); } },
            { title: 'MACD', render: function (row) { return StockPlatform.escapeHtml(row.macd == null ? '-' : row.macd); } },
        ], (data.priceSeries || []).slice(-10).reverse());
    }

    function renderHistory(items) {
        historyContainer.innerHTML = StockPlatform.renderTable([
            { title: 'ID', key: 'id' },
            { title: '股票', render: function (row) { return '<span class="mono">' + StockPlatform.escapeHtml(row.symbol) + '</span>'; } },
            { title: '范围', render: function (row) { return StockPlatform.escapeHtml(row.rangeType); } },
            { title: '最新价', render: function (row) { return StockPlatform.escapeHtml((row.summary || {}).latestPrice); } },
            { title: '时间', render: function (row) { return StockPlatform.escapeHtml(row.createdAt); } },
            { title: '操作', render: function (row) { return '<a href="#" class="link-btn" data-market-detail="' + row.id + '">查看</a>'; } },
        ], items);
    }

    function collectIndicators() {
        return Array.prototype.slice.call(document.querySelectorAll('input[name="indicator"]:checked')).map(function (el) {
            return el.value;
        });
    }

    function fillFormFromRecord(data) {
        StockPlatform.setValue('marketSymbol', data.symbol);
        StockPlatform.setValue('marketRange', data.rangeType);
        StockPlatform.setValue('marketStartDate', data.startDate);
        StockPlatform.setValue('marketEndDate', data.endDate);
        StockPlatform.setValue('marketSource', 'Tushare');
    }

    async function loadHistory() {
        const data = await StockPlatform.request($, {
            url: endpoints.history,
            data: { page: 1, page_size: 8 },
        });
        renderHistory(data.items || []);
        return data.items || [];
    }

    async function loadDetail(recordId) {
        const data = await StockPlatform.request($, { url: endpoints.detailBase + recordId });
        fillFormFromRecord(data);
        renderSummary(data);
        renderIndicators(data);
    }

    async function runQuery() {
        const query = {
            symbol: StockPlatform.getStockInputValue('marketSymbol'),
            range: document.getElementById('marketRange').value,
            start_date: document.getElementById('marketStartDate').value,
            end_date: document.getElementById('marketEndDate').value,
            source: 'tushare',
            indicators: collectIndicators(),
        };
        const data = await StockPlatform.request($, { url: endpoints.quote, data: query });
        renderSummary(data);
        renderIndicators(data);
        return data;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            await StockPlatform.withButtonLoading(submitButton, '查询中...', async function () {
                StockPlatform.clearNotice();
                await runQuery();
                await loadHistory();
                StockPlatform.notice('技术分析已刷新');
            });
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '技术分析失败', true);
        }
    });

    historyContainer.addEventListener('click', function (event) {
        const target = event.target.closest('[data-market-detail]');
        if (!target) {
            return;
        }
        event.preventDefault();
        loadDetail(target.getAttribute('data-market-detail')).catch(function (error) {
            StockPlatform.notice(error.message || '加载技术详情失败', true);
        });
    });

    (async function init() {
        StockPlatform.initStockSelector($, 'marketSymbol');
        try {
            const recordId = StockPlatform.getQueryParam('record_id');
            const items = await loadHistory();
            if (recordId) {
                await loadDetail(recordId);
            } else if (items.length) {
                await loadDetail(items[0].id);
            } else {
                await runQuery();
                await loadHistory();
            }
        } catch (error) {
            StockPlatform.notice(error.message || '初始化失败', true);
        }
    })();
});
