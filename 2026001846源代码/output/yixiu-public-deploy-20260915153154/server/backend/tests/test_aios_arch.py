"""AIOS 新架构（aios_arch）单元测试。

覆盖：
- trace 落盘 + Langfuse 兼容 export
- opa_guard 策略求值 + write 拦截
- memory_layer 添加 / 检索 / 余弦相似度
- sandbox_pool 代码执行 + timeout
- mcp_gateway JSON-RPC + tools/list + tools/call
- a2a_registry AgentCard + message/send
- langgraph_supervisor StateGraph invoke + conditional_edges
- aios_runtime.supervisor_execute 端到端跑通
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
for path in (BACKEND_DIR, BACKEND_DIR.parent):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


class AiosArchTestBase(unittest.TestCase):
    """每个测试用临时 data 目录，避免互相污染。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        # 直接改子模块属性：模块内部函数读取全局时解析子模块
        import aios_arch.trace.trace_store as trace_mod
        import aios_arch.opa_guard.policy_engine as opa_mod
        import aios_arch.memory_layer.memory_store as memory_mod
        import aios_arch.sandbox_pool.sandbox_runner as sandbox_mod
        import aios_arch.a2a_registry.registry as a2a_mod
        self._mods = {
            "trace": trace_mod, "opa": opa_mod, "memory": memory_mod,
            "sandbox": sandbox_mod, "a2a": a2a_mod,
        }
        data_dir = self.tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        trace_mod.TRACE_DB_PATH = data_dir / "aios_trace.db"
        opa_mod.OPA_DB_PATH = data_dir / "aios_opa.db"
        memory_mod.MEMORY_DB_PATH = data_dir / "aios_memory.db"
        sandbox_mod.SANDBOX_DB_PATH = data_dir / "aios_sandbox.db"
        a2a_mod.A2A_DB_PATH = data_dir / "aios_a2a.db"

    def tearDown(self):
        self.tmp.cleanup()


class TraceModuleTest(AiosArchTestBase):
    def test_trace_lifecycle_and_export(self):
        from aios_arch.trace import (start_trace, end_trace, start_observation,
                                     end_observation, get_trace, export_batch)
        tid = start_trace("ut-supervisor", user_id="u-test",
                          metadata={"suite": "aios_arch"}, input_data={"goal": "g"})
        oid = start_observation(tid, "step:sense", type_="span", input_data={"k": 1})
        end_observation(oid, status="completed", output_data={"ok": True})
        end_trace(tid, status="completed", output_data={"run_id": tid})
        detail = get_trace(tid)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["name"], "ut-supervisor")
        self.assertEqual(len(detail["observations"]), 1)
        batch = export_batch(limit=5)
        self.assertGreaterEqual(batch["count"], 1)
        self.assertEqual(batch["batch"][0]["body"]["id"], tid)


class OpaGuardModuleTest(AiosArchTestBase):
    def test_opa_blocks_anonymous_write(self):
        from aios_arch.opa_guard import evaluate
        decision = evaluate(
            action="aios.execute.write", resource="aios:write",
            payload={"confirmed": True}, actor={"user_id": "anonymous", "role": "anonymous"},
            context={"kind": "write", "approve_all": False},
        )
        self.assertEqual(decision["decision"], "deny")
        self.assertIn("匿名", decision["reason"])

    def test_opa_approve_all_bypasses_write(self):
        from aios_arch.opa_guard import evaluate
        decision = evaluate(
            action="aios.execute.write", resource="aios:write",
            payload={"approve_all": True},
            actor={"user_id": "u-admin", "role": "admin"},
            context={"kind": "write", "approve_all": True},
        )
        self.assertEqual(decision["decision"], "allow")

    def test_opa_rate_limit_kicks_in(self):
        from aios_arch.opa_guard import register_policy, evaluate
        register_policy("ut_rl", "rate_limit",
                        {"kind": "rate_limit", "window_seconds": 60, "max_calls": 2},
                        priority=99, description="ut rate limit")
        actor = {"user_id": "u-rl", "role": "admin"}
        decisions = [evaluate("ut.action", "ut.res", {}, actor,
                             context={"kind": "read", "approve_all": True})
                     for _ in range(3)]
        self.assertEqual(decisions[0]["decision"], "allow")
        self.assertEqual(decisions[1]["decision"], "allow")
        self.assertEqual(decisions[2]["decision"], "deny")
        self.assertIn("速率超限", decisions[2]["reason"])


