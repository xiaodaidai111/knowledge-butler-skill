"""A2A Registry 对外 API。"""
from .registry import (  # noqa: F401
    register_agent, list_agents, get_agent, send_message,
    get_task, list_messages, handle_request, attach_flask_blueprint,
    reset_for_tests, A2A_DB_PATH, DEFAULT_AGENTS,
)
