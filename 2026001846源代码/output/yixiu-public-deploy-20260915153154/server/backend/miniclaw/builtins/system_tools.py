"""内置插件：系统操作工具（检修业务版）

提供天工（综合智能中枢）调度一修系统各业务模块的工具，所有工具均对接
真实后端接口或数据库，使天工能够真正“操作”系统、完成多步任务链。

覆盖能力：
- 系统概览（在线设备 / 待处理告警 / 待审核 / 今日任务）
- 检修任务查询与创建
- 知识库检索
- 智能问修（cook-agent）
- 知识图谱检索（LightRAG）
- agent（智能体）状态
"""
import logging
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from miniclaw.tools import BaseTool, ToolResult, ToolParameter

logger = logging.getLogger("miniclaw.system_tools")

# 本机后端基址，工具通过 HTTP 回调本系统各业务接口
BACKEND_BASE_URL = os.getenv("MINICLAW_BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")

# 六大 agent 定义（与前端 yixiuMock / routes.yixiu.AGENTS 对齐）
AGENTS_STATE = [
    {"id": "tiangong", "name": "天工", "role": "综合智能中枢", "duty": "统筹检索、作业、知识、协作和核查智能体，汇总系统状态与风险。", "status": "online", "ip": "10.10.1.10"},
    {"id": "guanwei", "name": "观微", "role": "智能检索器灵", "duty": "发现设备故障线索，解析故障现象、型号、图片和维修文档。", "status": "online", "ip": "10.10.1.21"},
    {"id": "zhiju", "name": "执矩", "role": "检修作业器灵", "duty": "编排标准作业步骤，推进工单流转并提醒高风险安全确认。", "status": "online", "ip": "10.10.1.22"},
    {"id": "bowen", "name": "博闻", "role": "知识管理器灵", "duty": "整理技术资料、维护知识网络、沉淀历史检修案例。", "status": "online", "ip": "10.10.1.23"},
    {"id": "heming", "name": "和鸣", "role": "协作调度器灵", "duty": "管理联系人、协调现场人员、发起专家支援与任务沟通。", "status": "online", "ip": "10.10.1.24"},
    {"id": "mingjian", "name": "明鉴", "role": "复检核查器灵", "duty": "执行复检评估、安全检查、质量核验和任务验收。", "status": "online", "ip": "10.10.1.25"},
]


