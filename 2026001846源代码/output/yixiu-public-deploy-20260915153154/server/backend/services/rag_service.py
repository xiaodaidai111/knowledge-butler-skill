"""
LightRAG 知识图谱检索服务
- LLM: 统一 AI Agent 网关（默认阿里云百炼 / Qwen）
- Embedding: 统一 AI Agent 网关（默认 DashScope text-embedding-v4）
- 支持 5 种查询模式: naive / local / global / hybrid / mix
"""
import os
import urllib.request
# 绕过系统代理，避免 tiktoken 等库因代理不可用而失败
os.environ.setdefault('NO_PROXY', '*')
urllib.request.getproxies = lambda: {}

import json
import asyncio
import logging
import numpy as np
from functools import partial
from typing import Optional
from services.ai_gateway import ai_agent

logger = logging.getLogger(__name__)

# ─── 全局 RAG 实例 ───
_rag_instance = None
_rag_initialized = False

WORKING_DIR = os.path.join(os.path.dirname(__file__), '..', 'lightrag_storage')
EMBEDDING_DIM = 1024


# ─── 统一 LLM 函数 ───
async def unified_llm_func(prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs):
    """统一 LLM 调用函数，兼容 LightRAG 接口"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    try:
        return await ai_agent.async_chat(
            messages=messages,
            model=kwargs.get("model") or ai_agent.settings.chat_model,
            temperature=kwargs.get("temperature", 0),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
    except Exception as e:
        logger.error("统一 LLM 调用失败: %s", e)
        return ""


# ─── DashScope Embedding 函数 ───
async def dashscope_embedding_func(texts: list[str], embedding_dim: int = EMBEDDING_DIM, **kwargs) -> np.ndarray:
    """统一向量化函数"""
    try:
        vectors = await ai_agent.async_embeddings(texts, model=os.getenv("EMBEDDING_MODEL", ai_agent.settings.embedding_model))
        return np.array(vectors)
    except Exception as e:
        logger.error("统一 Embedding 调用失败: %s", e)
        return np.zeros((len(texts), embedding_dim))


def get_rag_instance():
    """获取或创建 LightRAG 单例"""
    global _rag_instance, _rag_initialized
    if _rag_instance is not None:
        return _rag_instance

    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc

        os.makedirs(WORKING_DIR, exist_ok=True)

        _rag_instance = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=unified_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=EMBEDDING_DIM,
                max_token_size=8192,
                func=dashscope_embedding_func,
            ),
        )
        logger.info("LightRAG 实例已创建，工作目录: %s", WORKING_DIR)
        return _rag_instance
    except ImportError as e:
        logger.error("LightRAG 未安装，请运行: pip install lightrag-hku  错误: %s", e)
        return None
    except Exception as e:
        logger.error("LightRAG 初始化失败: %s", e)
        return None


async def init_rag_storage():
    """初始化存储（异步）"""
    global _rag_initialized
    rag = get_rag_instance()
    if rag is None:
        return False
    try:
        await rag.initialize_storages()
        _rag_initialized = True
        logger.info("LightRAG 存储已初始化")
        return True
    except Exception as e:
        logger.error("LightRAG 存储初始化失败: %s", e)
        return False


async def close_rag_storage():
    """关闭存储（异步）"""
    global _rag_instance, _rag_initialized
    if _rag_instance and _rag_initialized:
        try:
            await _rag_instance.finalize_storages()
            _rag_initialized = False
            logger.info("LightRAG 存储已关闭")
        except Exception as e:
            logger.error("LightRAG 存储关闭失败: %s", e)


# ─── 持久化事件循环（解决 Flask 多线程 + LightRAG worker 事件循环冲突） ───
_rag_loop = None
_rag_loop_thread = None


def _get_rag_loop():
    """获取或创建 RAG 专用持久事件循环"""
    global _rag_loop, _rag_loop_thread
    if _rag_loop is None or _rag_loop.is_closed():
        import threading
        _rag_loop = asyncio.new_event_loop()
        _rag_loop_thread = threading.Thread(target=_rag_loop.run_forever, daemon=True)
        _rag_loop_thread.start()
    return _rag_loop


def _run_async(coro):
    """在持久事件循环中运行异步函数，避免 Flask 多线程事件循环冲突"""
    import concurrent.futures
    loop = _get_rag_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=300)


async def _ainsert_text(text: str) -> bool:
    """异步插入文本"""
    rag = get_rag_instance()
    if rag is None:
        return False
    try:
        await rag.ainsert(text)
        logger.info("知识已插入: %s...", text[:50])
        return True
    except Exception as e:
        logger.error("知识插入失败: %s", e)
        return False


async def _aquery(question: str, mode: str = "hybrid") -> str:
    """异步查询"""
    from lightrag import QueryParam
    rag = get_rag_instance()
    if rag is None:
        return "错误：LightRAG 未初始化"
    try:
        result = await rag.aquery(question, param=QueryParam(mode=mode))
        if hasattr(result, '__aiter__'):
            # 流式结果，收集全部
            chunks = []
            async for chunk in result:
                chunks.append(chunk)
            return _normalize_rag_result(''.join(chunks), question)
        return _normalize_rag_result(result, question)
    except Exception as e:
        logger.error("LightRAG 查询失败: %s", e)
        return f"查询出错: {str(e)}"


# ─── 对外接口（同步，供 Flask 路由调用） ───

def _normalize_rag_result(result, question: str) -> str:
    if result is None:
        return _fallback_rag_answer(question)
    text = str(result).strip()
    if not text or text.lower() == "none":
        return _fallback_rag_answer(question)
    return text


def _fallback_rag_answer(question: str) -> str:
    q = question or "\u8bbe\u5907\u68c0\u4fee\u95ee\u9898"
    return (
        f"\u77e5\u8bc6\u5e93\u6682\u65f6\u6ca1\u6709\u76f4\u63a5\u547d\u4e2d\u201c{q}\u201d\u7684\u5b8c\u6574\u7b54\u6848\u3002"
        "\u5efa\u8bae\u5148\u6309\u6807\u51c6\u68c0\u4fee\u6d41\u7a0b\u6392\u67e5\uff1a"
        "1. \u65ad\u7535\u6216\u7184\u706b\u5e76\u505a\u597d\u5b89\u5168\u9632\u62a4\uff1b"
        "2. \u6838\u5bf9\u8bbe\u5907\u578b\u53f7\u3001\u6545\u969c\u73b0\u8c61\u3001\u62a5\u8b66\u4fe1\u606f\u548c\u6700\u8fd1\u4e00\u6b21\u7ef4\u62a4\u8bb0\u5f55\uff1b"
        "3. \u6309\u7535\u6e90/\u71c3\u6cb9\u6216\u4f9b\u80fd\u3001\u63a7\u5236\u4fe1\u53f7\u3001\u6267\u884c\u90e8\u4ef6\u3001\u673a\u68b0\u78e8\u635f\u7684\u987a\u5e8f\u9010\u9879\u68c0\u67e5\uff1b"
        "4. \u62cd\u6444\u73b0\u573a\u7167\u7247\u5e76\u8bb0\u5f55\u68c0\u6d4b\u6570\u636e\uff0c\u4fbf\u4e8e\u540e\u7eed\u5165\u5e93\u590d\u76d8\u3002"
    )


def insert_text(text: str) -> bool:
    """插入单条知识文本"""
    return _run_async(_ainsert_text(text))


def insert_chunks(chunks: list, source: str = "") -> dict:
    """批量插入切片文本，返回成功/失败计数。"""
    if not chunks:
        return {"success": True, "total": 0, "inserted": 0, "failed": 0}
    inserted = 0
    failed_items = []
    for idx, chunk in enumerate(chunks):
        text = str(chunk or "").strip()
        if not text:
            continue
        # 给每块加上来源前缀，便于检索时回溯
        full_text = f"[来源:{source or '未知'}]\n{text}" if source else text
        try:
            if _run_async(_ainsert_text(full_text)):
                inserted += 1
            else:
                failed_items.append(idx)
        except Exception as exc:
            logger.error("切片 %d 插入失败: %s", idx, exc)
            failed_items.append(idx)
    return {
        "success": len(failed_items) == 0,
        "total": len(chunks),
        "inserted": inserted,
        "failed": len(failed_items),
        "failed_indices": failed_items,
    }


def search_similar(query: str, limit: int = 5, mode: str = "hybrid") -> list:
    """
    向量相似度检索：调用 LightRAG 检索，返回 top 命中块。
    若 LightRAG 未就绪，回退到知识库 JSON 关键词匹配。
    """
    if not query:
        return []
    # 优先用 LightRAG hybrid 检索
    try:
        rag = get_rag_instance()
        if rag is not None:
            from lightrag import QueryParam
            result_text = _run_async(_aquery(query, mode=mode))
            # 把整段结果按段落切片返回
            if result_text and result_text != _fallback_rag_answer(query):
                paragraphs = [p.strip() for p in result_text.split("\n\n") if p.strip()]
                return [{"text": p, "score": 1.0, "source": "lightrag"} for p in paragraphs[:limit]]
    except Exception as exc:
        logger.warning("LightRAG 检索失败，回退到本地匹配: %s", exc)

    # 回退：从本地 knowledge_base.json 关键词匹配
    from services.knowledge_retriever import load_knowledge_base
    kb = load_knowledge_base()
    if not kb:
        return []
    query_lower = query.lower()
    scored = []
    for item in kb:
        text = json.dumps(item, ensure_ascii=False).lower()
        score = sum(1 for word in query_lower.split() if word and word in text)
        if score > 0:
            scored.append({"text": item.get("title", ""), "score": score, "source": "local", "raw": item})
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored[:limit]


def insert_knowledge_base(kb_path: str) -> dict:
    """批量导入 knowledge_base.json"""
    if not os.path.exists(kb_path):
        return {"success": False, "error": f"文件不存在: {kb_path}"}

    with open(kb_path, 'r', encoding='utf-8') as f:
        kb = json.load(f)

    success_count = 0
    errors = []
    for item in kb:
        title = item.get('title', '未知')
        content_parts = item.get('content', [])
        content = '\n'.join(content_parts) if isinstance(content_parts, list) else str(content_parts)
        keywords = item.get('keywords', [])
        tips = item.get('tips', '')

        text = f"【{title}】\n"
        if keywords:
            text += f"关键词：{', '.join(keywords)}\n"
        text += content
        if tips:
            text += f"\n提示：{tips}"

        if insert_text(text):
            success_count += 1
        else:
            errors.append(title)

    return {
        "success": True,
        "total": len(kb),
        "inserted": success_count,
        "failed": len(errors),
        "failed_items": errors
    }


def query(question: str, mode: str = "hybrid") -> str:
    """查询知识库"""
    return _run_async(_aquery(question, mode))


def get_stats() -> dict:
    """获取图谱统计信息"""
    rag = get_rag_instance()
    if rag is None:
        return {"initialized": False, "error": "LightRAG 未初始化"}

    stats = {
        "initialized": _rag_initialized,
        "working_dir": WORKING_DIR,
    }

    # 检查存储文件
    graph_file = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    doc_file = os.path.join(WORKING_DIR, "kv_store_full_docs.json")
    chunk_file = os.path.join(WORKING_DIR, "kv_store_text_chunks.json")

    if os.path.exists(graph_file):
        try:
            import networkx as nx
            G = nx.read_graphml(graph_file)
            stats["graph_nodes"] = G.number_of_nodes()
            stats["graph_edges"] = G.number_of_edges()
        except Exception:
            stats["graph_nodes"] = -1
            stats["graph_edges"] = -1

    if os.path.exists(doc_file):
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                docs = json.load(f)
            stats["documents"] = len(docs)
        except Exception:
            stats["documents"] = -1

    if os.path.exists(chunk_file):
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            stats["chunks"] = len(chunks)
        except Exception:
            stats["chunks"] = -1

    return stats


def is_available() -> bool:
    """检查 LightRAG 是否可用"""
    try:
        import lightrag
        return True
    except ImportError:
        return False
