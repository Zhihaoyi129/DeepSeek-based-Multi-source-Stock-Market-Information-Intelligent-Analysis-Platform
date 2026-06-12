StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('symbolForm');
    const searchForm = document.getElementById('symbolSearchForm');
    const submitButton = document.getElementById('symbolSubmit');
    const tableContainer = document.getElementById('symbolTable');

    function payloadFromForm() {
        return {
            symbol: document.getElementById('symbolCode').value.trim(),
            name: document.getElementById('symbolName').value.trim(),
            market: document.getElementById('symbolMarket').value.trim() || 'A股',
        };
    }

    function fillForm(row) {
        StockPlatform.setValue('symbolId', row.id || '');
        StockPlatform.setValue('symbolCode', row.symbol || '');
        StockPlatform.setValue('symbolName', row.name || '');
        StockPlatform.setValue('symbolMarket', row.market || 'A股');
    }

    function resetForm() {
        fillForm({ market: 'A股' });
    }

    function renderSymbols(items) {
        tableContainer.innerHTML = StockPlatform.renderTable([
            { title: '代码', render: function (row) { return '<span class="mono">' + StockPlatform.escapeHtml(row.symbol) + '</span>'; } },
            { title: '名称', render: function (row) { return StockPlatform.escapeHtml(row.name); } },
            { title: '市场', render: function (row) { return StockPlatform.renderBadge(row.market || 'A股', 'primary'); } },
            { title: '创建时间', render: function (row) { return StockPlatform.escapeHtml(row.createdAt || '-'); } },
            {
                title: '操作',
                render: function (row) {
                    return '<div class="table-actions">' + [
                        '<a href="#" class="link-btn" data-edit-symbol="' + row.id + '">编辑</a>',
                        '<a href="#" class="link-btn" data-delete-symbol="' + row.id + '">删除</a>',
                    ].join('') + '</div>';
                },
            },
        ], items);
    }

    async function loadSymbols() {
        const keyword = document.getElementById('symbolKeyword').value.trim();
        const data = await StockPlatform.request($, {
            url: endpoints.symbols,
            data: { keyword: keyword },
        });
        renderSymbols(data.items || []);
        StockPlatform.clearStockOptionsCache();
        return data.items || [];
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            await StockPlatform.withButtonLoading(submitButton, '保存中...', async function () {
                const id = document.getElementById('symbolId').value;
                const saved = await StockPlatform.request($, {
                    url: id ? endpoints.symbolBase + id : endpoints.symbols,
                    method: id ? 'PUT' : 'POST',
                    data: payloadFromForm(),
                    contentType: 'application/json',
                });
                resetForm();
                await loadSymbols();
                StockPlatform.notice('常用股票已保存');
            });
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '保存常用股票失败', true);
        }
    });

    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();
        loadSymbols().catch(function (error) {
            StockPlatform.notice(error.error || error.message || '搜索常用股票失败', true);
        });
    });

    tableContainer.addEventListener('click', async function (event) {
        const editTarget = event.target.closest('[data-edit-symbol]');
        const deleteTarget = event.target.closest('[data-delete-symbol]');
        if (!editTarget && !deleteTarget) {
            return;
        }
        event.preventDefault();
        try {
            const items = await loadSymbols();
            if (editTarget) {
                const row = items.find(function (item) {
                    return String(item.id) === editTarget.getAttribute('data-edit-symbol');
                });
                if (row) {
                    fillForm(row);
                }
                return;
            }
            if (!window.confirm('确定删除这只常用股票吗？')) {
                return;
            }
            await StockPlatform.request($, {
                url: endpoints.symbolBase + deleteTarget.getAttribute('data-delete-symbol'),
                method: 'DELETE',
            });
            resetForm();
            await loadSymbols();
            StockPlatform.notice('常用股票已删除');
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '操作常用股票失败', true);
        }
    });

    resetForm();
    loadSymbols().catch(function (error) {
        StockPlatform.notice(error.error || error.message || '加载常用股票失败', true);
    });
});
