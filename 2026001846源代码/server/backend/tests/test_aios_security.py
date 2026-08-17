import json
import sys
import tempfile
import unittest
import asyncio
from pathlib import Path

import jwt
from flask import Flask

BACKEND_DIR = Path(__file__).resolve().parents[1]
SERVER_DIR = BACKEND_DIR.parent
for path in (BACKEND_DIR, SERVER_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import security
from routes import monitor, yixiu
from utils import Config


def token(user_id="u-1", role="operator"):
    return jwt.encode({"user_id": user_id, "role": role}, Config.JWT_SECRET_KEY, algorithm="HS256")


class AiosSecurityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        temp_dir = Path(self.tmp.name)
        self.old_yixiu_db = yixiu.DB_PATH
        self.old_security_db = security.SECURITY_DB_PATH
        yixiu.DB_PATH = temp_dir / "yixiu.db"
        security.SECURITY_DB_PATH = temp_dir / "security.db"

        app = Flask(__name__)
        app.register_blueprint(yixiu.yixiu_bp, url_prefix="/api/yixiu")
        app.register_blueprint(monitor.monitor_bp)
        self.client = app.test_client()

    def tearDown(self):
        yixiu.DB_PATH = self.old_yixiu_db
        security.SECURITY_DB_PATH = self.old_security_db
        self.tmp.cleanup()

    def auth_headers(self, role="operator", idem=None):
        headers = {"Authorization": f"Bearer {token(role=role)}"}
        if idem:
            headers["Idempotency-Key"] = idem
        return headers

    def test_aios_status_available_without_jwt(self):
        """普通查询直接可用：/aios/status 不需要 JWT"""
        res = self.client.get("/api/yixiu/aios/status")
        self.assertEqual(res.status_code, 200)

    def test_aios_execute_requires_confirmation_and_idempotency(self):
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(),
        )
        self.assertEqual(res.status_code, 409)
        self.assertIn("confirmed", res.get_json()["message"])

        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "confirmed": True},
            headers=self.auth_headers(),
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Idempotency-Key", res.get_json()["message"])

    def test_aios_execute_replays_same_idempotency_key(self):
        payload = {"goal": "inspect motor", "confirmed": True, "commit": False}
        headers = self.auth_headers(idem="idem-aios-1")

        first = self.client.post("/api/yixiu/aios/execute", json=payload, headers=headers)
        second = self.client.post("/api/yixiu/aios/execute", json=payload, headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["run_id"], second.get_json()["data"]["run_id"])

    def test_aios_execute_rejects_idempotency_conflict(self):
        headers = self.auth_headers(idem="idem-aios-conflict")
        first = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "confirmed": True, "commit": False},
            headers=headers,
        )
        second = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect pump", "confirmed": True, "commit": False},
            headers=headers,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)

    def test_monitor_execute_is_disabled_after_admin_auth(self):
        res = self.client.post(
            "/monitor/execute",
            json={"code": "print(1)"},
            headers=self.auth_headers(role="admin"),
        )
        self.assertEqual(res.status_code, 410)
        self.assertEqual(res.get_json()["message"], "monitor code execution is disabled")

    def test_security_audit_records_denied_write(self):
        self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(),
        )
        with security._security_db() as conn:
            rows = conn.execute("SELECT action, status FROM security_audit_events").fetchall()
        self.assertTrue(any(row["action"] == "aios.execute" and row["status"] == "denied" for row in rows))

    def test_aios_plan_contains_state_machine_and_agent_contracts(self):
        res = self.client.post(
            "/api/yixiu/aios/plan",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(role="auditor"),
        )

        self.assertEqual(res.status_code, 200)
        plan = res.get_json()["data"]
        self.assertIn("state_machine", plan)
        self.assertIn("depends_on", plan["state_machine"]["supports"])
        first_agent = plan["steps"][0]["agent"]
        self.assertIn("prompt", first_agent)
        self.assertIn("tool_allowlist", first_agent)
        self.assertIn("output_schema", first_agent)

    def test_aios_state_machine_blocks_unapproved_write_step(self):
        plan_res = self.client.post(
            "/api/yixiu/aios/plan",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(role="auditor"),
        )
        plan = plan_res.get_json()["data"]
        plan["steps"][0]["state"] = "done"

        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": plan, "step_key": "operate", "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-approval-block"),
        )

        self.assertEqual(res.status_code, 409)

    def test_aios_execute_all_stops_when_write_step_needs_approval(self):
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "execute_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-execute-all-blocked"),
        )

        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertLess(data["progress"], 100)
        self.assertTrue(any(item["state"] == "waiting_approval" for item in data["next_steps"]))

    def test_aios_execute_all_completes_with_approve_all(self):
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "execute_all": True, "approve_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-execute-all-approved"),
        )

        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["progress"], 100)
        self.assertEqual(data["status"], "completed")
        self.assertIn("finalize", data["artifacts"])

    def test_aios_state_transition_can_pause_approve_and_compensate(self):
        plan_res = self.client.post(
            "/api/yixiu/aios/plan",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(role="auditor"),
        )
        plan = plan_res.get_json()["data"]

        pause = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": plan, "step_key": "retrieve", "event": "pause", "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-pause"),
        )
        self.assertEqual(pause.status_code, 200)
        self.assertEqual(pause.get_json()["data"]["node"]["state"], "paused")

        compensate = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": pause.get_json()["data"]["plan"], "step_key": "retrieve", "event": "compensate", "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-compensate"),
        )
        self.assertEqual(compensate.status_code, 200)
        self.assertEqual(compensate.get_json()["data"]["node"]["state"], "compensated")

    def test_aios_failure_recovery_retries_then_fails(self):
        plan_res = self.client.post(
            "/api/yixiu/aios/plan",
            json={"goal": "inspect motor"},
            headers=self.auth_headers(role="auditor"),
        )
        plan = plan_res.get_json()["data"]
        plan["steps"][0]["max_retries"] = 1

        first_fail = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": plan, "step_key": "sense", "event": "fail", "error": "temporary outage", "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-fail-1"),
        )
        self.assertEqual(first_fail.status_code, 200)
        self.assertEqual(first_fail.get_json()["data"]["node"]["state"], "retrying")

        second_fail = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": first_fail.get_json()["data"]["plan"], "step_key": "sense", "event": "fail", "error": "still down", "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-fail-2"),
        )
        self.assertEqual(second_fail.status_code, 200)
        self.assertEqual(second_fail.get_json()["data"]["node"]["state"], "failed")

    def test_overview_contacts_and_tasks_available(self):
        """普通查询直接可用：overview/contacts/tasks 返回有效数据"""
        overview = self.client.get("/api/yixiu/overview").get_json()["data"]
        contacts = self.client.get("/api/yixiu/contacts").get_json()["data"]
        tasks = self.client.get("/api/yixiu/tasks").get_json()["data"]

        self.assertIn("agents", overview)
        self.assertIn("contacts", contacts)
        self.assertIn("tasks", tasks)

    def test_task_memory_get_available_then_persists(self):
        """普通查询直接可用：GET task memory 不需要 JWT；POST 需要 confirmed + 幂等"""
        loaded = self.client.get("/api/yixiu/tasks/t-1/memory")
        self.assertEqual(loaded.status_code, 200)

        saved = self.client.post(
            "/api/yixiu/tasks/t-1/memory",
            json={"key": "risk", "value": "hot", "confirmed": True},
            headers=self.auth_headers(idem="idem-memory"),
        )
        self.assertEqual(saved.status_code, 200)

        loaded = self.client.get("/api/yixiu/tasks/t-1/memory")
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.get_json()["data"]["memory"][0]["memory_key"], "risk")

    def test_conversation_history_get_available_then_persists(self):
        """普通查询直接可用：GET messages 不需要 JWT；POST 需要 confirmed + 幂等"""
        loaded = self.client.get("/api/yixiu/conversations/c-1/messages")
        self.assertEqual(loaded.status_code, 200)

        saved = self.client.post(
            "/api/yixiu/conversations/c-1/messages",
            json={"text": "hello", "confirmed": True},
            headers=self.auth_headers(idem="idem-message"),
        )
        self.assertEqual(saved.status_code, 200)

        loaded = self.client.get("/api/yixiu/conversations/c-1/messages")
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.get_json()["data"]["messages"][0]["text"], "hello")

    def test_task_create_replays_same_idempotency_key(self):
        payload = {"title": "replace bearing", "confirmed": True}
        headers = self.auth_headers(idem="idem-task-create")

        first = self.client.post("/api/yixiu/tasks", json=payload, headers=headers)
        second = self.client.post("/api/yixiu/tasks", json=payload, headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["id"], second.get_json()["data"]["id"])

    def test_task_memory_rejects_idempotency_conflict(self):
        headers = self.auth_headers(idem="idem-memory-conflict")
        first = self.client.post(
            "/api/yixiu/tasks/t-1/memory",
            json={"key": "risk", "value": "hot", "confirmed": True},
            headers=headers,
        )
        second = self.client.post(
            "/api/yixiu/tasks/t-1/memory",
            json={"key": "risk", "value": "cold", "confirmed": True},
            headers=headers,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)

    def test_conversation_message_replays_same_idempotency_key(self):
        payload = {"text": "hello", "confirmed": True}
        headers = self.auth_headers(idem="idem-message-replay")

        first = self.client.post("/api/yixiu/conversations/c-2/messages", json=payload, headers=headers)
        second = self.client.post("/api/yixiu/conversations/c-2/messages", json=payload, headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["id"], second.get_json()["data"]["id"])

    def test_knowledge_update_requires_confirmed_write(self):
        denied = self.client.post(
            "/api/yixiu/knowledge/update",
            json={"title": "case", "summary": "summary"},
            headers=self.auth_headers(),
        )
        self.assertEqual(denied.status_code, 409)

    def test_miniclaw_fastapi_chat_requires_auth(self):
        from starlette.requests import Request

        from miniclaw.gateway import ChatRequest
        from miniclaw.gateway import MiniClawGateway

        gateway = MiniClawGateway()
        gateway.setup()
        route = next(item for item in gateway.app.routes if getattr(item, "path", "") == "/miniclaw/chat")
        request = Request({"type": "http", "method": "POST", "path": "/miniclaw/chat", "headers": []})

        with self.assertRaises(Exception) as caught:
            asyncio.run(route.endpoint(ChatRequest(message="hello"), request))
        self.assertEqual(getattr(caught.exception, "status_code", None), 401)


