"""Agent 上下文接力（Agent Context Relay, ACR）

设计依据
--------
Cache-to-Cache（Fu et al., ICLR 2026, arXiv:2510.03215）的核心判断是：多模型协作里
把内部表示压成文本再让下游重新解析，既丢语义又慢，应当直接传语义。

一休的 agent 是远端 API 调用，拿不到 KV-Cache，做不了真正的直传。因此本模块在
**应用上下文层**实现等价思路：agent 之间传递的不是拼接的对话文本，而是带证据、
带置信度、带引用的**结构化接力信封**；下游按自己声明的 consumes 接收投影后的切片，
而不是被动吞下全部上文。

三条硬规则
----------
1. goal / constraints 是只读不变量 —— 中间步骤不得改写，防止目标漂移。
2. 信封必须有界 —— 累积后按置信度裁剪，溢出的 fact 降级为 ref（只留指针）。
3. 下游声明 consumes，由网关裁剪 —— 不让上游提前总结（上游不知道下游要什么），
   也不全量透传（12 步之后上下文会爆）。

与 context_pack_cache 的关系
---------------------------
复用其相似度函数与缓存思路：任务形态相近时，整条接力链可直接复用，不必重跑。
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# 常量
# --------------------------------------------------------------------------- #

# 只读不变量：任何中间步骤都不得改写这些字段
INVARIANTS = ("goal", "constraints")

DEFAULT_CONSTRAINTS = [
    "不修改生产数据与配置",
    "涉密与隐私内容不外发",
    "对外发布类动作必须人工确认",
]

DEFAULT_MAX_FACTS = 24
DEFAULT_MAX_REFS = 30
DEFAULT_MAX_ARTIFACTS = 16

# 默认最小投影：下游没声明 consumes 时给什么
MINIMAL_CONSUMES = ("goal", "constraints", "facts")

CONFIDENCE_FLOOR = 0.35  # 低于此值的 fact 直接降级为 ref，不进入下游输入


# --------------------------------------------------------------------------- #
# 信封结构
# --------------------------------------------------------------------------- #

def empty_envelope(run_id: str, task_id: str, goal: str,
                   constraints: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "task_id": task_id,
        "goal": goal,
        "constraints": list(constraints or DEFAULT_CONSTRAINTS),
        "facts": [],
        "refs": [],
        "artifacts": [],
        "open_questions": [],
        "degraded": False,
        "chain": [],
        "updated_at": time.time(),
    }


def envelope_digest(envelope: Dict[str, Any]) -> str:
    """信封指纹：用于判断两条接力链是否等价（配合语义缓存）。"""
    parts = [
        str(envelope.get("goal", "")),
        "|".join(sorted(str(f.get("claim", "")) for f in envelope.get("facts", [])[:8])),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def envelope_size(envelope: Dict[str, Any]) -> Dict[str, int]:
    """可观测量：裁剪前后各字段条目数，用于验证有界性。"""
    return {
        "facts": len(envelope.get("facts", [])),
        "refs": len(envelope.get("refs", [])),
        "artifacts": len(envelope.get("artifacts", [])),
        "open_questions": len(envelope.get("open_questions", [])),
        "chain": len(envelope.get("chain", [])),
    }


# --------------------------------------------------------------------------- #
# 上游产出 → 结构化要素
# --------------------------------------------------------------------------- #

def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _fact(claim: str, evidence_ref: str = "", confidence: float = 0.6) -> Dict[str, Any]:
    return {
        "claim": _clip(claim, 240),
        "evidence_ref": evidence_ref,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
    }


def extract_facts(step: Dict[str, Any], result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从步骤产出里抽出可传递的事实。

    置信度口径（刻意保守）：
      有引用依据支撑 → 0.80；只有摘要无依据 → 0.60；带待确认标记 → 0.45。
    这样下游能一眼看出哪些结论是「查过资料得出的」，哪些只是「这一步说了这么一句」。
    """
    action = str(step.get("action") or "")
    summary = str(result.get("summary") or "").strip()
    refs = result.get("references") or []
    has_evidence = bool(refs) or bool(result.get("rag_hits"))
    needs_confirm = bool(result.get("needs_confirmation")) or bool(result.get("approval"))

    confidence = 0.80 if has_evidence else 0.60
    if needs_confirm:
        confidence = min(confidence, 0.45)

    facts: List[Dict[str, Any]] = []
    if summary:
        first_ref = ""
        if refs and isinstance(refs[0], dict):
            first_ref = str(refs[0].get("id") or refs[0].get("title") or "")
        facts.append(_fact(summary, first_ref, confidence))

    # 各动作的额外结论：只挑对下游真正有用的，不做无差别搬运
    if action == "sense_overview":
        focus = result.get("focus_task") or {}
        if focus.get("id"):
            facts.append(_fact(
                f"锁定任务 {focus.get('id')}（{focus.get('title') or focus.get('name') or '未命名'}）",
                str(focus.get("id")), 0.85,
            ))
        counts = result.get("counts") or {}
        if counts:
            facts.append(_fact(
                "现场统计：" + "，".join(f"{k} {v}" for k, v in list(counts.items())[:6]),
                "snapshot", 0.75,
            ))
    elif action == "retrieve_knowledge":
        grouped = result.get("grouped") or {}
        if grouped:
            facts.append(_fact(
                "召回分布：" + "，".join(f"{k}×{v}" for k, v in list(grouped.items())[:6]),
                str(refs[0].get("id") if refs and isinstance(refs[0], dict) else ""), 0.7,
            ))
    elif action == "orchestrate_task":
        for key in ("steps", "assignments", "deliverables"):
            items = result.get(key)
            if isinstance(items, list) and items:
                facts.append(_fact(
                    f"{key}：{_clip('；'.join(str(x) for x in items[:4]), 180)}", "", 0.7,
                ))
    elif action == "prepare_recheck":
        gates = result.get("gates") or result.get("checks") or []
        if isinstance(gates, list) and gates:
            facts.append(_fact(
                "质量门禁：" + "；".join(_clip(g, 60) for g in gates[:4]), "", 0.75,
            ))
    return facts


