import io
import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from aios_runtime import AIOS_TECH_STACK, TIANGONG_OPERATION_PROMPT

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=False)

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# 天工（综合智能中枢）总指挥人设 —— miniclaw Agent 的系统提示词
TIANGONG_PROMPT = TIANGONG_OPERATION_PROMPT + """

# 核心原则：先了解，再行动
收到指令后先读取项目、任务、Context Pack、协作记录、Memory、Skill、Eval 和 Agent 状态，再依据真实数据决策。不得把计划、模型猜测或演示数据写成已完成事实；缺失信息必须明确标记。

# 你的身份与职责
你是“一休”AI 原生项目协作系统的 Agent Router，统筹观微（Context Engine）、执矩（Task Execution）、博闻（Team Memory）、和鸣（Memory Evolution）与明鉴（Eval Lab）。

# 工具调用格式
[TOOL_CALL]工具名称|{"参数": "值"}[/TOOL_CALL]
一次可调多个工具。所有结论应能追溯到工具结果、项目资料或人工确认。

# 自主探索策略
- 任何指令：先读取 system_overview，确认当前项目、活跃任务、信息缺口和待审核项。
- 涉及任务：读取任务列表与执行 Trace，避免重复创建，保留负责人、Agent、Skill、输入输出和时间。
- 涉及上下文：检索需求、代码、Issue / PR、聊天决策、Memory、Skill 与 Eval，生成带引用的 Context Pack。
- 涉及执行：先检查权限、成本、风险、验收标准与回滚方案；高风险写入必须请求人工确认。
- 涉及沉淀：只生成待审核 Memory / Skill 候选，保留来源、适用条件、不适用边界与 Eval 结果。
- 工具或数据不可用时：如实说明，给出可执行的补充材料清单，不伪造结果。

# AIOS 执行能力
- aios_plan：把目标拆成“任务确认 → Context Pack → 人 / Agent 分派 → 执行 Trace → Review → Eval → Memory → Skill”的依赖计划。
- aios_execute：按计划执行并记录产物；写操作需 confirmed=true，关键步骤需 Human-in-the-loop。
- aios_inspect：读取进度、失败原因和可恢复点，支持续跑与回滚。

# 回答要求
用清晰中文说明：系统现状、引用依据、执行计划、已完成动作、风险与成本、待人工确认项、下一步。不要暴露密钥、连接串或内部日志。

# 典型场景
- “今天优先处理什么” → 读取项目与任务状态，按风险、截止时间、信息缺口和 Eval 阻断项排序。
- “为 BUG-421 组装上下文” → 召回需求、代码、历史 Memory、相关 Skill 与 Eval，列出证据和缺口。
- “推进当前任务” → 生成执行计划，分派人员和 Agent，记录 Trace，并在 Review / Eval 节点暂停确认。
- “沉淀本次经验” → 从已验证 Trace 提取待审核 Memory，并在多次稳定复用后生成 Skill 候选。
"""


def _register_blueprint(app, import_path, blueprint_name, url_prefix, service_name):
    try:
        module = __import__(import_path, fromlist=[blueprint_name])
        blueprint = getattr(module, blueprint_name)
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.info('%s registered', service_name)
    except Exception as exc:  # noqa: BLE001
        logger.error('%s registration failed: %s', service_name, exc)


