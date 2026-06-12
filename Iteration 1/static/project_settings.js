StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const statusContainer = document.getElementById('settingsStatus');

    function renderStatus(data) {
        statusContainer.innerHTML = [
            {
                title: '数据库状态',
                detail: data.database,
            },
            {
                title: 'DeepSeek 状态',
                detail: (data.deepseek.enabled ? '已启用' : '未启用') + ' · ' + (data.deepseek.remark || '-'),
            },
            {
                title: '行情数据源',
                detail: (data.marketSource.provider || 'mock') + ' · ' + (data.marketSource.remark || '-'),
            },
            {
                title: '数据统计',
                detail: '股票 ' + data.statistics.symbols + ' / 情感 ' + data.statistics.sentimentRecords + ' / 技术 ' + data.statistics.marketRecords + ' / 决策 ' + data.statistics.decisionRecords,
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
        StockPlatform.setValue('deepseekRemark', settings.deepseek.remark);
        StockPlatform.setValue('marketSourceProvider', settings.marketSource.provider);
        StockPlatform.setValue('marketSourceRemark', settings.marketSource.remark);
    }

    async function loadStatus() {
        const status = await StockPlatform.request($, { url: endpoints.status });
        renderStatus(status);
    }

    document.getElementById('deepseekForm').addEventListener('submit', function (event) {
        event.preventDefault();
        StockPlatform.request($, {
            url: endpoints.deepseek,
            method: 'PUT',
            data: {
                enabled: document.getElementById('deepseekEnabled').value === 'true',
                base_url: document.getElementById('deepseekBaseUrl').value.trim(),
                api_key: document.getElementById('deepseekApiKey').value.trim(),
                model_name: document.getElementById('deepseekModelName').value.trim(),
                remark: document.getElementById('deepseekRemark').value.trim(),
            },
            contentType: 'application/json',
        }).then(function () {
            StockPlatform.notice('DeepSeek 配置已保存');
            return loadStatus();
        }).catch(function (error) {
            StockPlatform.notice(error.error || error.message || '保存 DeepSeek 配置失败', true);
        });
    });

    document.getElementById('marketSourceForm').addEventListener('submit', function (event) {
        event.preventDefault();
        StockPlatform.request($, {
            url: endpoints.marketSource,
            method: 'PUT',
            data: {
                provider: document.getElementById('marketSourceProvider').value,
                token: document.getElementById('marketSourceToken').value.trim(),
                remark: document.getElementById('marketSourceRemark').value.trim(),
            },
            contentType: 'application/json',
        }).then(function () {
            StockPlatform.notice('行情数据源配置已保存');
            return loadStatus();
        }).catch(function (error) {
            StockPlatform.notice(error.error || error.message || '保存行情配置失败', true);
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
