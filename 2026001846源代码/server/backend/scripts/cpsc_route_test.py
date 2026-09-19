"""CPSC 路由层集成测试：验证 /team-os/context/pack 与缓存统计接口真的接上了。

设计说明
--------
本测试**打桩替换大模型调用**（monkeypatch UnifiedAIAgent.chat），原因有两条：
  1. 缓存命中只可能发生在「上一轮大模型成功产出」之后，依赖真实 API 会让测试不稳定；
  2. 实测本机 DashScope 免费额度已耗尽（HTTP 403），真实调用必然失败。
打桩后，测试验证的是 CPSC 自身的挂载与状态流转，与大模型可用性解耦。

同时覆盖一条重要边界：**大模型失败时不得写入缓存**（否则会把降级结果当成模型结论复用）。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TASK = {
    "query": "发动机异响",
    "deviceName": "CG-125 摩托车发动机",
    "deviceModel": "CG-125",
    "category": "发动机",
    "faultType": "异响",
    "maintenanceLevel": "标准协作",
}

FAKE_MODEL_OUTPUT = json.dumps({
    "phenomenon_summary": "[打桩模型结论] 摩托车发动机异响，疑似气门间隙偏大。",
    "match_score": 88,
    "risk": "medium",
    "stop_advice": "停机冷却后再拆检",
    "causes": ["气门间隙异常", "正时链条张紧器失效"],
    "positions": ["气门室", "正时链条"],
    "tools": ["塞尺", "扭力扳手"],
    "visual_findings": ["气门室盖周边油迹"],
    "recommended_sop": [{"step": 1, "action": "停机冷却"}, {"step": 2, "action": "复测异响"}],
    "safety": ["断开蓄电池负极"],
    "audit": {"risk_level": "medium", "must_check": ["气门间隙"], "auditor": "明鉴"},
}, ensure_ascii=False)

ok = True


def check(label, cond, detail=""):
    global ok
    print(("  [PASS] " if cond else "  [FAIL] ") + label + (("  " + str(detail)) if detail else ""))
    if not cond:
        ok = False


print("=== CPSC 路由层集成测试（大模型已打桩）===")

from services.ai_gateway import ai_agent  # noqa: E402
from unified_app import create_unified_app  # noqa: E402

CALLS = {"n": 0}


def fake_chat(messages, **kwargs):
    CALLS["n"] += 1
    # 验证 ① 前缀复用：system 必须是字节一致的稳定前缀，且内容不得混入任务信息
    system = messages[0]["content"]
    user = messages[1]["content"]
    assert messages[0]["role"] == "system", "前缀必须放在 system 角色"
    assert "【任务】" not in system, "稳定前缀里不允许出现任务相关内容"
    assert "【任务】" in user, "可变载荷必须放在 user 角色"
    return FAKE_MODEL_OUTPUT


ai_agent.chat = fake_chat

app = create_unified_app()
client = app.test_client()

check("POST /cache/clear", client.post("/api/yixiu/team-os/context/cache/clear").status_code == 200)

# ---- 第 1 次：未命中 → 调用模型 → 写入缓存 ----
r1 = client.post("/api/yixiu/team-os/context/pack", json=TASK)
d1 = (r1.get_json() or {}).get("data", {})
c1, l1 = d1.get("cpsc", {}), d1.get("llm", {})
check("第 1 次状态码 200", r1.status_code == 200, r1.status_code)
check("第 1 次为 miss", c1.get("cache") == "miss", c1.get("cache"))
check("前缀字符数为 575", c1.get("prefix_chars") == 575, c1.get("prefix_chars"))
check("前缀指纹已记录", c1.get("prefix_fingerprint") == "d096219ebd2be13b", c1.get("prefix_fingerprint"))
check("模型确实被调用", CALLS["n"] == 1, CALLS["n"])
check("模型结论已生效", "打桩模型结论" in str(d1.get("phenomenon_summary", "")), d1.get("phenomenon_summary"))
check("llm.reused 为 False", l1.get("reused") is False, l1.get("reused"))

# ---- 第 2 次同任务：应精确命中，且不再调用模型 ----
before = CALLS["n"]
r2 = client.post("/api/yixiu/team-os/context/pack", json=TASK)
d2 = (r2.get_json() or {}).get("data", {})
c2, l2 = d2.get("cpsc", {}), d2.get("llm", {})
check("第 2 次为 exact", c2.get("cache") == "exact", c2.get("cache"))
check("第 2 次未再调用模型", CALLS["n"] == before, f'{before} -> {CALLS["n"]}')
check("llm.reused 为 True", l2.get("reused") is True, l2.get("reused"))
check("复用字段非空", bool(c2.get("reused_fields")), c2.get("reused_fields"))
check("复用后结论仍在", "打桩模型结论" in str(d2.get("phenomenon_summary", "")), d2.get("phenomenon_summary"))

# ---- 第 3 次近似任务：语义命中 ----
similar = dict(TASK, query="发动机异响伴随怠速不稳")
r3 = client.post("/api/yixiu/team-os/context/pack", json=similar)
c3 = ((r3.get_json() or {}).get("data", {}) or {}).get("cpsc", {})
check("近似任务为 semantic 命中", c3.get("cache") == "semantic", (c3.get("cache"), c3.get("similarity")))

# ---- 第 4 次跨类别任务：必须是 miss（假阳性防护）----
cross = dict(TASK, query="空调制冷不足", category="空调系统", deviceName="乘用车", deviceModel="大众朗逸")
r4 = client.post("/api/yixiu/team-os/context/pack", json=cross)
c4 = ((r4.get_json() or {}).get("data", {}) or {}).get("cpsc", {})
check("跨类别必须 miss（防错误复用）", c4.get("cache") == "miss", (c4.get("cache"), c4.get("similarity")))

# ---- 大模型失败时不得写缓存 ----
def failing_chat(messages, **kwargs):
    raise RuntimeError("simulated upstream failure")


ai_agent.chat = failing_chat
before_calls = CALLS["n"]
fresh = dict(TASK, query="传动链条打滑", category="传动系统")
r5 = client.post("/api/yixiu/team-os/context/pack", json=fresh)
c5 = ((r5.get_json() or {}).get("data", {}) or {}).get("cpsc", {})
check("大模型失败时仍返回 200（降级）", r5.status_code == 200, r5.status_code)
check("大模型失败时判定为 miss", c5.get("cache") == "miss", c5.get("cache"))

r6 = client.post("/api/yixiu/team-os/context/pack", json=fresh)
c6 = ((r6.get_json() or {}).get("data", {}) or {}).get("cpsc", {})
check("失败结果未被缓存（第 2 次仍 miss）", c6.get("cache") == "miss", c6.get("cache"))

# ---- 统计接口 ----
stats = (client.get("/api/yixiu/team-os/context/cache/stats").get_json() or {}).get("data", {})
check("stats.algorithm == CPSC", stats.get("algorithm") == "CPSC", stats.get("algorithm"))
check("lookups == 6", stats.get("lookups") == 6, stats.get("lookups"))
check("hits == 2", stats.get("hits") == 2, stats.get("hits"))
check("exact_hits == 1", stats.get("exact_hits") == 1, stats.get("exact_hits"))
check("semantic_hits == 1", stats.get("semantic_hits") == 1, stats.get("semantic_hits"))
check("entries == 2（仅两条不同形态入库；失败与跨类别命中均不重复入库）", stats.get("entries") == 2, stats.get("entries"))

print()
print("全部通过" if ok else "存在失败项")
sys.exit(0 if ok else 1)
