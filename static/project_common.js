(function (window) {
    function bootstrap(callback) {
        window.layui.use(['jquery'], function () {
            callback(window.layui.jquery);
        });
    }

    function request($, options) {
        return new Promise(function (resolve, reject) {
            const useJson = options.contentType === 'application/json' && options.data && typeof options.data === 'object';
            $.ajax({
                url: options.url,
                type: options.method || 'GET',
                data: useJson ? JSON.stringify(options.data) : options.data,
                contentType: options.contentType,
                processData: !useJson,
                success: function (payload) {
                    if (payload && payload.code === 0) {
                        resolve(payload.data);
                        return;
                    }
                    reject(payload || { message: '请求失败' });
                },
                error: function (_response, error) {
                    reject(error || { message: '网络请求失败' });
                },
            });
        });
    }

    function notice(message, isError) {
        const el = document.getElementById('pageNotice');
        if (!el) {
            return;
        }
        el.textContent = message || '';
        el.classList.remove('hidden', 'is-error', 'is-success');
        el.classList.add(isError ? 'is-error' : 'is-success');
    }

    function clearNotice() {
        const el = document.getElementById('pageNotice');
        if (!el) {
            return;
        }
        el.textContent = '';
        el.classList.add('hidden');
        el.classList.remove('is-error', 'is-success');
    }

    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function renderBadge(label, tone) {
        return '<span class="badge badge-' + escapeHtml(tone || 'default') + '">' + escapeHtml(label) + '</span>';
    }

    function renderKeyValues(items) {
        if (!items || !items.length) {
            return '<div class="empty-state">暂无数据</div>';
        }
        return items.map(function (item) {
            return (
                '<div class="kv-item">' +
                '<span class="kv-key">' + escapeHtml(item.label) + '</span>' +
                '<span class="kv-value">' + escapeHtml(item.value) + '</span>' +
                '</div>'
            );
        }).join('');
    }

    function renderTable(columns, rows) {
        if (!rows || !rows.length) {
            return '<div class="empty-state">暂无记录</div>';
        }
        const head = columns.map(function (column) {
            return '<th>' + escapeHtml(column.title) + '</th>';
        }).join('');
        const body = rows.map(function (row) {
            return '<tr>' + columns.map(function (column) {
                const value = typeof column.render === 'function' ? column.render(row) : row[column.key];
                return '<td>' + value + '</td>';
            }).join('') + '</tr>';
        }).join('');
        return '<table class="data-table"><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
    }

    function getQueryParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    }

    function buildQuery(params) {
        const query = [];
        Object.keys(params).forEach(function (key) {
            const value = params[key];
            if (value === undefined || value === null || value === '') {
                return;
            }
            if (Array.isArray(value)) {
                value.forEach(function (item) {
                    query.push(encodeURIComponent(key) + '=' + encodeURIComponent(item));
                });
                return;
            }
            query.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
        });
        return query.join('&');
    }

    function setValue(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.value = value == null ? '' : value;
        }
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value == null ? '' : value;
        }
    }

    function setButtonLoading(button, isLoading, loadingText) {
        if (!button) {
            return;
        }
        if (isLoading) {
            if (!button.dataset.originalText) {
                button.dataset.originalText = button.textContent;
            }
            button.disabled = true;
            button.classList.add('is-loading');
            button.textContent = loadingText || '处理中...';
            return;
        }
        button.disabled = false;
        button.classList.remove('is-loading');
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }

    async function withButtonLoading(button, loadingText, task) {
        setButtonLoading(button, true, loadingText);
        try {
            return await task();
        } finally {
            setButtonLoading(button, false);
        }
    }

    let stockOptionsPromise = null;
    let stockOptionsRows = [];

    function clearStockOptionsCache() {
        stockOptionsPromise = null;
        stockOptionsRows = [];
    }

    function loadStockOptions($) {
        if (!stockOptionsPromise) {
            stockOptionsPromise = request($, {
                url: (window.GLOBAL_ENDPOINTS || {}).symbolOptions || '/api/symbols/options',
            }).then(function (rows) {
                stockOptionsRows = rows || [];
                return stockOptionsRows;
            }).catch(function () {
                stockOptionsPromise = null;
                stockOptionsRows = [];
                return [];
            });
        }
        return stockOptionsPromise;
    }

    function stockOptionLabel(row) {
        return (row.symbol || '') + (row.name ? ' · ' + row.name : '');
    }

    function ensureStockDatalist(id, rows) {
        let list = document.getElementById(id);
        if (!list) {
            list = document.createElement('datalist');
            list.id = id;
            document.body.appendChild(list);
        }
        list.innerHTML = (rows || []).map(function (row) {
            return (
                '<option value="' + escapeHtml(stockOptionLabel(row)) + '"></option>'
            );
        }).join('');
    }

    function normalizeStockInputValue(value, rows) {
        const text = String(value || '').trim();
        if (!text) {
            return '';
        }
        const direct = text.split('·')[0].trim();
        const normalizedDirect = direct.toUpperCase();
        const matched = (rows || stockOptionsRows || []).find(function (row) {
            const symbol = String(row.symbol || '').toUpperCase();
            const name = String(row.name || '').trim();
            return (
                symbol === text.toUpperCase() ||
                symbol === normalizedDirect ||
                name === text ||
                stockOptionLabel(row) === text
            );
        });
        return matched ? matched.symbol : normalizedDirect;
    }

    function getStockInputValue(inputId) {
        const input = document.getElementById(inputId);
        return input ? normalizeStockInputValue(input.value, stockOptionsRows) : '';
    }

    async function initStockSelector($, inputId) {
        const input = document.getElementById(inputId);
        if (!input) {
            return [];
        }
        const rows = await loadStockOptions($);
        const listId = inputId + 'StockOptions';
        ensureStockDatalist(listId, rows);
        input.setAttribute('list', listId);
        input.setAttribute('autocomplete', 'off');
        ['change', 'blur'].forEach(function (eventName) {
            input.addEventListener(eventName, function () {
                input.value = normalizeStockInputValue(input.value, rows);
            });
        });
        return rows;
    }

    async function initStockSelectors($, inputIds) {
        const rows = await loadStockOptions($);
        (inputIds || []).forEach(function (inputId) {
            const input = document.getElementById(inputId);
            if (!input) {
                return;
            }
            const listId = inputId + 'StockOptions';
            ensureStockDatalist(listId, rows);
            input.setAttribute('list', listId);
            input.setAttribute('autocomplete', 'off');
            ['change', 'blur'].forEach(function (eventName) {
                input.addEventListener(eventName, function () {
                    input.value = normalizeStockInputValue(input.value, rows);
                });
            });
        });
        return rows;
    }

    async function initStockAppendSelector($, pickerId, addButtonId, targetId) {
        await initStockSelector($, pickerId);
        const picker = document.getElementById(pickerId);
        const button = document.getElementById(addButtonId);
        const target = document.getElementById(targetId);
        if (!picker || !button || !target) {
            return;
        }
        button.addEventListener('click', function () {
            const symbol = normalizeStockInputValue(picker.value, stockOptionsRows);
            if (!symbol) {
                return;
            }
            const current = target.value
                .replace(/\n/g, ',')
                .split(',')
                .map(function (item) { return item.trim().toUpperCase(); })
                .filter(Boolean);
            if (current.indexOf(symbol) === -1) {
                current.push(symbol);
            }
            target.value = current.join(', ');
            picker.value = '';
        });
    }

    function showProgressOverlay(overlayId, textId, barId, steps) {
        const overlay = document.getElementById(overlayId);
        const text = document.getElementById(textId);
        const bar = document.getElementById(barId);
        if (!overlay || !text) {
            return function () {};
        }
        const progressSteps = steps && steps.length ? steps : ['处理中...'];
        let index = 0;
        let timer = null;

        function syncProgress() {
            text.textContent = progressSteps[index];
            if (bar) {
                bar.style.width = Math.round(((index + 1) / progressSteps.length) * 92) + '%';
            }
        }

        overlay.classList.add('is-visible');
        overlay.setAttribute('aria-hidden', 'false');
        syncProgress();
        timer = window.setInterval(function () {
            index = Math.min(index + 1, progressSteps.length - 1);
            syncProgress();
            if (index === progressSteps.length - 1 && timer) {
                window.clearInterval(timer);
            }
        }, 1400);

        return function () {
            if (timer) {
                window.clearInterval(timer);
            }
            overlay.classList.remove('is-visible');
            overlay.setAttribute('aria-hidden', 'true');
            if (bar) {
                bar.style.width = '0';
            }
        };
    }

    function sentimentLabel(value) {
        return {
            positive: '正面',
            neutral: '中性',
            negative: '负面',
        }[value] || value || '-';
    }

    function decisionLabel(value) {
        return {
            buy: '买入',
            sell: '卖出',
            hold: '观望',
        }[value] || value || '-';
    }

    function lineChart(containerId, values, labels) {
        const el = document.getElementById(containerId);
        if (!el) {
            return;
        }
        if (!values || !values.length) {
            el.innerHTML = '<div class="empty-state">暂无图表数据</div>';
            return;
        }
        const width = 760;
        const height = 260;
        const max = Math.max.apply(null, values);
        const min = Math.min.apply(null, values);
        const points = values.map(function (value, index) {
            const x = (index / Math.max(values.length - 1, 1)) * (width - 40) + 20;
            const y = height - 20 - ((value - min) / Math.max(max - min, 1)) * (height - 50);
            return x.toFixed(2) + ',' + y.toFixed(2);
        }).join(' ');
        el.innerHTML =
            '<svg viewBox="0 0 ' + width + ' ' + height + '" class="line-chart">' +
            '<polyline points="' + points + '" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"></polyline>' +
            '</svg>' +
            '<div class="chart-meta">' +
            '<span>' + escapeHtml(labels[0] || '') + '</span>' +
            '<span>' + escapeHtml(labels[labels.length - 1] || '') + '</span>' +
            '</div>';
    }

    function candlestickChart(containerId, rows) {
        const el = document.getElementById(containerId);
        if (!el) {
            return;
        }
        const items = (rows || []).filter(function (item) {
            return item && item.open != null && item.high != null && item.low != null && item.close != null;
        });
        if (!items.length) {
            el.innerHTML = '<div class="empty-state">暂无 K 线数据</div>';
            return;
        }

        const width = 900;
        const height = 320;
        const padLeft = 52;
        const padRight = 22;
        const padTop = 18;
        const padBottom = 38;
        const chartWidth = width - padLeft - padRight;
        const chartHeight = height - padTop - padBottom;
        const high = Math.max.apply(null, items.map(function (item) { return Number(item.high); }));
        const low = Math.min.apply(null, items.map(function (item) { return Number(item.low); }));
        const span = Math.max(high - low, 1);
        const slot = chartWidth / items.length;
        const bodyWidth = Math.max(4, Math.min(14, slot * 0.56));

        function y(value) {
            return padTop + ((high - Number(value)) / span) * chartHeight;
        }

        const grid = [0, 0.25, 0.5, 0.75, 1].map(function (ratio) {
            const yy = padTop + ratio * chartHeight;
            const label = (high - ratio * span).toFixed(2);
            return (
                '<line x1="' + padLeft + '" y1="' + yy.toFixed(2) + '" x2="' + (width - padRight) + '" y2="' + yy.toFixed(2) + '" class="candle-grid"></line>' +
                '<text x="10" y="' + (yy + 4).toFixed(2) + '" class="candle-axis">' + escapeHtml(label) + '</text>'
            );
        }).join('');

        const candles = items.map(function (item, index) {
            const x = padLeft + slot * index + slot / 2;
            const openY = y(item.open);
            const closeY = y(item.close);
            const highY = y(item.high);
            const lowY = y(item.low);
            const top = Math.min(openY, closeY);
            const bodyHeight = Math.max(Math.abs(closeY - openY), 2);
            const rising = Number(item.close) >= Number(item.open);
            const tone = rising ? 'is-up' : 'is-down';
            return (
                '<g class="candle ' + tone + '">' +
                '<line x1="' + x.toFixed(2) + '" y1="' + highY.toFixed(2) + '" x2="' + x.toFixed(2) + '" y2="' + lowY.toFixed(2) + '"></line>' +
                '<rect x="' + (x - bodyWidth / 2).toFixed(2) + '" y="' + top.toFixed(2) + '" width="' + bodyWidth.toFixed(2) + '" height="' + bodyHeight.toFixed(2) + '"></rect>' +
                '</g>'
            );
        }).join('');

        const first = items[0] || {};
        const last = items[items.length - 1] || {};
        el.classList.remove('empty-state');
        el.innerHTML =
            '<svg viewBox="0 0 ' + width + ' ' + height + '" class="candlestick-chart" role="img" aria-label="K线图">' +
            grid +
            '<line x1="' + padLeft + '" y1="' + (height - padBottom) + '" x2="' + (width - padRight) + '" y2="' + (height - padBottom) + '" class="candle-axis-line"></line>' +
            candles +
            '</svg>' +
            '<div class="chart-meta">' +
            '<span>' + escapeHtml(first.date || '') + '</span>' +
            '<span>红涨绿跌</span>' +
            '<span>' + escapeHtml(last.date || '') + '</span>' +
            '</div>';
    }

    window.StockPlatform = {
        bootstrap: bootstrap,
        request: request,
        notice: notice,
        clearNotice: clearNotice,
        escapeHtml: escapeHtml,
        renderBadge: renderBadge,
        renderKeyValues: renderKeyValues,
        renderTable: renderTable,
        getQueryParam: getQueryParam,
        buildQuery: buildQuery,
        setValue: setValue,
        setText: setText,
        setButtonLoading: setButtonLoading,
        withButtonLoading: withButtonLoading,
        showProgressOverlay: showProgressOverlay,
        clearStockOptionsCache: clearStockOptionsCache,
        loadStockOptions: loadStockOptions,
        getStockInputValue: getStockInputValue,
        initStockSelector: initStockSelector,
        initStockSelectors: initStockSelectors,
        initStockAppendSelector: initStockAppendSelector,
        sentimentLabel: sentimentLabel,
        decisionLabel: decisionLabel,
        lineChart: lineChart,
        candlestickChart: candlestickChart,
    };
})(window);
