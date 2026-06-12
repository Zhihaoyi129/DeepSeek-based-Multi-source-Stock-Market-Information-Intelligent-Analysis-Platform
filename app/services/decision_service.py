from __future__ import annotations

from app.models.stock_analysis import MarketAnalysisRecord, SentimentAnalysisRecord
from app.services.deepseek_service import generate_decision_with_deepseek


def evaluate_decision(sentiment, price, ma5, rsi, include_deepseek=True):
    if sentiment == 'positive' and rsi < 70 and price > ma5:
        decision = 'buy'
        matched_rules = ['情感为正面', 'RSI 小于 70', '当前价格高于 MA5']
        reason_text = '情感、强弱指标与短周期均线同时支持，规则命中买入条件。'
    elif sentiment == 'negative' or rsi > 70:
        decision = 'sell'
        matched_rules = ['情感为负面' if sentiment == 'negative' else 'RSI 大于 70']
        reason_text = '出现负面情绪或超买信号，规则命中卖出条件。'
    else:
        decision = 'hold'
        matched_rules = ['未满足买入与卖出条件']
        reason_text = '当前信号不够集中，建议继续观望。'

    if include_deepseek:
        deepseek_placeholder = generate_decision_with_deepseek({
            'sentiment': sentiment,
            'price': price,
            'ma5': ma5,
            'rsi': rsi,
            'decision': decision,
            'matchedRules': matched_rules,
            'reasonText': reason_text,
        })
    else:
        deepseek_placeholder = {
            'message': '演示种子数据未调用 DeepSeek。',
            'model': 'local-seed',
        }
    return {
        'decision': decision,
        'matchedRules': matched_rules,
        'reasonText': reason_text,
        'deepseekPlaceholder': deepseek_placeholder,
    }


def resolve_sentiment(sentiment_record_id=None, manual_sentiment=None):
    if manual_sentiment:
        return manual_sentiment, None
    if sentiment_record_id:
        record = SentimentAnalysisRecord.query.get(sentiment_record_id)
        if record is None:
            raise ValueError('情感分析记录不存在')
        return record.sentiment, record
    raise ValueError('必须提供情感记录或手动情感结论')


def resolve_market_metrics(market_record_id=None, price=None, ma5=None, rsi=None):
    market_record = None
    if market_record_id:
        market_record = MarketAnalysisRecord.query.get(market_record_id)
        if market_record is None:
            raise ValueError('技术分析记录不存在')
        summary = market_record.get_summary()
        price = price if price is not None else summary.get('price')
        ma5 = ma5 if ma5 is not None else summary.get('ma5')
        rsi = rsi if rsi is not None else summary.get('rsi')

    if price is None or ma5 is None or rsi is None:
        raise ValueError('price、ma5、rsi 不能为空')
    return {
        'price': float(price),
        'ma5': float(ma5),
        'rsi': float(rsi),
        'marketRecord': market_record,
    }