def _internal_headers(payload: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    try:
        import jwt
        from utils import Config
        token = jwt.encode(
            {
                "user_id": "tiangong-aios",
                "role": "admin",
                "exp": datetime.utcnow() + timedelta(hours=2),
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256",
        )
        headers["Authorization"] = f"Bearer {token}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("内部身份生成失败，按匿名请求继续: %s", exc)
    if payload and payload.get("idempotency_key"):
        headers["Idempotency-Key"] = str(payload["idempotency_key"])
    return headers


def _http_get(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
    import requests
    url = path if path.startswith("http") else f"{BACKEND_BASE_URL}{path}"
    resp = requests.get(url, params=params, headers=_internal_headers(), timeout=timeout)
    return {"status": resp.status_code, "data": resp.json() if resp.content else {}}


def _http_post(path: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
    import requests
    url = path if path.startswith("http") else f"{BACKEND_BASE_URL}{path}"
    resp = requests.post(url, json=payload or {}, headers=_internal_headers(payload), timeout=timeout)
    return {"status": resp.status_code, "data": resp.json() if resp.content else {}}


def _safe_http(callable_fn, *args, **kwargs) -> ToolResult:
    """统一封装 HTTP 调用异常，返回 ToolResult。"""
    try:
        result = callable_fn(*args, **kwargs)
        status = result.get("status", 0)
        data = result.get("data", {})
        if status == 401:
            return ToolResult(success=False, output="", error="接口需要登录鉴权，暂无法在内部直接调用")
        if status >= 400:
            return ToolResult(success=False, output="", error=f"接口返回 {status}: {data}")
        return ToolResult(success=True, output=json.dumps(data, ensure_ascii=False), metadata={"raw": data})
    except Exception as exc:  # noqa: BLE001
        logger.error("HTTP 工具调用失败: %s", exc)
        return ToolResult(success=False, output="", error=f"调用失败: {exc}")


class SystemOverviewTool(BaseTool):
    name = "system_overview"
    description = "获取一修系统整体概览，包括在线设备数、待处理告警、待审核案例、今日检修任务数。用于天工生成系统状态简报。"
    parameters = []

    def execute(self, **kwargs) -> ToolResult:
        return _safe_http(_http_get, "/api/dashboard/overview")


class MaintenanceTaskTool(BaseTool):
    name = "maintenance_task"
    description = "查询或创建检修任务。action='list' 按状态筛选任务（status 可选 pending/in_progress/completed/all）；action='get' 按 id 获取任务详情；action='create' 创建新任务。"
    parameters = [
        ToolParameter(name="action", type="string", description="操作类型: list / get / create", required=True),
        ToolParameter(name="status", type="string", description="任务状态筛选，list 时可用：pending/in_progress/completed/all", required=False, default="all"),
        ToolParameter(name="task_id", type="string", description="任务ID，get 时必填", required=False),
        ToolParameter(name="data", type="object", description="创建任务的字段，create 时必填", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        action = (kwargs.get("action") or "").strip().lower()
        if action == "list":
            status = (kwargs.get("status") or "all").strip()
            params = {"status": status} if status and status != "all" else {}
            result = _safe_http(_http_get, "/api/maintenance-tasks/", params=params)
            if result.success:
                return result
            # HTTP 鉴权失败(401)时，天工作为系统内部智能体直接读数据库获取任务
            return self._list_from_db(status)
        if action == "get":
            task_id = kwargs.get("task_id")
            if not task_id:
                return ToolResult(success=False, output="", error="get 操作需要 task_id")
            return _safe_http(_http_get, f"/api/maintenance-tasks/{task_id}")
        if action == "create":
            data = kwargs.get("data") or {}
            return _safe_http(_http_post, "/api/maintenance-tasks/", payload=data)
        return ToolResult(success=False, output="", error=f"不支持的操作: {action}")

    @staticmethod
    def _cell(row: Any, key: str) -> str:
        try:
            value = row[key]
        except Exception:  # noqa: BLE001
            return ""
        return "" if value is None else str(value)

    def _list_from_db(self, status: str) -> ToolResult:
        """HTTP 接口需鉴权时的回退方案：直接读取检修任务表。"""
        try:
            from utils import get_db_connection
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, output="", error=f"任务接口需登录且无法读取数据库: {exc}")
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                where = "WHERE 1=1"
                params: List[Any] = []
                if status and status != "all":
                    where += " AND mr.status = %s"
                    params.append(status)
                cursor.execute(
                    f"""SELECT mr.id, mr.title, mr.severity, mr.status, mr.description,
                               mr.fault_code, mr.created_at, u.name AS assignee_name,
                               e.name AS equipment_name, e.model AS equipment_model
                        FROM maintenance_records mr
                        LEFT JOIN users u ON u.id = mr.user_id
                        LEFT JOIN equipment e ON e.id = mr.equipment_id
                        {where}
                        ORDER BY mr.created_at DESC
                        LIMIT 20""",
                    params,
                )
                rows = cursor.fetchall()
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, output="", error=f"读取任务数据库失败: {exc}")
        if not rows:
            return ToolResult(success=True, output=f"检修任务列表为空(status={status})", metadata={"tasks": []})
        lines = []
        for r in rows:
            lines.append(
                f"- [{self._cell(r, 'id')}] {self._cell(r, 'title')} | "
                f"{self._cell(r, 'equipment_name') or '未知设备'} ({self._cell(r, 'equipment_model')}) | "
                f"严重度:{self._cell(r, 'severity')} | 状态:{self._cell(r, 'status')} | "
                f"负责人:{self._cell(r, 'assignee_name') or '未分配'} | 创建:{self._cell(r, 'created_at')}"
            )
        return ToolResult(
            success=True,
            output=f"检修任务列表({len(rows)}条):\n" + "\n".join(lines),
            metadata={"tasks": [dict(r) for r in rows]},
        )


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "检索一修知识库（历史故障案例、维修手册、标准作业流程等）。通过关键词匹配知识条目。"
    parameters = [
        ToolParameter(name="keyword", type="string", description="检索关键词，如设备型号、故障现象、部件名称", required=True),
        ToolParameter(name="limit", type="integer", description="返回条目上限", required=False, default=10),
    ]

    def execute(self, **kwargs) -> ToolResult:
        keyword = (kwargs.get("keyword") or "").strip()
        if not keyword:
            return ToolResult(success=False, output="", error="检索关键词不能为空")
        limit = int(kwargs.get("limit", 10))
        result = _safe_http(_http_get, "/api/yixiu/knowledge", params={"keyword": keyword, "limit": limit})
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            items = raw.get("data", raw) if isinstance(raw, dict) else raw
            if isinstance(items, dict):
                items = items.get("items") or items.get("list") or items
            summary = self._summarize(items, keyword)
            return ToolResult(success=True, output=summary, metadata=result.metadata)
        return result

    @staticmethod
    def _summarize(items: Any, keyword: str) -> str:
        if not items:
            return f"未检索到与「{keyword}」相关的知识条目"
        if isinstance(items, dict):
            items = items.get("items") or items.get("list") or []
        rows: List[str] = []
        for idx, item in enumerate(items[:10], 1):
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or "未命名"
            equip = item.get("equipment") or item.get("model") or ""
            cat = item.get("category") or item.get("type") or ""
            rows.append(f"{idx}. {title}" + (f"（{equip}）" if equip else "") + (f" [{cat}]" if cat else ""))
        return f"检索「{keyword}」命中 {len(items)} 条知识：\n" + "\n".join(rows)


class RepairConsultTool(BaseTool):
    name = "repair_consult"
    description = "调用智能问修（观微/团团能力），根据故障描述给出排查建议。适用于设备故障诊断、检修方法咨询。"
    parameters = [
        ToolParameter(name="message", type="string", description="故障描述或问修问题", required=True),
        ToolParameter(name="action", type="string", description="问修动作类型，可选，如 diagnose/plan", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        message = (kwargs.get("message") or "").strip()
        if not message:
            return ToolResult(success=False, output="", error="问修内容不能为空")
        payload = {"message": message}
        if kwargs.get("action"):
            payload["action"] = kwargs["action"]
        result = _safe_http(_http_post, "/cook-agent/chat", payload=payload, timeout=45)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            text = raw.get("response") or raw.get("data", {}).get("response") or raw.get("answer") or ""
            if text:
                return ToolResult(success=True, output=text, metadata=result.metadata)
        return result


class KnowledgeGraphTool(BaseTool):
    name = "knowledge_graph"
    description = "查询知识图谱（LightRAG），支持多种检索模式：naive/local/global/hybrid/mix。用于结构化故障原因、部件关系、检修方案推理。"
    parameters = [
        ToolParameter(name="query", type="string", description="自然语言查询，如'CG-125发动机异响的原因和检修方案'", required=True),
        ToolParameter(name="mode", type="string", description="检索模式: naive/local/global/hybrid/mix", required=False, default="hybrid"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        query = (kwargs.get("query") or "").strip()
        if not query:
            return ToolResult(success=False, output="", error="图谱查询不能为空")
        mode = (kwargs.get("mode") or "hybrid").strip()
        result = _safe_http(_http_post, "/api/rag/query", payload={"query": query, "mode": mode}, timeout=45)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            text = raw.get("response") or raw.get("data", {}).get("response") or raw.get("answer") or ""
            if not text and isinstance(raw, dict):
                text = json.dumps(raw, ensure_ascii=False)[:1500]
            if text:
                return ToolResult(success=True, output=text, metadata=result.metadata)
        return result


class AiosPlanTool(BaseTool):
    name = "aios_plan"
    description = "天工 AIOS 任务规划工具。根据用户目标生成结构化执行计划，包含智能体分工、执行动作、目标页面和预期产物。适合复杂任务、跨智能体协作、检修闭环。"
    parameters = [
        ToolParameter(name="goal", type="string", description="用户目标或任务指令", required=True),
        ToolParameter(name="mode", type="string", description="规划模式：auto/risk/repair/support/review/knowledge", required=False, default="auto"),
        ToolParameter(name="task_id", type="string", description="可选，指定工单ID或工单编号", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        goal = (kwargs.get("goal") or "").strip()
        if not goal:
            return ToolResult(success=False, output="", error="AIOS 规划目标不能为空")
        payload = {"goal": goal, "mode": kwargs.get("mode") or "auto", "task_id": kwargs.get("task_id") or ""}
        result = _safe_http(_http_post, "/api/yixiu/aios/plan", payload=payload, timeout=20)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            steps = data.get("steps", []) if isinstance(data, dict) else []
            focus = data.get("focus", {}) if isinstance(data, dict) else {}
            lines = [f"AIOS 已生成 {len(steps)} 步计划，模式：{data.get('mode', 'auto')}。"]
            if focus:
                lines.append(f"重点对象：{focus.get('workOrderNo') or focus.get('id')} / {focus.get('equipment_name')} / {focus.get('fault_type')}")
            for idx, step in enumerate(steps, 1):
                agent = step.get("agent", {}).get("name", "智能体")
                lines.append(f"{idx}. {agent}：{step.get('title')} -> {step.get('expected_output')}")
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw, "plan": data})
        return result


class AiosExecuteTool(BaseTool):
    name = "aios_execute"
    description = "天工 AIOS 执行工具。执行 AIOS 计划中的单步或全部步骤，形成资料召回、作业编排、协作消息、复检清单和知识沉淀候选。支持走新架构（aios_arch.langgraph_supervisor + MCP Gateway + OPA Guard），通过 use_supervisor=True 或 AIOS_USE_SUPERVISOR=1 启用。"
    parameters = [
        ToolParameter(name="plan_id", type="string", description="AIOS 计划ID；如果不传，可以直接传 goal 生成并执行", required=False),
        ToolParameter(name="goal", type="string", description="用户目标；当没有 plan_id 时使用", required=False),
        ToolParameter(name="step_key", type="string", description="单步执行的步骤 key，如 sense/retrieve/operate/collaborate/review/archive", required=False),
        ToolParameter(name="execute_all", type="boolean", description="是否执行完整计划", required=False, default=False),
        ToolParameter(name="commit", type="boolean", description="是否写入协作消息等业务记录", required=False, default=True),
        ToolParameter(name="use_supervisor", type="boolean", description="是否走新架构 langgraph_supervisor（默认按环境变量 AIOS_USE_SUPERVISOR）", required=False, default=False),
        ToolParameter(name="approve_all", type="boolean", description="走新架构时是否一次性批准所有 write 步骤", required=False, default=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        goal = kwargs.get("goal") or ""
        plan_id = kwargs.get("plan_id") or ""
        if not plan_id and not goal:
            return ToolResult(success=False, output="", error="执行 AIOS 需要 plan_id 或 goal")

        use_supervisor = bool(kwargs.get("use_supervisor")) or os.getenv("AIOS_USE_SUPERVISOR", "0") == "1"
        if use_supervisor:
            return self._execute_via_supervisor(kwargs, goal=goal)

        payload = {
            "plan_id": plan_id,
            "goal": goal,
            "step_key": kwargs.get("step_key") or "",
            "execute_all": bool(kwargs.get("execute_all", False)),
            "commit": kwargs.get("commit", True) is not False,
            "confirmed": True,
            "idempotency_key": kwargs.get("idempotency_key") or f"aios-exec-{uuid.uuid4().hex[:12]}",
        }
        result = _safe_http(_http_post, "/api/yixiu/aios/execute", payload=payload, timeout=30)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            artifacts = data.get("artifacts", {}) if isinstance(data, dict) else {}
            lines = [f"AIOS 执行进度 {data.get('progress', 0)}%，状态：{data.get('status', 'running')}。"]
            for key, artifact in artifacts.items():
                lines.append(f"- {key}: {artifact.get('summary', '已完成')}")
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw})
        return result

    def _execute_via_supervisor(self, kwargs: Dict[str, Any], goal: str) -> ToolResult:
        """新架构路径：OPA 拦截 -> supervisor_execute -> MCP Gateway 调用工具。"""
        from aios_runtime import supervisor_execute
        try:
            from aios_arch.opa_guard import evaluate as opa_evaluate
            decision = opa_evaluate(
                action="aios.execute.supervisor",
                resource="aios:execute",
                payload=kwargs,
                actor={"user_id": "aios_execute_tool", "role": "admin"},
                context={"kind": "write", "approve_all": bool(kwargs.get("approve_all"))},
            )
            if decision["decision"] == "deny":
                return ToolResult(success=False, output="", error=f"OPA 拒绝: {decision['reason']}",
                                  metadata={"opa_decision_id": decision["decision_id"]})
        except Exception as exc:  # noqa: BLE001
            logger.warning("OPA 评估失败，继续执行: %s", exc)

        try:
            outcome = supervisor_execute(
                goal=goal,
                mode=str(kwargs.get("mode") or "auto"),
                task_id=str(kwargs.get("task_id") or ""),
                execute_all=bool(kwargs.get("execute_all", True)),
                approve_all=bool(kwargs.get("approve_all", True)),
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, output="", error=f"supervisor 执行失败: {exc}")
        artifacts = outcome.get("artifacts", {}) or {}
        final_report = outcome.get("final_report", {}) or {}
        lines = [
            f"AIOS Supervisor run_id={outcome.get('run_id') or ''}",
            f"trace_id={outcome.get('trace_id') or ''}",
            f"completed_steps={list((final_report.get('completed') or []))}",
        ]
        for key, artifact in artifacts.items():
            status = artifact.get("status", "completed") if isinstance(artifact, dict) else "completed"
            lines.append(f"- {key}: {status}")
        if outcome.get("error"):
            return ToolResult(success=False, output="", error=outcome["error"], metadata=outcome)
        return ToolResult(success=True, output="\n".join(lines), metadata=outcome)


class AiosInspectTool(BaseTool):
    name = "aios_inspect"
    description = "查看、续跑或取消天工 AIOS 运行。action='detail' 查看运行详情，action='events' 查看事件流，action='resume' 继续执行，action='cancel' 取消长任务。"
    parameters = [
        ToolParameter(name="action", type="string", description="detail / events / resume / cancel", required=True),
        ToolParameter(name="run_id", type="string", description="AIOS 运行ID", required=False),
        ToolParameter(name="agent_id", type="string", description="events 时可按智能体过滤", required=False),
        ToolParameter(name="execute_all", type="boolean", description="resume 时是否继续执行全部可执行步骤", required=False, default=True),
        ToolParameter(name="approve_all", type="boolean", description="resume 时是否批准所有需要确认的步骤", required=False, default=False),
        ToolParameter(name="reason", type="string", description="cancel 时的取消原因", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        action = (kwargs.get("action") or "").strip().lower()
        run_id = (kwargs.get("run_id") or "").strip()
        if action == "detail":
            if not run_id:
                return ToolResult(success=False, output="", error="查看详情需要 run_id")
            result = _safe_http(_http_get, f"/api/yixiu/aios/runs/{run_id}")
        elif action == "events":
            params = {}
            if run_id:
                params["run_id"] = run_id
            if kwargs.get("agent_id"):
                params["agent_id"] = kwargs["agent_id"]
            result = _safe_http(_http_get, "/api/yixiu/aios/events", params=params)
        elif action == "resume":
            if not run_id:
                return ToolResult(success=False, output="", error="续跑需要 run_id")
            payload = {
                "run_id": run_id,
                "execute_all": bool(kwargs.get("execute_all", True)),
                "approve_all": bool(kwargs.get("approve_all", False)),
                "confirmed": True,
                "idempotency_key": f"aios-resume-{uuid.uuid4().hex[:12]}",
            }
            result = _safe_http(_http_post, "/api/yixiu/aios/resume", payload=payload, timeout=45)
        elif action == "cancel":
            if not run_id:
                return ToolResult(success=False, output="", error="取消长任务需要 run_id")
            result = _safe_http(
                _http_post,
                "/api/yixiu/aios/cancel",
                payload={"run_id": run_id, "reason": kwargs.get("reason") or "用户取消长任务"},
                timeout=20,
            )
        else:
            return ToolResult(success=False, output="", error=f"不支持的 AIOS inspect 操作: {action}")
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            if action == "events":
                events = data.get("events", []) if isinstance(data, dict) else []
                lines = [f"AIOS 事件 {len(events)} 条："]
                for item in events[:12]:
                    lines.append(f"- {item.get('created_at')} {item.get('agent_name')}：{item.get('title')} / {item.get('status')}")
                return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw})
            if action in {"detail", "resume"} and isinstance(data, dict):
                plan = data.get("plan") or {}
                return ToolResult(success=True, output=f"AIOS {data.get('id') or data.get('run_id') or run_id} 状态：{data.get('status')}，进度：{data.get('progress', plan.get('progress', 0))}%。", metadata={"raw": raw})
            if action == "cancel" and isinstance(data, dict):
                run = data.get("run") or {}
                return ToolResult(success=True, output=f"AIOS {run_id} 已取消，状态：{run.get('status', 'cancelled')}。", metadata={"raw": raw})
        return result


class AgentStatusTool(BaseTool):
    name = "agent_status"
    description = "获取六大 agent（智能体）的当前状态与职责，用于天工统筹调度、判断该把任务分派给哪个 agent。"
    parameters = [
        ToolParameter(name="agent_id", type="string", description="可选，指定 agent ID（tiangong/guanwei/zhiju/bowen/heming/mingjian），不填则返回全部", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        agent_id = (kwargs.get("agent_id") or "").strip()
        result = _safe_http(_http_get, "/api/yixiu/agents", params={"agent_id": agent_id} if agent_id else {})
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            agents = data.get("agents", []) if isinstance(data, dict) else []
            if agents:
                lines = []
                for a in agents:
                    metrics = a.get("metrics") or {}
                    lines.append(
                        f"- {a['name']}（{a['role']}）[{a['status']}]: {a['duty']} "
                        f"执行{metrics.get('event_count', 0)}次"
                    )
                return ToolResult(success=True, output="六大 agent 状态：\n" + "\n".join(lines), metadata={"agents": agents})
        if agent_id:
            for a in AGENTS_STATE:
                if a["id"] == agent_id:
                    return ToolResult(success=True, output=json.dumps(a, ensure_ascii=False), metadata={"agent": a})
            return ToolResult(success=False, output="", error=f"未找到 agent: {agent_id}")
        lines = []
        for a in AGENTS_STATE:
            lines.append(f"- {a['name']}（{a['role']}）[{a['status']}]: {a['duty']}")
        return ToolResult(success=True, output="六大 agent 状态：\n" + "\n".join(lines), metadata={"agents": AGENTS_STATE})


class AgentInvokeTool(BaseTool):
    name = "agent_invoke"
    description = "调用指定一修智能体执行业务任务。适合让观微查知识、执矩生成步骤、博闻沉淀知识、和鸣总结协作、明鉴核查质量。"
    parameters = [
        ToolParameter(name="agent_id", type="string", description="智能体ID：tiangong/guanwei/zhiju/bowen/heming/mingjian", required=True),
        ToolParameter(name="goal", type="string", description="需要该智能体完成的业务目标", required=True),
        ToolParameter(name="task_id", type="string", description="可选，关联检修任务ID", required=False),
        ToolParameter(name="commit", type="boolean", description="是否写入执行记录", required=False, default=True),
    ]

    def execute(self, **kwargs) -> ToolResult:
        agent_id = (kwargs.get("agent_id") or "").strip()
        goal = (kwargs.get("goal") or "").strip()
        if not agent_id or not goal:
            return ToolResult(success=False, output="", error="agent_id 和 goal 不能为空")
        payload = {"goal": goal, "task_id": kwargs.get("task_id") or "", "commit": kwargs.get("commit", True)}
        result = _safe_http(_http_post, f"/api/yixiu/agents/{agent_id}/invoke", payload=payload, timeout=30)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            summary = data.get("result", {}).get("summary") if isinstance(data, dict) else ""
            return ToolResult(success=True, output=summary or json.dumps(data, ensure_ascii=False), metadata={"raw": raw})
        return result


class DatabaseStatusTool(BaseTool):
    name = "database_status"
    description = "检查或初始化一修业务数据库。action='status' 查看状态，action='bootstrap' 初始化基础表、模板和智能体记忆。"
    parameters = [
        ToolParameter(name="action", type="string", description="status / bootstrap", required=False, default="status"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        action = (kwargs.get("action") or "status").strip().lower()
        if action == "bootstrap":
            result = _safe_http(_http_post, "/api/yixiu/database/bootstrap", payload={})
        else:
            result = _safe_http(_http_get, "/api/yixiu/database/status")
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            sqlite_status = data.get("sqlite", {}) if isinstance(data, dict) else {}
            mysql_status = data.get("mysql", {}) if isinstance(data, dict) else {}
            lines = [
                f"一修业务库：{'正常' if sqlite_status.get('ok') else '异常'}",
                f"既有业务库：{'正常' if mysql_status.get('ok') else mysql_status.get('message', '暂不可用')}",
            ]
            tables = sqlite_status.get("tables") or {}
            if tables:
                lines.append("核心表：" + "，".join(f"{k}:{v}" for k, v in tables.items()))
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw})
        return result


class AiosPlatformTool(BaseTool):
    name = "aios_platform"
    description = "查看天工 AIOS 平台能力，包括智能体配置、Team、Workflow、会话、记忆、RAG、工具、审批、Trace、权限和渠道。"
    parameters = []

    def execute(self, **kwargs) -> ToolResult:
        result = _safe_http(_http_get, "/api/yixiu/aios/platform", timeout=20)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            counts = data.get("counts") or {}
            lines = [
                "天工 AIOS 平台能力：",
                f"- 智能体：{counts.get('agents', 0)} 个，Team：{counts.get('teams', 0)} 个",
                f"- 会话：{counts.get('sessions', 0)} 个，长期记忆：{counts.get('memories', 0)} 条",
                f"- 运行记录：{counts.get('runs', 0)} 条，待审批：{counts.get('pending_approvals', 0)} 条",
                "- 支持：多智能体协作、Workflow 编排、RAG、工具调用、后台任务、人工审批、Trace 和多渠道接入",
            ]
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw})
        return result


class AiosApprovalTool(BaseTool):
    name = "aios_approval"
    description = "查看或处理 AIOS 人工审批。用于高风险写入、知识入库、任务流转前的人机协同确认。"
    parameters = [
        ToolParameter(name="action", type="string", description="list / decide", required=False, default="list"),
        ToolParameter(name="approval_id", type="string", description="审批ID，decide 时必填", required=False),
        ToolParameter(name="decision", type="string", description="approved / rejected", required=False),
        ToolParameter(name="note", type="string", description="审批备注", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        action = (kwargs.get("action") or "list").strip().lower()
        if action == "decide":
            approval_id = (kwargs.get("approval_id") or "").strip()
            decision = (kwargs.get("decision") or "").strip()
            if not approval_id or decision not in {"approved", "rejected"}:
                return ToolResult(success=False, output="", error="处理审批需要 approval_id 和 approved/rejected")
            result = _safe_http(
                _http_post,
                f"/api/yixiu/aios/approvals/{approval_id}/decision",
                payload={"decision": decision, "note": kwargs.get("note") or "", "decided_by": "天工"},
            )
        else:
            result = _safe_http(_http_get, "/api/yixiu/aios/approvals", params={"status": "pending"})
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            if action == "decide":
                return ToolResult(success=True, output=f"审批已处理：{data.get('status')}", metadata={"raw": raw})
            approvals = data.get("approvals", []) if isinstance(data, dict) else []
            lines = [f"待审批 {len(approvals)} 条："]
            for item in approvals[:10]:
                lines.append(f"- {item.get('id')} {item.get('title')} / {item.get('created_at')}")
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw})
        return result


class FileParseTool(BaseTool):
    name = "file_parse"
    description = "解析 PDF/DOCX/TXT/MD/CSV 知识文件：上传→切片→embedding→入库。适合让观微/博闻把现场资料沉淀到知识库。"
    parameters = [
        ToolParameter(name="file_id", type="string", description="已上传文件的ID（如 file-xxx），不填则需 file_path", required=False),
        ToolParameter(name="file_path", type="string", description="服务端文件绝对路径，不填则用 file_id 查询", required=False),
        ToolParameter(name="source", type="string", description="知识来源标签，默认文件名", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        from services.file_parser import parse_file
        from services.rag_service import insert_chunks
        file_path = kwargs.get("file_path")
        source = kwargs.get("source") or ""
        if not file_path:
            file_id = (kwargs.get("file_id") or "").strip()
            if not file_id:
                return ToolResult(success=False, output="", error="需要 file_id 或 file_path")
            # 通过 /files 查询拿存储路径
            result = _safe_http(_http_get, "/api/yixiu/files", params={"keyword": file_id})
            if not result.success:
                return result
            raw = result.metadata.get("raw", {})
            files = (raw.get("data") or {}).get("files", []) if isinstance(raw, dict) else []
            match = next((f for f in files if f.get("id") == file_id), None)
            if not match:
                return ToolResult(success=False, output="", error=f"未找到文件: {file_id}")
            source = source or match.get("name", "")
            # 服务端路径需要从配置反推
            from pathlib import Path
            try:
                from flask import current_app
                upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "yixiu"
                file_path = str(upload_dir / match.get("stored_name", ""))
            except Exception:
                return ToolResult(success=False, output="", error="无法解析服务端路径，请直接传 file_path")
        try:
            chunks = parse_file(file_path)
            if not chunks:
                return ToolResult(success=False, output="", error="文件无可提取文本")
            ingestion = insert_chunks(chunks, source=source or "file_parse_tool")
            summary = f"文件已切片入库：{ingestion.get('inserted', 0)}/{ingestion.get('total', 0)} 块成功"
            return ToolResult(success=True, output=summary, metadata={"chunks": len(chunks), "ingestion": ingestion})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, output="", error=f"解析失败: {exc}")


class VisionAnalyzeTool(BaseTool):
    name = "vision_analyze"
    description = "图片识别：调用视觉模型分析设备故障图片，输出设备、异常部位、故障迹象和安全风险。适合观微分析现场照片。"
    parameters = [
        ToolParameter(name="file_id", type="string", description="已上传图片文件ID", required=True),
    ]

    def execute(self, **kwargs) -> ToolResult:
        file_id = (kwargs.get("file_id") or "").strip()
        if not file_id:
            return ToolResult(success=False, output="", error="需要 file_id")
        # 调用 /files/<id>/content 拿图片，再走视觉模型
        # 直接走 /search 接口（已集成 _analyze_image），或调用 /files 的解析结果
        result = _safe_http(_http_get, f"/api/yixiu/files/{file_id}/content")
        if not result.success:
            return result
        # /content 返回二进制，无法走 _safe_http 的 json 解析；这里改用 /search 触发分析
        # 退而求其次：调用 /files 列表拿 analysis
        list_result = _safe_http(_http_get, "/api/yixiu/files")
        if list_result.success:
            raw = list_result.metadata.get("raw", {})
            files = (raw.get("data") or {}).get("files", []) if isinstance(raw, dict) else []
            match = next((f for f in files if f.get("id") == file_id), None)
            if match:
                analysis = match.get("analysis") or match.get("metadata", {})
                if isinstance(analysis, str):
                    try:
                        import json as _json
                        analysis = _json.loads(analysis)
                    except Exception:
                        analysis = {"summary": analysis}
                summary = analysis.get("summary") or analysis.get("equipment") or "无可识别内容"
                return ToolResult(success=True, output=f"图片识别结果：{summary}", metadata={"analysis": analysis, "file": match})
        return ToolResult(success=False, output="", error=f"未找到文件或无分析结果: {file_id}")


class RagQueryTool(BaseTool):
    name = "rag_query"
    description = "向量相似度检索（RAG）：基于 LightRAG hybrid 模式检索知识图谱，返回 top 命中块。适合观微做故障判断依据召回。"
    parameters = [
        ToolParameter(name="query", type="string", description="自然语言查询，如'CG-125 发动机异响原因'", required=True),
        ToolParameter(name="limit", type="integer", description="返回命中数上限", required=False, default=5),
        ToolParameter(name="mode", type="string", description="检索模式: naive/local/global/hybrid/mix", required=False, default="hybrid"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        query = (kwargs.get("query") or "").strip()
        if not query:
            return ToolResult(success=False, output="", error="query 不能为空")
        limit = int(kwargs.get("limit", 5))
        mode = (kwargs.get("mode") or "hybrid").strip()
        result = _safe_http(_http_get, "/api/yixiu/knowledge/similar", params={"query": query, "limit": limit, "mode": mode})
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            hits = data.get("hits", []) if isinstance(data, dict) else []
            if not hits:
                return ToolResult(success=True, output=f"未检索到与「{query}」相关的知识块", metadata={"raw": raw})
            lines = [f"RAG 检索命中 {len(hits)} 块："]
            for idx, hit in enumerate(hits, 1):
                text = (hit.get("text") or "")[:120]
                lines.append(f"{idx}. [{hit.get('source', 'unknown')}] {text}")
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw, "hits": hits})
        return result


class SopGenerateTool(BaseTool):
    name = "sop_generate"
    description = "生成检修标准作业流程（SOP）步骤、工具备件清单和安全确认项。适合执矩为检修工单生成可执行作业方案。"
    parameters = [
        ToolParameter(name="category", type="string", description="设备类别，如'配电柜'/'发动机'", required=False, default="通用设备"),
        ToolParameter(name="maintenanceLevel", type="string", description="检修等级，如'一级'/'二级'/'三级'", required=False, default="二级检修"),
        ToolParameter(name="fault_type", type="string", description="故障类型，如'过热'/'异响'/'渗漏'", required=False, default="待确认"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        payload = {
            "category": kwargs.get("category") or "通用设备",
            "maintenanceLevel": kwargs.get("maintenanceLevel") or "二级检修",
            "faultType": kwargs.get("fault_type") or kwargs.get("fault") or "待确认",
            "deviceName": kwargs.get("device_name") or kwargs.get("category") or "设备",
            "deviceModel": kwargs.get("model") or "待确认型号",
            "query": kwargs.get("query") or f"{kwargs.get('fault_type', '')} {kwargs.get('category', '')} 检修方案",
        }
        result = _safe_http(_http_post, "/api/yixiu/search", payload=payload, timeout=20)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            sop = data.get("sop", []) if isinstance(data, dict) else []
            safety = data.get("safety", []) if isinstance(data, dict) else []
            tools_list = data.get("tools") or data.get("spares") or []
            lines = [f"已生成 {len(sop)} 步 SOP，{len(safety)} 项安全确认。"]
            for idx, step in enumerate(sop, 1):
                if isinstance(step, dict):
                    lines.append(f"{idx}. {step.get('action') or step.get('title', '')}（{step.get('duration', '约15分钟')}）")
                else:
                    lines.append(f"{idx}. {step}")
            if safety:
                lines.append("安全确认：" + "、".join(safety[:5]))
            if tools_list:
                lines.append("工具备件：" + "、".join(str(t) for t in tools_list[:8]))
            return ToolResult(success=True, output="\n".join(lines), metadata={"raw": raw, "sop": sop, "safety": safety})
        return result


class TaskUpdateTool(BaseTool):
    name = "task_update"
    description = "更新检修工单状态、负责人或备注。适合执矩推进工单流转、写入作业证据。高风险写入需 confirmed + 幂等键。"
    parameters = [
        ToolParameter(name="task_id", type="string", description="工单ID，如 task-xxx 或 YX-20260803-001", required=True),
        ToolParameter(name="status", type="string", description="新状态：pending/in_progress/done/failed/needs_recheck", required=False),
        ToolParameter(name="operator", type="string", description="操作人", required=False, default="天工"),
        ToolParameter(name="note", type="string", description="备注/作业证据", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        task_id = (kwargs.get("task_id") or "").strip()
        if not task_id:
            return ToolResult(success=False, output="", error="task_id 不能为空")
        payload = {
            "status": kwargs.get("status") or "in_progress",
            "operator": kwargs.get("operator") or "天工",
            "note": kwargs.get("note") or "",
            "confirmed": True,
            "idempotency_key": f"task-update-{uuid.uuid4().hex[:12]}",
        }
        result = _safe_http(_http_post, f"/api/yixiu/tasks/{task_id}/status", payload=payload, timeout=15)
        if result.success and result.metadata.get("raw"):
            raw = result.metadata["raw"]
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            return ToolResult(success=True, output=f"工单 {task_id} 已更新为 {data.get('status', payload['status'])}", metadata={"raw": raw})
        return result


def register(api):
    api.register_tool(SystemOverviewTool())
    api.register_tool(MaintenanceTaskTool())
    api.register_tool(KnowledgeSearchTool())
    api.register_tool(RepairConsultTool())
    api.register_tool(KnowledgeGraphTool())
    api.register_tool(AiosPlanTool())
    api.register_tool(AiosExecuteTool())
    api.register_tool(AiosInspectTool())
    api.register_tool(AgentStatusTool())
    api.register_tool(AgentInvokeTool())
    api.register_tool(DatabaseStatusTool())
    api.register_tool(AiosPlatformTool())
    api.register_tool(AiosApprovalTool())
    # 真实能力工具：让 AIOS 执行链路的 mock 分支可被 Tool 调用替换
    api.register_tool(FileParseTool())
    api.register_tool(VisionAnalyzeTool())
    api.register_tool(RagQueryTool())
    api.register_tool(SopGenerateTool())
    api.register_tool(TaskUpdateTool())