def extract_refs(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """引用只保留指针（kind/id/title），不搬运正文。"""
    out: List[Dict[str, Any]] = []
    for item in (result.get("references") or [])[:24]:
        if not isinstance(item, dict):
            continue
        out.append({
            "kind": str(item.get("type") or item.get("category") or "资料"),
            "id": str(item.get("id") or item.get("source") or item.get("title") or ""),
            "title": _clip(item.get("title") or item.get("name"), 80),
        })
    return out


def extract_questions(result: Dict[str, Any]) -> List[str]:
    """未决问题：交给下游继续追，而不是就地丢弃。"""
    out: List[str] = []
    for key in ("gaps", "missing", "open_questions", "warnings"):
        items = result.get(key)
        if isinstance(items, list):
            out.extend(_clip(x, 140) for x in items[:6] if str(x).strip())
    if result.get("needs_confirmation"):
        out.append("本步产出需人工确认后才能作为下游依据")
    return out


def _merge_by_key(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]],
                  key) -> List[Dict[str, Any]]:
    """按 key 去重合并；重复出现的条目保留置信度更高的那条。"""
    merged: Dict[str, Dict[str, Any]] = {}
    for item in list(existing) + list(incoming):
        k = key(item)
        if not k:
            k = hashlib.sha256(str(item).encode("utf-8")).hexdigest()[:12]
        if k in merged:
            old, new = merged[k], item
            if float(new.get("confidence", 0)) > float(old.get("confidence", 0)):
                merged[k] = new
        else:
            merged[k] = item
    return list(merged.values())


# --------------------------------------------------------------------------- #
# 有界性：累积后裁剪
# --------------------------------------------------------------------------- #