class MemoryLayerModuleTest(AiosArchTestBase):
    def test_memory_add_search_returns_relevant(self):
        from aios_arch.memory_layer import add, search, list_memories, update, delete
        m1 = add("u-m", "tiangong", "配电柜过热故障导致停机")
        m2 = add("u-m", "tiangong", "通风系统检查与负载测试")
        m3 = add("u-m", "tiangong", "天气晴朗")
        self.assertTrue(m1 and m2 and m3)
        hits = search("u-m", "配电柜过热", top_k=2)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0]["id"], m1)
        self.assertGreater(hits[0]["score"], 0)
        self.assertTrue(update(m1, content="配电柜过热故障 - 复测温度"))
        self.assertEqual(len(list_memories("u-m")), 3)
        self.assertTrue(delete(m1))
        self.assertEqual(len(list_memories("u-m")), 2)


class SandboxPoolModuleTest(AiosArchTestBase):
    def test_sandbox_runs_python(self):
        from aios_arch.sandbox_pool import run_code, list_runs, get_run
        result = run_code("print(1 + 2)", language="python", timeout=5)
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("3", result["stdout"])
        self.assertFalse(result["timed_out"])
        self.assertGreaterEqual(len(list_runs()), 1)
        self.assertIsNotNone(get_run(result["id"]))

    def test_sandbox_timeout(self):
        from aios_arch.sandbox_pool import run_code
        result = run_code("import time; time.sleep(5)", language="python", timeout=1)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], 124)

    def test_sandbox_rejects_unsupported_language(self):
        from aios_arch.sandbox_pool import run_code
        result = run_code("//", language="cobol", timeout=2)
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("unsupported", result["error"])


class McpGatewayModuleTest(AiosArchTestBase):
    def test_mcp_initialize_and_tools_list(self):
        from aios_arch.mcp_gateway import handle_request, list_tools
        resp = handle_request({"jsonrpc": "2.0", "id": "1", "method": "initialize"})
        self.assertEqual(resp["result"]["serverInfo"]["name"], "aios-mcp-gateway")
        tools_resp = handle_request({"jsonrpc": "2.0", "id": "2", "method": "tools/list"})
        self.assertIn("tools", tools_resp["result"])
        names = [t["name"] for t in tools_resp["result"]["tools"]]
        self.assertIn("system_overview", names)
        self.assertIn("aios_plan", names)
        # 与 list_tools() 一致
        self.assertEqual(len(list_tools()), len(names))

    def test_mcp_call_unknown_tool_returns_error(self):
        from aios_arch.mcp_gateway import handle_request
        resp = handle_request({"jsonrpc": "2.0", "id": "3", "method": "tools/call",
                                "params": {"name": "nonexistent_tool", "arguments": {}}})
        # BaseTool.execute 在错误时返回 success=False，content 里包含 [error]
        self.assertIn("result", resp)
        self.assertTrue(resp["result"].get("isError"))

    def test_mcp_method_not_found(self):
        from aios_arch.mcp_gateway import handle_request
        resp = handle_request({"jsonrpc": "2.0", "id": "4", "method": "ghost"})
        self.assertEqual(resp["error"]["code"], -32601)


class A2aRegistryModuleTest(AiosArchTestBase):
    def test_default_agents_seeded(self):
        from aios_arch.a2a_registry import list_agents, get_agent
        agents = list_agents()
        ids = {a["id"] for a in agents}
        for expected in ("tiangong", "guanwei", "zhiju", "bowen", "heming", "mingjian"):
            self.assertIn(expected, ids)
        t = get_agent("tiangong")
        self.assertEqual(t["name"], "天工")
        self.assertGreater(len(t["skills"]), 0)

    def test_register_custom_agent(self):
        from aios_arch.a2a_registry import register_agent, get_agent
        aid = register_agent({"id": "ut-agent", "name": "UT",
                              "description": "ut", "skills": [],
                              "url": "a2a://ut-agent", "version": "0.0.1"})
        self.assertEqual(aid, "ut-agent")
        self.assertEqual(get_agent("ut-agent")["version"], "0.0.1")

    def test_send_message_routes_to_subagent(self):
        from aios_arch.a2a_registry import send_message, get_task, list_messages
        # 注：AgentInvokeTool 实际会失败（无 HTTP 后端），但消息记录与状态仍写入
        outcome = send_message("tiangong", "guanwei", "查一下配电柜故障",
                               context_id="ctx-ut", task_id="task-ut-1")
        self.assertEqual(outcome["context_id"], "ctx-ut")
        self.assertEqual(outcome["task_id"], "task-ut-1")
        self.assertIn(outcome["status"], {"completed", "failed"})
        task = get_task("task-ut-1")
        self.assertIsNotNone(task)
        self.assertEqual(len(list_messages(task_id="task-ut-1")), 2)