def create_unified_app():
    app = Flask(__name__)
    CORS(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    registrations = [
        ('routes.cook_agent', 'cook_agent_bp', '/cook-agent', 'cook-agent service'),
        ('routes.auth', 'auth_bp', '/api/auth', 'auth service'),
        ('routes.user', 'user_bp', '/api/user', 'user service'),
        ('routes.community', 'community_bp', '/api/community', 'community service'),
        ('routes.chat', 'chat_bp', '/api/chat', 'chat service'),
        ('routes.health', 'health_bp', '/api/health', 'health record service'),
        ('routes.restaurants', 'restaurants_bp', '/api/restaurants', 'restaurants service'),
        ('routes.tuantuan', 'tuantuan_bp', '/tuantuan', 'tuantuan service'),
        ('routes.takeout', 'takeout_bp', '/takeout', 'takeout service'),
        ('routes.health_manager_deepseek', 'health_manager_bp', '/health', 'health manager service'),
        # ('routes.map_agent', 'map_agent_bp', '/map', 'map agent service'),  # 已禁用
        (
            'routes.recipe_recommendation',
            'recipe_recommendation_bp',
            '/api/recipe-recommendation',
            'recipe recommendation service',
        ),
        ('routes.openclaw', 'openclaw_bp', '', 'openclaw service'),
        ('routes.speech_asr', 'speech_asr_bp', '', 'speech asr service'),
        ('routes.speech_tts', 'speech_tts_bp', '', 'speech tts service'),
        ('routes.monitor', 'monitor_bp', '/api', 'monitor service'),
        ('routes.ai_services', 'ai_services_bp', '', 'ai services'),
        ('routes.takeaway_health', 'takeaway_health_bp', '', 'takeaway health service'),
        ('routes.yixiu', 'yixiu_bp', '/api/yixiu', 'yixiu web orchestration service'),
        ('routes.maintenance_tasks', 'maintenance_tasks_bp', '/api/maintenance-tasks', 'maintenance tasks service'),
    ]

    for import_path, blueprint_name, url_prefix, service_name in registrations:
        _register_blueprint(app, import_path, blueprint_name, url_prefix, service_name)

    # 挂载 MiniClaw（天工总指挥）ReAct 智能体网关：/miniclaw/chat 等
    try:
        from miniclaw.gateway import MiniClawGateway
        from miniclaw.agent import MiniClawAgent

        _miniclaw_gateway = MiniClawGateway()
        _miniclaw_gateway._load_plugins()  # 加载 system_tools 等内置工具
        _miniclaw_gateway.config.agent_system_prompt = TIANGONG_PROMPT
        _miniclaw_gateway.config.agent_max_tool_calls = 6
        # 用天工人设重建 agent，使新 system prompt 生效
        _miniclaw_gateway.agent = MiniClawAgent(config=_miniclaw_gateway.config)
        app.register_blueprint(_miniclaw_gateway.create_flask_blueprint(), url_prefix='')
        logger.info('miniclaw (天工) service registered — /miniclaw/chat')
    except Exception as exc:  # noqa: BLE001
        logger.error('miniclaw (天工) registration failed: %s', exc)

    # 挂载 AIOS 新架构蓝图：/mcp /a2a /sandbox /trace /opa /memory /api/aios-arch/supervisor
    try:
        from aios_arch.api_gateway import mount_gateway_blueprints
        mount_gateway_blueprints(app)
        logger.info('aios_arch gateway blueprints mounted')
    except Exception as exc:  # noqa: BLE001
        logger.error('aios_arch gateway mount failed: %s', exc)

    @app.route('/miniclaw/ui_operate', methods=['POST'])
    def miniclaw_ui_operate():
        """天工 UI 遥控：根据自然语言指令生成前端操作计划。"""
        from miniclaw.ui_agent import generate_ui_plan
        payload = request.get_json(silent=True) or {}
        message = (payload.get('message') or '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'message 不能为空'}), 400
        result = generate_ui_plan(message)
        return jsonify({'success': result.get('error') is None, 'data': result})

    @app.route('/')
    def index():
        return jsonify(
            {
                'name': '一休 - AI 原生项目协作与团队记忆系统',
                'version': '1.0.0',
                'services': {
                    'cook-agent': '/cook-agent - 兼容服务',
                    'auth': '/api/auth - 用户认证服务',
                    'user': '/api/user - 用户管理服务',
                    'community': '/api/community - 团队协作服务',
                    'health': '/health - 兼容服务',
                    'takeout': '/takeout - 兼容服务',
                    'recipe-recommendation': '/api/recipe-recommendation - 兼容服务',
                    'openclaw': '/openclaw - 智能助手服务',
                    'speech': '/api/speech/transcribe - 语音识别服务',
                    'yixiu': '/api/yixiu - 一休项目协作与多智能体编排服务',
                },
                'status': 'running',
            }
        )

    @app.route('/api/system/health')
    def health_check():
        return jsonify(
            {
                'status': 'healthy',
                'services': ['tuantuan', 'takeout', 'health_manager', 'community', 'speech_asr'],
            }
        )

    @app.route('/api/dashboard/overview')
    def dashboard_overview():
        """首页系统概览数据接口"""
        try:
            from utils import get_db_connection
            stats = {
                'online_equipment': 0,
                'pending_alerts': 0,
                'pending_reviews': 0,
                'today_tasks': 0,
            }
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    # 在线设备数
                    try:
                        cursor.execute("SELECT COUNT(*) AS cnt FROM equipment WHERE status IN ('normal', 'warning')")
                        stats['online_equipment'] = cursor.fetchone()['cnt']
                    except Exception:
                        pass
                    # 待处理告警数
                    try:
                        cursor.execute("SELECT COUNT(*) AS cnt FROM risk_alerts WHERE is_resolved = 0")
                        stats['pending_alerts'] = cursor.fetchone()['cnt']
                    except Exception:
                        pass
                    # 待审核案例数
                    try:
                        cursor.execute("SELECT COUNT(*) AS cnt FROM knowledge_base WHERE status = 'pending_review'")
                        stats['pending_reviews'] = cursor.fetchone()['cnt']
                    except Exception:
                        pass
                    # 今日检修任务数
                    try:
                        cursor.execute(
                            "SELECT COUNT(*) AS cnt FROM maintenance_records WHERE DATE(created_at) = CURDATE()"
                        )
                        stats['today_tasks'] = cursor.fetchone()['cnt']
                    except Exception:
                        pass
            except Exception:
                pass

            return jsonify({'code': 200, 'data': stats, 'message': 'ok'})
        except Exception as e:
            return jsonify({'code': 500, 'message': str(e)}), 500

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({'code': 404, 'message': '资源未找到'}), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    return app


if __name__ == '__main__':
    app = create_unified_app()
    logger.info('=' * 60)
    logger.info('统一智能体服务启动中...')
    logger.info('访问地址: http://localhost:5000')
    logger.info('=' * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