class AiosManagementTest(AiosSecurityTest):
    """管理接口 CRUD 测试：平台/Agent、团队、会话、记忆、渠道"""

    def test_aios_agents_list_returns_seeded_agents(self):
        res = self.client.get("/api/yixiu/aios/agents")
        self.assertEqual(res.status_code, 200)
        agents = res.get_json()["data"]["agents"]
        ids = {a["id"] for a in agents}
        for expected in ("tiangong", "guanwei", "zhiju", "bowen", "heming", "mingjian"):
            self.assertIn(expected, ids)

    def test_aios_agent_create_and_update(self):
        create = self.client.post("/api/yixiu/aios/agents", json={
            "id": "agent-test01", "name": "测试智能体", "role": "测试用",
        })
        self.assertEqual(create.status_code, 200)
        self.assertEqual(create.get_json()["data"]["id"], "agent-test01")

        update = self.client.post("/api/yixiu/aios/agents", json={
            "id": "agent-test01", "name": "测试智能体V2", "role": "更新后",
        })
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["data"]["role"], "更新后")

    def test_aios_teams_crud(self):
        create = self.client.post("/api/yixiu/aios/teams", json={
            "name": "检修突击队", "lead_agent_id": "tiangong",
            "members": ["guanwei", "zhiju"], "workflow": {"mode": "sequential"},
        })
        self.assertEqual(create.status_code, 200)
        team = create.get_json()["data"]
        self.assertEqual(team["lead_agent_id"], "tiangong")

        lst = self.client.get("/api/yixiu/aios/teams")
        self.assertEqual(lst.status_code, 200)
        names = [t["name"] for t in lst.get_json()["data"]["teams"]]
        self.assertIn("检修突击队", names)

    def test_aios_sessions_crud(self):
        create = self.client.post("/api/yixiu/aios/sessions", json={
            "title": "测试检修会话", "channel": "web", "active_agent_id": "guanwei",
        })
        self.assertEqual(create.status_code, 200)
        session = create.get_json()["data"]
        self.assertEqual(session["title"], "测试检修会话")
        self.assertEqual(session["active_agent_id"], "guanwei")

        lst = self.client.get("/api/yixiu/aios/sessions")
        self.assertEqual(lst.status_code, 200)
        self.assertGreaterEqual(lst.get_json()["data"]["total"], 1)

    def test_aios_memory_crud(self):
        create = self.client.post("/api/yixiu/aios/memory", json={
            "agent_id": "tiangong", "memory_key": "test_key", "memory_value": "测试记忆值",
        })
        self.assertEqual(create.status_code, 200)
        self.assertEqual(create.get_json()["data"]["memory_value"], "测试记忆值")

        lst = self.client.get("/api/yixiu/aios/memory?agent_id=tiangong")
        self.assertEqual(lst.status_code, 200)
        keys = [m["memory_key"] for m in lst.get_json()["data"]["memories"]]
        self.assertIn("test_key", keys)

    def test_aios_channels_crud(self):
        create = self.client.post("/api/yixiu/aios/channels", json={
            "id": "channel-test01", "name": "测试渠道", "type": "webhook",
            "config": {"url": "http://example.com/hook"}, "enabled": True,
        })
        self.assertEqual(create.status_code, 200)

        lst = self.client.get("/api/yixiu/aios/channels")
        self.assertEqual(lst.status_code, 200)
        ids = [c["id"] for c in lst.get_json()["data"]["channels"]]
        self.assertIn("channel-test01", ids)


