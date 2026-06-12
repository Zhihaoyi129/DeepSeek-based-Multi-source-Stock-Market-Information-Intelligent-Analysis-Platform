StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('decisionForm');
    const sentimentSelect = document.getElementById('decisionSentimentRecord');
    const marketSelect = document.getElementById('decisionMarketRecord');
    const resultContainer = document.getElementById('decisionResult');
    const historyContainer = document.getElementById('decisionHistory');
    let marketMap = {};

    function decisionTone(value) {
        if (value === 'buy') {
            return 'success';
        }
        if (value === 'sell') {
            return 'danger';
        }
        return 'warning';
    }

    function renderDecision(data) {
        resultContainer.innerHTML =
            '<div class="stack-item">' +
            '<h4>' + StockPlatform.escapeHtml(data.symbol) + ' 综合建议</h4>' +
            '<div class="stack-meta">' +
            StockPlatform.renderBadge(StockPlatform.decisionLabel(data.decision), decisionTone(data.decision)) +
            StockPlatform.renderBadge(StockPlatform.sentimentLabel(data.sentiment), 'primary') +
            '</div>' +
            '<p>' + StockPlatform.escapeHtml(data.reasonText || '') + '</p>' +
            '<div class="stack-list">' +
            StockPlatform.renderKeyValues([
                { label: '当前价格', value: data.price },
                { label: 'MA5', value: data.ma5 },
                { label: 'RSI', value: data.rsi },
                { label: '命中规则', value: (data.matchedRules || []).join(' / ') || '-' },
                { label: 'DeepSeek', value: data.deepseekPlaceholder || '占位中' },
            ]) +
            '</div>' +
            '</div>';
    }

    function renderHistory(items) {
        historyContainer.innerHTML = StockPlatform.renderTable([
            { title: 'ID', key: 'id' },
            { title: '股票', render: function (row) { return '<span class="mono">' + StockPlatform.escapeHtml(row.symbol) + '</span>'; } },
            { title: '建议', render: function (row) { return StockPlatform.renderBadge(StockPlatform.decisionLabel(row.decision), decisionTone(row.decision)); } },
            { title: '价格/MA5/RSI', render: function (row) { return StockPlatform.escapeHtml(row.price + ' / ' + row.ma5 + ' / ' + row.rsi); } },
            { title: '时间', render: function (row) { return StockPlatform.escapeHtml(row.createdAt); } },
            { title: '操作', render: function (row) { return '<a href="#" class="link-btn" data-decision-detail="' + row.id + '">查看</a>'; } },
        ], items);
    }

    function fillMarketMetrics(recordId) {
        const selected = marketMap[recordId];
        if (!selected) {
            return;
        }
        StockPlatform.setValue('decisionSymbol', selected.symbol);
        StockPlatform.setValue('decisionPrice', (selected.summary || {}).price);
        StockPlatform.setValue('decisionMa5', (selected.summary || {}).ma5);
        StockPlatform.setValue('decisionRsi', (selected.summary || {}).rsi);
    }

    async function loadSentimentOptions() {
        const data = await StockPlatform.request($, {
            url: endpoints.sentimentHistory,
            data: { page: 1, page_size: 20 },
        });
        const items = data.items || [];
        sentimentSelect.innerHTML = '<option value="">请选择</option>' + items.map(function (item) {
            return '<option value="' + item.id + '">' + StockPlatform.escapeHtml(item.symbol + ' · ' + item.title) + '</option>';
        }).join('');
        if (items.length) {
            sentimentSelect.value = String(items[0].id);
            StockPlatform.setValue('decisionSymbol', items[0].symbol);
        }
    }

    async function loadMarketOptions() {
        const data = await StockPlatform.request($, {
            url: endpoints.marketHistory,
            data: { page: 1, page_size: 20 },
        });
        const items = data.items || [];
        marketMap = {};
        items.forEach(function (item) {
            marketMap[item.id] = item;
        });
        marketSelect.innerHTML = '<option value="">请选择</option>' + items.map(function (item) {
            return '<option value="' + item.id + '">' + StockPlatform.escapeHtml(item.symbol + ' · ' + item.rangeType + ' · ' + ((item.summary || {}).latestDate || '-')) + '</option>';
        }).join('');
        if (items.length) {
            marketSelect.value = String(items[0].id);
            fillMarketMetrics(String(items[0].id));
        }
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
        renderDecision(data);
    }

    marketSelect.addEventListener('change', function () {
        fillMarketMetrics(marketSelect.value);
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            StockPlatform.clearNotice();
            const payload = {
                symbol: document.getElementById('decisionSymbol').value.trim(),
                sentiment_record_id: sentimentSelect.value || null,
                market_record_id: marketSelect.value || null,
                sentiment: document.getElementById('decisionManualSentiment').value || null,
                price: document.getElementById('decisionPrice').value || null,
                ma5: document.getElementById('decisionMa5').value || null,
                rsi: document.getElementById('decisionRsi').value || null,
            };
            const data = await StockPlatform.request($, {
                url: endpoints.generate,
                method: 'POST',
                data: payload,
                contentType: 'application/json',
            });
            renderDecision(data);
            await loadHistory();
            StockPlatform.notice('决策建议已生成');
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '生成决策失败', true);
        }
    });

    historyContainer.addEventListener('click', function (event) {
        const target = event.target.closest('[data-decision-detail]');
        if (!target) {
            return;
        }
        event.preventDefault();
        loadDetail(target.getAttribute('data-decision-detail')).catch(function (error) {
            StockPlatform.notice(error.message || '加载决策详情失败', true);
        });
    });

    (async function init() {
        try {
            await loadSentimentOptions();
            await loadMarketOptions();
            const recordId = StockPlatform.getQueryParam('record_id');
            const items = await loadHistory();
            if (recordId) {
                await loadDetail(recordId);
            } else if (items.length) {
                await loadDetail(items[0].id);
            }
        } catch (error) {
            StockPlatform.notice(error.message || '初始化失败', true);
        }
    })();
});
