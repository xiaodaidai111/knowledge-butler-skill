from datetime import datetime
import json
import logging
import os
import re

from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request
from services.ai_gateway import ai_agent

logger = logging.getLogger(__name__)

openclaw_bp = Blueprint('openclaw', __name__)

try:
    from routes.monitor import get_monitor

    monitor_available = True
except Exception as exc:
    monitor_available = False
    logger.warning('监控模块不可用，错误上报功能将被禁用: %s', exc)

load_dotenv()

DEEPSEEK_API_KEY = ai_agent.settings.api_key
DEEPSEEK_BASE_URL = ai_agent.settings.base_url

DEEPSEEK_MODELS = {
    ai_agent.settings.chat_model: {
        'name': f'{ai_agent.settings.provider} Chat',
        'max_tokens': 8192,
        'context_window': 64000,
        'provider': ai_agent.settings.provider,
        'strengths': ['通用对话', '知识问答', '代码生成', '文本创作'],
    },
    ai_agent.settings.vision_model: {
        'name': f'{ai_agent.settings.provider} Vision',
        'max_tokens': 8192,
        'context_window': 64000,
        'provider': ai_agent.settings.provider,
        'strengths': ['图片理解', '多模态分析', '检修图片识别', '结构化抽取'],
    },
}

DEFAULT_SYSTEM_PROMPT = """你是智学，本系统的智能助手。

你的职责是围绕当前设备检修知识检索与标准作业系统为用户提供帮助，优先回答与以下模块相关的问题：
1. 多模态检索：通过文本、图片、设备型号检索检修知识和手册
2. 智能问修：故障诊断、排查步骤、检修方法指导
3. 知识沉淀：检修案例入库、知识图谱查询、经验沉淀
4. 标准作业：检修标准流程、安全规范、合规指引
5. 检修评估：作业质量评分、风险闭环、整改建议
6. 用户中心：个人档案、检修记录、成就查看

回答要求：
- 优先结合本系统功能给出可执行建议，不要把自己描述成通用聊天机器人
- 用户问题不明确时，先基于当前系统场景做合理理解，再给出简洁追问
- 回答用中文，语气专业、清晰、实用
- 涉及安全操作时必须强调安全防护措施
- 如果问题超出系统能力边界，要明确说明，并尽量给出在本系统内可替代的帮助"""

OPENCLAW_CONFIG = {
    'default_model': ai_agent.settings.chat_model,
    'models': list(DEEPSEEK_MODELS.keys()),
    'max_tokens': 2048,
    'temperature': 0.7,
    'system_prompt': DEFAULT_SYSTEM_PROMPT,
    'auto_model_switch': True,
    'context_summary': True,
}

_conversation_history = {}
_conversation_summaries = {}

MAX_HISTORY_LENGTH = 30
MAX_CONTEXT_TOKENS = 12000
SUMMARY_TRIGGER_LENGTH = 20


def _estimate_tokens(text):
    if not text:
        return 0
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)


def _build_smart_context(user_id, system_prompt, new_message):
    history = _conversation_history.get(user_id, [])
    summary = _conversation_summaries.get(user_id, '')

    messages = []
    if summary:
        messages.append(
            {
                'role': 'system',
                'content': f'{system_prompt}\n\n[之前对话摘要]\n{summary}',
            }
        )
    elif system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})

    total_tokens = _estimate_tokens(system_prompt) + _estimate_tokens(summary)
    recent = []
    for msg in reversed(history):
        msg_tokens = _estimate_tokens(msg.get('content', ''))
        if total_tokens + msg_tokens > MAX_CONTEXT_TOKENS:
            break
        recent.insert(0, msg)
        total_tokens += msg_tokens

    messages.extend(recent)
    messages.append({'role': 'user', 'content': new_message})
    return messages


def _auto_select_model(message):
    if not OPENCLAW_CONFIG.get('auto_model_switch'):
        return OPENCLAW_CONFIG['default_model']

    reasoning_keywords = [
        '证明',
        '推导',
        '推理',
        '为什么',
        '原因',
        '分析',
        '比较',
        '计算',
        '求解',
        '公式',
        '定理',
        '逻辑',
        '步骤',
        'prove',
        'derive',
        'reason',
        'why',
        'analyze',
        'calculate',
        'math',
        'logic',
        'step by step',
    ]
    complex_indicators = ['详细', '深入', '全面', '系统', '完整', 'detailed', 'comprehensive', 'thorough', 'in depth']

    msg_lower = message.lower()
    reasoning_score = sum(1 for kw in reasoning_keywords if kw in msg_lower)
    complexity_score = sum(1 for kw in complex_indicators if kw in msg_lower)

    if reasoning_score >= 2 or (reasoning_score >= 1 and complexity_score >= 1):
        return ai_agent.settings.chat_model
    if len(message) > 200 and reasoning_score >= 1:
        return ai_agent.settings.chat_model
    return ai_agent.settings.chat_model