class LangGraphSupervisorModuleTest(AiosArchTestBase):
    def test_state_graph_invoke_runs_all_nodes(self):
        from aios_arch.langgraph_supervisor.graph import StateGraph

        def s(state):
            state["x"] = 1
            return {"x": state["x"]}

        def mid(state):
            return {"x": state["x"] + 10}

        def end(state):
            return {"final": state["x"]}

        g = StateGraph()
        g.add_node("s", s)
        g.add_node("m", mid)
        g.add_node("e", end)
        g.set_entry_point("s")
        g.add_edge("s", "m")
        g.add_edge("m", "e")
        g.set_finish_point("e")
        compiled = g.compile()
        result = compiled.invoke({})
        self.assertEqual(result["x"], 11)
        self.assertEqual(result["final"], 11)
        self.assertEqual(result["__steps__"], 3)

    def test_state_graph_conditional_edges(self):
        from aios_arch.langgraph_supervisor.graph import StateGraph

        def router(state):
            return "high" if state.get("n", 0) >= 10 else "low"

        g = StateGraph()
        g.add_node("start", lambda s: {"n": s.get("n", 0) + 5})
        g.add_node("branch_high", lambda s: {"path": "high"})
        g.add_node("branch_low", lambda s: {"path": "low"})
        g.add_node("finish", lambda s: {"done": True})
        g.set_entry_point("start")
        g.add_conditional_edges("start", router, {"high": "branch_high", "low": "branch_low"})
        g.add_edge("branch_high", "finish")
        g.add_edge("branch_low", "finish")
        g.set_finish_point("finish")
        compiled = g.compile()
        result = compiled.invoke({"n": 6})  # 6 -> +5 = 11 -> high
        self.assertEqual(result["path"], "high")
        self.assertTrue(result["done"])

    def test_supervisor_execute_end_to_end(self):
        """端到端：aios_runtime.supervisor_execute 跑完整闭环。
        由于没有 HTTP 后端，build_plan / execute_steps 会回退到空 plan，
        但应完成 trace + memory + finalize 的最小闭环。
        """
        from aios_runtime import supervisor_execute
        outcome = supervisor_execute(
            goal="ut 目标", mode="auto", task_id="ut-task-1",
            execute_all=True, approve_all=True,
            actor={"user_id": "u-supervisor", "role": "admin"},
            session_id="ut-session",
        )
        self.assertIn("run_id", outcome)
        self.assertIn("trace_id", outcome)
        self.assertIn("final_report", outcome)
        self.assertTrue(outcome.get("trace_id", "").startswith("trace-"))


class ApiGatewayMiddlewareTest(unittest.TestCase):
    def test_require_gateway_auth_blocks_no_token(self):
        from aios_arch.api_gateway.middleware import require_gateway_auth
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/"):
            @require_gateway_auth({"admin"})
            def handler():
                return "ok", 200
            resp = handler()
            self.assertEqual(resp[1], 401)

    def test_rate_limit_triggers_429(self):
        from aios_arch.api_gateway.middleware import rate_limit, _RATE_BUCKETS
        from flask import Flask, g

        app = Flask(__name__)
        _RATE_BUCKETS.clear()
        with app.test_request_context("/"):
            g.actor = {"user_id": "u-rl-ut", "role": "admin"}
            @rate_limit(window_seconds=60, max_calls=1)
            def handler():
                return "ok", 200
            self.assertEqual(handler()[1], 200)
            self.assertEqual(handler()[1], 429)


class FullAppMountTest(unittest.TestCase):
    def test_unified_app_mounts_aios_arch_blueprints(self):
        """挂载 mount_gateway_blueprints 后 app 应能找到 /mcp /a2a /sandbox 等路由。"""
        try:
            from unified_app import create_unified_app
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"unified_app 不可用: {exc}")
        app = create_unified_app()
        rules = {rule.rule for rule in app.url_map.iter_rules()}
        for prefix in ("/mcp/", "/a2a/", "/sandbox/run", "/trace/traces",
                       "/opa/policies", "/memory/memories",
                       "/api/aios-arch/supervisor/run"):
            self.assertTrue(any(r.startswith(prefix) for r in rules),
                            f"缺少路由前缀: {prefix}")


if __name__ == "__main__":
    unittest.main()