def prune(envelope: Dict[str, Any],
          max_facts: int = DEFAULT_MAX_FACTS,
          max_refs: int = DEFAULT_MAX_REFS,
          max_artifacts: int = DEFAULT_MAX_ARTIFACTS) -> Dict[str, Any]:
    """把信封压回有界。

    裁剪策略（不是简单丢弃）：
      · facts 按置信度降序保留 top-N；被挤出的 fact **降级为 ref**（只留 claim 摘要
        与证据指针），语义不丢、体积大减。
      · 低于 CONFIDENCE_FLOOR 的 fact 直接降级，不进入下游输入。
      · refs 按 (kind,id) 去重后保留最近 max_refs 条。
      · artifacts 只留最近 max_artifacts 条（产物本体在别处，这里只是索引）。
    """
    facts = sorted(envelope.get("facts", []), key=lambda f: -float(f.get("confidence", 0)))

    kept: List[Dict[str, Any]] = []
    demoted: List[Dict[str, Any]] = []
    for index, fact in enumerate(facts):
        if index < max_facts and float(fact.get("confidence", 0)) >= CONFIDENCE_FLOOR:
            kept.append(fact)
        else:
            demoted.append({
                "kind": "demoted_fact",
                "id": "f-" + hashlib.sha256(str(fact.get("claim", "")).encode("utf-8")).hexdigest()[:10],
                "title": _clip(fact.get("claim"), 80),
            })

    refs = _merge_by_key(envelope.get("refs", []), demoted,
                         lambda r: f"{r.get('kind')}::{r.get('id')}")
    refs = refs[-max_refs:]

    envelope["facts"] = kept
    envelope["refs"] = refs
    envelope["artifacts"] = envelope.get("artifacts", [])[-max_artifacts:]
    envelope["updated_at"] = time.time()
    return envelope


# --------------------------------------------------------------------------- #
# 构建：上游产出 → 新信封
# --------------------------------------------------------------------------- #

def build_relay(previous: Dict[str, Any], step: Dict[str, Any],
                result: Dict[str, Any]) -> Dict[str, Any]:
    """把一步的产出并入接力信封。

    不变量（goal / constraints）原样保留，任何步骤都无法通过 result 改写它们 ——
    这是防止多步流水线里目标漂移的关键。
    """
    env = dict(previous)
    env["facts"] = list(previous.get("facts", []))
    env["refs"] = list(previous.get("refs", []))
    env["artifacts"] = list(previous.get("artifacts", []))
    env["open_questions"] = list(previous.get("open_questions", []))
    env["chain"] = list(previous.get("chain", []))

    # 不变量强制回写：即便 result 里带了同名字段也一律忽略
    env["goal"] = previous.get("goal", "")
    env["constraints"] = list(previous.get("constraints", DEFAULT_CONSTRAINTS))

    env["facts"] = _merge_by_key(env["facts"], extract_facts(step, result),
                                 lambda f: str(f.get("claim", ""))[:80])
    env["refs"] = _merge_by_key(env["refs"], extract_refs(result),
                                lambda r: f"{r.get('kind')}::{r.get('id')}")

    questions = extract_questions(result)
    env["open_questions"] = list(dict.fromkeys(env["open_questions"] + questions))[:12]

    agent = step.get("agent") or {}
    env["artifacts"].append({
        "step": str(step.get("key") or ""),
        "agent": str(agent.get("name") or agent.get("id") or ""),
        "action": str(step.get("action") or ""),
        "summary": _clip(result.get("summary"), 200),
        "state": str(result.get("state") or ("failed" if result.get("error") else "done")),
    })

    if result.get("error") or result.get("state") == "failed":
        env["degraded"] = True

    env["chain"].append({
        "step": str(step.get("key") or ""),
        "from": str(agent.get("name") or agent.get("id") or ""),
        "action": str(step.get("action") or ""),
        "received": list(step.get("consumes") or MINIMAL_CONSUMES),
        "produced": sorted(set(
            [k for k in ("facts", "refs", "artifacts", "open_questions") if result.get(k) is not None]
            + (["degraded"] if result.get("error") else [])
        )),
        "fact_count": len(extract_facts(step, result)),
        "at": time.time(),
    })

    return prune(env)


