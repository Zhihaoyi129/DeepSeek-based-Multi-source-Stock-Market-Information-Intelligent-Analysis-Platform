from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta

from app.services.setting_service import get_setting

SUPPORTED_RANGE_TYPES = {
    '1m': 30,
    '3m': 90,
    '6m': 180,
    '1y': 365,
    'custom': None,
}
SUPPORTED_INDICATORS = ('ma5', 'ma10', 'ma20', 'rsi', 'macd', 'volume')
DEFAULT_INDICATORS = ['ma5', 'ma10', 'ma20', 'rsi', 'macd', 'volume']


def normalize_symbol(symbol):
    return (symbol or '').strip().upper()


def normalize_indicators(indicators):
    if not indicators:
        return list(DEFAULT_INDICATORS)
    result = []
    for item in indicators:
        indicator = (item or '').strip().lower()
        if indicator in SUPPORTED_INDICATORS and indicator not in result:
            result.append(indicator)
    return result or list(DEFAULT_INDICATORS)


def parse_date_input(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    raise ValueError('日期格式无效，应为 YYYY-MM-DD')


def resolve_range(range_type='3m', start_date=None, end_date=None):
    range_type = (range_type or '3m').lower()
    if range_type not in SUPPORTED_RANGE_TYPES:
        raise ValueError('不支持的时间范围')

    today = date.today()
    if range_type == 'custom':
        start = parse_date_input(start_date)
        end = parse_date_input(end_date)
        if start is None or end is None:
            raise ValueError('自定义范围必须提供开始和结束日期')
        if start > end:
            raise ValueError('开始日期不能晚于结束日期')
    else:
        end = parse_date_input(end_date) or today
        start = end - timedelta(days=SUPPORTED_RANGE_TYPES[range_type] - 1)

    if (end - start).days < 9:
        raise ValueError('查询区间过短，至少需要 10 天')
    return range_type, start, end


def _moving_average(values, period):
    result = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
            continue
        window = values[index - period + 1:index + 1]
        result.append(round(sum(window) / period, 2))
    return result


def _ema(values, period):
    result = []
    multiplier = 2 / (period + 1)
    ema_value = None
    for value in values:
        ema_value = value if ema_value is None else (value - ema_value) * multiplier + ema_value
        result.append(round(ema_value, 2))
    return result


def _rsi(values, period=14):
    if len(values) < period + 1:
        return [None] * len(values)

    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    gains = [max(delta, 0) for delta in deltas]
    losses = [abs(min(delta, 0)) for delta in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    output = [None] * len(values)

    for index in range(period, len(values) - 1):
        gain = gains[index]
        loss = losses[index]
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        if avg_loss == 0:
            output[index + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            output[index + 1] = round(100 - (100 / (1 + rs)), 2)
    return output


def _macd(values):
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    diff = [round(short - long, 2) for short, long in zip(ema12, ema26)]
    signal = _ema(diff, 9)
    histogram = [round(item - sig, 2) for item, sig in zip(diff, signal)]
    return diff, signal, histogram


def build_mock_quote(symbol, range_type='3m', start_date=None, end_date=None, indicators=None, source='mock'):
    normalized_symbol = normalize_symbol(symbol)
    if not normalized_symbol:
        raise ValueError('股票代码不能为空')

    normalized_indicators = normalize_indicators(indicators)
    resolved_range, start, end = resolve_range(range_type, start_date, end_date)
    total_days = (end - start).days + 1

    rng = random.Random(sum(ord(char) for char in normalized_symbol) + total_days)
    phase = (sum(ord(char) for char in normalized_symbol) % 360) / 57.3
    base_price = 12 + (sum(ord(char) for char in normalized_symbol) % 60)
    previous_close = float(base_price)
    series = []
    close_values = []

    for index in range(total_days):
        current_date = start + timedelta(days=index)
        wave = math.sin(index / 8 + phase) * 1.2 + math.cos(index / 15 + phase / 2) * 0.6
        change = wave + rng.uniform(-0.9, 0.9)
        close_price = max(1.2, previous_close + change)
        open_price = max(1.0, previous_close + rng.uniform(-0.8, 0.8))
        high_price = max(open_price, close_price) + abs(rng.uniform(0.2, 1.6))
        low_price = max(0.8, min(open_price, close_price) - abs(rng.uniform(0.2, 1.4)))
        volume = int(850000 + rng.randint(0, 420000) + abs(change) * 170000 + index * 2500)

        close_values.append(round(close_price, 2))
        series.append({
            'date': current_date.isoformat(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume,
        })
        previous_close = close_price

    ma5 = _moving_average(close_values, 5)
    ma10 = _moving_average(close_values, 10)
    ma20 = _moving_average(close_values, 20)
    rsi_values = _rsi(close_values, 14)
    macd_diff, macd_signal, macd_hist = _macd(close_values)

    for index, item in enumerate(series):
        item['ma5'] = ma5[index]
        item['ma10'] = ma10[index]
        item['ma20'] = ma20[index]
        item['rsi'] = rsi_values[index]
        item['macd'] = macd_diff[index]
        item['macdSignal'] = macd_signal[index]
        item['macdHistogram'] = macd_hist[index]

    latest = series[-1]
    first_close = series[0]['close']
    latest_close = latest['close']
    change_percent = round(((latest_close - first_close) / first_close) * 100, 2)
    average_volume = int(sum(item['volume'] for item in series) / len(series))

    indicator_result = {
        'latest': {
            'ma5': latest['ma5'],
            'ma10': latest['ma10'],
            'ma20': latest['ma20'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'macdSignal': latest['macdSignal'],
            'macdHistogram': latest['macdHistogram'],
        },
        'selectedIndicators': normalized_indicators,
    }
    summary = {
        'latestPrice': latest_close,
        'changePercent': change_percent,
        'highestPrice': max(item['high'] for item in series),
        'lowestPrice': min(item['low'] for item in series),
        'averageVolume': average_volume,
        'latestDate': latest['date'],
        'sourceName': source or 'mock',
        'price': latest_close,
        'ma5': latest['ma5'],
        'rsi': latest['rsi'],
    }

    return {
        'symbol': normalized_symbol,
        'rangeType': resolved_range,
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'indicators': normalized_indicators,
        'sourceName': source or 'mock',
        'priceSeries': series,
        'indicatorResult': indicator_result,
        'summary': summary,
    }


def build_tushare_quote(symbol, range_type='3m', start_date=None, end_date=None, indicators=None):
    normalized_symbol = normalize_symbol(symbol)
    if not normalized_symbol:
        raise ValueError('股票代码不能为空')

    market_source = get_setting('market_source')
    token = (market_source.get('token') or '').strip()
    if not token:
        raise ValueError('请先在系统设置中配置 Tushare Token')

    try:
        import tushare as ts
    except ImportError as exc:
        raise ValueError('当前环境未安装 tushare，请先安装 requirements.txt 中的依赖') from exc

    normalized_indicators = normalize_indicators(indicators)
    resolved_range, start, end = resolve_range(range_type, start_date, end_date)
    pro = ts.pro_api(token)
    fields = 'ts_code,trade_date,open,high,low,close,vol,amount'
    try:
        frame = pro.daily(
            ts_code=normalized_symbol,
            start_date=start.strftime('%Y%m%d'),
            end_date=end.strftime('%Y%m%d'),
            fields=fields,
        )
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f'Tushare 行情请求失败：{exc}') from exc

    if frame is None or frame.empty:
        raise ValueError('Tushare 未返回行情数据，请检查股票代码、Token 权限或日期范围')

    rows = frame.to_dict('records')
    rows.sort(key=lambda item: str(item.get('trade_date') or ''))
    series = []
    close_values = []
    for row in rows:
        trade_date = str(row.get('trade_date') or '')
        if len(trade_date) != 8:
            continue
        item = {
            'date': f'{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}',
            'open': _safe_round(row.get('open')),
            'high': _safe_round(row.get('high')),
            'low': _safe_round(row.get('low')),
            'close': _safe_round(row.get('close')),
            'volume': int(float(row.get('vol') or 0)),
            'amount': _safe_round(row.get('amount')),
        }
        if None in (item['open'], item['high'], item['low'], item['close']):
            continue
        close_values.append(item['close'])
        series.append(item)

    if len(series) < 10:
        raise ValueError('Tushare 返回的有效行情不足 10 条，无法计算技术指标')

    return _build_quote_payload(
        symbol=normalized_symbol,
        range_type=resolved_range,
        start=start,
        end=end,
        indicators=normalized_indicators,
        series=series,
        source='tushare',
    )


def _build_quote_payload(symbol, range_type, start, end, indicators, series, source):
    close_values = [item['close'] for item in series]
    ma5 = _moving_average(close_values, 5)
    ma10 = _moving_average(close_values, 10)
    ma20 = _moving_average(close_values, 20)
    rsi_values = _rsi(close_values, 14)
    macd_diff, macd_signal, macd_hist = _macd(close_values)

    for index, item in enumerate(series):
        item['ma5'] = ma5[index]
        item['ma10'] = ma10[index]
        item['ma20'] = ma20[index]
        item['rsi'] = rsi_values[index]
        item['macd'] = macd_diff[index]
        item['macdSignal'] = macd_signal[index]
        item['macdHistogram'] = macd_hist[index]

    latest = series[-1]
    first_close = series[0]['close']
    latest_close = latest['close']
    change_percent = round(((latest_close - first_close) / first_close) * 100, 2)
    average_volume = int(sum(item['volume'] for item in series) / len(series))
    indicator_result = {
        'latest': {
            'ma5': latest['ma5'],
            'ma10': latest['ma10'],
            'ma20': latest['ma20'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'macdSignal': latest['macdSignal'],
            'macdHistogram': latest['macdHistogram'],
        },
        'selectedIndicators': indicators,
    }
    summary = {
        'latestPrice': latest_close,
        'changePercent': change_percent,
        'highestPrice': max(item['high'] for item in series),
        'lowestPrice': min(item['low'] for item in series),
        'averageVolume': average_volume,
        'latestDate': latest['date'],
        'sourceName': source,
        'price': latest_close,
        'ma5': latest['ma5'],
        'rsi': latest['rsi'],
    }
    return {
        'symbol': symbol,
        'rangeType': range_type,
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'indicators': indicators,
        'sourceName': source,
        'priceSeries': series,
        'indicatorResult': indicator_result,
        'summary': summary,
    }


def _safe_round(value, precision=2):
    try:
        return round(float(value), precision)
    except (TypeError, ValueError):
        return None
