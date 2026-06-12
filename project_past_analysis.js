StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('pastAnalysisForm');
    const submitButton = document.getElementById('analysisSubmit');
    const summaryContainer = document.getElementById('analysisSummary');
    const newsContainer = document.getElementById('analysisNews');
    const reportContainer = document.getElementById('analysisReport');

    function renderMarkdown(value) {
        return StockPlatform.escapeHtml(value || '')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    function startOverlay() {
        return StockPlatform.showProgressOverlay('pastAnalysisLoading', 'pastAnalysisLoadingText', 'pastAnalysisLoadingBar', [
            '正在拉取行情数据...',
            '正在计算 MA、RSI 和涨跌幅...',
            '正在按股票和日期筛选新闻硬标签...',
            '正在汇总情感分析记录...',
            '正在调用 DeepSeek 做逻辑裁判...',
        ]);
    }

    function renderSummary(data) {
        const summary = (data.market || {}).summary || {};
        const stats = data.sentimentStats || {};
        summaryContainer.innerHTML = [
            { label: '最新价', value: summary.latestPrice || '-' },
            { label: '涨跌幅', value: (summary.changePercent || 0) + '%' },
            { label: 'RSI', value: summary.rsi || '-' },
            { label: 'MA5', value: summary.ma5 || '-' },
            { label: '新闻数', value: (data.news || []).length },
            { label: '情感均值', value: stats.averageScore || 0 },
        ].map(function (item) {
            return '<div class="mini-metric"><span class="label-text">' + StockPlatform.escapeHtml(item.label) + '</span><strong>' + StockPlatform.escapeHtml(item.value) + '</strong></div>';
        }).join('');

        const series = (data.market || {}).priceSeries || [];
        StockPlatform.lineChart(
            'analysisChart',
            series.map(function (item) { return item.close; }),
            series.map(function (item) { return item.date; })
        );
    }

    function renderNews(items) {
        if (!items || !items.length) {
            newsContainer.innerHTML = '<div class="empty-state">当前时间段暂无匹配新闻，请先执行自动新闻任务。</div>';
            return;
        }
        newsContainer.innerHTML = items.map(function (item) {
            return (
                '<div class="stack-item">' +
                '<h4>' + StockPlatform.escapeHtml(item.title) + '</h4>' +
                '<div class="stack-meta">' +
                StockPlatform.renderBadge(item.newsDate || '-', 'default') +
                StockPlatform.renderBadge(StockPlatform.sentimentLabel(item.sentiment), item.sentiment === 'negative' ? 'danger' : (item.sentiment === 'positive' ? 'success' : 'warning')) +
                StockPlatform.renderBadge('情感分 ' + item.sentimentScore, 'primary') +
                '</div>' +
                '<p>' + StockPlatform.escapeHtml(item.summary || item.content || '') + '</p>' +
                '</div>'
            );
        }).join('');
    }

    function renderReport(data) {
        reportContainer.classList.remove('empty-state');
        reportContainer.innerHTML =
            '<div class="stack-meta">' +
            StockPlatform.renderBadge(data.model || 'deepseek-chat', 'primary') +
            '</div>' +
            '<div class="report-content">' + renderMarkdown(data.aiReport || 'DeepSeek 未返回归因报告。') + '</div>';
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        const stopOverlay = startOverlay();
        try {
            StockPlatform.setButtonLoading(submitButton, true, 'AI 思考中...');
            const data = await StockPlatform.request($, {
                url: endpoints.analyze,
                method: 'POST',
                contentType: 'application/json',
                data: {
                    symbol: StockPlatform.getStockInputValue('analysisSymbol'),
                    range: document.getElementById('analysisRange').value,
                    start_date: document.getElementById('analysisStartDate').value,
                    end_date: document.getElementById('analysisEndDate').value,
                },
            });
            renderSummary(data);
            renderNews(data.news || []);
            renderReport(data);
            StockPlatform.notice('过往归因分析已生成');
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '过往归因分析失败', true);
        } finally {
            StockPlatform.setButtonLoading(submitButton, false);
            stopOverlay();
        }
    });

    StockPlatform.initStockSelector($, 'analysisSymbol');
});
