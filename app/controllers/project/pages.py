from flask import Blueprint, redirect, render_template, url_for

bp = Blueprint('project_pages', __name__)


@bp.route('/')
def home():
    return redirect(url_for('project_pages.dashboard_page'))


@bp.route('/project/dashboard')
def dashboard_page():
    return render_template('project_dashboard.html', page_key='dashboard', page_title='平台总览')


@bp.route('/project/sentiment')
def sentiment_page():
    return render_template('project_sentiment.html', page_key='sentiment', page_title='新闻与政策文本情感分析')


@bp.route('/project/market')
def market_page():
    return render_template('project_market.html', page_key='market', page_title='技术指标与交易数据可视化')


@bp.route('/project/decision')
def decision_page():
    return render_template('project_decision.html', page_key='decision', page_title='多源数据融合与决策建议')


@bp.route('/project/past-analysis')
def past_analysis_page():
    return render_template('project_past_analysis.html', page_key='past_analysis', page_title='过往涨跌归因分析')


@bp.route('/project/tasks')
def tasks_page():
    return render_template('project_tasks.html', page_key='tasks', page_title='定时任务管理')


@bp.route('/project/symbols')
def symbols_page():
    return render_template('project_symbols.html', page_key='symbols', page_title='常用股票管理')


@bp.route('/project/ai')
def ai_page():
    return render_template('project_ai.html', page_key='ai', page_title='AI 对话助手')


@bp.route('/project/history')
def history_page():
    return render_template('project_history.html', page_key='history', page_title='分析任务历史中心')


@bp.route('/project/settings')
def settings_page():
    return render_template('project_settings.html', page_key='settings', page_title='系统设置')