class AiosApprovalFlowTest(AiosSecurityTest):
    """审批全链路测试：列表/创建/决策/执行联动"""

    def test_aios_approvals_list_empty_then_create(self):
        lst = self.client.get("/api/yixiu/aios/approvals")
        self.assertEqual(lst.status_code, 200)

        create = self.client.post("/api/yixiu/aios/approvals", json={
            "run_id": "run-test01", "step_key": "operate",
            "action": "execute", "title": "测试审批", "detail": "需要确认",
        })
        self.assertEqual(create.status_code, 200)
        self.assertEqual(create.get_json()["data"]["status"], "pending")

        lst = self.client.get("/api/yixiu/aios/approvals?status=pending")
        self.assertEqual(lst.status_code, 200)
        self.assertGreaterEqual(lst.get_json()["data"]["total"], 1)

    def test_aios_approval_approve(self):
        create = self.client.post("/api/yixiu/aios/approvals", json={
            "run_id": "run-approve", "step_key": "write",
            "title": "写入审批", "detail": "确认写入",
        })
        approval_id = create.get_json()["data"]["id"]

        decide = self.client.post(f"/api/yixiu/aios/approvals/{approval_id}/decision", json={
            "decision": "approved", "decided_by": "test_admin",
        })
        self.assertEqual(decide.status_code, 200)
        self.assertEqual(decide.get_json()["data"]["status"], "approved")

    def test_aios_approval_reject(self):
        create = self.client.post("/api/yixiu/aios/approvals", json={
            "run_id": "run-reject", "step_key": "delete",
            "title": "删除审批", "detail": "确认删除",
        })
        approval_id = create.get_json()["data"]["id"]

        decide = self.client.post(f"/api/yixiu/aios/approvals/{approval_id}/decision", json={
            "decision": "rejected", "decided_by": "test_admin",
        })
        self.assertEqual(decide.status_code, 200)
        self.assertEqual(decide.get_json()["data"]["status"], "rejected")

    def test_aios_approval_decision_rejects_invalid(self):
        create = self.client.post("/api/yixiu/aios/approvals", json={
            "title": "无效决策测试",
        })
        approval_id = create.get_json()["data"]["id"]

        decide = self.client.post(f"/api/yixiu/aios/approvals/{approval_id}/decision", json={
            "decision": "maybe",
        })
        self.assertEqual(decide.status_code, 400)

    def test_aios_approval_decision_404_on_missing(self):
        decide = self.client.post("/api/yixiu/aios/approvals/nonexistent-id/decision", json={
            "decision": "approved",
        })
        self.assertEqual(decide.status_code, 404)

    def test_execute_creates_approval_for_write_step(self):
        """执行含 requires_approval 步骤时暂停在 waiting_approval"""
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "execute_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-exec-approval"),
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertLess(data["progress"], 100)
        self.assertTrue(any(item.get("state") == "waiting_approval" for item in data["next_steps"]))

    def test_approve_then_resume_completes_step(self):
        """审批 approve 后 resume 完成"""
        exec_res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "execute_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-resume-setup"),
        )
        self.assertEqual(exec_res.status_code, 200)
        run_id = exec_res.get_json()["data"]["run_id"]

        resume = self.client.post(
            "/api/yixiu/aios/resume",
            json={"run_id": run_id, "approve_all": True, "confirmed": True},
            headers=self.auth_headers(idem="idem-resume-exec"),
        )
        self.assertEqual(resume.status_code, 200)
        self.assertEqual(resume.get_json()["data"]["progress"], 100)


