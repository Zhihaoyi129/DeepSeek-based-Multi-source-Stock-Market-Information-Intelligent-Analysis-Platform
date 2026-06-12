(function (window) {
    function bootstrap(callback) {
        window.layui.use(['jquery'], function () {
            callback(window.layui.jquery);
        });
    }

    function request($, options) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: options.url,
                type: options.method || 'GET',
                data: options.data,
                contentType: options.contentType,
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
        sentimentLabel: sentimentLabel,
        decisionLabel: decisionLabel,
        lineChart: lineChart,
    };
})(window);
