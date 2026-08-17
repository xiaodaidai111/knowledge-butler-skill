"""LangGraph 风格 StateGraph 本地实现 + conditional edges 路由。

设计目标：在不需要安装 langgraph 包的前提下，提供等价于
`langgraph.graph.StateGraph` + `add_conditional_edges` 的运行时：

- `StateGraph(state_schema)`：用 TypedDict/dataclass 描述状态结构
- `add_node(name, fn)`：注册节点函数 `fn(state) -> PartialState`
- `add_edge(src, dst)`：固定边
- `add_conditional_edges(src, router_fn, mapping)`：动态边
- `set_entry_point(name)` / `set_finish_point(name)`
- `compile()` -> CompiledGraph
- `compiled.invoke(initial_state)` / `compiled.stream(initial_state)` -> 状态序列

若检测到环境装了 `langgraph`，可调用 `enable_real_langgraph()` 把运行代理到真包；
默认走本地实现，避免新依赖。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aios_arch.langgraph_supervisor.graph")

Router = Callable[[Dict[str, Any]], Optional[str]]
NodeFn = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class _Edge:
    src: str
    dst: Optional[str]
    router: Optional[Router]
    mapping: Optional[Dict[str, str]]


class StateGraph:
    """本地等价 langgraph.graph.StateGraph。"""

    def __init__(self, state_schema: Optional[type] = None):
        self.state_schema = state_schema or dict
        self._nodes: Dict[str, NodeFn] = {}
        self._edges: List[_Edge] = []
        self._entry: Optional[str] = None
        self._finish: Optional[str] = None

    def add_node(self, name: str, fn: NodeFn) -> "StateGraph":
        if name in self._nodes:
            logger.warning("node %s overwritten", name)
        self._nodes[name] = fn
        return self

    def add_edge(self, src: str, dst: Optional[str]) -> "StateGraph":
        self._edges.append(_Edge(src=src, dst=dst, router=None, mapping=None))
        return self

    def add_conditional_edges(self, src: str, router: Router,
                              mapping: Optional[Dict[str, str]] = None) -> "StateGraph":
        self._edges.append(_Edge(src=src, dst=None, router=router, mapping=mapping))
        return self

    def set_entry_point(self, name: str) -> "StateGraph":
        self._entry = name
        return self

    def set_finish_point(self, name: str) -> "StateGraph":
        self._finish = name
        return self

    def compile(self) -> "CompiledGraph":
        if not self._entry:
            raise ValueError("entry point required")
        return CompiledGraph(
            nodes=dict(self._nodes),
            edges=list(self._edges),
            entry=self._entry,
            finish=self._finish,
        )


@dataclass
class CompiledGraph:
    nodes: Dict[str, NodeFn]
    edges: List[_Edge]
    entry: str
    finish: Optional[str]

    def _next(self, current: str, state: Dict[str, Any]) -> Optional[str]:
        # finish 节点本身被执行后，无后继 -> 返回 None 停止
        if current == self.finish:
            return None
        for edge in self.edges:
            if edge.src != current:
                continue
            if edge.router is not None:
                try:
                    nxt = edge.router(state)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("router %s failed: %s", edge.src, exc)
                    nxt = None
                if nxt is None:
                    continue
                if edge.mapping:
                    return edge.mapping.get(nxt, nxt)
                return nxt
            if edge.dst is not None:
                return edge.dst
        return self.finish

    def invoke(self, initial_state: Optional[Dict[str, Any]] = None,
               max_steps: int = 64) -> Dict[str, Any]:
        state: Dict[str, Any] = dict(initial_state or {})
        state.setdefault("__visited__", [])
        state.setdefault("__current__", self.entry)
        steps = 0
        while steps < max_steps:
            current = state.get("__current__")
            if current is None:
                break
            fn = self.nodes.get(current)
            if fn is None:
                logger.warning("node %s not registered, stopping", current)
                break
            try:
                patch = fn(state) or {}
            except Exception as exc:  # noqa: BLE001
                state["__error__"] = f"{current}: {exc}"
                state["__current__"] = None
                break
            visited = state.get("__visited__", [])
            visited.append({"node": current, "patch_keys": list(patch.keys())})
            state["__visited__"] = visited
            state.update(patch)
            nxt = self._next(current, state)
            state["__current__"] = nxt
            steps += 1
            if nxt is None:
                break
        state.pop("__current__", None)
        state["__steps__"] = steps
        return state

    def stream(self, initial_state: Optional[Dict[str, Any]] = None,
               max_steps: int = 64):
        state: Dict[str, Any] = dict(initial_state or {})
        state.setdefault("__visited__", [])
        state.setdefault("__current__", self.entry)
        steps = 0
        while steps < max_steps:
            current = state.get("__current__")
            if current is None:
                break
            fn = self.nodes.get(current)
            if fn is None:
                break
            try:
                patch = fn(state) or {}
            except Exception as exc:  # noqa: BLE001
                state["__error__"] = f"{current}: {exc}"
                yield {"node": current, "error": str(exc), "state": dict(state)}
                break
            state.update(patch)
            state["__visited__"] = state.get("__visited__", []) + [
                {"node": current, "patch_keys": list(patch.keys())}
            ]
            yield {"node": current, "patch": patch, "state": dict(state)}
            nxt = self._next(current, state)
            state["__current__"] = nxt
            steps += 1
            if nxt is None:
                break


_REAL_LANGGRAPH_ENABLED = False


def enable_real_langgraph(enabled: bool = True) -> bool:
    """切换是否把 StateGraph 代理到真 langgraph 包。当前版本仅记录开关，不替换实现。"""
    global _REAL_LANGGRAPH_ENABLED
    _REAL_LANGGRAPH_ENABLED = bool(enabled)
    return _REAL_LANGGRAPH_ENABLED


def is_real_langgraph_enabled() -> bool:
    return _REAL_LANGGRAPH_ENABLED