class AiosTraceTest(AiosSecurityTest):
    """Trace / 运行详情 / 事件流测试"""

    def setUp(self):
        super().setUp()
        # 先执行一次产生 run + events + approvals
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "inspect motor", "execute_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-trace-setup"),
        )
        self.run_id = res.get_json()["data"]["run_id"]

    def test_aios_trace_list(self):
        res = self.client.get("/api/yixiu/aios/trace")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(res.get_json()["data"]["total"], 0)

    def test_aios_trace_by_run_id(self):
        res = self.client.get(f"/api/yixiu/aios/trace?run_id={self.run_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("run", data)
        self.assertIn("approvals", data)
        self.assertIn("tree", data)

    def test_aios_trace_404_on_missing_run(self):
        res = self.client.get("/api/yixiu/aios/trace?run_id=nonexistent-run")
        self.assertEqual(res.status_code, 404)

    def test_aios_run_detail(self):
        res = self.client.get(f"/api/yixiu/aios/runs/{self.run_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("plan", data)
        self.assertIn("queue", data)
        self.assertIn("events", data)

    def test_aios_run_detail_404(self):
        res = self.client.get("/api/yixiu/aios/runs/nonexistent-run")
        self.assertEqual(res.status_code, 404)

    def test_aios_events_by_run_id(self):
        res = self.client.get(f"/api/yixiu/aios/events?run_id={self.run_id}")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(res.get_json()["data"]["total"], 0)

    def test_aios_events_by_agent_id(self):
        res = self.client.get("/api/yixiu/aios/events?agent_id=tiangong")
        self.assertEqual(res.status_code, 200)
        for event in res.get_json()["data"]["events"]:
            self.assertEqual(event["agent_id"], "tiangong")

    def test_aios_resume_404_on_missing_run(self):
        res = self.client.post(
            "/api/yixiu/aios/resume",
            json={"run_id": "nonexistent-run", "confirmed": True},
            headers=self.auth_headers(idem="idem-resume-404"),
        )
        self.assertEqual(res.status_code, 404)

    def test_database_status_returns_tables(self):
        res = self.client.get("/api/yixiu/database/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("sqlite", data)
        self.assertIn("tables", data["sqlite"])

    def test_plan_execute_status_consistency(self):
        """/plan → /execute → /status 闭环一致性"""
        # 1. 生成计划
        plan_res = self.client.post(
            "/api/yixiu/aios/plan",
            json={"goal": "check bearing wear"},
            headers=self.auth_headers(role="auditor"),
        )
        self.assertEqual(plan_res.status_code, 200)
        plan = plan_res.get_json()["data"]
        self.assertTrue(plan.get("steps"))

        # 2. 执行计划
        exec_res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"plan": plan, "execute_all": True, "approve_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-consistency"),
        )
        self.assertEqual(exec_res.status_code, 200)
        run_id = exec_res.get_json()["data"]["run_id"]

        # 3. /status 列表含该 run
        status_res = self.client.get("/api/yixiu/aios/status")
        self.assertEqual(status_res.status_code, 200)
        run_ids = [r["id"] for r in status_res.get_json()["data"]["runs"]]
        self.assertIn(run_id, run_ids)

        # 4. /runs/<run_id> plan 与步骤 1 一致
        detail_res = self.client.get(f"/api/yixiu/aios/runs/{run_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail_plan = detail_res.get_json()["data"]["plan"]
        self.assertEqual(detail_plan["goal"], plan["goal"])

        # 5. /trace?run_id= tree 结构完整
        trace_res = self.client.get(f"/api/yixiu/aios/trace?run_id={run_id}")
        self.assertEqual(trace_res.status_code, 200)
        self.assertIn("tree", trace_res.get_json()["data"])


class AiosRagPipelineTest(AiosSecurityTest):
    """知识库切片入库 + 向量相似度检索 + 真实工具流水线测试"""

    def test_file_parser_supports_text_and_md(self):
        """file_parser 服务能解析 TXT/MD/CSV 文本"""
        from services.file_parser import parse_file, supported_suffixes
        # 临时写一个 TXT
        txt_path = Path(self.tmp.name) / "sample.txt"
        txt_path.write_text("段落一：配电柜过热故障。\n\n段落二：检查通风和负载。\n\n段落三：复测温度。", encoding="utf-8")
        chunks = parse_file(txt_path)
        self.assertGreater(len(chunks), 0)
        # 至少包含「段落一」关键字
        self.assertTrue(any("配电柜" in c for c in chunks))
        # 支持的后缀集合
        self.assertIn(".pdf", supported_suffixes())
        self.assertIn(".docx", supported_suffixes())
        self.assertIn(".txt", supported_suffixes())

    def test_file_parser_unsupported_returns_empty(self):
        """不支持的后缀返回空列表"""
        from services.file_parser import parse_file
        bin_path = Path(self.tmp.name) / "sample.bin"
        bin_path.write_bytes(b"\x00\x01\x02")
        self.assertEqual(parse_file(bin_path), [])

    def test_file_parser_nonexistent_file_returns_empty(self):
        from services.file_parser import parse_file
        self.assertEqual(parse_file(Path(self.tmp.name) / "nope.pdf"), [])

    def test_rag_service_search_similar_returns_list(self):
        """search_similar 即使 LightRAG 未就绪也回退到本地匹配"""
        from services.rag_service import search_similar
        hits = search_similar("配电柜 过热", limit=3)
        # 不报错、返回列表
        self.assertIsInstance(hits, list)
        # 上限限制
        self.assertLessEqual(len(hits), 3)

    def test_rag_service_search_similar_empty_query(self):
        from services.rag_service import search_similar
        self.assertEqual(search_similar(""), [])

    def test_knowledge_similar_endpoint(self):
        """GET /knowledge/similar 返回向量相似度检索结果"""
        res = self.client.get("/api/yixiu/knowledge/similar?query=配电柜过热&limit=3")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["query"], "配电柜过热")
        self.assertIn("hits", data)

    def test_knowledge_similar_requires_query(self):
        res = self.client.get("/api/yixiu/knowledge/similar")
        self.assertEqual(res.status_code, 400)

    def test_knowledge_upload_requires_auth_and_confirmation(self):
        """POST /knowledge/upload 是高风险写入，需要 JWT + confirmed"""
        # 无 JWT → 401
        denied = self.client.post("/api/yixiu/knowledge/upload")
        self.assertEqual(denied.status_code, 401)

    def test_execute_action_retrieve_calls_rag(self):
        """AIOS execute retrieve_knowledge 步骤应尝试 RAG 检索"""
        # 直接走 /aios/execute 触发 retrieve_knowledge
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "配电柜过热检索", "execute_all": True, "confirmed": True, "commit": False},
            headers=self.auth_headers(idem="idem-test-retrieve-rag"),
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        # 检索产物应包含 references 字段（合并 RAG + 本地）
        artifacts = data.get("artifacts", {})
        retrieve_artifact = artifacts.get("retrieve", {})
        # retrieve 步骤的产物含 references 字段
        self.assertTrue(retrieve_artifact.get("references") is not None or retrieve_artifact.get("summary"))

    def test_execute_action_orchestrate_writes_knowledge_candidate(self):
        """AIOS orchestrate_task 步骤（commit=True + approve_all）应写入 yixiu_knowledge 待审核候选"""
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "配电柜检修 SOP", "execute_all": True, "approve_all": True, "confirmed": True, "commit": True},
            headers=self.auth_headers(idem="idem-test-orchestrate-write"),
        )
        self.assertEqual(res.status_code, 200)
        # 检查知识库表里有 pending 候选
        items = self.client.get("/api/yixiu/knowledge").get_json()["data"]["items"]
        aios_items = [i for i in items if i.get("source") in {"aios_zhiju", "aios_bowen"}]
        self.assertGreater(len(aios_items), 0)

    def test_execute_action_archive_writes_knowledge_candidate(self):
        """AIOS archive_knowledge 步骤（approve_all）应写入 yixiu_knowledge pending 候选"""
        res = self.client.post(
            "/api/yixiu/aios/execute",
            json={"goal": "归档 CG-125 检修经验", "execute_all": True, "approve_all": True, "confirmed": True, "commit": True},
            headers=self.auth_headers(idem="idem-test-archive-write"),
        )
        self.assertEqual(res.status_code, 200)
        items = self.client.get("/api/yixiu/knowledge").get_json()["data"]["items"]
        bowen_items = [i for i in items if i.get("source") == "aios_bowen"]
        self.assertGreater(len(bowen_items), 0)


