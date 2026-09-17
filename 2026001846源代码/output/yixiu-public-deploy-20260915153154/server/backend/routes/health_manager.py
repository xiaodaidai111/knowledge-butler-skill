from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

health_manager_bp = Blueprint('health_manager', __name__)

@health_manager_bp.route('/')
def index():
    return jsonify({
        'service': '健康糖豆',
        'description': '健康管理智能体服务',
        'endpoints': {
            'chat': '/api/qwen/chat - 健康管理聊天'
        }
    })

@health_manager_bp.route('/api/qwen/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    messages = data.get("messages", [])
    user_context = data.get("user_context", {})

    if not messages:
        return jsonify({"error": "Empty messages"}), 400

    formatted_messages = []
    for msg in messages:
        role = "assistant" if msg.get("role") == "bot" else "user"
        formatted_messages.append({
            "role": role,
            "content": msg.get("content", "")
        })

    try:
        from HealthManager.HealthManager.agent import generate_health_response
        result = generate_health_response(formatted_messages, user_context)
    except Exception as e:
        logger.error("健康糖豆服务错误: %s", str(e).encode('utf-8', errors='replace').decode('utf-8'))
        result = {"reply": "服务暂时不可用，请稍后再试", "thinking_process": []}

    if isinstance(result, dict):
        response_text = result.get("reply", "")
        thinking_process = result.get("thinking_process", [])
    else:
        response_text = str(result)
        thinking_process = []

    return jsonify({
        "success": True,
        "reply": response_text,
        "thinking_process": thinking_process,
    })