def _should_summarize(user_id):
    history = _conversation_history.get(user_id, [])
    return len(history) >= SUMMARY_TRIGGER_LENGTH * 2


def _get_openai_client():
    try:
        from openai import OpenAI

        if not DEEPSEEK_API_KEY:
            logger.warning('AI API Key 未配置')
            return None
        return ai_agent.client()
    except ImportError:
        logger.error('openai 库未安装，请运行: pip install openai')
        return None


def _generate_summary(user_id):
    history = _conversation_history.get(user_id, [])
    if len(history) < 4:
        return

    client = _get_openai_client()
    if not client:
        return

    old_messages = history[: len(history) - 6]
    recent_messages = history[len(history) - 6 :]
    summary_content = '\n'.join(
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in old_messages
    )

    try:
        response = client.chat.completions.create(
            model=ai_agent.settings.chat_model,
            messages=[
                {
                    'role': 'system',
                    'content': '请用简洁中文总结以下对话的关键信息，保留重要事实、决策和上下文，不超过 200 字。',
                },
                {'role': 'user', 'content': summary_content},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        new_summary = (response.choices[0].message.content or '').strip()

        existing_summary = _conversation_summaries.get(user_id, '')
        if existing_summary and new_summary:
            combined = client.chat.completions.create(
                    model=ai_agent.settings.chat_model,
                messages=[
                    {
                        'role': 'system',
                        'content': '请将两段对话摘要合并为一段简洁摘要，保留所有关键信息，不超过 200 字。',
                    },
                    {'role': 'user', 'content': f'摘要1:\n{existing_summary}\n\n摘要2:\n{new_summary}'},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            new_summary = (combined.choices[0].message.content or '').strip()

        _conversation_summaries[user_id] = new_summary
        _conversation_history[user_id] = recent_messages
        logger.info('用户 %s 的对话已自动摘要，保留最近 %s 条消息', user_id, len(recent_messages))
    except Exception as e:
        logger.error('生成对话摘要失败: %s', str(e))


def _record_conversation(user_id, user_message, assistant_message):
    history = _conversation_history.setdefault(user_id, [])
    history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': assistant_message})
    if len(history) > MAX_HISTORY_LENGTH * 2:
        _conversation_history[user_id] = history[-MAX_HISTORY_LENGTH * 2 :]


def _call_deepseek(message, model, temperature, max_tokens, system_prompt, user_id='anonymous'):
    client = _get_openai_client()
    if not client:
        return None, 'AI API 未配置或 openai 库未安装', model, False

    if OPENCLAW_CONFIG.get('context_summary') and _should_summarize(user_id):
        _generate_summary(user_id)

    selected_model = _auto_select_model(message) if model == 'auto' else model
    actual_model = selected_model if selected_model in DEEPSEEK_MODELS else ai_agent.settings.chat_model
    model_info = DEEPSEEK_MODELS[actual_model]
    messages = _build_smart_context(user_id, system_prompt, message)

    try:
        kwargs = {
            'model': actual_model,
            'messages': messages,
            'max_tokens': min(int(max_tokens), model_info['max_tokens']),
            'stream': False,
        }
        kwargs['temperature'] = temperature

        response = client.chat.completions.create(**kwargs)
        ai_message = (response.choices[0].message.content or '').strip()
        _record_conversation(user_id, message, ai_message)
        model_switched = actual_model != model and model != 'auto'
        return ai_message, None, actual_model, model_switched
    except Exception as e:
        logger.error('AI API 调用失败: %s', str(e))
        return None, f'AI API 调用失败: {str(e)}', actual_model, False


def _call_deepseek_stream(message, model, temperature, max_tokens, system_prompt, user_id='anonymous'):
    client = _get_openai_client()
    if not client:
        yield json.dumps({'error': 'AI API 未配置或 openai 库未安装'}, ensure_ascii=False)
        return

    if OPENCLAW_CONFIG.get('context_summary') and _should_summarize(user_id):
        _generate_summary(user_id)

    selected_model = _auto_select_model(message) if model == 'auto' else model
    actual_model = selected_model if selected_model in DEEPSEEK_MODELS else ai_agent.settings.chat_model
    model_info = DEEPSEEK_MODELS[actual_model]
    messages = _build_smart_context(user_id, system_prompt, message)

    try:
        kwargs = {
            'model': actual_model,
            'messages': messages,
            'max_tokens': min(int(max_tokens), model_info['max_tokens']),
            'stream': True,
        }
        kwargs['temperature'] = temperature

        yield json.dumps({'model': actual_model}, ensure_ascii=False) + '\n'
        stream = client.chat.completions.create(**kwargs)
        full_response = ''

        for chunk in stream:
            content = ''
            if chunk.choices and chunk.choices[0].delta:
                content = chunk.choices[0].delta.content or ''
            if not content:
                continue
            full_response += content
            yield json.dumps({'content': content}, ensure_ascii=False) + '\n'

        _record_conversation(user_id, message, full_response)
    except Exception as e:
        logger.error('AI 流式调用失败: %s', str(e))
        yield json.dumps({'error': f'AI API 调用失败: {str(e)}'}, ensure_ascii=False) + '\n'


@openclaw_bp.route('/openclaw/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}

    try:
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'code': 400, 'message': '缺少必要参数: message'}), 400

        model = data.get('model', OPENCLAW_CONFIG['default_model'])
        temperature = data.get('temperature', OPENCLAW_CONFIG['temperature'])
        max_tokens = data.get('max_tokens', OPENCLAW_CONFIG['max_tokens'])
        system_prompt = data.get('system_prompt', OPENCLAW_CONFIG['system_prompt'])
        user_id = data.get('user_id') or data.get('conversation_id') or 'anonymous'

        logger.info("OpenClaw 请求: message='%s...', model='%s', user='%s'", message[:50], model, user_id)

        response, error, actual_model, model_switched = _call_deepseek(
            message, model, temperature, max_tokens, system_prompt, user_id
        )
        if error:
            return jsonify({'code': 503, 'message': error}), 503

        resp_data = {
            'response': response,
            'model': actual_model,
            'timestamp': datetime.now().isoformat(),
        }
        if model_switched:
            resp_data['model_switched'] = True
            resp_data['switch_reason'] = '根据问题复杂度自动切换到推理模型'

        return jsonify({'code': 200, 'message': 'success', 'data': resp_data})
    except Exception as e:
        logger.error('OpenClaw 聊天错误: %s', str(e))
        if monitor_available:
            try:
                from openclaw_monitor import ErrorCategory, ErrorSeverity

                monitor = get_monitor()
                monitor._generate_error_report(
                    error_type=type(e).__name__,
                    message=f'OpenClaw 聊天错误: {str(e)}',
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM,
                    context={
                        'endpoint': '/openclaw/chat',
                        'message': data.get('message', '')[:100],
                        'model': data.get('model', ''),
                    },
                )
            except Exception as monitor_error:
                logger.error('生成错误报告失败: %s', monitor_error)

        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@openclaw_bp.route('/openclaw/config', methods=['GET'])
def get_config():
    return jsonify(
        {
            'code': 200,
            'message': 'success',
            'data': {
                'default_model': OPENCLAW_CONFIG['default_model'],
                'models': OPENCLAW_CONFIG['models'],
                'max_tokens': OPENCLAW_CONFIG['max_tokens'],
                'temperature': OPENCLAW_CONFIG['temperature'],
                'system_prompt': OPENCLAW_CONFIG['system_prompt'],
                'auto_model_switch': OPENCLAW_CONFIG.get('auto_model_switch', True),
                'context_summary': OPENCLAW_CONFIG.get('context_summary', True),
                'api_status': 'configured' if DEEPSEEK_API_KEY else 'not_configured',
            },
        }
    )


@openclaw_bp.route('/openclaw/config', methods=['PUT'])
def update_config():
    try:
        data = request.get_json(silent=True) or {}

        if 'default_model' in data:
            OPENCLAW_CONFIG['default_model'] = data['default_model']
        if 'max_tokens' in data:
            OPENCLAW_CONFIG['max_tokens'] = data['max_tokens']
        if 'temperature' in data:
            OPENCLAW_CONFIG['temperature'] = data['temperature']
        if 'system_prompt' in data:
            OPENCLAW_CONFIG['system_prompt'] = data['system_prompt']
        if 'auto_model_switch' in data:
            OPENCLAW_CONFIG['auto_model_switch'] = bool(data['auto_model_switch'])
        if 'context_summary' in data:
            OPENCLAW_CONFIG['context_summary'] = bool(data['context_summary'])

        logger.info('OpenClaw 配置已更新: %s', OPENCLAW_CONFIG)
        return jsonify({'code': 200, 'message': '配置更新成功', 'data': OPENCLAW_CONFIG})
    except Exception as e:
        logger.error('更新 OpenClaw 配置错误: %s', str(e))
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@openclaw_bp.route('/openclaw/models', methods=['GET'])
def get_models():
    model_list = []
    for model_id, info in DEEPSEEK_MODELS.items():
        model_list.append(
            {
                'id': model_id,
                'name': info['name'],
                'max_tokens': info['max_tokens'],
                'context_window': info['context_window'],
                'strengths': info['strengths'],
            }
        )

    return jsonify(
        {
            'code': 200,
            'message': 'success',
            'data': {
                'models': model_list,
                'default': OPENCLAW_CONFIG['default_model'],
                'auto_switch': OPENCLAW_CONFIG.get('auto_model_switch', True),
                'api_status': 'configured' if DEEPSEEK_API_KEY else 'not_configured',
            },
        }
    )


@openclaw_bp.route('/openclaw/health', methods=['GET'])
def health():
    active_users = len([k for k, v in _conversation_history.items() if v])
    total_messages = sum(len(v) for v in _conversation_history.values())

    return jsonify(
        {
            'code': 200,
            'message': 'OpenClaw 服务运行正常',
            'data': {
                'status': 'healthy',
                'api_configured': bool(DEEPSEEK_API_KEY),
                'api_base_url': DEEPSEEK_BASE_URL,
                'version': '3.0.0',
                'active_users': active_users,
                'total_messages': total_messages,
                'features': {
                    'auto_model_switch': OPENCLAW_CONFIG.get('auto_model_switch', True),
                    'context_summary': OPENCLAW_CONFIG.get('context_summary', True),
                    'smart_context': True,
                    'streaming': True,
                },
                'timestamp': datetime.now().isoformat(),
            },
        }
    )


@openclaw_bp.route('/openclaw/stream', methods=['POST'])
def stream_chat():
    data = request.get_json(silent=True) or {}

    try:
        message = data.get('message', '').strip()
        model = data.get('model', OPENCLAW_CONFIG['default_model'])
        temperature = data.get('temperature', OPENCLAW_CONFIG['temperature'])
        max_tokens = data.get('max_tokens', OPENCLAW_CONFIG['max_tokens'])
        system_prompt = data.get('system_prompt', OPENCLAW_CONFIG['system_prompt'])
        user_id = data.get('user_id') or data.get('conversation_id') or 'anonymous'

        if not message:
            return jsonify({'code': 400, 'message': '消息不能为空'}), 400

        return Response(
            _call_deepseek_stream(message, model, temperature, max_tokens, system_prompt, user_id),
            mimetype='text/event-stream',
        )
    except Exception as e:
        logger.error('OpenClaw 流式聊天错误: %s', str(e))
        if monitor_available:
            try:
                from openclaw_monitor import ErrorCategory, ErrorSeverity

                monitor = get_monitor()
                monitor._generate_error_report(
                    error_type=type(e).__name__,
                    message=f'OpenClaw 流式聊天错误: {str(e)}',
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM,
                    context={
                        'endpoint': '/openclaw/stream',
                        'message': data.get('message', '')[:100],
                    },
                )
            except Exception as monitor_error:
                logger.error('生成错误报告失败: %s', monitor_error)

        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@openclaw_bp.route('/openclaw/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id', 'anonymous')
    history_messages = _conversation_history.get(user_id, [])
    summary = _conversation_summaries.get(user_id, '')

    formatted = []
    for i in range(0, len(history_messages), 2):
        pair = {'user': history_messages[i]['content']}
        if i + 1 < len(history_messages):
            pair['assistant'] = history_messages[i + 1]['content']
        formatted.append(pair)

    return jsonify(
        {
            'code': 200,
            'message': 'success',
            'data': {
                'user_id': user_id,
                'total_messages': len(history_messages),
                'has_summary': bool(summary),
                'summary': summary,
                'messages': formatted,
            },
        }
    )


@openclaw_bp.route('/openclaw/history', methods=['DELETE'])
def clear_history():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id', request.args.get('user_id', 'anonymous'))

    _conversation_history.pop(user_id, None)
    _conversation_summaries.pop(user_id, None)

    logger.info('已清除用户 %s 的对话历史和摘要', user_id)
    return jsonify({'code': 200, 'message': '对话历史已清除'})


@openclaw_bp.route('/openclaw/summary', methods=['POST'])
def manual_summary():
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id', 'anonymous')
        history = _conversation_history.get(user_id, [])

        if not history:
            return jsonify({'code': 200, 'message': '没有可摘要的对话历史', 'data': {'summary': ''}})

        _generate_summary(user_id)
        summary = _conversation_summaries.get(user_id, '')

        return jsonify(
            {
                'code': 200,
                'message': '摘要生成成功',
                'data': {
                    'summary': summary,
                    'remaining_messages': len(_conversation_history.get(user_id, [])),
                },
            }
        )
    except Exception as e:
        logger.error('手动摘要失败: %s', str(e))
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500
