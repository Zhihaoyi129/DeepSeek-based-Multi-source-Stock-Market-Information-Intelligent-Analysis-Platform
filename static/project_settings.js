StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const statusContainer = document.getElementById('settingsStatus');
    const deepseekSubmit = document.getElementById('deepseekSubmit');
    const marketSourceSubmit = document.getElementById('marketSourceSubmit');

    function renderStatus(data) {
        const statistics = data.statistics || {};
        const deepseek = data.deepseek || {};
        const marketSource = data.marketSource || {};
        statusContainer.innerHTML = [
            {
                title: '数据库状态',
                detail: data.database || 'unknown',
            },
            {
                title: 'DeepSeek 状态',
                detail: (deepseek.enabled ? '已启用' : '未启用') + ' · ' + (deepseek.remark || '-'),
            },
            {
                title: '行情数据源',
                detail: 'Tushare · ' + (marketSource.hasToken ? 'Token 已配置' : 'Token 未配置') + ' · ' + (marketSource.remark || '-'),
            },
            {
                title: '数据统计',
                detail: '股票 ' + (statistics.symbols || 0) + ' / 新闻 ' + (statistics.newsRecords || 0) + ' / 情感 ' + (statistics.sentimentRecords || 0) + ' / 技术 ' + (statistics.marketRecords || 0) + ' / 决策 ' + (statistics.decisionRecords || 0) + ' / 任务 ' + (statistics.tasks || 0) + ' / AI对话 ' + (statistics.aiChatRecords || 0),
            },
        ].map(function (item) {
            return '<div class="stack-item"><h4>' + StockPlatform.escapeHtml(item.title) + '</h4><p>' + StockPlatform.escapeHtml(item.detail) + '</p></div>';
        }).join('');
    }

    async function loadSettings() {
        const settings = await StockPlatform.request($, { url: endpoints.settings });
        StockPlatform.setValue('deepseekEnabled', String(settings.deepseek.enabled));
        StockPlatform.setValue('deepseekBaseUrl', settings.deepseek.baseUrl);
        StockPlatform.setValue('deepseekModelName', settings.deepseek.modelName);
        StockPlatform.setValue('deepseekTimeout', settings.deepseek.timeout || 30);
        StockPlatform.setValue('deepseekRemark', settings.deepseek.remark);
        StockPlatform.setValue(
            'deepseekApiKeyStatus',
            (settings.deepseek.apiKeyPreview || '未配置') + '（来源：' + (settings.deepseek.apiKeySource || '未配置') + '）'
        );
        document.getElementById('deepseekClearApiKey').checked = false;
        StockPlatform.setValue('marketSourceProvider', 'Tushare');
        StockPlatform.setValue(
            'marketSourceTokenStatus',
            (settings.marketSource.tokenPreview || '未配置') + '（' + (settings.marketSource.hasToken ? '数据库已保存' : '未配置') + '）'
        );
    }

    async function loadStatus() {
        const status = await StockPlatform.request($, { url: endpoints.status });
        renderStatus(status);
    }

    document.getElementById('deepseekForm').addEventListener('submit', function (event) {
        event.preventDefault();
        StockPlatform.withButtonLoading(deepseekSubmit, '保存中...', function () {
            return StockPlatform.request($, {
                url: endpoints.deepseek,
                method: 'PUT',
                data: {
                    enabled: document.getElementById('deepseekEnabled').value === 'true',
                    base_url: document.getElementById('deepseekBaseUrl').value.trim(),
                    api_key: document.getElementById('deepseekApiKey').value.trim(),
                    model_name: document.getElementById('deepseekModelName').value.trim(),
                    timeout: document.getElementById('deepseekTimeout').value.trim(),
                    clear_api_key: document.getElementById('deepseekClearApiKey').checked,
                    remark: document.getElementById('deepseekRemark').value.trim(),
                },
                contentType: 'application/json',
            });
        }).then(function () {
            StockPlatform.notice('DeepSeek 配置已保存');
            document.getElementById('deepseekApiKey').value = '';
            return Promise.all([loadSettings(), loadStatus()]);
        }).catch(function (error) {
            StockPlatform.notice(error.error || error.message || '保存 DeepSeek 配置失败', true);
        });
    });

    document.getElementById('marketSourceForm').addEventListener('submit', function (event) {
        event.preventDefault();
        StockPlatform.withButtonLoading(marketSourceSubmit, '保存中...', function () {
            return StockPlatform.request($, {
                url: endpoints.marketSource,
                method: 'PUT',
                data: {
                    token: document.getElementById('marketSourceToken').value.trim(),
                    remark: '固定使用 Tushare 获取真实行情数据',
                },
                contentType: 'application/json',
            });
        }).then(function () {
            StockPlatform.notice('Tushare 配置已保存');
            document.getElementById('marketSourceToken').value = '';
            return Promise.all([loadSettings(), loadStatus()]);
        }).catch(function (error) {
            StockPlatform.notice(error.error || error.message || '保存 Tushare 配置失败', true);
        });
    });

    (async function init() {
        try {
            await loadSettings();
            await loadStatus();
        } catch (error) {
            StockPlatform.notice(error.message || '初始化失败', true);
        }
    })();
});
