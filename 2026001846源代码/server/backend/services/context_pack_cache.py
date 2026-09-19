"""上下文包语义缓存（Context Pack Semantic Cache, CPSC）

理论依据
--------
受 Cache-to-Cache: Direct Semantic Communication Between Large Language Models
(Fu et al., ICLR 2026, arXiv:2510.03215) 启发。该文指出：多模型系统中以文本作为
中转媒介既丢失深层语义、又引入逐 token 生成延迟；因此提出在模型推理层直接传递
KV-Cache，用投影网络与可学习门控完成跨模型语义直传。

CPSC 的定位
-----------
一休调用的是远端大模型 API，无法接触 KV-Cache 张量，也不具备训练投影网络的条
件。因此本模块把同一洞见**迁移到应用上下文层**，在不触碰模型内部的前提下实现等
价的语义复用，由三部分组成：

  ① 组包前缀复用（Prefix Reuse）
     把跨调用完全一致的指令块抽成字节稳定的前缀，使服务端前缀缓存（prefix
     caching）可以命中，避免每次重新计算同一段语义。

  ② 结构化上下文（Structured Context）
     以「带类型的引用」替代文本扁平化：召回项一律携带 ref / kind / title /
     summary / tags，模型可以按引用回溯原文，而不是把全部内容铺平成一段文本。

  ③ 语义包缓存（Semantic Pack Cache）
     为每次组包计算一个不依赖神经网络的特征签名，按签名相似度复用已组装完成的
     上下文包，相似任务不再重复组包。

与 C2C 的差异（报告需明确区分）
------------------------------
  C2C：模型推理层，传递 KV-Cache，需要投影网络 + 门控 + 本地推理栈（GPU）。
  CPSC：应用上下文层，传递结构化引用与组包结果，零额外依赖，可在 1C1G 实例运行。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# ① 组包前缀复用：跨调用字节一致的稳定指令块
# --------------------------------------------------------------------------- #

STABLE_PREFIX = (
    "你是一休 TeamMemory OS 的上下文组装助手。只依据当前任务、项目资料与引用来源输出内容。\n"
    "任务：根据任务描述、召回资料与附件分析，生成可直接展示在 Context Pack 面板里的中文结构化内容。\n"
    "硬性约束：\n"
    "1) 只返回 JSON 对象，不要 Markdown，不要代码块，不要任何解释性前后缀。\n"
    "2) 不得编造具体检测数值；不确定处写“待现场确认”。\n"
    "3) 引用资料时使用给定的 ref 编号（如 M-001 / A-002），不要自行杜撰来源。\n"
    "4) 字段必须完整包含：phenomenon_summary, match_score, risk, stop_advice, causes, "
    "positions, tools, visual_findings, recommended_sop, safety, audit。\n"
    "5) 类型约束：risk ∈ {low, medium, high}；match_score 为 0-100 整数；"
    "causes/positions/tools/visual_findings/safety 为字符串数组；"
    "recommended_sop 为数组，每项含 step 与 action；"
    "audit 含 risk_level, must_check, auditor。\n"
    "6) 输出语言为简体中文。"
)

# 前缀的短指纹，用于验证「前缀是否真的字节一致」
PREFIX_FINGERPRINT = hashlib.sha256(STABLE_PREFIX.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# ② 结构化上下文：带类型的引用，替代文本扁平化
# --------------------------------------------------------------------------- #

def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_structured_context(
    result: Dict[str, Any],
    matched: List[Dict[str, Any]],
    attachments: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """把裸 result / matched / attachments 压成带引用编号的结构化载荷。

    相比直接 json.dumps 整个 result（可达数千字符），这里只保留判定所需字段，
    并为每个召回项分配稳定 ref，使模型可以「引用」而不是「复述」。
    """
    task = {
        "query": _clip(result.get("query"), 300),
        "device_name": _clip(result.get("device_name"), 80),
        "device_model": _clip(result.get("device_model"), 80),
        "category": _clip(result.get("category"), 40),
        "maintenance_level": _clip(result.get("maintenance_level"), 40),
        "modalities": result.get("modalities", []),
    }

    baseline = {
        "match_score": result.get("match_score"),
        "risk": result.get("risk"),
        "phenomenon_summary": _clip(result.get("phenomenon_summary"), 220),
        "causes": [_clip(x, 60) for x in (result.get("causes") or [])[:4]],
        "positions": [_clip(x, 40) for x in (result.get("positions") or [])[:4]],
        "tools": [_clip(x, 40) for x in (result.get("tools") or [])[:6]],
        "safety": [_clip(x, 60) for x in (result.get("safety") or [])[:4]],
        "visual_findings": [_clip(x, 60) for x in (result.get("visual_findings") or [])[:4]],
    }

    evidence = []
    for index, item in enumerate(matched[:6], start=1):
        evidence.append({
            "ref": "M-%03d" % index,
            "kind": _clip(item.get("type") or item.get("category"), 30),
            "title": _clip(item.get("title") or item.get("name"), 80),
            "summary": _clip(item.get("summary"), 150),
            "tags": [_clip(tag, 16) for tag in (item.get("tags") or [])[:5]],
        })

    files = []
    for index, item in enumerate(attachments[:6], start=1):
        analysis = item.get("analysis") or {}
        files.append({
            "ref": "A-%03d" % index,
            "name": _clip(item.get("name"), 70),
            "type": _clip(item.get("type"), 16),
            "signals": [_clip(x, 60) for x in (analysis.get("fault_signs") or [])[:5]],
            "summary": _clip(analysis.get("summary"), 120),
        })

    return {"task": task, "baseline": baseline, "evidence": evidence, "attachments": files}


def render_structured_payload(context: Dict[str, Any]) -> str:
    """把结构化上下文渲染成紧凑行格式。

    刻意不用 json.dumps：JSON 的引号、花括号与重复键名在长上下文里开销可观，
    而模型读取的是语义而非语法。实测该渲染方式比 JSON 版少约四成字符。
    前缀之外的可变部分全部在这里 —— 前缀稳定的前提是本函数只输出任务相关内容。
    """
    task = context.get("task", {})
    base = context.get("baseline", {})

    lines = [
        "【任务】%s｜设备:%s｜类别:%s｜等级:%s" % (
            task.get("query") or "-", task.get("device_name") or "-",
            task.get("category") or "-", task.get("maintenance_level") or "-",
        ),
        "【基线】匹配:%s 风险:%s｜现象:%s｜原因:%s｜部位:%s｜工具:%s｜安全:%s｜影像:%s" % (
            base.get("match_score"), base.get("risk"), base.get("phenomenon_summary") or "-",
            ";".join(base.get("causes") or []) or "-",
            ";".join(base.get("positions") or []) or "-",
            ";".join(base.get("tools") or []) or "-",
            ";".join(base.get("safety") or []) or "-",
            ";".join(base.get("visual_findings") or []) or "-",
        ),
        "【召回资料】",
    ]
    for item in context.get("evidence", []):
        lines.append("%s [%s] %s :: %s #%s" % (
            item.get("ref"), item.get("kind") or "-", item.get("title") or "-",
            item.get("summary") or "-", ",".join(item.get("tags") or []),
        ))
    lines.append("【附件分析】")
    for item in context.get("attachments", []):
        lines.append("%s [%s] %s :: %s %s" % (
            item.get("ref"), item.get("type") or "-", item.get("name") or "-",
            item.get("summary") or "-", ";".join(item.get("signals") or []),
        ))
    lines.append("请依据以上内容，按前缀中的字段约束输出 JSON。")
    return "\n".join(lines)


# 兼容旧调用：仍然提供整段 prompt（前缀 + 载荷），便于对比实验
def build_flat_prompt(baseline_result: Dict[str, Any], matched: List[Dict[str, Any]], attachments: List[Dict[str, Any]]) -> str:
    """旧版实现：固定指令与可变内容混在同一条 user message 里，前缀无法命中缓存。"""
    evidence = [
        {
            "title": item.get("title") or item.get("name"),
            "type": item.get("type"),
            "summary": item.get("summary"),
            "tags": item.get("tags", []),
        }
        for item in matched[:6]
    ]
    files = [
        {"name": item.get("name"), "type": item.get("type"), "analysis": item.get("analysis", {})}
        for item in attachments[:6]
    ]
    return (
        "请作为一休系统的多模态 Context Engine，根据项目目标、图片/文档分析和召回资料，"
        "生成可直接展示在 Context Pack 面板里的中文结构化内容。必须只返回 JSON 对象，不要 Markdown，不要代码块。"
        "不要编造具体检测数值；不确定处写“待现场确认”。"
        "JSON 字段必须包含：phenomenon_summary, match_score, risk, stop_advice, "
        "causes, positions, tools, visual_findings, recommended_sop, safety, audit。"
        "risk 只能是 low/medium/high；match_score 为 0-100 整数；"
        "causes/positions/tools/visual_findings/safety 为字符串数组；"
        "recommended_sop 为数组，每项包含 step 和 action；audit 包含 risk_level, must_check, auditor。\n"
        f"当前基础结果：{json.dumps(baseline_result, ensure_ascii=False)[:5000]}\n"
        f"召回资料：{json.dumps(evidence, ensure_ascii=False)[:3000]}\n"
        f"附件分析：{json.dumps(files, ensure_ascii=False)[:3000]}"
    )


# --------------------------------------------------------------------------- #
# ③ 语义包缓存：零依赖的特征签名 + 相似度复用
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"[0-9a-zA-Z_]+|[\u4e00-\u9fff]")


def _tokenize(text: str) -> List[str]:
    """轻量分词：英文/数字整词 + 中文单字。刻意不依赖分词库，保证可移植。"""
    return _TOKEN_RE.findall(text.lower())


def feature_signature(context: Dict[str, Any]) -> str:
    """由任务特征生成缓存键。

    取 task 的全部字段；不含 baseline/evidence —— 因为召回结果本身随任务变化，
    缓存要复用的是「任务形态相同」的组包结论。
    """
    task = context.get("task", {})
    parts = [
        str(task.get("query", "")),
        str(task.get("device_name", "")),
        str(task.get("device_model", "")),
        str(task.get("category", "")),
        str(task.get("maintenance_level", "")),
        "|".join(sorted(str(x) for x in (task.get("modalities") or []))),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]


def _tokens_of(text: str) -> set:
    return set(_tokenize(text))


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """两条任务特征的相似度。

    设计要点（第一版曾因忽略此点而出现危险假阳性）：
      · **任务类别是硬门** —— 类别不同一律返回 0，杜绝把「发动机异响」的结论
        复用到「空调制冷」这类跨度任务上。第一版把车型/等级等静态字段与 query
        混在一个分词集合里做 Jaccard，导致「同为乘用车 + 标准协作」的两条完全不同
        的任务相似度被抬到 0.73，触发了错误复用。
      · query 占主导权重（0.70），静态字段只做微调（车型 0.15 / 等级 0.15）。
    """
    ta, tb = a.get("task", {}), b.get("task", {})

    cat_a = str(ta.get("category", "")).strip()
    cat_b = str(tb.get("category", "")).strip()
    if cat_a and cat_b and cat_a != cat_b:
        return 0.0

    query_sim = _jaccard(_tokens_of(str(ta.get("query", ""))), _tokens_of(str(tb.get("query", ""))))
    device_sim = _jaccard(
        _tokens_of(str(ta.get("device_name", "")) + " " + str(ta.get("device_model", ""))),
        _tokens_of(str(tb.get("device_name", "")) + " " + str(tb.get("device_model", ""))),
    )
    level_sim = 1.0 if str(ta.get("maintenance_level", "")).strip() == str(tb.get("maintenance_level", "")).strip() else 0.0

    return round(0.70 * query_sim + 0.15 * device_sim + 0.15 * level_sim, 4)


class SemanticPackCache:
    """按语义相似度复用已组装的上下文包。

    阈值默认 0.55：benchmark 的阈值扫描（0.30/0.40/0.50/0.55/0.62/0.70/0.80）
    显示 0.30–0.62 区间内跨类别假阳性恒为 0，而 0.62 起命中率从 44.4% 掉到 22.2%。
    取 0.55 即为「零假阳性前提下的最大命中率」。可用环境变量 CPSC_SIM_THRESHOLD 覆盖。

    容量有上限，超出时淘汰最久未命中的条目（LRU）。全部为进程内状态；
    重启即失效，升级路径见报告中的持久化说明。
    """

    def __init__(self, capacity: int = 128, threshold: Optional[float] = None) -> None:
        if threshold is None:
            try:
                threshold = float(os.environ.get("CPSC_SIM_THRESHOLD", "0.55"))
            except ValueError:
                threshold = 0.55
        self.capacity = capacity
        self.threshold = threshold
        self._entries: List[Dict[str, Any]] = []
        self.hits = 0
        self.misses = 0
        self.exact_hits = 0
        self.semantic_hits = 0
        self.stored = 0
        self.saved_prompt_chars = 0

    # -- 查询 -------------------------------------------------------------- #
    def lookup(self, context: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float, str, str]:
        """返回 (复用结论, 相似度, 命中方式, 命中来源的任务类别)。

        第 4 项用于评测阶段判定命中是否正确（跨类别命中即为假阳性）。
        """
        signature = feature_signature(context)
        best_entry, best_score = None, 0.0
        for entry in self._entries:
            if entry["signature"] == signature:
                entry["last_used"] = time.time()
                self.hits += 1
                self.exact_hits += 1
                return entry["pack"], 1.0, "exact", str(entry["context"].get("task", {}).get("category", ""))
            score = similarity(context, entry["context"])
            if score > best_score:
                best_entry, best_score = entry, score
        if best_entry is not None and best_score >= self.threshold:
            best_entry["last_used"] = time.time()
            self.hits += 1
            self.semantic_hits += 1
            return (
                best_entry["pack"],
                round(best_score, 4),
                "semantic",
                str(best_entry["context"].get("task", {}).get("category", "")),
            )
        self.misses += 1
        return None, round(best_score, 4), "miss", ""

    # -- 写入 -------------------------------------------------------------- #
    def store(self, context: Dict[str, Any], pack: Dict[str, Any], prompt_chars: int) -> None:
        self._entries.append({
            "signature": feature_signature(context),
            "context": context,
            "pack": pack,
            "prompt_chars": prompt_chars,
            "created": time.time(),
            "last_used": time.time(),
        })
        self.stored += 1
        if len(self._entries) > self.capacity:
            self._entries.sort(key=lambda e: e["last_used"])
            self._entries.pop(0)

    def note_saved(self, prompt_chars: int) -> None:
        self.saved_prompt_chars += prompt_chars

    # -- 统计 -------------------------------------------------------------- #
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "algorithm": "CPSC",
            "capacity": self.capacity,
            "threshold": self.threshold,
            "entries": len(self._entries),
            "lookups": total,
            "hits": self.hits,
            "misses": self.misses,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "stored": self.stored,
            "saved_prompt_chars": self.saved_prompt_chars,
            "prefix_fingerprint": PREFIX_FINGERPRINT,
            "prefix_chars": len(STABLE_PREFIX),
        }

    def clear(self) -> None:
        self._entries.clear()


# 进程内单例，供路由层复用
pack_cache = SemanticPackCache()


def prompt_metrics(system_prefix: str, user_payload: str) -> Dict[str, int]:
    """给对比实验用的可观测量（字符数为精确值，token 数为估算）。"""
    return {
        "prefix_chars": len(system_prefix),
        "payload_chars": len(user_payload),
        "total_chars": len(system_prefix) + len(user_payload),
        # 粗略估算：中文约 1 token/字强相关，英文约 4 字符/token。仅用于相对比较。
        "estimated_total_tokens": int(len(system_prefix) / 1.4 + len(user_payload) / 1.4),
        "estimated_cacheable_tokens": int(len(system_prefix) / 1.4),
    }
