StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('sentimentForm');
    const historyContainer = document.getElementById('sentimentHistory');
    const resultContainer = document.getElementById('sentimentResult');

    function sentimentTone(value) {
        if (value === 'positive') {
            return 'success';
        }
        if (value === 'negative') {
            return 'danger';
        }
        return 'warning';
    }

    function renderResult(data) {
        resultContainer.innerHTML =
            '<div class="stack-item">' +
            '<h4>' + StockPlatform.escapeHtml(data.title) + '</h4>' +
            '<div class="stack-meta">' +
            StockPlatform.renderBadge(StockPlatform.sentimentLabel(data.sentiment), sentimentTone(data.sentiment)) +
            StockPlatform.renderBadge(data.symbol, 'primary') +
            StockPlatform.renderBadge(data.analysisMode || 'local-demo', 'default') +
            '</div>' +
            '<p>' + StockPlatform.escapeHtml(data.summary || '') + '</p>' +
            '<div class="stack-list">' +
            StockPlatform.renderKeyValues([
                { label: '来源类型', value: data.sourceType },
                { label: '发布时间', value: data.publishedAt || '-' },
                { label: '置信度', value: data.confidence || '-' },
                { label: '风险提示', value: data.riskNotes || '-' },
                { label: '关键词', value: (data.keywords || []).join(', ') || '-' },
                { label: 'DeepSeek', value: data.deepseek ? data.deepseek.message : '占位中' },
            ]) +
            '</div>' +
            '</div>';
    }

    function renderHistory(items) {
        historyContainer.innerHTML = StockPlatform.renderTable([
            { title: 'ID', key: 'id' },
            { title: '标题', render: function (row) { return StockPlatform.escapeHtml(row.title); } },
            { title: '股票', render: function (row) { return '<span class="mono">' + StockPlatform.escapeHtml(row.symbol) + '</span>'; } },
            { title: '情感', render: function (row) { return StockPlatform.renderBadge(StockPlatform.sentimentLabel(row.sentiment), sentimentTone(row.sentiment)); } },
            { title: '时间', render: function (row) { return StockPlatform.escapeHtml(row.createdAt); } },
            { title: '操作', render: function (row) { return '<a href="#" class="link-btn" data-sentiment-detail="' + row.id + '">查看</a>'; } },
        ], items);
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
        renderResult(data);
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            StockPlatform.clearNotice();
            const payload = {
                title: document.getElementById('sentimentTitle').value.trim(),
                symbol: document.getElementById('sentimentSymbol').value.trim(),
                source_type: document.getElementById('sentimentSourceType').value,
                published_at: document.getElementById('sentimentPublishedAt').value.trim(),
                content: document.getElementById('sentimentContent').value.trim(),
            };
            const data = await StockPlatform.request($, {
                url: endpoints.analyze,
                method: 'POST',
                data: payload,
                contentType: 'application/json',
            });
            renderResult(data);
            StockPlatform.notice('情感分析已完成');
            await loadHistory();
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '情感分析失败', true);
        }
    });

    historyContainer.addEventListener('click', function (event) {
        const target = event.target.closest('[data-sentiment-detail]');
        if (!target) {
            return;
        }
        event.preventDefault();
        loadDetail(target.getAttribute('data-sentiment-detail')).catch(function (error) {
            StockPlatform.notice(error.message || '加载详情失败', true);
        });
    });

    (async function init() {
        try {
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