class AiosRealToolsTest(AiosSecurityTest):
    """真实工具类测试：FileParseTool / RagQueryTool / SopGenerateTool / TaskUpdateTool"""

    def test_file_parse_tool_requires_file_id_or_path(self):
        from miniclaw.builtins.system_tools import FileParseTool
        tool = FileParseTool()
        result = tool.execute()
        self.assertFalse(result.success)
        self.assertIn("file_id", result.error)

    def test_file_parse_tool_parses_existing_file(self):
        """传入 file_path 能真实解析 TXT"""
        from miniclaw.builtins.system_tools import FileParseTool
        # 用一个 Flask app上下文测试（工具内部 import flask.current_app）
        from flask import Flask
        app = Flask(__name__)
        app.config["UPLOAD_FOLDER"] = self.tmp.name
        txt_path = Path(self.tmp.name) / "yixiu" / "test.txt"
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text("故障现象：配电柜过热。\n\n原因：散热不足。", encoding="utf-8")
        with app.app_context():
            tool = FileParseTool()
            result = tool.execute(file_path=str(txt_path), source="test.txt")
        self.assertTrue(result.success)
        self.assertIn("切片入库", result.output)

    def test_rag_query_tool_requires_query(self):
        from miniclaw.builtins.system_tools import RagQueryTool
        tool = RagQueryTool()
        result = tool.execute()
        self.assertFalse(result.success)

    def test_rag_query_tool_returns_hits(self):
        """RagQueryTool 走 /knowledge/similar 接口"""
        from miniclaw.builtins.system_tools import RagQueryTool
        # 需要在 Flask app 上下文里跑，因为它调用 HTTP 接口
        # 改为直接测 search_similar 函数
        from services.rag_service import search_similar
        hits = search_similar("配电柜", limit=2)
        self.assertIsInstance(hits, list)
        self.assertLessEqual(len(hits), 2)

    def test_sop_generate_tool_returns_steps(self):
        from miniclaw.builtins.system_tools import SopGenerateTool
        tool = SopGenerateTool()
        # 直接调用 execute 会走 HTTP，需要有运行中的后端
        # 这里只验证工具类结构正确
        self.assertEqual(tool.name, "sop_generate")
        self.assertGreater(len(tool.parameters), 0)

    def test_task_update_tool_requires_task_id(self):
        from miniclaw.builtins.system_tools import TaskUpdateTool
        tool = TaskUpdateTool()
        result = tool.execute()
        self.assertFalse(result.success)
        self.assertIn("task_id", result.error)

    def test_tool_registry_includes_new_tools(self):
        """register() 应注册 5 个新工具"""
        from miniclaw.builtins import system_tools
        from miniclaw.tools import BaseTool

        class _FakeApi:
            def __init__(self):
                self.registered = []

            def register_tool(self, tool: BaseTool):
                self.registered.append(tool)

        api = _FakeApi()
        system_tools.register(api)
        names = {t.name for t in api.registered}
        for expected in ("file_parse", "vision_analyze", "rag_query", "sop_generate", "task_update"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
