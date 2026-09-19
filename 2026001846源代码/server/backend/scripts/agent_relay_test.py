# -*- coding: utf-8 -*-
"""Agent 上下文接力（ACR）自检

覆盖六条容易静默写错的性质：
  1. 累积    —— 多步之后 fact/ref/artifact 确实叠加，且去重
  2. 有界    —— 超出上限时按置信度裁剪，溢出的 fact 降级为 ref（不是丢弃）
  3. 投影    —— 下游声明的 consumes 生效，没声明的不下发
  4. 不变量  —— goal / constraints 无法被任何步骤的 result 改写
  5. 降级    —— 上游失败会标记 degraded 并带给下游一句警示
  6. 语义复用—— 同形态任务命中，跨类别（维修 vs 知识）必须不命中
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent_relay import (  # noqa: E402
    CONFIDENCE_FLOOR,
    DEFAULT_MAX_FACTS,
    RelayChainCache,
    build_relay,
    empty_envelope,
    envelope_size,
    project_relay,
    prune,
)

ok = True


def check(label, cond, detail=""):
    global ok
    print(("  [PASS] " if cond else "  [FAIL] ") + label + (("  " + str(detail)) if detail else ""))
    if not cond:
        ok = False


def step(key, agent, action, consumes):
    return {"key": key, "agent": {"id": agent, "name": agent.upper()}, "action": action, "consumes": consumes}


print("=== Agent 上下文接力自检 ===")

# ---- 1. 累积 ----
env = empty_envelope("run-1", "task-1", "修复支付回调幂等问题", ["不修改生产库"])
env = build_relay(env, step("sense", "tiangong", "sense_overview", ["goal"]),
                  {"summary": "已锁定任务", "focus_task": {"id": "t-9", "title": "支付回调"},
                   "counts": {"待办": 3}})
after_sense = envelope_size(env)
env = build_relay(env, step("retrieve", "guanwei", "retrieve_knowledge", ["goal", "facts"]),
                  {"summary": "召回 4 条依据", "references": [
                      {"id": "m-1", "type": "Memory", "title": "幂等键校验"},
                      {"id": "m-2", "type": "SOP", "title": "回调重试处理"}]})
after_retrieve = envelope_size(env)
check("fact 随步骤累积", after_retrieve["facts"] > after_sense["facts"], f'{after_sense["facts"]} -> {after_retrieve["facts"]}')
check("ref 被采集", after_retrieve["refs"] >= 2, after_retrieve["refs"])
check("chain 记录每一步", after_retrieve["chain"] == 2, after_retrieve["chain"])

# ---- 2. 有界 + 降级为 ref ----
big = empty_envelope("run-2", "t", "目标")
big["facts"] = [{"claim": f"事实{i}", "evidence_ref": "", "confidence": 0.5 + i / 100.0}
                for i in range(DEFAULT_MAX_FACTS + 12)]
before_facts = len(big["facts"])
before_refs = len(big["refs"])
prune(big, max_facts=DEFAULT_MAX_FACTS)
check(f"facts 被裁到上限 {DEFAULT_MAX_FACTS}", len(big["facts"]) == DEFAULT_MAX_FACTS, len(big["facts"]))
check("被挤出的 fact 降级为 ref（不是丢弃）", len(big["refs"]) == before_facts - DEFAULT_MAX_FACTS + before_refs, len(big["refs"]))
check("裁剪后 ref 里带 demoted_fact 类型", any(r.get("kind") == "demoted_fact" for r in big["refs"]))
check("保留的是置信度最高的那批", big["facts"][0]["confidence"] >= big["facts"][-1]["confidence"],
      f'{big["facts"][0]["confidence"]} vs {big["facts"][-1]["confidence"]}')

low = empty_envelope("run-3", "t", "目标")
low["facts"] = [{"claim": "低置信度结论", "evidence_ref": "", "confidence": CONFIDENCE_FLOOR - 0.1}]
prune(low)
check("低于置信度下限的 fact 不进下游", len(low["facts"]) == 0 and len(low["refs"]) == 1,
      f'facts={len(low["facts"])} refs={len(low["refs"])}')

# ---- 3. 投影 ----
proj_min = project_relay(env, ["goal"])
check("未声明的字段不下发", "facts" not in proj_min and "refs" not in proj_min, sorted(proj_min.keys()))
proj_full = project_relay(env, ["goal", "facts", "refs", "open_questions"])
check("声明的字段下发", all(k in proj_full for k in ("facts", "refs", "open_questions")), sorted(proj_full.keys()))
check("不变量始终下发（不受 consumes 影响）", "goal" in proj_min and "constraints" in proj_min)
check("携带接力元信息", proj_full["_relay"]["from_chain"] == 2, proj_full["_relay"])

# ---- 4. 不变量不可改写 ----
tampered = build_relay(env, step("x", "evil", "sense_overview", ["goal"]),
                       {"summary": "试图改目标", "goal": "改成别的事情", "constraints": []})
check("goal 不被 result 改写", tampered["goal"] == env["goal"], tampered["goal"])
check("constraints 不被 result 改写", tampered["constraints"] == env["constraints"], tampered["constraints"])

# ---- 5. 降级传播 ----
env_bad = build_relay(env, step("operate", "zhiju", "orchestrate_task", ["goal"]),
                      {"summary": "执行中断", "error": "上游超时"})
check("上游失败标记 degraded", env_bad["degraded"] is True)
proj_bad = project_relay(env_bad, ["goal", "facts"])
check("降级警示随投影下发", "warning" in proj_bad["_relay"], proj_bad["_relay"].get("warning"))

# ---- 6. 语义复用（复用 CPSC 的相似度与类别硬门）----
cache = RelayChainCache(threshold=0.70)
repair_plan = {"goal": "摩托车发动机异响排查", "mode": "repair", "focus_keyword": "异响",
               "focus": {"equipment_name": "CG-125 摩托车发动机", "equipment_model": "CG-125"}}
same_plan = {"goal": "摩托车发动机异响排查与复检", "mode": "repair", "focus_keyword": "异响",
             "focus": {"equipment_name": "CG-125 摩托车发动机", "equipment_model": "CG-125"}}
other_plan = {"goal": "整理知识库里的接口文档", "mode": "knowledge", "focus_keyword": "文档",
              "focus": {"equipment_name": "一休 Web 端", "equipment_model": "v1"}}

hit, score, how = cache.lookup(repair_plan)
check("空缓存为 miss", hit is None and how == "miss", how)
cache.store(repair_plan, env)

hit, score, how = cache.lookup(same_plan)
check("同形态任务语义命中", hit is not None and how == "semantic", f"{how} {score}")

hit, score, how = cache.lookup(other_plan)
check("跨类别任务必须 miss（类别硬门）", hit is None and how == "miss", f"{how} {score}")

stats = cache.stats()
check("缓存统计可用", stats["lookups"] == 3 and stats["hits"] == 1, stats)

print()
print("全部通过" if ok else "存在失败项")
sys.exit(0 if ok else 1)