# --------------------------------------------------------------------------- #
# 投影：信封 → 下游输入
# --------------------------------------------------------------------------- #

def project_relay(envelope: Dict[str, Any], consumes: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """按下游声明的 consumes 裁剪出它真正需要的那一片。

    不做全量透传：12 步之后信封会把 prompt 撑爆。
    也不让上游提前总结：上游并不知道下游要什么，过早压缩会丢信息。
    由下游声明、由这里裁剪，是两边都不得罪的做法。
    """
    wanted = set(consumes or MINIMAL_CONSUMES)
    # 不变量永远下发，不接受声明裁剪
    wanted.update(INVARIANTS)

    projected: Dict[str, Any] = {
        "_relay": {
            "digest": envelope_digest(envelope),
            "from_chain": len(envelope.get("chain", [])),
            "degraded": bool(envelope.get("degraded")),
            "size": envelope_size(envelope),
        }
    }
    for field in ("goal", "constraints", "facts", "refs", "artifacts", "open_questions"):
        if field in wanted:
            projected[field] = envelope.get(field, [] if field != "goal" else "")

    if envelope.get("degraded"):
        projected["_relay"]["warning"] = "上游有步骤降级完成，相关结论需人工复核后再采信"
    return projected


# --------------------------------------------------------------------------- #
# 语义复用：同形态任务的接力链直接复用（复用 CPSC 的相似度）
# --------------------------------------------------------------------------- #

def relay_shape(plan: Dict[str, Any]) -> Dict[str, Any]:
    """把 plan 压成 CPSC 相似度函数认得的任务形态。"""
    focus = plan.get("focus") or {}
    return {
        "query": str(plan.get("goal") or "")[:200],
        "device_name": str(focus.get("equipment_name") or focus.get("project_name") or ""),
        "device_model": str(focus.get("equipment_model") or focus.get("project") or ""),
        "category": str(plan.get("mode") or "auto"),
        "maintenance_level": str(plan.get("focus_keyword") or ""),
    }


class RelayChainCache:
    """同形态任务的接力链复用。

    复用 context_pack_cache.similarity：它带「任务类别硬门」，类别不同一律返回 0，
    杜绝把维修类任务的接力链套到知识类任务上（该硬门是第一版假阳性排障的产物）。
    """

    def __init__(self, capacity: int = 64, threshold: float = 0.70) -> None:
        self.capacity = capacity
        self.threshold = threshold
        self._entries: List[Dict[str, Any]] = []
        self.hits = 0
        self.misses = 0

    def lookup(self, plan: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float, str]:
        from services.context_pack_cache import similarity

        shape = {"task": relay_shape(plan)}
        best, best_score = None, 0.0
        for entry in self._entries:
            if entry["digest"] == envelope_digest(plan.get("_envelope") or {}):
                self.hits += 1
                return entry["envelope"], 1.0, "exact"
            score = similarity(shape, {"task": entry["shape"]})
            if score > best_score:
                best, best_score = entry, score
        if best is not None and best_score >= self.threshold:
            self.hits += 1
            return best["envelope"], round(best_score, 4), "semantic"
        self.misses += 1
        return None, round(best_score, 4), "miss"

    def store(self, plan: Dict[str, Any], envelope: Dict[str, Any]) -> None:
        self._entries.append({
            "shape": relay_shape(plan),
            "envelope": envelope,
            "digest": envelope_digest(envelope),
            "at": time.time(),
        })
        if len(self._entries) > self.capacity:
            self._entries.pop(0)

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._entries),
            "lookups": total,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "threshold": self.threshold,
        }


relay_cache = RelayChainCache()
