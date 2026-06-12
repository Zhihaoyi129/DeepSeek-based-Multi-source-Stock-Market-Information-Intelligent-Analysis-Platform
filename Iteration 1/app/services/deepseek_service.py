PLACEHOLDER_MESSAGE = 'DeepSeek integration pending'


def _build_placeholder(task_name, payload=None):
    return {
        'enabled': False,
        'task': task_name,
        'message': PLACEHOLDER_MESSAGE,
        'result': None,
        'request': payload or {},
    }


def analyze_sentiment_with_deepseek(payload):
    return _build_placeholder('sentiment_analysis', payload)


def generate_decision_with_deepseek(payload):
    return _build_placeholder('decision_advice', payload)
