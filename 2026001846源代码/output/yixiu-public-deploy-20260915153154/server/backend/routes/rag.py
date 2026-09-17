"""
LightRAG 知识图谱检索 API
- POST /api/rag/query   — 查询知识库
- POST /api/rag/insert  — 插入知识
- GET  /api/rag/stats   — 图谱统计
- POST /api/rag/init    — 初始化/批量导入知识库
"""
import os
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

rag_bp = Blueprint("rag", __name__)


@rag_bp.route("/query", methods=["POST"])
def rag_query():
    """查询知识图谱"""
    from services.rag_service import query, is_available

    if not is_available():
        return jsonify({"code": 503, "message": "LightRAG 未安装，请运行: pip install lightrag-hku"}), 503

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    mode = data.get("mode", "hybrid")  # naive / local / global / hybrid / mix

    if not question:
        return jsonify({"code": 400, "message": "缺少 question 参数"}), 400

    valid_modes = ["naive", "local", "global", "hybrid", "mix"]
    if mode not in valid_modes:
        return jsonify({"code": 400, "message": f"无效的 mode，可选: {', '.join(valid_modes)}"}), 400

    try:
        answer = query(question, mode=mode)
        return jsonify({
            "code": 200,
            "data": {
                "question": question,
                "mode": mode,
                "answer": answer
            }
        })
    except Exception as e:
        logger.error("RAG 查询失败: %s", e)
        return jsonify({"code": 500, "message": f"查询失败: {str(e)}"}), 500


@rag_bp.route("/insert", methods=["POST"])
def rag_insert():
    """插入知识文本"""
    from services.rag_service import insert_text, is_available

    if not is_available():
        return jsonify({"code": 503, "message": "LightRAG 未安装"}), 503

    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"code": 400, "message": "缺少 text 参数"}), 400

    try:
        success = insert_text(text)
        if success:
            return jsonify({"code": 200, "message": "知识已插入"})
        else:
            return jsonify({"code": 500, "message": "插入失败"}), 500
    except Exception as e:
        logger.error("RAG 插入失败: %s", e)
        return jsonify({"code": 500, "message": f"插入失败: {str(e)}"}), 500


@rag_bp.route("/stats", methods=["GET"])
def rag_stats():
    """获取图谱统计"""
    from services.rag_service import get_stats

    try:
        stats = get_stats()
        return jsonify({"code": 200, "data": stats})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@rag_bp.route("/init", methods=["POST"])
def rag_init():
    """初始化：批量导入知识库到 LightRAG"""
    from services.rag_service import insert_knowledge_base, is_available, init_rag_storage
    import asyncio

    if not is_available():
        return jsonify({"code": 503, "message": "LightRAG 未安装，请运行: pip install lightrag-hku"}), 503

    data = request.get_json() or {}
    kb_path = data.get("kb_path", "")

    # 如果没指定路径，使用默认路径
    if not kb_path:
        candidates = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'maintenance_knowledge_base.json'),
            os.path.join(os.path.dirname(__file__), '..', 'takeout-agent', 'data', 'knowledge_base.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'map-agent', 'knowledge_base.json'),
        ]
        for p in candidates:
            full = os.path.abspath(p)
            if os.path.exists(full):
                kb_path = full
                break

    if not kb_path or not os.path.exists(kb_path):
        return jsonify({"code": 400, "message": "知识库文件未找到，请指定 kb_path"}), 400

    try:
        # 初始化存储
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(init_rag_storage())
        except RuntimeError:
            asyncio.run(init_rag_storage())

        # 批量导入
        result = insert_knowledge_base(kb_path)
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        logger.error("RAG 初始化失败: %s", e)
        return jsonify({"code": 500, "message": f"初始化失败: {str(e)}"}), 500


@rag_bp.route("/health", methods=["GET"])
def rag_health():
    """健康检查"""
    from services.rag_service import is_available, get_stats

    available = is_available()
    stats = get_stats() if available else {}
    return jsonify({
        "code": 200,
        "data": {
            "available": available,
            "initialized": stats.get("initialized", False),
            "graph_nodes": stats.get("graph_nodes", 0),
            "graph_edges": stats.get("graph_edges", 0),
        }
    })
