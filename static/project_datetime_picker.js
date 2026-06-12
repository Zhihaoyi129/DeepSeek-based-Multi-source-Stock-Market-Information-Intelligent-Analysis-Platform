(function (window, document) {
    const picker = document.createElement('div');
    picker.className = 'datetime-picker hidden';
    document.body.appendChild(picker);

    let activeInput = null;
    let activeMode = 'date';
    let viewDate = new Date();
    let selectedDate = null;

    function pad(value) {
        return String(value).padStart(2, '0');
    }

    function formatDate(date) {
        return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
    }

    function formatDateTime(date, hour, minute, second) {
        return formatDate(date) + ' ' + pad(hour) + ':' + pad(minute) + ':' + pad(second);
    }

    function parseValue(value) {
        const text = String(value || '').trim();
        const match = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/);
        if (!match) {
            return null;
        }
        const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
        if (Number.isNaN(date.getTime())) {
            return null;
        }
        return {
            date: date,
            hour: Number(match[4] || 0),
            minute: Number(match[5] || 0),
            second: Number(match[6] || 0),
        };
    }

    function sameDay(left, right) {
        return left && right &&
            left.getFullYear() === right.getFullYear() &&
            left.getMonth() === right.getMonth() &&
            left.getDate() === right.getDate();
    }

    function setInputValue(date) {
        if (!activeInput || !date) {
            return;
        }
        if (activeMode === 'datetime') {
            const hour = Number(picker.querySelector('[data-time-hour]').value || 0);
            const minute = Number(picker.querySelector('[data-time-minute]').value || 0);
            const second = Number(picker.querySelector('[data-time-second]').value || 0);
            activeInput.value = formatDateTime(date, hour, minute, second);
        } else {
            activeInput.value = formatDate(date);
        }
        activeInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function positionPicker() {
        if (!activeInput) {
            return;
        }
        const rect = activeInput.getBoundingClientRect();
        picker.style.left = Math.min(rect.left, window.innerWidth - 330) + 'px';
        picker.style.top = (rect.bottom + 8) + 'px';
    }

    function render() {
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();
        const first = new Date(year, month, 1);
        const startOffset = first.getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const parsed = parseValue(activeInput ? activeInput.value : '');
        const time = parsed || { hour: 9, minute: 30, second: 0 };
        const cells = [];

        for (let index = 0; index < startOffset; index += 1) {
            cells.push('<button type="button" class="dt-day is-empty" disabled></button>');
        }
        for (let day = 1; day <= daysInMonth; day += 1) {
            const date = new Date(year, month, day);
            const classes = ['dt-day'];
            if (sameDay(date, selectedDate)) {
                classes.push('is-selected');
            }
            if (sameDay(date, new Date())) {
                classes.push('is-today');
            }
            cells.push(
                '<button type="button" class="' + classes.join(' ') + '" data-day="' + day + '">' + day + '</button>'
            );
        }

        picker.innerHTML =
            '<div class="dt-panel">' +
            '<div class="dt-head">' +
            '<button type="button" class="dt-nav" data-prev>&lt;</button>' +
            '<strong>' + year + ' 年 ' + pad(month + 1) + ' 月</strong>' +
            '<button type="button" class="dt-nav" data-next>&gt;</button>' +
            '</div>' +
            '<div class="dt-week"><span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span></div>' +
            '<div class="dt-grid">' + cells.join('') + '</div>' +
            (activeMode === 'datetime' ?
                '<div class="dt-time">' +
                '<input data-time-hour type="number" min="0" max="23" value="' + pad(time.hour) + '">' +
                '<span>:</span>' +
                '<input data-time-minute type="number" min="0" max="59" value="' + pad(time.minute) + '">' +
                '<span>:</span>' +
                '<input data-time-second type="number" min="0" max="59" value="' + pad(time.second) + '">' +
                '</div>' : '') +
            '<div class="dt-actions">' +
            '<button type="button" class="secondary-btn" data-clear>清空</button>' +
            '<button type="button" class="secondary-btn" data-today>今天</button>' +
            '<button type="button" class="primary-btn" data-confirm>确定</button>' +
            '</div>' +
            '</div>';
    }

    function open(input) {
        activeInput = input;
        activeMode = input.dataset.datetimePicker || 'date';
        const parsed = parseValue(input.value);
        selectedDate = parsed ? parsed.date : new Date();
        viewDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
        render();
        positionPicker();
        picker.classList.remove('hidden');
    }

    function close() {
        picker.classList.add('hidden');
        activeInput = null;
    }

    picker.addEventListener('click', function (event) {
        event.stopPropagation();
        const target = event.target;
        if (target.matches('[data-prev]')) {
            viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
            render();
            return;
        }
        if (target.matches('[data-next]')) {
            viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
            render();
            return;
        }
        if (target.matches('[data-day]')) {
            selectedDate = new Date(viewDate.getFullYear(), viewDate.getMonth(), Number(target.dataset.day));
            if (activeMode === 'date') {
                setInputValue(selectedDate);
                close();
            } else {
                setInputValue(selectedDate);
                render();
            }
            return;
        }
        if (target.matches('[data-today]')) {
            selectedDate = new Date();
            viewDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
            setInputValue(selectedDate);
            if (activeMode === 'datetime') {
                render();
            } else {
                close();
            }
            return;
        }
        if (target.matches('[data-clear]')) {
            if (activeInput) {
                activeInput.value = '';
                activeInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
            close();
            return;
        }
        if (target.matches('[data-confirm]')) {
            setInputValue(selectedDate || new Date());
            close();
        }
    });

    document.addEventListener('click', function (event) {
        const target = event.target;
        if (target.matches('[data-datetime-picker]')) {
            event.preventDefault();
            open(target);
            return;
        }
        if (!picker.contains(target)) {
            close();
        }
    });

    window.addEventListener('resize', positionPicker);
    window.addEventListener('scroll', positionPicker, true);
})(window, document);
