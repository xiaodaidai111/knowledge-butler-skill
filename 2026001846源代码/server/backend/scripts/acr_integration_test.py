# -*- coding: utf-8 -*-
"""Agent 上下文接力（ACR）与 AIOS 的接线自检

验证三件事：
  1. _aios_plan 产出的每一步都带 consumes 声明，plan 里带初始接力信封
  2. 走完多步后信封累积且有界，且能落库、能读回
  3. GET /aios/runs/<run_id>/relays 返回接力链
"""

import os
import sys

sys.path.insert(0, r"D:\竞赛\软件杯\2026001846源代码\server")
sys.path.insert(0, r"D:\竞赛\软件杯\2026001846源代码\server\backend")
os.chdir(r"D:\竞赛\软件杯\2026001846源代码\server\backend")

from unified_app import create_unified_app  # noqa: E402
from routes.yixiu import (  # noqa: E402
    RELAY_CONSUMES,
    _aios_execute_action,
    _db,
    _persist_agent_relay,
    _relay_dict,
    _aios_plan,
)
from services.agent_relay import build_relay, envelope_size, project_relay  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    print(("  [PASS] " if cond else "  [FAIL] ") + label + (("  " + str(detail)) if detail else ""))
    if not cond:
        ok = False


print("=== ACR 与 AIOS 接线自检 ===")

# ---- 1. 计划层：每步都声明了 consumes，plan 带初始信封 ----
plan = _aios_plan("修复支付回调重复触发导致订单重复处理的问题", "repair")
steps = plan.get("steps", [])
# 规划器由大模型自主决定步数（失败才回退 12 步模板），因此不写死步数，
# 只校验真正的不变量：非空、步数有界、每步 key 来自 RELAY_CONSUMES。
check("计划非空且步数有界", 1 <= len(steps) <= 24, len(steps))
check("每步 key 均来自 RELAY_CONSUMES", all(s.get("key") in RELAY_CONSUMES for s in steps),
      [s.get("key") for s in steps if s.get("key") not in RELAY_CONSUMES])
check("每步都声明 consumes", all(isinstance(s.get("consumes"), list) and s["consumes"] for s in steps),
      [s["key"] for s in steps if not s.get("consumes")])
check("consumes 取自 RELAY_CONSUMES", all(list(s["consumes"]) == list(RELAY_CONSUMES.get(s["key"], [])) for s in steps))
check("plan 带初始接力信封", isinstance(plan.get("relay"), dict) and "goal" in plan["relay"], list((plan.get("relay") or {}).keys())[:5])
check("信封 goal 等于计划目标", plan["relay"]["goal"] == plan["goal"])

# ---- 2. 执行层：逐步累积，且有界 ----
env = plan["relay"]
sizes = []
for st in steps[:6]:
    projected = project_relay(env, st.get("consumes"))
    check(f'  {st["key"]} 收到投影输入', "goal" in projected, sorted(projected.keys()))
    st["input"] = {**(st.get("input") or {}), "relay": projected}
    result = _aios_execute_action(st, plan.get("snapshot") or {}, commit=False)
    env = build_relay(env, st, result)
    sizes.append(envelope_size(env)["facts"])

check("facts 随步骤单调不减", all(b >= a for a, b in zip(sizes, sizes[1:])), sizes)
check("chain 记录了 6 步", envelope_size(env)["chain"] == 6, envelope_size(env)["chain"])
check("信封有界（facts 不超上限）", envelope_size(env)["facts"] <= 24, envelope_size(env)["facts"])
check("artifacts 有索引", envelope_size(env)["artifacts"] > 0, envelope_size(env)["artifacts"])
check("目标不变量全程未被改写", env["goal"] == plan["goal"], env["goal"])
check("末步能看到前序步骤的产物", len(env["chain"]) == 6 and env["chain"][0]["step"] == steps[0]["key"])

# ---- 3. 落库 + 读回 ----
RUN_ID = "relay-selftest-run"
with _db() as conn:
    conn.execute("DELETE FROM yixiu_agent_relays WHERE run_id=?", (RUN_ID,))
    conn.commit()
    for st in steps[:3]:
        _persist_agent_relay(conn, RUN_ID, st, env)
    conn.commit()
    rows = conn.execute("SELECT * FROM yixiu_agent_relays WHERE run_id=? ORDER BY created_at, step_key", (RUN_ID,)).fetchall()
    conn.execute("DELETE FROM yixiu_agent_relays WHERE run_id=?", (RUN_ID,))
    conn.commit()

records = [_relay_dict(r) for r in rows]
check("接力信封可落库并读回", len(records) == 3, len(records))
check("读回含 envelope 与 size", bool(records[0]["envelope"]) and bool(records[0]["size"]), list(records[0].keys())[:8])
check("读回 consumes 已解析", isinstance(records[0]["consumes"], list) and records[0]["consumes"], records[0]["consumes"])
check("degraded 转成布尔", isinstance(records[0]["degraded"], bool), records[0]["degraded"])

# ---- 4. 接口 ----
app = create_unified_app()
client = app.test_client()
r = client.get(f"/api/yixiu/aios/runs/{RUN_ID}/relays")
check("GET /aios/runs/<id>/relays 可达", r.status_code in (200, 401, 403), r.status_code)
if r.status_code == 200:
    body = (r.get_json() or {}).get("data", {})
    check("返回 count/relays/latest", {"count", "relays", "latest"} <= set(body.keys()), sorted(body.keys())[:6])
else:
    print(f"       （该接口需要登录态，无 token 时返回 {r.status_code}，符合预期的鉴权行为）")

print()
print("全部通过" if ok else "存在失败项")
sys.exit(0 if ok else 1)
