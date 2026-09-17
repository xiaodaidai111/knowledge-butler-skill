import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from utils import Config

# 注册/登录与个人资料是本项目的核心链路，必须保证可用。
# 其它智能体/路由模块如果存在语法/依赖问题，也不应阻塞服务启动。
from routes.auth import auth_bp
from routes.user import user_bp

try:
    from routes.health import health_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    health_bp = None
    logging.getLogger(__name__).error(f"routes.health 加载失败，将跳过注册: {e}")

try:
    from routes.chat import chat_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    chat_bp = None
    logging.getLogger(__name__).error(f"routes.chat 加载失败，将跳过注册: {e}")

try:
    from routes.cook_agent import cook_agent_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    cook_agent_bp = None
    logging.getLogger(__name__).error(f"routes.cook_agent 加载失败，将跳过注册: {e}")

try:
    from routes.restaurants import restaurants_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    restaurants_bp = None
    logging.getLogger(__name__).error(f"routes.restaurants 加载失败，将跳过注册: {e}")

try:
    from routes.openclaw import openclaw_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    openclaw_bp = None
    logging.getLogger(__name__).error(f"routes.openclaw 加载失败，将跳过注册: {e}")

try:
    from routes.restaurant_marker import restaurant_marker_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    restaurant_marker_bp = None
    logging.getLogger(__name__).error(f"routes.restaurant_marker 加载失败，将跳过注册: {e}")

try:
    from routes.community import community_bp  # noqa: F401
except Exception as e:  # noqa: BLE001
    community_bp = None
    logging.getLogger(__name__).error(f"routes.community 加载失败，将跳过注册: {e}")

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # 上传目录配置
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')

    if health_bp:
        app.register_blueprint(health_bp, url_prefix='/api/health')
    if chat_bp:
        app.register_blueprint(chat_bp, url_prefix='/api')
    if restaurants_bp:
        app.register_blueprint(restaurants_bp, url_prefix='/api/restaurants')
    if cook_agent_bp:
        app.register_blueprint(cook_agent_bp, url_prefix='/cook-agent')
    if openclaw_bp:
        app.register_blueprint(openclaw_bp, url_prefix='/api')
    if restaurant_marker_bp:
        app.register_blueprint(restaurant_marker_bp, url_prefix='/api/restaurant-marker')
    if community_bp:
        app.register_blueprint(community_bp, url_prefix='/api/community')

    @app.route('/')
    def hello():
        return '健康饮食智能体系统后端服务运行中 (重构版本)'

    # 全局错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'message': '资源未找到'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    return app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("团团系统 - 模块化重构版")
    print("=" * 60)
    print("启动服务...")
    print(f"数据库: {Config.DATABASE_NAME}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
