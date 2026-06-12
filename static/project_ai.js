StockPlatform.bootstrap(function ($) {
    const endpoints = window.PAGE_ENDPOINTS;
    const form = document.getElementById('aiChatForm');
    const input = document.getElementById('aiMessageInput');
    const submitButton = document.getElementById('aiSubmitButton');
    const clearButton = document.getElementById('clearAiHistory');
    const messages = document.getElementById('aiMessages');

    function nowText() {
        const now = new Date();
        return now.getFullYear() + '-' +
            String(now.getMonth() + 1).padStart(2, '0') + '-' +
            String(now.getDate()).padStart(2, '0') + ' ' +
            String(now.getHours()).padStart(2, '0') + ':' +
            String(now.getMinutes()).padStart(2, '0');
    }

    function formatInline(text) {
        return StockPlatform.escapeHtml(text)
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    }

    function renderMarkdownText(value) {
        const lines = String(value || '').replace(/\r\n/g, '\n').split('\n');
        const output = [];
        let paragraph = [];
        let listType = '';
        let inCode = false;
        let codeLines = [];

        function closeParagraph() {
            if (paragraph.length) {
                output.push('<p>' + paragraph.map(formatInline).join('<br>') + '</p>');
                paragraph = [];
            }
        }

        function closeList() {
            if (listType) {
                output.push('</' + listType + '>');
                listType = '';
            }
        }

        lines.forEach(function (line) {
            if (line.indexOf('```') === 0) {
                if (inCode) {
                    output.push('<pre><code>' + StockPlatform.escapeHtml(codeLines.join('\n')) + '</code></pre>');
                    codeLines = [];
                    inCode = false;
                    return;
                }
                closeParagraph();
                closeList();
                inCode = true;
                return;
            }
            if (inCode) {
                codeLines.push(line);
                return;
            }
            if (!line.trim()) {
                closeParagraph();
                closeList();
                return;
            }

            const heading = line.match(/^(#{1,4})\s+(.+)$/);
            if (heading) {
                closeParagraph();
                closeList();
                const level = heading[1].length;
                output.push('<h' + level + '>' + formatInline(heading[2]) + '</h' + level + '>');
                return;
            }

            const unordered = line.match(/^\s*[-*]\s+(.+)$/);
            const ordered = line.match(/^\s*\d+\.\s+(.+)$/);
            if (unordered || ordered) {
                closeParagraph();
                const targetType = unordered ? 'ul' : 'ol';
                if (listType !== targetType) {
                    closeList();
                    output.push('<' + targetType + '>');
                    listType = targetType;
                }
                output.push('<li>' + formatInline((unordered || ordered)[1]) + '</li>');
                return;
            }
            paragraph.push(line);
        });

        if (inCode) {
            output.push('<pre><code>' + StockPlatform.escapeHtml(codeLines.join('\n')) + '</code></pre>');
        }
        closeParagraph();
        closeList();
        return output.join('');
    }

    function appendMessage(role, content, timeText, modelName) {
        const isUser = role === 'user';
        messages.insertAdjacentHTML(
            'beforeend',
            '<div class="ai-message ' + (isUser ? 'is-user' : 'is-ai') + '">' +
            '<div class="ai-message-meta">' +
            '<strong>' + (isUser ? '我' : 'AI 助手') + '</strong>' +
            '<span>' + StockPlatform.escapeHtml(timeText || nowText()) + (modelName ? ' · ' + StockPlatform.escapeHtml(modelName) : '') + '</span>' +
            '</div>' +
            '<div class="ai-message-body">' + renderMarkdownText(content) + '</div>' +
            '</div>'
        );
        messages.scrollTop = messages.scrollHeight;
        return messages.lastElementChild.querySelector('.ai-message-body');
    }

    function updateMessageBody(body, content) {
        body.innerHTML = renderMarkdownText(content);
        messages.scrollTop = messages.scrollHeight;
    }

    function renderHistory(items) {
        messages.innerHTML = '';
        if (!items || !items.length) {
            appendMessage('ai', '可以询问新闻情绪、技术指标、多源融合决策，或让 AI 帮你解释当前平台的分析逻辑。', nowText());
            return;
        }
        items.forEach(function (item) {
            appendMessage('user', item.question, item.createdAt);
            appendMessage('ai', item.answer, item.createdAt, item.modelName);
        });
    }

    function setLoading(isLoading) {
        input.disabled = isLoading;
        StockPlatform.setButtonLoading(submitButton, isLoading, '发送中...');
    }

    async function loadHistory() {
        const items = await StockPlatform.request($, { url: endpoints.history });
        renderHistory(items || []);
    }

    function parseSsePacket(packet) {
        const event = { name: 'message', payload: {} };
        let data = '';
        packet.split('\n').forEach(function (line) {
            if (line.indexOf('event:') === 0) {
                event.name = line.slice(6).trim();
            }
            if (line.indexOf('data:') === 0) {
                data += line.slice(5).trim();
            }
        });
        if (!data) {
            return event;
        }
        try {
            event.payload = JSON.parse(data);
        } catch (error) {
            event.payload = { message: 'AI 流式响应格式异常。' };
        }
        return event;
    }

    async function submitNormalChat(message) {
        const data = await StockPlatform.request($, {
            url: endpoints.chat,
            method: 'POST',
            data: { message: message },
            contentType: 'application/json',
        });
        appendMessage('ai', data.reply || data.answer || '', data.createdAt || nowText(), data.modelName);
    }

    async function submitStreamChat(message) {
        if (!endpoints.streamChat || !window.ReadableStream) {
            await submitNormalChat(message);
            return;
        }

        const aiBody = appendMessage('ai', '', nowText());
        const response = await fetch(endpoints.streamChat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ message: message }),
        });
        if (!response.ok || !response.body) {
            throw new Error('AI 流式请求失败。');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let reply = '';

        while (true) {
            const result = await reader.read();
            if (result.done) {
                break;
            }
            buffer += decoder.decode(result.value, { stream: true });
            const packets = buffer.split('\n\n');
            buffer = packets.pop() || '';

            for (let index = 0; index < packets.length; index += 1) {
                const event = parseSsePacket(packets[index]);
                if (event.name === 'delta') {
                    reply += event.payload.content || '';
                    updateMessageBody(aiBody, reply);
                }
                if (event.name === 'error') {
                    const messageText = event.payload.message || 'AI 对话失败。';
                    updateMessageBody(aiBody, messageText);
                    const error = new Error(messageText);
                    error.handledInMessage = true;
                    throw error;
                }
            }
        }

        if (buffer.trim()) {
            const event = parseSsePacket(buffer);
            if (event.name === 'error') {
                const messageText = event.payload.message || 'AI 对话失败。';
                updateMessageBody(aiBody, messageText);
                const error = new Error(messageText);
                error.handledInMessage = true;
                throw error;
            }
        }
        if (!reply) {
            updateMessageBody(aiBody, 'AI 没有返回内容。');
        }
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) {
            return;
        }
        appendMessage('user', message, nowText());
        input.value = '';
        try {
            setLoading(true);
            await submitStreamChat(message);
            StockPlatform.notice('AI 回复成功');
        } catch (error) {
            if (!error.handledInMessage) {
                appendMessage('ai', error.error || error.message || 'AI 对话失败', nowText());
            }
            StockPlatform.notice(error.error || error.message || 'AI 对话失败', true);
        } finally {
            setLoading(false);
            input.focus();
        }
    });

    clearButton.addEventListener('click', async function () {
        if (!window.confirm('确定清空 AI 对话记录吗？')) {
            return;
        }
        try {
            await StockPlatform.withButtonLoading(clearButton, '清空中...', async function () {
                await StockPlatform.request($, {
                    url: endpoints.history,
                    method: 'DELETE',
                });
            });
            renderHistory([]);
            StockPlatform.notice('AI 对话记录已清空');
        } catch (error) {
            StockPlatform.notice(error.error || error.message || '清空记录失败', true);
        }
    });

    loadHistory().catch(function (error) {
        StockPlatform.notice(error.error || error.message || '加载 AI 对话记录失败', true);
    });
});
