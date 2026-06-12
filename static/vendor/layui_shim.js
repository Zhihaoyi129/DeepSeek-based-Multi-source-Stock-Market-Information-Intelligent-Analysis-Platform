(function (window) {
    if (window.layui && window.layui.jquery) {
        return;
    }

    function param(data) {
        if (!data) {
            return '';
        }
        const pairs = [];
        Object.keys(data).forEach(function (key) {
            const value = data[key];
            if (value === undefined || value === null || value === '') {
                return;
            }
            if (Array.isArray(value)) {
                value.forEach(function (item) {
                    pairs.push(encodeURIComponent(key) + '=' + encodeURIComponent(item));
                });
                return;
            }
            pairs.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
        });
        return pairs.join('&');
    }

    function ajax(options) {
        const method = (options.type || options.method || 'GET').toUpperCase();
        const headers = Object.assign({}, options.headers || {});
        let url = options.url;
        let body = null;
        const query = method === 'GET' ? param(options.data) : '';

        if (query) {
            url += (url.indexOf('?') >= 0 ? '&' : '?') + query;
        } else if (method !== 'GET' && options.data !== undefined) {
            const useJson = options.contentType === 'application/json' || headers['Content-Type'] === 'application/json';
            if (useJson || typeof options.data === 'object') {
                headers['Content-Type'] = 'application/json';
                body = typeof options.data === 'string' ? options.data : JSON.stringify(options.data);
            } else {
                headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
                body = String(options.data);
            }
        }

        return fetch(url, {
            method: method,
            headers: headers,
            body: body,
        }).then(function (response) {
            return response.text().then(function (text) {
                let parsed = text;
                try {
                    parsed = text ? JSON.parse(text) : null;
                } catch (error) {
                    parsed = text;
                }
                if (!response.ok) {
                    if (typeof options.error === 'function') {
                        options.error(response, parsed);
                    }
                    throw parsed;
                }
                if (typeof options.success === 'function') {
                    options.success(parsed);
                }
                return parsed;
            });
        }).catch(function (error) {
            if (typeof options.error === 'function') {
                options.error(null, error);
            }
            throw error;
        });
    }

    const jquery = {
        ajax: ajax,
        param: param,
        each: function (items, callback) {
            if (!items) {
                return;
            }
            Array.prototype.forEach.call(items, function (item, index) {
                callback(index, item);
            });
        },
    };

    window.layui = {
        jquery: jquery,
        use: function (_modules, callback) {
            callback();
        },
    };
})(window);
