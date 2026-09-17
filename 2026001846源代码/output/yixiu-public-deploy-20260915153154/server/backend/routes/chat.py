import re
import logging
import json
from datetime import datetime
from flask import Blueprint, request
from utils import get_db_connection, success_response, error_response, validate_required_fields, decode_token
from llm_core import conversation_manager, llm_config, prompt_manager
from services.ai_gateway import ai_agent

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)


def filter_response(response: str) -> str:
    """过滤和格式化回复内容，确保符合问修助手的回复要求"""
    if not response:
        return response

    # 移除Markdown格式标记
    response = re.sub(r'#{1,6}\s+', '', response)
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
    response = re.sub(r'\*(.*?)\*', r'\1', response)
    response = re.sub(r'`(.*?)`', r'\1', response)
    response = re.sub(r'```[\s\S]*?```', '', response)
    response = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', response)

    # 移除特殊符号，保留中文标点
    response = re.sub(r'[*_`#~]', '', response)

    # 清理多余的空行
    response = re.sub(r'\n{3,}', '\n\n', response)

    response = response.strip()
    return response


@chat_bp.route('/conversations', methods=['POST'])
def create_conversation():
    conversation_id = conversation_manager.create_conversation()
    return success_response({
        'conversation_id': conversation_id,
        'created_at': datetime.now().isoformat()
    }, '会话创建成功')


@chat_bp.route('/messages', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if not data:
            return error_response(400, '请求数据格式错误')

        conversation_id = data.get('conversation_id', '').strip()
        user_msg_content = data.get('message', '').strip()
        page_context = data.get('page_context') or data.get('user_context') or {}

        is_valid, error_msg = validate_required_fields(data, ['conversation_id', 'message'])
        if not is_valid:
            return error_response(400, error_msg)
        if len(user_msg_content) > 500:
            return error_response(400, '消息内容不能超过500字')

        conversation_manager.add_message(conversation_id, 'user', user_msg_content, {'type': 'user_input'})

        thinking_steps = [
            {'type': 'thought', 'step': '接收用户消息', 'content': f'用户输入: {user_msg_content}'},
            {'type': 'thought', 'step': '初始化AI模型', 'content': f'准备调用{ai_agent.settings.provider}模型'}
        ]

        # 加载用户检修能力档案作为上下文
        user_prefs_str = ''
        token = request.headers.get('Authorization')
        if token:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = decode_token(token)
            if payload:
                user_id = payload['user_id']
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # 查询用户检修能力档案（新表）
                        try:
                            cursor.execute(
                                'SELECT specialty, skill_level, equipment_specialties, custom_notes FROM user_maintenance_profiles WHERE user_id = %s',
                                (user_id,)
                            )
                            prefs = cursor.fetchone()
                            if prefs:
                                user_prefs_str = (
                                    f"\n用户检修档案：\n"
                                    f"- 专业方向：{prefs['skill_level'] or '未设置'}\n"
                                    f"- 专业领域：{prefs['specialty'] or '未设置'}\n"
                                    f"- 擅长设备：{prefs['equipment_specialties'] or '未设置'}\n"
                                    f"- 备注：{prefs['custom_notes'] or '无'}\n"
                                    f"请根据用户的技能等级调整回答的深度和专业程度。"
                                )
                                thinking_steps.append({
                                    'type': 'observation', 'step': '加载用户档案',
                                    'content': f'检测到用户档案: {prefs["specialty"]}, {prefs["skill_level"]}'
                                })
                        except Exception:
                            # 新表不存在时静默降级
                            pass
                except Exception as e:
                    logger.error(f"Error loading user profile: {str(e)}")

        try:
            llm = llm_config.create_llm()
            if not llm:
                thinking_steps.append({'type': 'observation', 'step': 'API配置错误', 'content': '统一AI API配置无效'})
                expert_response = "抱歉，智能问修助手的AI服务暂时不可用，请检查API配置。"
                conversation_manager.add_message(conversation_id, 'assistant', expert_response, {
                    'type': 'error', 'thinking_process': thinking_steps
                })
                return success_response({
                    'response': expert_response,
                    'conversation_id': conversation_id,
                    'thinking_process': thinking_steps
                }, '消息发送成功')

            thinking_steps.append({
                'type': 'action', 'step': '调用统一AI模型',
                'content': '发送请求', 'params': {'model': llm_config.model_name}
            })
            page_context_str = ''
            if isinstance(page_context, dict) and page_context:
                page_context_str = (
                    "\n\n当前页面上下文：\n"
                    + json.dumps(page_context, ensure_ascii=False, indent=2)[:6000]
                    + "\n请优先结合这些系统内容回答；如果上下文不足，再说明需要补充的信息。"
                )
            system_prompt = prompt_manager.get_prompt("default") + user_prefs_str + page_context_str
            history = conversation_manager.get_conversation_history(conversation_id, limit=10)
            messages = [{"role": "system", "content": system_prompt}]

            for turn in history:
                if turn['role'] in ('user', 'assistant'):
                    messages.append({'role': turn['role'], 'content': turn['content']})

            thinking_steps.append({
                'type': 'action', 'step': '构建对话上下文',
                'content': f'包含 {len(messages)} 条消息'
            })
            thinking_steps.append({'type': 'action', 'step': '等待AI响应', 'content': 'AI模型正在生成回复...'})

            from langchain_core.messages import HumanMessage, SystemMessage
            langchain_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    langchain_messages.append(SystemMessage(content=msg['content']))
                elif msg['role'] == 'user':
                    langchain_messages.append(HumanMessage(content=msg['content']))

            response = llm.invoke(langchain_messages)
            expert_response = response.content

            thinking_steps.append({'type': 'observation', 'step': '接收AI响应', 'content': '成功获取回复'})

            if "<think>" in expert_response:
                think_match = re.search(r'<think>(.*?)</think>', expert_response, re.DOTALL)
                if think_match:
                    thinking_steps.insert(0, {
                        'type': 'thought', 'step': '模型底层思考',
                        'content': think_match.group(1).strip()
                    })
                    expert_response = re.sub(r'<think>.*?</think>', '', expert_response, flags=re.DOTALL).strip()

            conversation_manager.add_message(conversation_id, 'assistant', expert_response, {
                'type': 'final_response', 'thinking_process': thinking_steps
            })

            return success_response({
                'response': expert_response,
                'conversation_id': conversation_id,
                'thinking_process': thinking_steps
            }, '消息发送成功')

        except Exception as e:
            logger.error(f"Error processing AI message: {str(e)}", exc_info=True)
            thinking_steps.append({'type': 'observation', 'step': '处理失败', 'content': str(e)})
            expert_response = f"抱歉，处理您的请求时出现错误: {str(e)}"
            conversation_manager.add_message(conversation_id, 'assistant', expert_response, {
                'type': 'error', 'thinking_process': thinking_steps
            })
            return success_response({
                'response': expert_response,
                'conversation_id': conversation_id,
                'thinking_process': thinking_steps
            }, '处理出错')

    except Exception as e:
        return error_response(500, f'内部服务器错误：{str(e)}')
