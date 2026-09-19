"""CPSC（上下文包语义缓存）对比实验

对照：
  baseline —— 固定指令与可变内容混排在同一条 user message（旧实现，前缀不可命中）
  CPSC     —— 稳定前缀进 system + 结构化紧凑载荷进 user + 语义包缓存

本机未配置大模型 API，因此：
  · prompt 体积、前缀可缓存比例、缓存命中率、**跨类别假阳性** —— 均为精确可测
  · 耗时只测「结构化上下文构建 + 缓存查询」这一段，标注为本地段耗时

评测口径（关键）
  命中来源任务类别 == 当前任务类别 → 正确命中
  命中来源任务类别 != 当前任务类别 → **假阳性（错误复用，必须为 0）**
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.context_pack_cache import (  # noqa: E402
    PREFIX_FINGERPRINT,
    STABLE_PREFIX,
    SemanticPackCache,
    build_flat_prompt,
    build_structured_context,
    prompt_metrics,
    render_structured_payload,
)


def make_result(query, device, model, category, level):
    return {
        "query": query,
        "device_name": device,
        "device_model": model,
        "category": category,
        "maintenance_level": level,
        "modalities": ["text", "image"],
        "match_score": 82,
        "risk": "medium",
        "phenomenon_summary": f"{device}在{query}工况下出现异常，需结合召回资料判定。",
        "causes": ["气门间隙异常", "正时链条张紧器失效", "化油器怠速油路堵塞", "火花塞积碳"],
        "positions": ["气门室", "正时链条", "化油器"],
        "tools": ["塞尺", "扭力扳手", "内窥镜", "真空表"],
        "safety": ["停机冷却后作业", "断开蓄电池负极"],
        "visual_findings": ["气门室盖周边油迹"],
    }


def make_matched():
    return [
        {
            "id": "motor-engine-valve-sop",
            "title": "CG-125/同类单缸发动机气门间隙检查 SOP",
            "type": "标准作业流程 SOP",
            "summary": "停机冷却后拆检气门室盖，用塞尺检查进/排气门间隙，调整后复装并进行冷车、热车异响复测。",
            "tags": ["摩托车发动机", "气门间隙", "异响"],
        },
        {
            "id": "motor-engine-noise-case",
            "title": "摩托车发动机异响与怠速不稳排查案例",
            "type": "历史故障案例",
            "summary": "围绕气门机构、正时链条/张紧器、摇臂/凸轮轴、机油润滑、火花塞、化油器怠速油路和进气漏气排查。",
            "tags": ["发动机异响", "怠速不稳", "复检"],
        },
        {
            "id": "vehicle-flood-sop",
            "title": "车辆泡水后处置与复检 SOP",
            "type": "标准作业流程 SOP",
            "summary": "按涉水深度分级，检查进气、电气、内饰与油液，出具处置建议。",
            "tags": ["泡水", "涉水", "电气"],
        },
    ]


def make_attachments():
    return [
        {
            "id": "f-1",
            "name": "发动机异响录音说明.png",
            "type": "图片",
            "analysis": {"fault_signs": ["气门室盖密封处渗油"], "summary": "现场照片显示气门室周边油迹"},
        }
    ]


# (标签, query, 设备, 型号, 类别, 等级)
SCENARIOS = [
    ("T01", "发动机异响", "CG-125 摩托车发动机", "CG-125", "发动机", "标准协作"),
    ("T02", "发动机异响", "CG-125 摩托车发动机", "CG-125", "发动机", "标准协作"),
    ("T03", "发动机异响伴随怠速不稳", "CG-125 摩托车发动机", "CG-125", "发动机", "标准协作"),
    ("T04", "气门间隙异常导致异响", "CG-125 摩托车发动机", "CG-125", "发动机", "深度检修"),
    ("T05", "冷车启动异响", "CG-125 摩托车发动机", "CG-125", "发动机", "标准协作"),
    ("T06", "车辆泡水后电气排查", "乘用车", "大众朗逸", "车辆泡水", "应急处理"),
    ("T07", "制动系统异响", "乘用车", "大众朗逸", "制动系统", "标准协作"),
    ("T08", "空调制冷不足", "乘用车", "大众朗逸", "空调系统", "标准协作"),
    ("T09", "发动机异响", "CG-125 摩托车发动机", "CG-125", "发动机", "标准协作"),
]


def simulate_pack(device, query):
    return {
        "phenomenon_summary": f"[模型结论] {device} {query}",
        "match_score": 88,
        "risk": "medium",
        "causes": ["气门间隙异常"],
        "positions": ["气门室"],
        "tools": ["塞尺"],
        "visual_findings": [],
        "recommended_sop": [{"step": 1, "action": "停机冷却"}],
        "safety": ["断开蓄电池"],
        "audit": {"risk_level": "medium", "must_check": ["气门间隙"], "auditor": "明鉴"},
    }


def run(threshold):
    cache = SemanticPackCache(capacity=128, threshold=threshold)
    matched, attachments = make_matched(), make_attachments()

    rows = []
    base_total = cpsc_total = llm_calls = false_positive = 0

    for tag, query, device, model, category, level in SCENARIOS:
        result = make_result(query, device, model, category, level)
        flat = build_flat_prompt(result, matched, attachments)

        t0 = time.perf_counter()
        context = build_structured_context(result, matched, attachments)
        payload = render_structured_payload(context)
        metrics = prompt_metrics(STABLE_PREFIX, payload)
        cached, score, how, source_category = cache.lookup(context)
        build_ms = (time.perf_counter() - t0) * 1000

        correct = ""
        if cached is None:
            cache.store(context, simulate_pack(device, query), metrics["total_chars"])
            llm_calls += 1
        else:
            cache.note_saved(metrics["total_chars"])
            if source_category and category and source_category != category:
                correct = "假阳性"
                false_positive += 1
            else:
                correct = "正确"

        base_total += len(flat)
        cpsc_total += metrics["total_chars"]
        rows.append({
            "任务": tag, "query": query, "类别": category,
            "基线字符": len(flat), "CPSC字符": metrics["total_chars"],
            "前缀字符": metrics["prefix_chars"], "载荷字符": metrics["payload_chars"],
            "缓存": how, "相似度": score, "命中来源类别": source_category or "-",
            "判定": correct or "-", "本地耗时ms": round(build_ms, 3),
            "调用模型": "否(复用)" if cached is not None else "是",
        })

    return rows, base_total, cpsc_total, llm_calls, false_positive, cache


def print_rows(rows):
    print("%-5s %-22s %-8s %-10s %-10s %-8s %-9s %-9s %-8s %-10s %s" % (
        "任务", "query", "类别", "基线字符", "CPSC字符", "缓存", "相似度", "来源类别", "判定", "本地ms", "调模型"))
    print("-" * 116)
    for r in rows:
        print("%-5s %-22s %-8s %-10d %-10d %-8s %-9s %-9s %-8s %-10s %s" % (
            r["任务"], r["query"][:20], r["类别"], r["基线字符"], r["CPSC字符"],
            r["缓存"], r["相似度"], r["命中来源类别"], r["判定"], r["本地耗时ms"], r["调用模型"]))


def main():
    print("=" * 116)
    print("CPSC 对比实验｜稳定前缀指纹 %s（%d 字符）" % (PREFIX_FINGERPRINT, len(STABLE_PREFIX)))
    print("=" * 116)
    rows, base_total, cpsc_total, llm_calls, fp, cache = run(threshold=0.55)
    print_rows(rows)

    stats = cache.stats()
    print("-" * 116)
    print("【体积】基线 %d 字符 → CPSC %d 字符，变化 %+.1f%%" % (
        base_total, cpsc_total, (cpsc_total / base_total - 1) * 100))
    print("【前缀】稳定前缀 %d 字符／次，占 CPSC 单次载荷 %.1f%%，可被服务端前缀缓存复用" % (
        len(STABLE_PREFIX), len(STABLE_PREFIX) * len(rows) / cpsc_total * 100))
    print("【缓存】查询 %d 次，命中 %d 次（精确 %d／语义 %d），命中率 %.1f%%，跨类别假阳性 %d 次" % (
        stats["lookups"], stats["hits"], stats["exact_hits"], stats["semantic_hits"],
        stats["hit_rate"] * 100, fp))
    print("【调用】大模型调用 %d 次（原 %d 次），减少 %.1f%%" % (
        llm_calls, len(rows), (1 - llm_calls / len(rows)) * 100))

    print()
    print("阈值扫描（观察命中率与假阳性的权衡）")
    print("%-8s %-10s %-10s %-12s %s" % ("阈值", "命中率", "假阳性", "模型调用", "说明"))
    print("-" * 116)
    sweep = []
    for th in (0.30, 0.40, 0.50, 0.55, 0.62, 0.70, 0.80):
        _, bt, ct, calls, fp2, c2 = run(threshold=th)
        s2 = c2.stats()
        note = "安全" if fp2 == 0 else "存在错误复用"
        sweep.append({"threshold": th, "hit_rate": s2["hit_rate"], "false_positive": fp2,
                      "llm_calls": calls, "safe": fp2 == 0})
        print("%-8.2f %-10s %-10d %-12d %s" % (th, "%.1f%%" % (s2["hit_rate"] * 100), fp2, calls, note))
    print("=" * 116)
    print("注：本机未配置大模型 API，所有指标在「结构化上下文 + 缓存」这一层测得，不含模型生成耗时。")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cpsc_benchmark_result.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({
            "prefix_chars": len(STABLE_PREFIX), "prefix_fingerprint": PREFIX_FINGERPRINT,
            "rows": rows, "stats": stats,
            "baseline_chars_total": base_total, "cpsc_chars_total": cpsc_total,
            "llm_calls": llm_calls, "false_positive": fp,
            "threshold_sweep": sweep,
        }, fh, ensure_ascii=False, indent=2)
    print("明细已写入 " + out)


if __name__ == "__main__":
    main()
