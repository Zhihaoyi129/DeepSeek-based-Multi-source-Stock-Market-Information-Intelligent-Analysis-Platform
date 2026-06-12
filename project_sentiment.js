StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('sentimentForm');
    const submitButton = document.getElementById('sentimentSubmit');
    const historyContainer = document.getElementById('sentimentHistory');
    const pagerContainer = document.getElementById('sentimentPager');
    const resultContainer = document.getElementById('sentimentResult');
    const historyState = {
        page: 1,
        pageSize: 8,
        total: 0,
        totalPages: 1,
    };

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
                { label: 'DeepSeek', value: data.deepseek ? data.deepseek.message : '已接入' },
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

    function renderPager() {
        const total = Number(historyState.total) || 0;
        const totalPages = Math.max(Number(historyState.totalPages) || 1, 1);
        const page = Math.min(Math.max(Number(historyState.page) || 1, 1), totalPages);
        const start = total ? (page - 1) * historyState.pageSize + 1 : 0;
        const end = total ? Math.min(page * historyState.pageSize, total) : 0;

        pagerContainer.innerHTML =
            '<div class="pager-summary">共 ' + total + ' 条，当前 ' + start + '-' + end + ' 条</div>' +
            '<div class="pager-actions">' +
            '<button class="secondary-btn pager-btn" type="button" data-history-page="1"' + (page <= 1 ? ' disabled' : '') + '>首页</button>' +
            '<button class="secondary-btn pager-btn" type="button" data-history-page="' + (page - 1) + '"' + (page <= 1 ? ' disabled' : '') + '>上一页</button>' +
            '<span class="pager-current">第 ' + page + ' / ' + totalPages + ' 页</span>' +
            '<button class="secondary-btn pager-btn" type="button" data-history-page="' + (page + 1) + '"' + (page >= totalPages ? ' disabled' : '') + '>下一页</button>' +
            '<button class="secondary-btn pager-btn" type="button" data-history-page="' + totalPages + '"' + (page >= totalPages ? ' disabled' : '') + '>末页</button>' +
            '</div>';
    }

    async function loadHistory(page) {
        historyState.page = Math.max(Number(page) || historyState.page, 1);
        const data = await StockPlatform.request($, {
            url: endpoints.history,
            data: { page: historyState.page, page_size: historyState.pageSize },
        });
        historyState.total = Number(data.total) || 0;
        historyState.page = Number(data.page) || historyState.page;
        historyState.pageSize = Number(data.pageSize) || historyState.pageSize;
        historyState.totalPages = Math.max(Number(data.totalPages) || Math.ceil(historyState.total / historyState.pageSize) || 1, 1);
        renderHistory(data.items || []);
        renderPager();
        return data.items || [];
    }

    async function loadDetail(recordId) {
        const data = await StockPlatform.request($, { url: endpoints.detailBase + recordId });
        renderResult(data);
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            await StockPlatform.withButtonLoading(submitButton, 'AI 思考中...', async function () {
                StockPlatform.clearNotice();
                const payload = {
                    title: document.getElementById('sentimentTitle').value.trim(),
                    symbol: StockPlatform.getStockInputValue('sentimentSymbol'),
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
                await loadHistory(1);
            });
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

    pagerContainer.addEventListener('click', function (event) {
        const target = event.target.closest('[data-history-page]');
        if (!target || target.disabled) {
            return;
        }
        const page = Number(target.getAttribute('data-history-page'));
        if (!page || page === historyState.page) {
            return;
        }
        loadHistory(page).catch(function (error) {
            StockPlatform.notice(error.message || '加载分页记录失败', true);
        });
    });

    (async function init() {
        StockPlatform.initStockSelector($, 'sentimentSymbol');
        try {
            const recordId = StockPlatform.getQueryParam('record_id');
            const items = await loadHistory(1);
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
