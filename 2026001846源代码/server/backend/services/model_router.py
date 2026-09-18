"""Cost-aware model routing shared by the API and the workbench UI."""
from __future__ import annotations

import os
import re
from typing import Any


HIGH_RISK = re.compile(r"发布|生产|权限|密钥|支付|迁移|删除|安全|架构|回滚|高风险|review|eval|审计", re.I)
DEEP_REASONING = re.compile(r"根因|复杂|规划|重构|推理|对比|研究|长任务|跨模块|诊断|证明", re.I)
ECONOMY_TASK = re.compile(r"摘要|提取|分类|改写|格式|翻译|标题|检索|问候|状态|简报|去重|你好|您好|谢谢|在吗|hi|hello", re.I)
CODE_TASK = re.compile(r"代码|bug|接口|数据库|测试|脚本|组件|前端|后端|context pack|skill", re.I)

TIER_META = {
    "economy": {"label": "经济档", "max_tokens": 800, "temperature": 0.25, "cost": 0.04, "saving": 78},
    "balanced": {"label": "均衡档", "max_tokens": 1800, "temperature": 0.35, "cost": 0.18, "saving": 46},
    "reasoning": {"label": "推理档", "max_tokens": 3200, "temperature": 0.2, "cost": 0.42, "saving": 12},
    "vision": {"label": "多模态档", "max_tokens": 1800, "temperature": 0.2, "cost": 0.28, "saving": 34},
}


def _configured_model(provider: str, tier: str, default_model: str, vision_model: str) -> str:
    if tier == "vision":
        return vision_model or default_model
    keys = {
        "economy": ("AI_MODEL_ECONOMY", f"{provider.upper()}_ECONOMY_MODEL"),
        "balanced": ("AI_MODEL_BALANCED", f"{provider.upper()}_BALANCED_MODEL"),
        "reasoning": ("AI_MODEL_REASONING", f"{provider.upper()}_REASONING_MODEL"),
    }[tier]
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    # Safe default: reduce token budget even when the provider has only one configured model.
    return default_model


def recommend_model_route(
    message: str,
    policy: dict[str, Any] | None,
    provider: str,
    default_model: str,
    vision_model: str = "",
    has_attachments: bool = False,
) -> dict[str, Any]:
    policy = policy if isinstance(policy, dict) else {}
    mode = str(policy.get("mode") or "balanced").lower()
    quality_floor = max(60, min(100, int(policy.get("qualityFloor") or policy.get("quality_floor") or 85)))
    auto_escalate = bool(policy.get("autoEscalate", policy.get("auto_escalate", True)))
    text = str(message or "").strip()
    score = 1
    reasons: list[str] = []
    risk = "low"

    if has_attachments:
        tier = "vision"
        reasons.append("任务包含图片或资料附件，需要多模态理解")
    else:
        if ECONOMY_TASK.search(text):
            score -= 1
            reasons.append("属于摘要、分类或轻量整理任务")
        if CODE_TASK.search(text):
            score += 1
            reasons.append("涉及代码或工程上下文，需要稳定的指令遵循")
        if DEEP_REASONING.search(text) or len(text) > 500:
            score += 1
            reasons.append("任务包含复杂分析、长上下文或多步推理")
        if HIGH_RISK.search(text):
            score += 2
            risk = "high"
            reasons.append("涉及高风险变更或质量门禁，需要更强核查能力")
        if mode == "cost":
            score -= 1
            reasons.append("当前策略优先控制成本")
        elif mode == "quality":
            score += 1
            reasons.append("当前策略优先保证质量")
        if quality_floor >= 92:
            score += 1
            reasons.append("质量门槛较高，路由档位上调一级")
        elif quality_floor <= 75:
            score -= 1
            reasons.append("质量门槛允许轻量处理，优先降低调用成本")
        tier = "economy" if score <= 0 else "balanced" if score <= 2 else "reasoning"

    budget = float(policy.get("maxCost") or policy.get("max_cost") or 0.5)
    budget = max(0.01, budget)
    requested_tier = tier
    high_risk_approval = bool(policy.get("highRiskApproval", policy.get("high_risk_approval", True)))
    if tier != "vision" and risk != "high" and budget < float(TIER_META[tier]["cost"]):
        affordable = [name for name in ("economy", "balanced", "reasoning") if float(TIER_META[name]["cost"]) <= budget]
        tier = affordable[-1] if affordable else "economy"
        if tier != requested_tier:
            reasons.append(f"单任务预算不足以使用{TIER_META[requested_tier]['label']}，已降至{TIER_META[tier]['label']}")

    meta = TIER_META[tier]
    model_name = _configured_model(provider, tier, default_model, vision_model)
    estimated_cost = float(meta["cost"])
    over_budget = estimated_cost > budget
    if over_budget:
        reasons.append("预计费用高于单任务预算，执行前需要人工确认或压缩上下文")

    escalation_tier = "balanced" if tier == "economy" else "reasoning" if tier == "balanced" else tier
    escalation_model = _configured_model(provider, escalation_tier, default_model, vision_model)

    return {
        "tier": tier,
        "tier_label": meta["label"],
        "provider": provider or "configured-provider",
        "model": model_name or "configured-default",
        "max_tokens": int(meta["max_tokens"]),
        "temperature": float(meta["temperature"]),
        "estimated_cost": round(estimated_cost, 2),
        "budget_limit": round(budget, 2),
        "over_budget": over_budget,
        "saving_percent": int(meta["saving"]),
        "risk": risk,
        "quality_floor": quality_floor,
        "requires_approval": (risk == "high" and high_risk_approval) or over_budget,
        "auto_escalate": auto_escalate,
        "escalation_tier": escalation_tier if auto_escalate and tier in {"economy", "balanced"} else "",
        "escalation_model": escalation_model if auto_escalate and tier in {"economy", "balanced"} else "",
        "reason": "；".join(reasons) or "按默认均衡策略处理当前任务",
        "policy_mode": mode,
    }
