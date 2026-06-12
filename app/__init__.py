from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config.config import config

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(config['default'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# 初始化数据库
db = SQLAlchemy(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# 注册所有蓝图
from app.controllers.auth import bp as auth_bp
from app.controllers.common import bp as common_bp
from app.controllers.menu import bp as menu_bp
from app.controllers.project.pages import bp as project_pages_bp
from app.controllers.project.dashboard import bp as project_dashboard_bp
from app.controllers.project.sentiment import bp as project_sentiment_bp
from app.controllers.project.market import bp as project_market_bp
from app.controllers.project.decision import bp as project_decision_bp
from app.controllers.project.history import bp as project_history_bp
from app.controllers.project.past_analysis import bp as project_past_analysis_bp
from app.controllers.project.settings import bp as project_settings_bp
from app.controllers.project.ai import bp as project_ai_bp
from app.controllers.project.tasks import bp as project_tasks_bp
from app.controllers.project.symbols import bp as project_symbols_bp
from app.controllers.system import bp as system_bp
from app.controllers.timezone import bp as timezone_bp
from app.controllers.user import bp as user_bp

app.register_blueprint(project_pages_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(common_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(project_dashboard_bp)
app.register_blueprint(project_sentiment_bp)
app.register_blueprint(project_market_bp)
app.register_blueprint(project_decision_bp)
app.register_blueprint(project_past_analysis_bp)
app.register_blueprint(project_history_bp)
app.register_blueprint(project_settings_bp)
app.register_blueprint(project_ai_bp)
app.register_blueprint(project_tasks_bp)
app.register_blueprint(project_symbols_bp)
app.register_blueprint(system_bp)
app.register_blueprint(timezone_bp)
app.register_blueprint(user_bp)

# 导入用户模型
from app.models.user import User
from app.models.stock_analysis import (
    AIChatRecord,
    DecisionSuggestionRecord,
    MarketAnalysisRecord,
    ScheduledTask,
    SentimentAnalysisRecord,
    StockNewsRecord,
    StockSymbol,
    SystemSetting,
    TaskRunLog,
)

# 创建数据库表
with app.app_context():
    db.create_all()
    from app.services.seed_service import seed_project_data
    seed_project_data()

from app.services.scheduler_service import init_scheduler
init_scheduler(app)


# 登录管理器回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
