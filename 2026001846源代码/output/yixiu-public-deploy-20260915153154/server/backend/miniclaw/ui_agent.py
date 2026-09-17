"""天工 UI 遥控 Agent

不直接调用后端业务接口，而是让 LLM 根据用户指令生成一份「UI 操作计划」，
由前端按计划遥控界面（移动虚拟鼠标、切换页面、在 agent 输入框打字、点发送），
实现“天工操作应用”的可视化演示。

输出格式：
    [UI_PLAN]
    [
      {"action": "navigate", "agent": "guanwei"},
      {"action": "type", "text": "CG-125 发动机异响"},
      {"action": "click_send"},
      {"action": "wait", "seconds": 3},
      {"action": "navigate", "agent": "tiangong"},
      {"action": "done"}
    ]
    [/UI_PLAN]
    天工的总结说明……
"""
import json
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger("miniclaw.ui_agent")

# 六大 agent（前端页面映射）
AGENTS_DESC = """可用 agent 页面（action=navigate 的 agent 取值）：
- tiangong  天工：统筹调度总览（首页）
- guanwei   观微：故障检索、资料召回
- zhiju     执矩：检修作业、任务流转
- heming    和鸣：联系人、人员协作
- mingjian  明鉴：复检核查、任务验收
- bowen     博闻：知识文件、资料沉淀"""

UI_ACTIONS_DESC = """可用操作（UI_PLAN 数组中的元素）：
- {"action": "navigate", "agent": "agent id"}   切换到指定 agent 页面
- {"action": "type", "text": "输入内容"}       在当前页面的输入框打字
- {"action": "click_send"}                      点击发送按钮，提交给当前 agent
- {"action": "wait", "seconds": 3}              等待 agent 返回结果（建议 2-4 秒）
- {"action": "done"}                            操作完成，回到汇总"""

TIANGONG_UI_PROMPT = f"""你是天工，一修设备检修系统的综合智能中枢。这次你通过「遥控操作」前端界面来完成任务——你会生成一份 UI 操作计划，前端会按计划移动鼠标、切换页面、在 agent 输入框打字并点击发送，就像你亲自在操作应用一样。

# 可用页面
{AGENTS_DESC}

# 可用操作
{UI_ACTIONS_DESC}

# 规则
1. 先把用户指令拆解为依次访问的 agent 与对应输入内容，再输出操作计划。
2. 每个 agent 的操作顺序固定为：navigate → type → click_send → wait。
3. 所有步骤结束后，必须 navigate 回 tiangong，并以 done 收尾。
4. type 的内容要符合该 agent 的职责（观微填故障描述、执矩填任务指令、和鸣填人员需求、明鉴填复检意见、博闻填资料问题）。
5. 不要在一次 type 里塞过多内容，保持像真人输入的自然长度。

# 输出格式（严格遵守）
先输出操作计划，用 [UI_PLAN] 和 [/UI_PLAN] 包裹一个 JSON 数组；
然后空一行，用中文给出本次操作的总结说明（做了什么、预期各 agent 返回什么、下一步建议）。

# 示例
用户：帮我用观微查一下 CG-125 发动机异响，然后让执矩建个检修任务
天工：
[UI_PLAN]
[
  {{"action": "navigate", "agent": "guanwei"}},
  {{"action": "type", "text": "CG-125 发动机热车后异响，请检索故障线索"}},
  {{"action": "click_send"}},
  {{"action": "wait", "seconds": 3}},
  {{"action": "navigate", "agent": "zhiju"}},
  {{"action": "type", "text": "创建检修任务：CG-125 发动机异响排查，优先级高"}},
  {{"action": "click_send"}},
  {{"action": "wait", "seconds": 3}},
  {{"action": "navigate", "agent": "tiangong"}},
  {{"action": "done"}}
]
[/UI_PLAN]
我已依次遥控观微检索故障、执矩创建检修任务。观微会返回故障线索与参考依据，执矩会生成工单并提醒高风险安全确认，稍后我汇总两路结果给出处置建议。
"""


_PLAN_RE = re.compile(r"\[UI_PLAN\](.*?)\[/UI_PLAN\]", re.DOTALL)


def generate_ui_plan(message: str) -> Dict[str, Any]:
    """根据用户自然语言指令生成 UI 操作计划。

    返回: {"plan": [...], "summary": "...", "reply": "..."}
    """
    from services.ai_gateway import ai_agent

    if not ai_agent.settings.configured:
        return {
            "plan": [],
            "summary": "AI 网关未配置，无法生成操作计划。",
            "reply": "",
            "error": "AI gateway not configured",
        }

    messages = [
        {"role": "system", "content": TIANGONG_UI_PROMPT},
        {"role": "user", "content": message},
    ]
    try:
        reply = ai_agent.chat(messages=messages, temperature=0.3, max_tokens=1200)
    except Exception as exc:  # noqa: BLE001
        logger.error("天工 UI 计划生成失败: %s", exc)
        return {"plan": [], "summary": f"生成失败: {exc}", "reply": "", "error": str(exc)}

    plan = _parse_plan(reply)
    summary = _parse_summary(reply, plan)
    return {"plan": plan, "summary": summary, "reply": reply, "error": None}


def _parse_plan(reply: str) -> List[Dict[str, Any]]:
    """从 LLM 回复中提取 [UI_PLAN] JSON 数组。"""
    match = _PLAN_RE.search(reply or "")
    if not match:
        return []
    raw = match.group(1).strip()
    # 容错：去掉可能的前后噪声
    first_bracket = raw.find("[")
    last_bracket = raw.rfind("]")
    if first_bracket >= 0 and last_bracket > first_bracket:
        raw = raw[first_bracket:last_bracket + 1]
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("UI_PLAN JSON 解析失败: %s | raw=%s", exc, raw[:200])
        return []
    if not isinstance(plan, list):
        return []
    # 只保留合法操作
    valid_actions = {"navigate", "type", "click_send", "wait", "done"}
    cleaned: List[Dict[str, Any]] = []
    for step in plan:
        if not isinstance(step, dict):
            continue
        action = step.get("action")
        if action not in valid_actions:
            continue
        cleaned.append(step)
    # 保证以 done 收尾
    if not cleaned or cleaned[-1].get("action") != "done":
        cleaned.append({"action": "done"})
    return cleaned


def _parse_summary(reply: str, plan: List[Dict[str, Any]]) -> str:
    """提取 [UI_PLAN] 之后的总结文本；若没有则根据 plan 生成简述。"""
    match = _PLAN_RE.search(reply or "")
    if match:
        tail = reply[match.end():].strip()
        if tail:
            return tail
    if not plan:
        return "天工未能生成有效操作计划。"
    steps_desc = []
    for s in plan:
        a = s.get("action")
        if a == "navigate":
            steps_desc.append(f"切换到 {s.get('agent', '?')}")
        elif a == "type":
            steps_desc.append(f"输入「{s.get('text', '')}」")
        elif a == "click_send":
            steps_desc.append("点击发送")
        elif a == "wait":
            steps_desc.append(f"等待 {s.get('seconds', 3)}s")
        elif a == "done":
            steps_desc.append("完成")
    return "操作计划：" + " → ".join(steps_desc)
