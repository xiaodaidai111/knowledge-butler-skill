import logging
from flask import Blueprint, request
from datetime import datetime, date

from utils import get_db_connection, success_response, error_response, token_required

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/today', methods=['GET'])
@token_required
def get_today_health():
    """获取今日检修概况"""
    user_id = request.user_id
    today = date.today().isoformat()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 查询今日检修记录
            cursor.execute('''
                SELECT id, title, record_type, severity, status, equipment_id, start_time, end_time
                FROM maintenance_records
                WHERE user_id = %s AND DATE(created_at) = %s
                ORDER BY created_at DESC
            ''', (user_id, today))
            records = cursor.fetchall()

            # 统计数据
            total_tasks = len(records)
            completed_tasks = sum(1 for r in records if r.get('status') == 'completed')
            in_progress_tasks = sum(1 for r in records if r.get('status') == 'in_progress')
            pending_tasks = sum(1 for r in records if r.get('status') == 'pending')

            # 检修类型分布
            type_counts = {}
            for r in records:
                rtype = r.get('record_type', 'routine')
                type_counts[rtype] = type_counts.get(rtype, 0) + 1

            # 查询今日告警数
            try:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM risk_alerts WHERE is_resolved = 0 AND DATE(created_at) = %s",
                    (today,)
                )
                alert_count = cursor.fetchone()['cnt']
            except Exception:
                alert_count = 0

            task_list = []
            for r in records:
                task_list.append({
                    'id': r['id'],
                    'name': r['title'],
                    'type': r.get('record_type', 'routine'),
                    'severity': r.get('severity', 'medium'),
                    'status': r['status'],
                    'start_time': str(r.get('start_time', '')),
                    'end_time': str(r.get('end_time', '')),
                })

            return success_response({
                'summary': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': in_progress_tasks,
                    'pending_tasks': pending_tasks,
                    'alert_count': alert_count,
                },
                'type_distribution': type_counts,
                'tasks': task_list,
            }, '获取今日检修概况成功')
    except Exception as e:
        logger.warning(f"获取今日检修概况失败: {e}")
        return success_response({
            'summary': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'pending_tasks': 0,
                'alert_count': 0,
            },
            'type_distribution': {},
            'tasks': [],
        }, '暂无今日检修数据')


@health_bp.route('/goals', methods=['GET'])
@token_required
def get_goals():
    """获取检修目标/计划"""
    user_id = request.user_id
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, code, equipment_category, maintenance_level, estimated_duration
                FROM standard_procedures
                WHERE is_active = 1
                ORDER BY maintenance_level, name
                LIMIT 20
            ''')
            procedures = cursor.fetchall()

        return success_response({
            'procedures': procedures
        }, '获取标准作业流程成功')
    except Exception:
        return success_response({'procedures': []}, '暂无标准作业流程')


@health_bp.route('/goals', methods=['PUT'])
@token_required
def update_goals():
    """更新检修目标（预留接口）"""
    return success_response(None, '更新成功')


@health_bp.route('/meal', methods=['POST'])
@token_required
def record_meal():
    """记录检修作业（兼容旧接口路径）"""
    user_id = request.user_id
    data = request.get_json()
    if not data:
        return error_response(400, '请求数据格式错误')

    title = data.get('title', '检修记录')
    record_type = data.get('record_type', 'routine')
    description = data.get('description', '')
    equipment_id = data.get('equipment_id')

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO maintenance_records (user_id, title, record_type, description, equipment_id, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            ''', (user_id, title, record_type, description, equipment_id))
            conn.commit()
            return success_response({'id': cursor.lastrowid}, '记录检修作业成功')
    except Exception as e:
        logger.warning(f"记录检修作业失败: {e}")
        return error_response(500, f'记录失败：{str(e)}')


@health_bp.route('/water', methods=['POST'])
@token_required
def record_water():
    """更新检修进度（兼容旧接口路径）"""
    user_id = request.user_id
    data = request.get_json() or {}
    record_id = data.get('record_id')
    status = data.get('status', 'in_progress')

    if not record_id:
        return error_response(400, '缺少记录ID')

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE maintenance_records SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            ''', (status, record_id, user_id))
            conn.commit()
            return success_response(None, '更新检修进度成功')
    except Exception as e:
        logger.warning(f"更新检修进度失败: {e}")
        return error_response(500, f'更新失败：{str(e)}')


@health_bp.route('/chat', methods=['POST'])
@token_required
def health_chat():
    """标准作业智能问答（兼容旧接口路径）"""
    data = request.get_json()
    if not data:
        return error_response(400, "请求数据格式错误")

    messages = data.get("messages", [])
    if not messages:
        return error_response(400, "消息内容不能为空")

    formatted_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        if role == "bot":
            role = "assistant"
        elif role not in ["user", "assistant", "system"]:
            role = "user"

        content = msg.get("content", "").strip()
        if content:
            formatted_messages.append({"role": role, "content": content})

    if not formatted_messages:
        return error_response(400, "有效消息为空")

    try:
        from llm_core import llm_config
        llm = llm_config.create_llm()
        if not llm:
            return error_response(500, "AI服务暂时不可用，请稍后再试")

        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        system_msg = SystemMessage(content="你是设备检修标准作业智能助手，专注于解答标准作业流程、安全规范和检修方法相关的问题。请给出专业、准确、可操作的回答。")
        langchain_messages = [system_msg]
        for msg in formatted_messages:
            if msg['role'] == 'system':
                langchain_messages.append(SystemMessage(content=msg['content']))
            elif msg['role'] == 'user':
                langchain_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                langchain_messages.append(AIMessage(content=msg['content']))

        response = llm.invoke(langchain_messages)
        return success_response({
            "reply": response.content,
            "thinking_process": []
        })
    except Exception as e:
        logger.error(f"标准作业问答错误: {str(e)}")
        return error_response(500, "AI服务暂时不可用，请稍后再试")
