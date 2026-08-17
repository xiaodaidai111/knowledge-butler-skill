from flask import Blueprint, request, jsonify
import logging
import os
import sys
import io

logger = logging.getLogger(__name__)

map_agent_bp = Blueprint('map_agent', __name__)

_map_agent_mod = None
_map_agent_mtime = None
LOCATION_PLACEHOLDERS = {"", "当前位置", "定位中", "定位中...", "获取位置中", "探索中", "检测地理位置..."}

def _load_map_agent():
    global _map_agent_mod, _map_agent_mtime

    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANGCHAIN_TRACING_V2'] = 'false'
    os.environ['LANGCHAIN_API_KEY'] = ''
    os.environ['LANGCHAIN_ENDPOINT'] = ''
    
    import importlib.util
    map_agent_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'map-agent')
    map_agent_dir = os.path.abspath(map_agent_dir)
    main_file = os.path.join(map_agent_dir, 'main.py')

    try:
        current_mtime = os.path.getmtime(main_file)
    except OSError:
        current_mtime = None

    if _map_agent_mod is not None and _map_agent_mtime == current_mtime:
        return _map_agent_mod

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    if map_agent_dir not in sys.path:
        sys.path.insert(0, map_agent_dir)
    
    spec = importlib.util.spec_from_file_location(
        "map_agent_main",
        main_file
    )
    _map_agent_mod = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(_map_agent_mod)
        _map_agent_mtime = current_mtime
    except UnicodeEncodeError:
        _map_agent_mod = None
        _map_agent_mtime = None
        raise
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return _map_agent_mod

@map_agent_bp.route('/')
def index():
    return jsonify({
        'service': '推荐小泽',
        'description': '地图智能体服务',
        'endpoints': {
            'messages': '/api/messages - 地图智能体对话'
        }
    })

@map_agent_bp.route('/api/messages', methods=['POST'])
def chat():
    global _map_agent_mod, _map_agent_mtime
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conversation_id = data.get("conversation_id", "")
    message = data.get("message", "")
    location = str(data.get("location", "") or "").strip()
    location_coords = data.get("location_coords")
    preferences = data.get("preferences")

    if location in LOCATION_PLACEHOLDERS or "IP定位" in location or "默认定位" in location:
        location = ""
        location_coords = None

    if not location:
        location_coords = None

    if not message:
        return jsonify({"error": "Empty message"}), 400

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        mod = _load_map_agent()
        result = mod.agent.process(
            message,
            location_hint=location,
            location_coords=location_coords,
            preferences=preferences,
        )
        if isinstance(result, dict):
            response = result.get("reply", "")
            thinking_process = result.get("thinking_process", [])
            pois = result.get("pois", [])
        else:
            response = str(result)
            thinking_process = []
            pois = []
    except UnicodeEncodeError:
        _map_agent_mod = None
        _map_agent_mtime = None
        response = "AI response contained unsupported characters."
        thinking_process = []
        pois = []
    except Exception as e:
        _map_agent_mod = None
        _map_agent_mtime = None
        logger.error("Map agent error: %s", repr(e))
        response = "Service temporarily unavailable."
        thinking_process = []
        pois = []
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return jsonify({
        "response": response,
        "thinking_process": thinking_process,
        "pois": pois,
        "status": "success",
        "conversation_id": conversation_id
    })
