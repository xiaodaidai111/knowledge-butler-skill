"""
知识库检索服务
- 第一阶段：Context Stuffing（直接注入上下文）
- 第二阶段：向量检索（数据增长后自动启用，预留接口）
"""
import json
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 阈值：低于此数量使用 Context Stuffing，高于此数量切换到向量检索
CONTEXT_STUFFING_THRESHOLD = 20


def _find_kb_path() -> Optional[str]:
    """查找 knowledge_base.json 的路径"""
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'maintenance_knowledge_base.json'),
        os.path.join(os.path.dirname(__file__), '..', 'takeout-agent', 'data', 'knowledge_base.json'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'map-agent', 'knowledge_base.json'),
    ]
    for p in candidates:
        full = os.path.abspath(p)
        if os.path.exists(full):
            return full
    return None


def load_knowledge_base(kb_path: Optional[str] = None) -> List[Dict]:
    """加载知识库 JSON"""
    path = kb_path or _find_kb_path()
    if not path or not os.path.exists(path):
        logger.warning("知识库文件未找到: %s", path)
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error("加载知识库失败: %s", e)
        return []


def build_context(kb_path: Optional[str] = None) -> str:
    """
    Context Stuffing：将知识库全部内容格式化为上下文字符串。
    适合条目数 < 20 的场景，直接注入 system prompt。
    """
    kb = load_knowledge_base(kb_path)
    if not kb:
        return ""

    sections = []
    for item in kb:
        title = item.get('title', '未知')
        content_parts = item.get('content', [])
        if isinstance(content_parts, list):
            content = '\n'.join(content_parts)
        else:
            content = str(content_parts)
        tips = item.get('tips', '')
        keywords = item.get('keywords', [])
        section = f"【{title}】"
        if keywords:
            section += f"\n关键词：{', '.join(keywords)}"
        section += f"\n{content}"
        if tips:
            section += f"\n提示：{tips}"
        sections.append(section)

    return '\n\n---\n\n'.join(sections)


def retrieve(query: str, kb_path: Optional[str] = None, top_k: int = 3) -> str:
    """
    智能检索入口：
    - 条目数 < 阈值：返回全部上下文（Context Stuffing）
    - 条目数 >= 阈值：使用关键词匹配（后续可替换为向量检索）
    """
    kb = load_knowledge_base(kb_path)
    if not kb:
        return ""

    if len(kb) < CONTEXT_STUFFING_THRESHOLD:
        # Context Stuffing：全部注入
        return build_context(kb_path)

    # 简单关键词匹配（后续替换为向量检索）
    query_lower = query.lower()
    scored = []
    for item in kb:
        score = 0
        title = item.get('title', '').lower()
        keywords = [k.lower() for k in item.get('keywords', [])]
        content = ' '.join(item.get('content', [])).lower() if isinstance(item.get('content'), list) else str(item.get('content', '')).lower()
        haystack = f"{title}\n{' '.join(keywords)}\n{content}"

        if query_lower and query_lower in haystack:
            score += 5

        for keyword in keywords:
            if keyword and keyword in query_lower:
                score += 4

        # 标题匹配权重最高
        for word in query_lower.split():
            if word in title:
                score += 3
            if any(word in kw for kw in keywords):
                score += 2
            if word in content:
                score += 1

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_items = [item for _, item in scored[:top_k]]

    if not top_items:
        return build_context(kb_path)  # 无匹配时返回全部

    sections = []
    for item in top_items:
        title = item.get('title', '未知')
        content_parts = item.get('content', [])
        content = '\n'.join(content_parts) if isinstance(content_parts, list) else str(content_parts)
        sections.append(f"【{title}】\n{content}")

    return '\n\n---\n\n'.join(sections)


# 预留：向量检索初始化（数据增长后启用）
_vector_store = None

def init_vector_store(kb_path: Optional[str] = None):
    """
    预留接口：初始化向量存储。
    当知识库条目增长到 50+ 时，可在此集成：
    - LangChain InMemoryVectorStore
    - FAISS
    - ChromaDB
    """
    global _vector_store
    logger.info("向量检索初始化（预留接口，当前使用 Context Stuffing）")
    # TODO: 数据增长后实现
    # from langchain_community.vectorstores import FAISS
    # from langchain_openai import OpenAIEmbeddings
    # kb = load_knowledge_base(kb_path)
    # docs = [Document(page_content=item.get('title','') + '\n' + '\n'.join(item.get('content',[])), metadata={"id": item.get('id','')}) for item in kb]
    # _vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())
    pass
