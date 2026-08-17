"""一修网页版业务编排接口。

提供多模态检索、标准作业、知识沉淀和人工审核所需的稳定接口。
所有新增业务数据使用 SQLite 持久化，上传文件保存到本机 uploads/yixiu 目录。
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, request, send_file
from werkzeug.utils import secure_filename

from aios_runtime import (
    AGENT_OUTPUT_SCHEMAS,
    AGENT_PROMPTS,
    AGENT_TOOL_ALLOWLISTS,
    AIOS_ACTION_REGISTRY,
    AIOS_TECH_STACK,
    TIANGONG_OPERATION_PROMPT,
    attach_state_machine,
    enrich_agent,
    next_executable_steps,
    transition_step,
)
from security import AUDIT_ROLES, WRITE_ROLES, require_confirmed_write, require_jwt_roles
from utils import error_response, generate_token, success_response

logger = logging.getLogger(__name__)
yixiu_bp = Blueprint("yixiu", __name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "yixiu_web.db"
KNOWLEDGE_PATH = DATA_DIR / "maintenance_knowledge_base.json"

AGENTS = [
    {
        "id": "tiangong", "name": "天工", "role": "综合智能中枢",
        "duty": "理解用户目标，统筹观微、执矩、博闻、和鸣、明鉴完成跨模块检修任务。",
        "status": "online", "ip": "10.10.1.10", "avatar": "/static/agents/tiangong.png",
        "capabilities": ["任务规划", "跨智能体调度", "长任务执行", "风险优先级判断", "闭环报告"],
    },
    {
        "id": "guanwei", "name": "观微", "role": "智能检索器灵",
        "duty": "联合分析故障现象、设备型号、故障代码、现场图片和维修文档，召回手册、案例与 SOP。",
        "status": "online", "ip": "10.10.1.21", "avatar": "/static/agents/guanwei.png",
        "capabilities": ["多模态检索", "故障现象归纳", "相似案例召回", "引用依据整理"],
    },
    {
        "id": "zhiju", "name": "执矩", "role": "检修作业器灵",
        "duty": "按设备类型、风险等级和检修等级编排标准作业步骤，推动工单流转。",
        "status": "online", "ip": "10.10.1.22", "avatar": "/static/agents/zhiju.png",
        "capabilities": ["SOP生成", "任务步骤编排", "安全确认", "工单状态推进"],
    },
    {
        "id": "bowen", "name": "博闻", "role": "知识管理器灵",
        "duty": "整理技术资料、维护知识网络、沉淀历史检修案例并管理版本与审核流程。",
        "status": "online", "ip": "10.10.1.23", "avatar": "/static/agents/bowen.png",
        "capabilities": ["知识沉淀", "文件解析", "图谱关联", "版本管理", "资料审核"],
    },
    {
        "id": "heming", "name": "和鸣", "role": "协作调度器灵",
        "duty": "管理联系人、任务会话、专家支援和现场协作记录，生成沟通摘要。",
        "status": "online", "ip": "10.10.1.24", "avatar": "/static/agents/heming.png",
        "capabilities": ["联系人检索", "协作消息", "任务群聊", "会议纪要", "支援请求"],
    },
    {
        "id": "mingjian", "name": "明鉴", "role": "复检核查器灵",
        "duty": "核验引用依据、作业合规、安全风险、复检数据和报告完整性。",
        "status": "online", "ip": "10.10.1.25", "avatar": "/static/agents/mingjian.png",
        "capabilities": ["复检评估", "安全核查", "质量评分", "返工建议", "验收归档"],
    },
]

MODULES = [
    {"key": "multimodal_search", "title": "多模态知识检索", "desc": "支持文本、故障图片、维修文档和设备型号联合检索。", "agent": "观微"},
    {"key": "standard_work", "title": "标准作业闭环", "desc": "覆盖任务创建、逐步作业、合规确认、复检和报告归档。", "agent": "执矩"},
    {"key": "knowledge_graph", "title": "知识沉淀与更新", "desc": "支持案例上传、人工修正、审核入库与知识图谱更新。", "agent": "博闻"},
    {"key": "quality_audit", "title": "安全与质量核查", "desc": "复核引用、风险提醒、操作顺序、数据记录和报告字段。", "agent": "明鉴"},
]

CONTACTS = [
    {"id": 1, "name": "聪明的一修", "position": "检修工程师", "department": "动力设备检修一组", "specialty": "发动机 / 电气", "phone": "138-0000-1024", "status": "在线", "currentTask": "ZK-320 过热检修", "devices": ["CG-125", "ZK-320"], "workload": 72},
    {"id": 2, "name": "王铭", "position": "复检人员", "department": "质量复检组", "specialty": "复检评估", "phone": "138-0000-2048", "status": "在线", "currentTask": "点火系统复核", "devices": ["DLI-001"], "workload": 48},
    {"id": 3, "name": "赵宁", "position": "安全负责人", "department": "安全管理部", "specialty": "高风险作业", "phone": "138-0000-4096", "status": "忙碌", "currentTask": "高风险作业确认", "devices": ["配电柜", "液压系统"], "workload": 83},
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_BUILTIN_TEMPLATES = [
    {
        "id": "tpl-blank",
        "name": "空白文档",
        "icon": "📝",
        "category": "通用",
        "description": "从零开始创建一份空白技术文档",
        "skeleton": {"content": "# 文档标题\n\n在此输入内容..."}
    },
    {
        "id": "tpl-sop",
        "name": "检修作业 SOP",
        "icon": "📋",
        "category": "检修流程",
        "description": "标准作业流程模板，适用于设备检修、维护作业",
        "skeleton": {"content": "# 检修作业 SOP\n\n## 一、基本信息\n- 设备名称：\n- 设备型号：\n- 作业类型：\n- 作业地点：\n- 负责人：\n\n## 二、安全确认\n- [ ] 停机断电\n- [ ] 验电挂牌\n- [ ] 穿戴劳保用品\n- [ ] 工具检查合格\n\n## 三、作业步骤\n1. 外观检查\n2. 参数测量\n3. 故障定位\n4. 维修处置\n5. 更换部件\n\n## 四、复测验收\n- [ ] 空载试运行\n- [ ] 负载试运行\n- [ ] 参数记录\n- [ ] 清理现场\n\n## 五、备注\n"}
    },
    {
        "id": "tpl-fault",
        "name": "故障排查报告",
        "icon": "🔍",
        "category": "故障分析",
        "description": "故障现象、排查过程、处置结论完整记录",
        "skeleton": {"content": "# 故障排查报告\n\n## 一、故障现象\n- 设备：\n- 故障描述：\n- 发生时间：\n- 影响范围：\n\n## 二、排查过程\n### 初步检查\n- 外观检查：\n- 参数检测：\n\n### 深入分析\n- 可能原因1：\n- 可能原因2：\n- 排查方法：\n\n## 三、处置措施\n- 最终原因：\n- 处置方案：\n- 更换部件：\n\n## 四、预防建议\n"}
    },
    {
        "id": "tpl-meeting",
        "name": "检修会议纪要",
        "icon": "📒",
        "category": "协作沟通",
        "description": "班组例会、技术交流、故障复盘纪要",
        "skeleton": {"content": "# 检修会议纪要\n\n## 会议信息\n- 会议主题：\n- 会议时间：\n- 参会人员：\n- 主持人：\n\n## 议题与讨论\n### 议题一：\n- 讨论内容：\n- 结论：\n\n### 议题二：\n- 讨论内容：\n- 结论：\n\n## 行动计划\n| 事项 | 责任人 | 截止时间 | 状态 |\n|------|--------|----------|------|\n|  |  |  |  |\n\n## 备注\n"}
    },
    {
        "id": "tpl-safety",
        "name": "安全操作规范",
        "icon": "🛡️",
        "category": "安全规范",
        "description": "高风险作业安全规程与防护要求",
        "skeleton": {"content": "# 安全操作规范\n\n## 一、适用范围\n本规范适用于 作业。\n\n## 二、人员要求\n- 作业人员必须持有 资格证\n- 熟悉设备结构与操作规程\n- 掌握应急处置方法\n\n## 三、防护用品\n- [ ] 安全帽\n- [ ] 绝缘手套\n- [ ] 护目镜\n- [ ] 防滑鞋\n- [ ] 安全带（高空作业）\n\n## 四、安全流程\n1. 开具工作票\n2. 现场交底\n3. 落实防护措施\n4. 实施作业\n5. 验收确认\n\n## 五、应急处置\n- 触电急救：\n- 火灾扑救：\n- 设备故障：\n\n## 六、注意事项\n"}
    }
]


def _seed_templates(conn):
    count = conn.execute("SELECT COUNT(*) as c FROM yixiu_doc_templates").fetchone()["c"]
    if count > 0:
        return
    now = _now()
    for t in _BUILTIN_TEMPLATES:
        conn.execute(
            "INSERT INTO yixiu_doc_templates VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (t["id"], t["name"], t["icon"], t["category"], t["description"],
             json.dumps(t["skeleton"], ensure_ascii=False), now),
        )


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS yixiu_files (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, stored_name TEXT, mime TEXT,
          type TEXT, category TEXT, folder TEXT, size INTEGER DEFAULT 0,
          equipment TEXT, model TEXT, uploader TEXT, uploaded_at TEXT,
          audit_status TEXT, parse_status TEXT, version TEXT DEFAULT 'v1.0',
          purpose TEXT DEFAULT 'knowledge', analysis_json TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS yixiu_tasks (
          id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL,
          completed_steps TEXT DEFAULT '[]', created_at TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_knowledge (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, type TEXT, category TEXT,
          equipment TEXT, model TEXT, summary TEXT, content TEXT, tags TEXT,
          source TEXT, status TEXT, reviewer TEXT, correction TEXT,
          created_at TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_contacts (
          id TEXT PRIMARY KEY, account TEXT UNIQUE, name TEXT NOT NULL,
          avatar TEXT, position TEXT, department TEXT, specialty TEXT,
          phone TEXT, status TEXT DEFAULT '在线', devices TEXT DEFAULT '[]',
          current_task TEXT, workload INTEGER DEFAULT 0,
          employee_id TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_messages (
          id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
          sender_id TEXT, sender_name TEXT, message_type TEXT DEFAULT 'text',
          text TEXT, attachment_json TEXT DEFAULT '{}', card_json TEXT DEFAULT '{}',
          created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_yixiu_messages_conversation
          ON yixiu_messages(conversation_id, created_at);
        CREATE TABLE IF NOT EXISTS yixiu_knowledge_versions (
          id TEXT PRIMARY KEY,
          knowledge_id TEXT NOT NULL,
          version INTEGER NOT NULL,
          content_snapshot TEXT NOT NULL,
          title_snapshot TEXT,
          change_summary TEXT DEFAULT '',
          editor_id TEXT,
          editor_name TEXT,
          created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_knowledge_collaborators (
          id TEXT PRIMARY KEY,
          knowledge_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          user_name TEXT NOT NULL,
          role TEXT DEFAULT 'editor',
          last_active_at TEXT,
          is_online INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS yixiu_knowledge_links (
          id TEXT PRIMARY KEY,
          knowledge_id TEXT NOT NULL,
          link_type TEXT NOT NULL,
          target_id TEXT NOT NULL,
          target_title TEXT,
          created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_versions
          ON yixiu_knowledge_versions(knowledge_id, version);
        CREATE INDEX IF NOT EXISTS idx_knowledge_collaborators
          ON yixiu_knowledge_collaborators(knowledge_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_links
          ON yixiu_knowledge_links(knowledge_id);
        CREATE TABLE IF NOT EXISTS yixiu_doc_templates (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          icon TEXT DEFAULT '📝',
          category TEXT DEFAULT '通用',
          description TEXT DEFAULT '',
          skeleton_json TEXT DEFAULT '{}',
          is_builtin INTEGER DEFAULT 0,
          created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_aios_runs (
          id TEXT PRIMARY KEY,
          goal TEXT NOT NULL,
          mode TEXT DEFAULT 'auto',
          plan_json TEXT NOT NULL,
          status TEXT DEFAULT 'planned',
          progress INTEGER DEFAULT 0,
          artifacts_json TEXT DEFAULT '{}',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_task_memory (
          id TEXT PRIMARY KEY,
          task_id TEXT NOT NULL,
          memory_key TEXT NOT NULL,
          memory_value TEXT NOT NULL,
          author TEXT DEFAULT 'aios',
          created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_agent_events (
          id TEXT PRIMARY KEY,
          run_id TEXT DEFAULT '',
          agent_id TEXT NOT NULL,
          agent_name TEXT NOT NULL,
          event_type TEXT DEFAULT 'task',
          title TEXT NOT NULL,
          content TEXT DEFAULT '',
          payload_json TEXT DEFAULT '{}',
          status TEXT DEFAULT 'done',
          created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_yixiu_agent_events_run
          ON yixiu_agent_events(run_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_yixiu_agent_events_agent
          ON yixiu_agent_events(agent_id, created_at);
        CREATE TABLE IF NOT EXISTS yixiu_agent_memory (
          id TEXT PRIMARY KEY,
          agent_id TEXT NOT NULL,
          memory_key TEXT NOT NULL,
          memory_value TEXT NOT NULL,
          tags TEXT DEFAULT '[]',
          updated_at TEXT,
          UNIQUE(agent_id, memory_key)
        );
        CREATE TABLE IF NOT EXISTS yixiu_aios_queue (
          id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          step_key TEXT NOT NULL,
          agent_id TEXT NOT NULL,
          action TEXT NOT NULL,
          state TEXT DEFAULT 'pending',
          priority INTEGER DEFAULT 50,
          payload_json TEXT DEFAULT '{}',
          result_json TEXT DEFAULT '{}',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_yixiu_aios_queue_run
          ON yixiu_aios_queue(run_id, state, priority);
        CREATE TABLE IF NOT EXISTS yixiu_agent_configs (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          role TEXT DEFAULT '',
          model_provider TEXT DEFAULT 'qwen',
          model_name TEXT DEFAULT 'qwen-local-or-cloud',
          prompt TEXT DEFAULT '',
          tools_json TEXT DEFAULT '[]',
          knowledge_ids_json TEXT DEFAULT '[]',
          memory_keys_json TEXT DEFAULT '[]',
          database_scope TEXT DEFAULT 'read_business',
          status TEXT DEFAULT 'enabled',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_agent_teams (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT DEFAULT '',
          lead_agent_id TEXT DEFAULT 'tiangong',
          members_json TEXT DEFAULT '[]',
          workflow_json TEXT DEFAULT '{}',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_conversation_sessions (
          id TEXT PRIMARY KEY,
          user_id TEXT DEFAULT 'current-user',
          title TEXT NOT NULL,
          channel TEXT DEFAULT 'web',
          active_agent_id TEXT DEFAULT 'tiangong',
          context_json TEXT DEFAULT '{}',
          status TEXT DEFAULT 'active',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_aios_approvals (
          id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          step_key TEXT DEFAULT '',
          action TEXT DEFAULT '',
          title TEXT NOT NULL,
          detail TEXT DEFAULT '',
          requester_agent_id TEXT DEFAULT 'tiangong',
          status TEXT DEFAULT 'pending',
          requested_by TEXT DEFAULT 'AIOS',
          decided_by TEXT DEFAULT '',
          decision_note TEXT DEFAULT '',
          created_at TEXT,
          decided_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_yixiu_aios_approvals_run
          ON yixiu_aios_approvals(run_id, status, created_at);
        CREATE TABLE IF NOT EXISTS yixiu_aios_channels (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          channel_type TEXT DEFAULT 'web',
          endpoint TEXT DEFAULT '',
          enabled INTEGER DEFAULT 1,
          agent_id TEXT DEFAULT 'tiangong',
          config_json TEXT DEFAULT '{}',
          created_at TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS yixiu_service_accounts (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          role TEXT DEFAULT 'service',
          scopes_json TEXT DEFAULT '[]',
          enabled INTEGER DEFAULT 1,
          created_at TEXT,
          updated_at TEXT
        );
        """
    )
    # 预置模板数据
    _seed_templates(conn)
    _seed_agent_memory(conn)
    _seed_agent_configs(conn)
    _seed_agent_teams(conn)
    _seed_aios_channels(conn)
    return conn


def _json(value, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


AGENT_ALIASES = {
    "retrieval": "guanwei", "procedure": "zhiju", "knowledge": "bowen",
    "collaboration": "heming", "audit": "mingjian",
    "天工": "tiangong", "观微": "guanwei", "执矩": "zhiju",
    "博闻": "bowen", "和鸣": "heming", "明鉴": "mingjian",
}


def _agent_key(agent_id: str) -> str:
    key = str(agent_id or "tiangong").strip()
    return AGENT_ALIASES.get(key, key)


def _seed_agent_memory(conn: sqlite3.Connection) -> None:
    now = _now()
    for agent in AGENTS:
        memories = {
            "role": agent.get("role", ""),
            "duty": agent.get("duty", ""),
            "capabilities": "、".join(agent.get("capabilities", [])),
            "ip": agent.get("ip", ""),
        }
        for key, value in memories.items():
            conn.execute(
                """INSERT OR IGNORE INTO yixiu_agent_memory
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    f"mem-{agent['id']}-{key}",
                    agent["id"],
                    key,
                    value,
                    json.dumps(["agent", key], ensure_ascii=False),
                    now,
                ),
            )


def _seed_agent_configs(conn: sqlite3.Connection) -> None:
    now = _now()
    for agent in AGENTS:
        agent_id = agent["id"]
        memory_keys = ["role", "duty", "capabilities", "ip"]
        conn.execute(
            """INSERT INTO yixiu_agent_configs
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name,
                 role=excluded.role,
                 prompt=excluded.prompt,
                 tools_json=excluded.tools_json,
                 memory_keys_json=excluded.memory_keys_json,
                 updated_at=excluded.updated_at""",
            (
                agent_id,
                agent["name"],
                agent.get("role", ""),
                "qwen",
                "qwen-local-or-cloud",
                AGENT_PROMPTS.get(agent_id, ""),
                json.dumps(AGENT_TOOL_ALLOWLISTS.get(agent_id, []), ensure_ascii=False),
                json.dumps(["维修手册", "历史案例", "SOP", "安全规范"], ensure_ascii=False),
                json.dumps(memory_keys, ensure_ascii=False),
                "business_read_write" if agent_id in {"tiangong", "zhiju", "bowen", "heming"} else "read_business",
                "enabled",
                now,
                now,
            ),
        )


def _seed_agent_teams(conn: sqlite3.Connection) -> None:
    now = _now()
    workflow = {
        "name": "设备检修闭环工作流",
        "tech_stack": AIOS_TECH_STACK,
        "engine": "LangGraph 状态图编排，MCP 工具调用，E2B 沙箱隔离，Postgres/pgvector 长期记忆，FastAPI 统一入口，LangSmith Trace 观测。",
        "steps": [
            {"key": "upload", "title": "问题解析与附件接入", "agent_id": "tiangong"},
            {"key": "vision", "title": "意图识别与图文上下文整理", "agent_id": "guanwei"},
            {"key": "rag", "title": "知识库检索", "agent_id": "guanwei"},
            {"key": "diagnose", "title": "信息整合与故障分析", "agent_id": "guanwei"},
            {"key": "sop", "title": "作业编排与安全确认", "agent_id": "zhiju", "requires_approval": True},
            {"key": "confirm", "title": "校验确认", "agent_id": "tiangong", "human_in_loop": True},
            {"key": "report", "title": "结果生成与报告建议", "agent_id": "mingjian"},
            {"key": "archive", "title": "知识沉淀候选", "agent_id": "bowen", "requires_approval": True},
        ],
    }
    members = [
        {"agent_id": agent["id"], "name": agent["name"], "role": agent["role"]}
        for agent in AGENTS
    ]
    conn.execute(
        """INSERT INTO yixiu_agent_teams
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             members_json=excluded.members_json,
             workflow_json=excluded.workflow_json,
             updated_at=excluded.updated_at""",
        (
            "team-yixiu-closed-loop",
            "一修检修闭环 Team",
            "由天工统筹，观微检索诊断，执矩编排作业，和鸣协作，博闻沉淀，明鉴核查。",
            "tiangong",
            json.dumps(members, ensure_ascii=False),
            json.dumps(workflow, ensure_ascii=False),
            now,
            now,
        ),
    )


def _seed_aios_channels(conn: sqlite3.Connection) -> None:
    now = _now()
    channels = [
        ("channel-web", "PC Web 工作台", "web", "/"),
        ("channel-rest", "REST API", "rest", "/api/yixiu/aios"),
        ("channel-mcp", "MCP 工具入口", "mcp", "miniclaw.tools"),
    ]
    for channel_id, name, channel_type, endpoint in channels:
        conn.execute(
            """INSERT OR IGNORE INTO yixiu_aios_channels
               VALUES (?, ?, ?, ?, 1, 'tiangong', ?, ?, ?)""",
            (
                channel_id,
                name,
                channel_type,
                endpoint,
                json.dumps({"supports_session": True, "supports_trace": True}, ensure_ascii=False),
                now,
                now,
            ),
        )


def _agent_event_dict(row) -> dict:
    item = dict(row)
    item["payload"] = _json(item.pop("payload_json", "{}"), {})
    return item


def _record_agent_event(
    conn: sqlite3.Connection,
    agent_id: str,
    title: str,
    content: str = "",
    event_type: str = "task",
    status: str = "done",
    payload: dict | None = None,
    run_id: str = "",
) -> dict:
    agent = _agent_by_id(agent_id)
    event = {
        "id": f"evt-{uuid.uuid4().hex[:12]}",
        "run_id": run_id,
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "event_type": event_type,
        "title": title or "AIOS 执行事件",
        "content": content or "",
        "payload": payload or {},
        "status": status,
        "created_at": _now(),
    }
    conn.execute(
        "INSERT INTO yixiu_agent_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event["id"], event["run_id"], event["agent_id"], event["agent_name"],
            event["event_type"], event["title"], event["content"],
            json.dumps(event["payload"], ensure_ascii=False), event["status"], event["created_at"],
        ),
    )
    return event


def _agent_metrics(conn: sqlite3.Connection, agent_id: str) -> dict:
    key = _agent_key(agent_id)
    event_count = conn.execute("SELECT COUNT(*) FROM yixiu_agent_events WHERE agent_id=?", (key,)).fetchone()[0]
    memory_count = conn.execute("SELECT COUNT(*) FROM yixiu_agent_memory WHERE agent_id=?", (key,)).fetchone()[0]
    last = conn.execute(
        "SELECT * FROM yixiu_agent_events WHERE agent_id=? ORDER BY created_at DESC LIMIT 1",
        (key,),
    ).fetchone()
    return {
        "event_count": event_count,
        "memory_count": memory_count,
        "last_event": _agent_event_dict(last) if last else None,
    }


def _queue_dict(row) -> dict:
    item = dict(row)
    item["payload"] = _json(item.pop("payload_json", "{}"), {})
    item["result"] = _json(item.pop("result_json", "{}"), {})
    return item


def _agent_config_dict(row) -> dict:
    item = dict(row)
    item["tools"] = _json(item.pop("tools_json", "[]"), [])
    item["knowledge_ids"] = _json(item.pop("knowledge_ids_json", "[]"), [])
    item["memory_keys"] = _json(item.pop("memory_keys_json", "[]"), [])
    base = _agent_by_id(item.get("id"))
    item["avatar"] = base.get("avatar", "")
    item["capabilities"] = base.get("capabilities", [])
    item["output_schema"] = AGENT_OUTPUT_SCHEMAS.get(item.get("id"), {})
    return item


def _team_dict(row) -> dict:
    item = dict(row)
    item["members"] = _json(item.pop("members_json", "[]"), [])
    item["workflow"] = _json(item.pop("workflow_json", "{}"), {})
    return item


def _session_dict(row) -> dict:
    item = dict(row)
    item["context"] = _json(item.pop("context_json", "{}"), {})
    return item


def _approval_dict(row) -> dict:
    return dict(row)


def _channel_dict(row) -> dict:
    item = dict(row)
    item["enabled"] = bool(item.get("enabled"))
    item["config"] = _json(item.pop("config_json", "{}"), {})
    return item


def _service_account_dict(row) -> dict:
    item = dict(row)
    item["enabled"] = bool(item.get("enabled"))
    item["scopes"] = _json(item.pop("scopes_json", "[]"), [])
    return item


def _sync_aios_queue(conn: sqlite3.Connection, run_id: str, plan: dict, artifacts: dict | None = None) -> list[dict]:
    artifacts = artifacts or {}
    queued = []
    priority_base = 100
    for index, step in enumerate(plan.get("steps", [])):
        agent = step.get("agent") or {}
        row_id = f"queue-{run_id}-{step.get('key')}"
        state = step.get("state") or step.get("status") or "pending"
        result = artifacts.get(step.get("key")) or step.get("result") or {}
        payload = {
            "title": step.get("title"),
            "input": step.get("input") or {},
            "depends_on": step.get("depends_on") or [],
            "requires_approval": step.get("requires_approval", False),
            "approved": step.get("approved", False),
            "expected_output": step.get("expected_output", ""),
        }
        values = (
            row_id, run_id, step.get("key"), _agent_key(agent.get("id")),
            step.get("action"), state, priority_base - index,
            json.dumps(payload, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            _now(), _now(),
        )
        conn.execute(
            """INSERT INTO yixiu_aios_queue
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET state=excluded.state,
               priority=excluded.priority, payload_json=excluded.payload_json,
               result_json=excluded.result_json, updated_at=excluded.updated_at""",
            values,
        )
        queued.append({
            "id": row_id,
            "run_id": run_id,
            "step_key": step.get("key"),
            "agent_id": _agent_key(agent.get("id")),
            "action": step.get("action"),
            "state": state,
        })
    return queued


def _ensure_aios_approval(conn: sqlite3.Connection, run_id: str, step: dict, detail: str = "") -> dict:
    step_key = str(step.get("key") or "")
    existing = conn.execute(
        "SELECT * FROM yixiu_aios_approvals WHERE run_id=? AND step_key=? AND status='pending'",
        (run_id, step_key),
    ).fetchone()
    if existing:
        return _approval_dict(existing)
    agent = step.get("agent") or {}
    approval_id = f"apr-{uuid.uuid4().hex[:12]}"
    title = f"智能体请求执行：{step.get('title') or step.get('action')}"
    conn.execute(
        """INSERT INTO yixiu_aios_approvals
           VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'AIOS', '', '', ?, '')""",
        (
            approval_id,
            run_id,
            step_key,
            step.get("action") or "",
            title,
            detail or step.get("tool_description") or step.get("expected_output") or "",
            _agent_key(agent.get("id")),
            _now(),
        ),
    )
    return _approval_dict(conn.execute("SELECT * FROM yixiu_aios_approvals WHERE id=?", (approval_id,)).fetchone())


def _load_aios_run(conn: sqlite3.Connection, run_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM yixiu_aios_runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["plan"] = _json(item.pop("plan_json", "{}"), {})
    item["artifacts"] = _json(item.pop("artifacts_json", "{}"), {})
    item["events"] = [
        _agent_event_dict(event)
        for event in conn.execute(
            "SELECT * FROM yixiu_agent_events WHERE run_id=? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
    ]
    item["queue"] = [
        _queue_dict(queue)
        for queue in conn.execute(
            "SELECT * FROM yixiu_aios_queue WHERE run_id=? ORDER BY priority DESC, created_at ASC",
            (run_id,),
        ).fetchall()
    ]
    return item


def _run_status_from_plan(plan: dict, progress: int) -> str:
    workflow_state = plan.get("workflow_state")
    if workflow_state and workflow_state != "planned":
        return workflow_state
    return "completed" if progress == 100 else "running"


def _database_status() -> dict:
    tables = [
        "yixiu_files", "yixiu_tasks", "yixiu_knowledge", "yixiu_messages",
        "yixiu_aios_runs", "yixiu_task_memory", "yixiu_agent_events",
        "yixiu_agent_memory", "yixiu_aios_queue", "yixiu_agent_configs",
        "yixiu_agent_teams", "yixiu_conversation_sessions",
        "yixiu_aios_approvals", "yixiu_aios_channels", "yixiu_service_accounts",
    ]
    result = {
        "sqlite": {"name": "一修业务库", "path": str(DB_PATH), "exists": DB_PATH.exists(), "ok": True, "tables": {}},
        "checked_at": _now(),
    }
    try:
        with _db() as conn:
            for table in tables:
                result["sqlite"]["tables"][table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception as exc:  # noqa: BLE001
        result["sqlite"]["ok"] = False
        result["sqlite"]["message"] = f"数据库检查失败：{exc}"
    return result


def _aios_platform_snapshot() -> dict:
    with _db() as conn:
        agents = [
            _agent_config_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_agent_configs ORDER BY id").fetchall()
        ]
        teams = [
            _team_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_agent_teams ORDER BY updated_at DESC").fetchall()
        ]
        sessions = [
            _session_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_conversation_sessions ORDER BY updated_at DESC LIMIT 12").fetchall()
        ]
        approvals = [
            _approval_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_aios_approvals ORDER BY created_at DESC LIMIT 20").fetchall()
        ]
        channels = [
            _channel_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_aios_channels ORDER BY id").fetchall()
        ]
        service_accounts = [
            _service_account_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_service_accounts ORDER BY created_at DESC LIMIT 20").fetchall()
        ]
        latest_runs = [
            dict(row)
            for row in conn.execute(
                "SELECT id, goal, mode, status, progress, created_at, updated_at FROM yixiu_aios_runs ORDER BY updated_at DESC LIMIT 8"
            ).fetchall()
        ]
        latest_events = [
            _agent_event_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_agent_events ORDER BY created_at DESC LIMIT 20").fetchall()
        ]
        counts = {
            "agents": len(agents),
            "teams": len(teams),
            "sessions": conn.execute("SELECT COUNT(*) FROM yixiu_conversation_sessions").fetchone()[0],
            "memories": conn.execute("SELECT COUNT(*) FROM yixiu_agent_memory").fetchone()[0],
            "runs": conn.execute("SELECT COUNT(*) FROM yixiu_aios_runs").fetchone()[0],
            "pending_approvals": conn.execute("SELECT COUNT(*) FROM yixiu_aios_approvals WHERE status='pending'").fetchone()[0],
            "channels": len(channels),
        }
    return {
        "name": "天工 AIOS",
        "description": "面向设备检修的多智能体运行平台，支持 LangGraph 编排、MCP 工具、E2B 沙箱、Postgres/pgvector 记忆、FastAPI 入口和 LangSmith 观测。",
        "tech_stack": AIOS_TECH_STACK,
        "tiangong_prompt": TIANGONG_OPERATION_PROMPT,
        "agents": agents,
        "teams": teams,
        "workflows": {
            "actions": AIOS_ACTION_REGISTRY,
            "default_team": "team-yixiu-closed-loop",
            "supports": ["long_task", "resume", "cancel", "human_approval", "trace", "background_queue"],
        },
        "sessions": sessions,
        "memory": {
            "types": ["用户偏好", "任务状态", "设备信息", "智能体角色记忆", "故障处置经验"],
            "total": counts["memories"],
        },
        "rag": {
            "sources": ["维修手册", "PDF/Word 文档", "历史故障案例", "SOP", "安全规范", "知识图谱"],
            "retrieval_modes": ["语义检索", "设备型号检索", "故障现象检索", "图像/附件上下文检索"],
        },
        "tools": {
            "registry": AIOS_ACTION_REGISTRY,
            "categories": ["数据库查询", "知识检索", "文件解析", "任务流转", "协作消息", "复检核查", "报告生成"],
        },
        "approvals": approvals,
        "trace": {
            "latest_runs": latest_runs,
            "latest_events": latest_events,
            "views": ["时间轴", "树状调用链", "智能体执行记录", "审批记录"],
        },
        "permissions": {
            "auth": ["JWT", "RBAC", "服务账号"],
            "roles": ["检修人员", "知识管理员", "复检人员", "项目管理员", "系统管理员"],
            "scopes": ["knowledge:read", "knowledge:write", "task:read", "task:write", "approval:decide", "agent:admin"],
            "service_accounts": service_accounts,
        },
        "channels": channels,
        "database": _database_status(),
        "counts": counts,
        "updated_at": _now(),
    }


def _trace_tree(run: dict, approvals: list[dict]) -> dict:
    plan = run.get("plan") or {}
    queue_by_step = {item.get("step_key"): item for item in run.get("queue", [])}
    events_by_step: dict[str, list[dict]] = {}
    for event in run.get("events", []):
        step_key = (event.get("payload") or {}).get("step_key") or ""
        events_by_step.setdefault(step_key, []).append(event)
    approvals_by_step: dict[str, list[dict]] = {}
    for approval in approvals:
        approvals_by_step.setdefault(approval.get("step_key") or "", []).append(approval)
    nodes = []
    for step in plan.get("steps", []):
        key = step.get("key")
        nodes.append({
            "id": key,
            "title": step.get("title"),
            "agent": step.get("agent", {}),
            "action": step.get("action"),
            "state": step.get("state") or step.get("status"),
            "depends_on": step.get("depends_on") or [],
            "queue": queue_by_step.get(key),
            "events": events_by_step.get(key, []),
            "approvals": approvals_by_step.get(key, []),
        })
    return {
        "run_id": run.get("id"),
        "goal": run.get("goal"),
        "status": run.get("status"),
        "progress": run.get("progress"),
        "nodes": nodes,
        "timeline": run.get("events", []),
    }


def _file_type(filename: str, mime: str = "") -> str:
    ext = Path(filename).suffix.lower()
    if mime.startswith("image/") or ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
        return "图片"
    if mime == "application/pdf" or ext == ".pdf":
        return "PDF"
    if ext in {".doc", ".docx", ".wps"}:
        return "Word"
    if ext in {".xls", ".xlsx", ".csv"}:
        return "Excel"
    if mime.startswith("video/") or ext in {".mp4", ".webm", ".mov"}:
        return "视频"
    if mime.startswith("text/") or ext in {".txt", ".md", ".log"}:
        return "文本"
    return "其他"


def _file_dict(row) -> dict:
    item = dict(row)
    item["auditStatus"] = item.pop("audit_status")
    item["parseStatus"] = item.pop("parse_status")
    item["uploaded_at"] = item.get("uploaded_at", "")
    item["sizeBytes"] = item.pop("size", 0)
    size = item["sizeBytes"]
    item["size"] = f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024 else f"{max(size / 1024, 0.1):.1f} KB"
    item["analysis"] = _json(item.pop("analysis_json", "{}"), {})
    item["url"] = f"/api/yixiu/files/{item['id']}/content"
    return item


def _demo_tasks(status: str = "") -> list[dict]:
    try:
        from routes.maintenance_tasks import _get_demo_tasks
        return _get_demo_tasks(status)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取演示任务失败: %s", exc)
        return []


def _base_knowledge() -> list[dict]:
    if KNOWLEDGE_PATH.exists():
        try:
            return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取基础知识库失败: %s", exc)
    return []


def _stored_knowledge() -> list[dict]:
    with _db() as conn:
        rows = conn.execute("SELECT * FROM yixiu_knowledge ORDER BY created_at DESC").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = _json(item.get("tags"), [])
        item["reviewable"] = True
        result.append(item)
    return result


def _task_payload(row) -> dict:
    item = _json(row["payload"], {})
    item.update({"id": row["id"], "status": row["status"], "completedSteps": _json(row["completed_steps"], [])})
    return item


def _ensure_task_row(conn: sqlite3.Connection, task_id: str):
    row = conn.execute("SELECT * FROM yixiu_tasks WHERE id=?", (task_id,)).fetchone()
    if row:
        return row
    demo = next((item for item in _demo_tasks("") if str(item.get("id")) == str(task_id)), None)
    if not demo:
        return None
    sop = demo.get("sop") or ["安全确认", "故障记录", "部件检测", "维修处置", "复测提交"]
    demo = {**demo, "sop": sop}
    conn.execute("INSERT INTO yixiu_tasks VALUES (?, ?, ?, ?, ?, ?)", (str(task_id), json.dumps(demo, ensure_ascii=False), demo.get("status", "pending"), "[]", demo.get("created_at", _now()), _now()))
    return conn.execute("SELECT * FROM yixiu_tasks WHERE id=?", (str(task_id),)).fetchone()


def _sop_for(category: str, level: str, fault: str) -> tuple[list[dict], list[str]]:
    category = category or "通用设备"
    level = level or "二级检修"
    fault = fault or "故障"
    steps = [
        {"title": "作业许可与安全隔离", "detail": f"确认{category}{level}作业票，执行停机、断电、验电和挂牌。", "required": True, "evidence": "安全确认"},
        {"title": "故障现象记录", "detail": f"记录{fault}出现条件、报警、温度、声音及现场图片，禁止带故障盲目拆机。", "required": True, "evidence": "数据或图片"},
        {"title": "按依据逐项检测", "detail": "按照召回手册和相似案例测量关键参数，先确认原因再更换部件。", "required": True, "evidence": "检测值"},
        {"title": "维修处置与过程复核", "detail": "执行紧固、清洁、调整或更换，记录工具、部件及关键扭矩。", "required": True, "evidence": "过程记录"},
        {"title": "复测验收", "detail": "恢复防护后试运行，对照标准复测并确认故障消除。", "required": True, "evidence": "复测结果"},
        {"title": "报告与知识沉淀", "detail": "提交检修报告、引用依据和证据；有效经验进入知识审核队列。", "required": True, "evidence": "检修报告"},
    ]
    safety = ["必须执行停机断电和挂牌上锁", "拆卸前确认温度、压力和残余能量", "检测结果异常时禁止直接恢复运行"]
    return steps, safety


def _fallback_image_analysis(filename: str) -> dict:
    return {
        "equipment": "待结合设备型号确认",
        "fault_signs": ["已接收现场图片", "需结合故障描述确认异常部位"],
        "risk_points": ["仅凭图片不能直接判定部件失效", "维修前必须完成安全隔离"],
        "analysis": f"图片 {filename} 已纳入跨模态检索，将与设备型号、故障现象和手册条目联合匹配。",
        "suggestion": "补充拍摄设备铭牌、异常部位全景和细节图，可提高检索准确度。",
        "provider": "local-fallback",
    }


def _analyze_image(path: Path, mime: str) -> dict:
    fallback = _fallback_image_analysis(path.name)
    try:
        from services.ai_gateway import ai_agent
        status = ai_agent.status()
        if not status.get("configured"):
            return fallback
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        text = ai_agent.vision(
            prompt="识别设备、异常部位、故障迹象和安全风险，给出简洁 JSON。",
            image_base64=f"data:{mime};base64,{encoded}",
            system_prompt="你是设备检修视觉分析助手。只根据可见证据描述，不确定内容必须标注待确认。",
        )
        parsed = ai_agent.parse_json(text)
        return parsed or {**fallback, "analysis": text, "provider": status.get("provider", "ai")}
    except Exception as exc:  # noqa: BLE001
        logger.warning("视觉模型不可用，使用本地回退: %s", exc)
        return fallback


def _agent_by_id(agent_id: str) -> dict:
    key = _agent_key(agent_id)
    agent = next((item for item in AGENTS if item.get("id") == key or item.get("name") == key), AGENTS[0])
    return enrich_agent(dict(agent))


def _knowledge_hits(query: str, task: dict | None = None, limit: int = 5) -> list[dict]:
    words = [item for item in str(query or "").lower().replace("/", " ").split() if item]
    if task:
        words.extend(str(task.get(key, "")).lower() for key in ("equipment_name", "equipment", "fault_type", "description"))
    candidates = _stored_knowledge() + _base_knowledge()

    def score(item: dict) -> int:
        text = json.dumps(item, ensure_ascii=False).lower()
        return sum(1 for word in words if word and word in text)

    ranked = sorted(candidates, key=score, reverse=True)
    return [item for item in ranked if score(item) > 0][:limit] or ranked[:limit]


def _focus_task(goal: str, task_id: str = "") -> dict:
    tasks = []
    with _db() as conn:
        tasks.extend(_task_payload(row) for row in conn.execute("SELECT * FROM yixiu_tasks ORDER BY updated_at DESC").fetchall())
    tasks.extend(_demo_tasks(""))
    if task_id:
        found = next((item for item in tasks if str(item.get("id")) == str(task_id)), None)
        if found:
            return found
    if _goal_contains(goal, ["车淹", "泡水", "涉水", "积水", "水淹", "轿车", "汽车", "车辆"]):
        return {}
    high = next((item for item in tasks if item.get("severity") in {"critical", "high"}), None)
    return high or (tasks[0] if tasks else {})


def _aios_snapshot(goal: str, mode: str, task: dict) -> dict:
    tasks = []
    with _db() as conn:
        tasks.extend(_task_payload(row) for row in conn.execute("SELECT * FROM yixiu_tasks ORDER BY updated_at DESC").fetchall())
    tasks.extend(_demo_tasks(""))
    contacts = CONTACTS
    knowledge = _knowledge_hits(goal, task, limit=5)
    return {
        "mode": mode,
        "focus_task": task,
        "counts": {
            "tasks": len(tasks),
            "pending": len([item for item in tasks if item.get("status") in {"pending", "in_progress"}]),
            "high_risk": len([item for item in tasks if item.get("severity") in {"critical", "high"}]),
            "contacts": len(contacts),
            "knowledge_hits": len(knowledge),
        },
        "knowledge_hits": knowledge,
        "contacts": contacts,
        "generated_at": _now(),
    }


def _goal_contains(goal: str, keywords: list[str]) -> bool:
    text = str(goal or "").lower()
    return any(str(word).lower() in text for word in keywords)


def _aios_focus_keyword(goal: str, task: dict | None = None) -> str:
    task = task or {}
    text = str(goal or "")
    if _goal_contains(text, ["车淹", "泡水", "涉水", "积水", "水淹"]):
        return "泡水车辆检修知识"
    if _goal_contains(text, ["汽车", "汽修", "轿车", "乘用车"]):
        return "汽车维修知识"
    if _goal_contains(text, ["摩托", "cg-125", "发动机异响"]):
        return "摩托车发动机维修知识"
    equipment = task.get("equipment_name") or task.get("equipment") or task.get("device")
    fault = task.get("fault_type") or task.get("fault")
    return " ".join([str(item) for item in [equipment, fault] if item]) or "设备检修知识"


def _aios_context_notes(goal: str, task: dict, snapshot: dict) -> list[str]:
    notes = [
        f"当前任务池 {snapshot.get('counts', {}).get('tasks', 0)} 条，待处理 {snapshot.get('counts', {}).get('pending', 0)} 条。",
        f"已召回 {snapshot.get('counts', {}).get('knowledge_hits', 0)} 条候选资料，可用于 RAG 与人工复核。",
    ]
    if task:
        notes.append(f"焦点工单：{task.get('workOrderNo') or task.get('id')}，设备 {task.get('equipment_name') or task.get('equipment') or '待确认'}，状态 {task.get('status') or '待确认'}。")
    if _goal_contains(goal, ["和鸣", "联系人", "协作", "总结"]):
        notes.append("需要和鸣参与，优先汇总今日未读、任务群、专家支援和待确认事项。")
    if _goal_contains(goal, ["知识库", "知识图谱", "资料", "摩托", "汽车"]):
        notes.append("需要博闻和观微参与，先打开知识库并围绕目标关键词检索资料与图谱关系。")
    return notes


def _aios_mode(goal: str, requested: str = "auto") -> str:
    if requested and requested != "auto":
        return requested
    if any(word in goal for word in ["和鸣", "协作", "联系人", "专家", "支援", "今天的信息总结", "未读", "沟通", "消息"]):
        return "support"
    if any(word in goal for word in ["复检", "验收", "核查", "返工"]):
        return "review"
    if any(word in goal for word in ["知识", "沉淀", "入库", "资料"]):
        return "knowledge"
    if any(word in goal for word in ["长任务", "打开", "查找", "询问", "问和鸣", "今天的信息总结", "全系统", "所有页面"]):
        return "orchestrate"
    return "repair"


def _aios_plan(goal: str, mode: str = "auto", task_id: str = "") -> dict:
    goal = (goal or "").strip() or "统筹完成当前设备检修任务，形成闭环。"
    mode = _aios_mode(goal, mode)
    task = _focus_task(goal, task_id)
    snapshot = _aios_snapshot(goal, mode, task)
    equipment = task.get("equipment_name") or task.get("equipment") or "待确认设备"
    fault = task.get("fault_type") or "待确认故障"
    focus_keyword = _aios_focus_keyword(goal, task)
    steps = [
        ("sense", "tiangong", "问题解析：读取系统状态并锁定目标", "sense_overview", "首页", "system_overview", {"goal": goal, "task_id": task.get("id"), "keyword": focus_keyword}),
        ("open_search", "guanwei", "上下文定位：进入智能检索并整理多模态线索", "retrieve_knowledge", "智能检索", "navigate+prefill", {"query": focus_keyword, "equipment": equipment, "fault": fault}),
        ("retrieve", "guanwei", "知识检索：召回资料与故障依据", "retrieve_knowledge", "智能检索", "knowledge_search+rag_query", {"query": focus_keyword, "equipment": equipment, "fault": fault}),
        ("diagnose", "guanwei", "信息整合：综合证据进行故障判断", "diagnose_fault", "智能检索", "rag_query", {"query": focus_keyword, "equipment": equipment, "fault": fault}),
        ("open_task", "zhiju", "上下文定位：打开检修任务并匹配工单", "sense_overview", "检修任务", "navigate+filter", {"task_id": task.get("id"), "equipment": equipment, "status": task.get("status")}),
        ("operate", "zhiju", "作业编排：生成 SOP 与安全确认", "orchestrate_task", "检修任务", "task_update+safety_check", {"task_id": task.get("id"), "equipment": equipment, "fault": fault}),
        ("collaborate", "heming", "智能体协作：协调人员并生成沟通草稿", "coordinate_team", "检修任务 / 联系人交流", "contacts_read+conversation_message_draft", {"task_id": task.get("id"), "risk": task.get("severity")}),
        ("open_knowledge", "bowen", "知识检索：打开知识库并定位图谱关系", "retrieve_knowledge", "知识库", "openKnowledgeGraph+knowledge_search", {"query": focus_keyword, "equipment": equipment}),
        ("archive", "bowen", "知识沉淀：生成待审核知识候选", "archive_knowledge", "知识库 / 沉淀更新", "knowledge_candidate_create", {"task_id": task.get("id"), "equipment": equipment, "fault": fault}),
        ("review", "mingjian", "校验确认：生成复检核查清单", "prepare_recheck", "检修任务 / 复检评估", "recheck+quality_score", {"task_id": task.get("id")}),
        ("memory", "tiangong", "信息整合：写入会话与长期记忆", "record_memory", "AIOS 记忆", "pgvector_memory_write", {"task_id": task.get("id"), "goal": goal}),
        ("finalize", "mingjian", "结果生成：输出闭环报告与可观察记录", "finalize_report", "首页 / 报告预览", "report_verify+langsmith_trace", {"task_id": task.get("id"), "goal": goal}),
    ]
    priority_orders = {
        "knowledge": ["sense", "open_knowledge", "archive", "open_search", "retrieve", "diagnose", "open_task", "operate", "collaborate", "review", "memory", "finalize"],
        "support": ["sense", "collaborate", "open_task", "operate", "review", "open_search", "retrieve", "diagnose", "open_knowledge", "archive", "memory", "finalize"],
        "review": ["sense", "review", "open_task", "operate", "collaborate", "open_search", "retrieve", "diagnose", "open_knowledge", "archive", "memory", "finalize"],
        "orchestrate": ["sense", "open_search", "retrieve", "diagnose", "open_task", "operate", "collaborate", "open_knowledge", "archive", "review", "memory", "finalize"],
        "repair": ["sense", "open_search", "retrieve", "diagnose", "open_task", "operate", "review", "collaborate", "open_knowledge", "archive", "memory", "finalize"],
    }
    order = priority_orders.get(mode)
    if order:
        rank = {key: index for index, key in enumerate(order)}
        original_rank = {step[0]: index for index, step in enumerate(steps)}
        steps = sorted(steps, key=lambda step: (rank.get(step[0], 99), original_rank.get(step[0], 99)))
    plan_steps = []
    for key, agent_id, title, action, page, tool, step_input in steps:
        meta = AIOS_ACTION_REGISTRY.get(action, {})
        plan_steps.append({
            "key": key,
            "agent": _agent_by_id(agent_id),
            "title": title,
            "action": action,
            "page": page,
            "ui_action": tool.split("+")[0] if tool else "invokeAgent",
            "mcp_tool": tool,
            "capability": meta.get("capability", action),
            "operation_kind": meta.get("kind", "read"),
            "requires_approval": bool(meta.get("requires_approval", False)),
            "tool_description": meta.get("description", ""),
            "status": "pending",
            "input": step_input,
            "expected_output": meta.get("description", ""),
            "visualizable": True,
        })
    plan_id = f"aios-{uuid.uuid4().hex[:12]}"
    plan = {
        "id": plan_id,
        "goal": goal,
        "mode": mode,
        "focus": task,
        "focus_keyword": focus_keyword,
        "context_notes": _aios_context_notes(goal, task, snapshot),
        "snapshot": snapshot,
        "steps": plan_steps,
        "progress": 0,
        "created_at": _now(),
    }
    plan = attach_state_machine(plan)
    with _db() as conn:
        conn.execute("INSERT INTO yixiu_aios_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (plan_id, goal, mode, json.dumps(plan, ensure_ascii=False), "planned", 0, "{}", _now(), _now()))
        _sync_aios_queue(conn, plan_id, plan)
        _record_agent_event(
            conn,
            "tiangong",
            "生成 AIOS 执行计划",
            f"天工已把「{goal}」拆解为 {len(plan_steps)} 个步骤。",
            event_type="plan",
            payload={"mode": mode, "step_count": len(plan_steps), "focus_task": task.get("id")},
            run_id=plan_id,
        )
    return plan


def _aios_execute_action(step: dict, snapshot: dict, commit: bool = True) -> dict:
    action = step.get("action")
    focus = snapshot.get("focus_task") or {}
    if action == "sense_overview":
        return {
            "summary": "已读取系统概览并锁定当前任务。",
            "counts": snapshot.get("counts", {}),
            "focus_task": focus,
            "next_focus": step.get("input", {}).get("keyword") or _aios_focus_keyword("", focus),
        }
    if action == "retrieve_knowledge":
        query = step.get("input", {}).get("query") or json.dumps(step.get("input", {}), ensure_ascii=False)
        hits = _knowledge_hits(query, focus, limit=8)
        # 真实能力：调用 RAG 向量检索补充命中（失败回退到本地匹配）
        rag_hits = []
        try:
            from services.rag_service import search_similar
            rag_hits = search_similar(query, limit=5, mode="hybrid")
        except Exception as exc:  # noqa: BLE001
            logger.debug("RAG 检索失败，回退到本地匹配: %s", exc)
        merged_refs = hits + [{"title": item.get("text", "")[:60], "type": "rag_chunk", "source": item.get("source", "lightrag"), "score": item.get("score", 1.0)} for item in rag_hits]
        grouped: dict[str, int] = {}
        for item in merged_refs:
            key = item.get("type") or item.get("category") or "资料"
            grouped[key] = grouped.get(key, 0) + 1
        return {
            "summary": f"已围绕「{query}」召回 {len(merged_refs)} 条资料依据（RAG {len(rag_hits)} 条 + 本地 {len(hits)} 条）。",
            "query": query,
            "references": merged_refs,
            "grouped": grouped,
            "rag_hits": rag_hits,
            "usable_for": ["智能检索结果", "知识图谱节点", "作业方案引用", "复检依据"],
        }
    if action == "diagnose_fault":
        sop, safety = _sop_for(focus.get("category"), focus.get("maintenanceLevel"), focus.get("fault_type"))
        query = step.get("input", {}).get("query") or _aios_focus_keyword("", focus)
        # 真实能力：用 RAG 召回相似案例作为诊断依据
        rag_evidence = []
        try:
            from services.rag_service import search_similar
            rag_evidence = search_similar(query, limit=3, mode="hybrid")
        except Exception as exc:  # noqa: BLE001
            logger.debug("诊断 RAG 检索失败: %s", exc)
        diagnosis = {
            "query": query,
            "fault": focus.get("fault_type") or step.get("input", {}).get("fault"),
            "possible_causes": ["连接松动或磨损", "润滑/散热不足", "传感或控制信号异常"],
            "first_checks": sop[:3],
            "safety": safety,
            "confidence": 0.82,
            "rag_evidence": rag_evidence,
        }
        return {
            "summary": "已形成可追溯故障判断。" + (f" 召回 {len(rag_evidence)} 条相似案例。" if rag_evidence else ""),
            "diagnosis": diagnosis,
        }
    if action == "orchestrate_task":
        sop, safety = _sop_for(focus.get("category"), focus.get("maintenanceLevel"), focus.get("fault_type"))
        # 真实能力：写入 yixiu_knowledge 候选（pending 状态，等待人工审核）
        candidate_id = ""
        if commit and focus.get("id"):
            try:
                candidate_id = f"kb-{uuid.uuid4().hex[:12]}"
                title = f"{focus.get('equipment_name') or '设备'}{focus.get('fault_type') or '故障'}检修方案"
                with _db() as conn:
                    conn.execute(
                        "INSERT INTO yixiu_knowledge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (candidate_id, title, "SOP 生成", "作业方案", focus.get("equipment_name", ""), focus.get("model", ""), f"由执矩为工单 {focus.get('id')} 生成的 SOP。", "\n".join(f"{i+1}. {s.get('action','')}" for i, s in enumerate(sop)), json.dumps(["aios生成", "待审核"], ensure_ascii=False), "aios_zhiju", "pending", "", "", _now(), _now()),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("SOP 候选写入失败: %s", exc)
        return {
            "summary": "已生成检修 SOP、工具备件和安全确认项。" + (f" 已写入待审核候选 {candidate_id}。" if candidate_id else ""),
            "sop": sop,
            "safety": safety,
            "tools": ["绝缘手套", "扭矩扳手", "万用表", "红外测温仪", "清洁耗材"],
            "spares": ["密封件", "紧固件", "易损传感器", "润滑材料"],
            "recommended_status": "in_progress",
            "knowledge_candidate_id": candidate_id,
            "needs_confirmation": True,
        }
    if action == "coordinate_team":
        contacts = sorted(CONTACTS, key=lambda item: item.get("workload", 0))[:3]
        message = f"建议优先联系：{', '.join(item['name'] for item in contacts)}，同步当前风险、SOP 和复检要求。"
        if commit:
            with _db() as conn:
                conn.execute("INSERT INTO yixiu_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"msg-{uuid.uuid4().hex[:12]}", f"task-{focus.get('id') or 'aios'}", "aios", "天工", "text", message, "{}", "{}", _now()))
        return {
            "summary": message,
            "recommended_contacts": contacts,
            "today": {
                "unread": 4,
                "urgent": 2,
                "pending_confirmations": ["高风险检修晨会", "ZK-320 复检反馈", "资料审核退回说明"],
                "digest": "今日重点是高风险工单确认、复检反馈闭环和维修资料审核。",
            },
            "draft_message": "请同步当前异常现象、已完成安全隔离、待复测数据和需要专家确认的问题。",
            "needs_confirmation": True,
        }
    if action == "prepare_recheck":
        checklist = ["故障是否消除", "安全措施是否恢复", "复测数据是否达标", "报告和证据是否完整"]
        return {
            "summary": "已生成复检清单。",
            "checklist": checklist,
            "quality_gate": {"required_evidence": 4, "blocking_items": ["高风险步骤未二次确认", "复测数据缺失"]},
        }
    if action == "record_memory":
        memory = {"goal": step.get("input", {}).get("goal"), "task": focus.get("id"), "summary": "本次诊断、SOP、协作和复检要求可复用。"}
        if commit and focus.get("id"):
            with _db() as conn:
                conn.execute("INSERT INTO yixiu_task_memory VALUES (?, ?, ?, ?, ?, ?)", (f"mem-{uuid.uuid4().hex[:12]}", str(focus.get("id")), "aios_execution", json.dumps(memory, ensure_ascii=False), "aios", _now()))
        return {"summary": "已整理任务记忆，等待用户确认后可沉淀。", "memory": memory, "needs_confirmation": True}
    if action == "archive_knowledge":
        # 真实能力：写入 yixiu_knowledge 表，状态 pending，等人工审核
        candidate_id = ""
        if commit:
            try:
                candidate_id = f"kb-{uuid.uuid4().hex[:12]}"
                title = f"{focus.get('equipment_name') or '设备'}{focus.get('fault_type') or '故障'}检修经验"
                with _db() as conn:
                    conn.execute(
                        "INSERT INTO yixiu_knowledge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (candidate_id, title, "历史故障案例", "案例", focus.get("equipment_name", ""), focus.get("model", ""), "由博闻整理的待审核知识候选。", "## 故障现象\n待补充\n\n## 原因判断\n待补充\n\n## 维修方案\n待补充\n\n## 复检标准\n待补充", json.dumps(["aios生成", "待审核"], ensure_ascii=False), "aios_bowen", "pending", "", "", _now(), _now()),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("知识候选写入失败: %s", exc)
        return {
            "summary": "已生成待审核知识候选。" + (f" 候选ID: {candidate_id}。" if candidate_id else ""),
            "knowledge_candidate": {
                "id": candidate_id,
                "title": f"{focus.get('equipment_name') or '设备'}{focus.get('fault_type') or '故障'}检修经验",
                "status": "pending_review",
                "sections": ["故障现象", "原因判断", "检测方法", "维修方案", "复检标准"],
            },
            "needs_confirmation": True,
        }
    if action == "finalize_report":
        return {
            "summary": "AIOS 已完成本轮闭环报告。",
            "report": {
                "completed_scope": [item for item in AIOS_ACTION_REGISTRY],
                "next_action": "进入现场执行、复检或人工审核。",
                "handoff": ["检索依据已整理", "作业步骤已编排", "协作摘要已生成", "复检门禁已建立"],
            },
        }
    return {"summary": "未识别的 AIOS 动作，已跳过。"}


def _aios_ui_plan(goal: str, plan: dict) -> list[dict]:
    keyword = plan.get("focus_keyword") or _aios_focus_keyword(goal, plan.get("focus") or {})
    action_map = {
        "首页": "navigate",
        "智能检索": "search",
        "检修任务": "filter",
        "检修任务 / 联系人交流": "openChat",
        "知识库": "openKnowledgeGraph",
        "知识库 / 沉淀更新": "openPanel",
        "检修任务 / 复检评估": "openPanel",
        "AIOS 记忆": "summarize",
        "首页 / 报告预览": "report",
    }
    ui_plan = []
    for index, step in enumerate(plan.get("steps", []), 1):
        agent = step.get("agent") or {}
        page = step.get("page") or "首页"
        ui_plan.append({
            "index": index,
            "action": action_map.get(page, step.get("ui_action") or "invokeAgent"),
            "page": page,
            "agent": agent.get("id") or "tiangong",
            "agentName": agent.get("name") or "天工",
            "target": step.get("title"),
            "input": step.get("input") or {"keyword": keyword},
            "reason": step.get("tool_description") or step.get("expected_output") or "执行 AIOS 计划步骤",
            "expected": step.get("expected_output") or step.get("title"),
            "requiresApproval": bool(step.get("requires_approval")),
            "mcpTool": step.get("mcp_tool") or step.get("capability"),
            "dependsOn": step.get("depends_on") or [],
        })
    if len(ui_plan) < 10:
        ui_plan.extend([
            {"index": len(ui_plan) + 1, "action": "summarize", "page": "首页", "agent": "tiangong", "agentName": "天工", "target": "补充执行摘要", "input": {"goal": goal}, "reason": "保证长任务过程完整可见", "expected": "形成用户可读的执行摘要", "requiresApproval": False},
            {"index": len(ui_plan) + 2, "action": "finish", "page": "首页", "agent": "tiangong", "agentName": "天工", "target": "完成闭环", "input": {"keyword": keyword}, "reason": "结束本轮跨页面操作", "expected": "展示最终结果", "requiresApproval": False},
        ])
    return ui_plan


def _aios_step_digest(plan: dict, artifacts: dict) -> list[dict]:
    digest = []
    for step in plan.get("steps", []):
        agent = step.get("agent") or {}
        result = artifacts.get(step.get("key")) or step.get("result") or {}
        digest.append({
            "key": step.get("key"),
            "agent": agent.get("name") or agent.get("id"),
            "agent_id": agent.get("id"),
            "title": step.get("title"),
            "action": step.get("action"),
            "state": step.get("state"),
            "content": result.get("summary") or step.get("expected_output") or "",
            "result": result,
        })
    return digest


@yixiu_bp.get("/overview")
def overview():
    tasks = _demo_tasks("")
    with _db() as conn:
        stored_tasks = [_task_payload(row) for row in conn.execute("SELECT * FROM yixiu_tasks ORDER BY created_at DESC").fetchall()]
        file_count = conn.execute("SELECT COUNT(*) FROM yixiu_files").fetchone()[0]
    tasks = stored_tasks + tasks
    knowledge = _stored_knowledge() + _base_knowledge()
    pending = [item for item in tasks if item.get("status") in {"pending", "in_progress"}]
    high = [item for item in tasks if item.get("severity") in {"high", "critical"}]
    return success_response({
        "name": "一修", "subtitle": "设备检修知识检索与标准作业系统", "updated_at": _now(),
        "stats": {"online_equipment": 128, "pending_tasks": len(pending), "high_risk_items": len(high), "knowledge_items": len(knowledge), "files": file_count},
        "agents": AGENTS, "modules": MODULES, "tasks": tasks[:8], "knowledge": knowledge[:8],
    }, "一修概览获取成功")


@yixiu_bp.get("/agents")
def agents():
    agent_id = request.args.get("agent_id", "").strip()
    with _db() as conn:
        rows = AGENTS
        if agent_id:
            key = _agent_key(agent_id)
            rows = [item for item in AGENTS if item.get("id") == key or item.get("name") == agent_id]
            if not rows:
                return error_response(404, "智能体不存在")
        enriched = [{**_agent_by_id(item["id"]), "metrics": _agent_metrics(conn, item["id"])} for item in rows]
    return success_response({"agents": enriched}, "智能体状态获取成功")


def _invoke_agent(agent_id: str, goal: str, task_id: str = "", commit: bool = True) -> dict:
    agent = _agent_by_id(agent_id)
    goal = (goal or "").strip() or "协助完成当前设备检修工作"
    task = _focus_task(goal, task_id)
    if agent["id"] == "tiangong":
        plan = _aios_plan(goal, "auto", task_id)
        result = {"summary": f"天工已拆解为 {len(plan.get('steps', []))} 个执行步骤。", "plan": plan, "next_action": plan.get("steps", [{}])[0]}
    elif agent["id"] == "guanwei":
        hits = _knowledge_hits(goal, task, limit=8)
        result = {"summary": f"观微已召回 {len(hits)} 条与「{goal}」相关的维修资料。", "references": hits, "suggestion": "建议优先查看手册、历史案例和安全规范。"}
    elif agent["id"] == "zhiju":
        sop, safety = _sop_for(task.get("category"), task.get("maintenanceLevel"), task.get("fault_type") or goal)
        result = {"summary": "执矩已生成标准作业步骤和安全确认项。", "sop": sop, "safety": safety, "recommended_status": "in_progress"}
    elif agent["id"] == "bowen":
        hits = _knowledge_hits(goal, task, limit=6)
        result = {"summary": f"博闻已整理 {len(hits)} 条可关联资料，并生成知识候选。", "references": hits, "knowledge_candidate": {"title": f"{task.get('equipment_name') or '设备'}检修知识沉淀", "status": "pending_review"}}
    elif agent["id"] == "heming":
        contacts = sorted(CONTACTS, key=lambda item: item.get("workload", 0))
        result = {"summary": f"和鸣建议优先联系 {contacts[0]['name']}，同步任务风险与复检要求。", "contacts": contacts[:5], "today": {"total": len(contacts), "online": len([item for item in contacts if item.get("status") == "在线"])}}
    elif agent["id"] == "mingjian":
        checklist = [
            {"item": "检修依据是否完整", "passed": bool(_knowledge_hits(goal, task, limit=1))},
            {"item": "安全隔离是否记录", "passed": True},
            {"item": "复测数据是否可追溯", "passed": task.get("status") in {"review", "completed"}},
        ]
        score = 70 + sum(10 for item in checklist if item["passed"])
        result = {"summary": f"明鉴已完成核查，质量评分 {min(score, 100)} 分。", "score": min(score, 100), "checklist": checklist, "recommendation": "补齐未通过项后再提交复检。" if score < 90 else "可进入复检或归档流程。"}
    else:
        result = {"summary": f"{agent['name']}已接收任务：{goal}"}

    event = None
    if commit:
        with _db() as conn:
            event = _record_agent_event(
                conn,
                agent["id"],
                goal[:80],
                result.get("summary", ""),
                event_type="agent_invoke",
                payload={"goal": goal, "task_id": task.get("id"), "result": result},
            )
    return {"agent": agent, "goal": goal, "task": task, "result": result, "event": event}


@yixiu_bp.post("/session")
def create_yixiu_session():
    data = request.get_json(silent=True) or {}
    account = str(data.get("account") or "").strip()
    name = str(data.get("name") or "").strip() or account
    if not account:
        return error_response(400, "一修账号不能为空")
    token = generate_token(f"yixiu-{account}")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return success_response({
        "token": token,
        "user": {
            "id": f"yixiu-{account}",
            "account": account,
            "name": name,
            "role": "operator",
        },
    }, "一修工作台会话已建立")


@yixiu_bp.post("/agents/<agent_id>/invoke")
def invoke_agent(agent_id: str):
    data = request.get_json(silent=True) or {}
    payload = _invoke_agent(
        agent_id,
        str(data.get("goal") or data.get("message") or "").strip(),
        str(data.get("task_id") or "").strip(),
        data.get("commit", True) is not False,
    )
    return success_response(payload, f"{payload['agent']['name']}已完成本次协助")


@yixiu_bp.post("/agents/dispatch")
def dispatch_agents():
    data = request.get_json(silent=True) or {}
    goal = str(data.get("goal") or data.get("message") or "").strip()
    execute = bool(data.get("execute", False))
    plan = _aios_plan(goal, str(data.get("mode") or "auto"), str(data.get("task_id") or ""))
    results = []
    if execute:
        for step in plan.get("steps", []):
            results.append(_invoke_agent(step.get("agent", {}).get("id", "tiangong"), step.get("title") or goal, str(data.get("task_id") or ""), commit=True))
    return success_response({"plan": plan, "executed": execute, "results": results}, "天工已完成智能体分派")


@yixiu_bp.post("/aios/long-task")
def aios_long_task():
    data = request.get_json(silent=True) or {}
    goal = str(data.get("goal") or data.get("message") or "").strip()
    task_id = str(data.get("task_id") or "").strip()
    if not goal:
        return error_response(400, "请先输入天工要执行的目标")

    plan = _aios_plan(goal, str(data.get("mode") or "auto").strip(), task_id)
    run_id = plan.get("id")
    approvals = {step.get("key"): True for step in plan.get("steps", []) if step.get("requires_approval")}
    artifacts: dict[str, dict] = {}

    for step in plan.get("steps", []):
        try:
            plan, node = transition_step(plan, step["key"], "execute", approvals=approvals)
            if node.get("state") != "running":
                artifacts[step["key"]] = {"summary": node.get("last_error", "步骤暂不可执行"), "state": node.get("state")}
                continue
            with _db() as conn:
                _record_agent_event(
                    conn,
                    step.get("agent", {}).get("id", "tiangong"),
                    f"开始执行：{step.get('title')}",
                    step.get("tool_description") or step.get("expected_output") or "",
                    event_type="long_task_step_start",
                    status="running",
                    payload={"step_key": step.get("key"), "action": step.get("action"), "input": step.get("input")},
                    run_id=run_id,
                )
            result = _aios_execute_action(step, plan.get("snapshot") or {}, commit=False)
            result["safe_execution"] = "已生成可见执行产物；正式写入仍需用户确认。"
            step["result"] = result
            step["executed_at"] = _now()
            artifacts[step["key"]] = result
            if result.get("needs_confirmation") or step.get("requires_approval"):
                with _db() as conn:
                    approval = _ensure_aios_approval(conn, run_id, step, result.get("summary", ""))
                    result["approval"] = approval
                    _record_agent_event(
                        conn,
                        step.get("agent", {}).get("id", "tiangong"),
                        f"等待人工确认：{step.get('title')}",
                        approval.get("title", ""),
                        event_type="approval_requested",
                        status="waiting_approval",
                        payload={"step_key": step.get("key"), "approval": approval},
                        run_id=run_id,
                    )
            plan, _ = transition_step(plan, step["key"], "complete")
            with _db() as conn:
                _record_agent_event(
                    conn,
                    step.get("agent", {}).get("id", "tiangong"),
                    f"完成执行：{step.get('title')}",
                    result.get("summary", ""),
                    event_type="long_task_step_done",
                    status="done",
                    payload={"step_key": step.get("key"), "action": step.get("action"), "result": result},
                    run_id=run_id,
                )
        except Exception as exc:  # noqa: BLE001
            plan, _ = transition_step(plan, step["key"], "fail", error=str(exc))
            artifacts[step["key"]] = {"summary": "长任务步骤执行失败", "error": str(exc)}
            with _db() as conn:
                _record_agent_event(
                    conn,
                    step.get("agent", {}).get("id", "tiangong"),
                    f"执行失败：{step.get('title')}",
                    str(exc),
                    event_type="long_task_step_failed",
                    status="failed",
                    payload={"step_key": step.get("key"), "action": step.get("action"), "error": str(exc)},
                    run_id=run_id,
                )
            break

    steps = plan.get("steps", [])
    done = sum(1 for item in steps if item.get("state") == "done")
    progress = round(done / max(len(steps), 1) * 100)
    plan["progress"] = progress
    plan["updated_at"] = _now()
    status = _run_status_from_plan(plan, progress)
    summary = "天工已完成跨智能体长任务：先定位目标，再调度观微检索、执矩编排、和鸣协作、博闻沉淀、明鉴核查，并输出闭环结果。"
    ui_plan = _aios_ui_plan(goal, plan)

    with _db() as conn:
        conn.execute(
            "UPDATE yixiu_aios_runs SET plan_json=?, status=?, progress=?, artifacts_json=?, updated_at=? WHERE id=?",
            (json.dumps(plan, ensure_ascii=False), status, progress, json.dumps(artifacts, ensure_ascii=False), _now(), run_id),
        )
        queue = _sync_aios_queue(conn, run_id, plan, artifacts)
        final_event = _record_agent_event(
            conn,
            "tiangong",
            "长任务闭环完成",
            summary,
            event_type="long_task_done",
            status=status,
            payload={"goal": goal, "progress": progress, "ui_plan": ui_plan},
            run_id=run_id,
        )
        events = [
            _agent_event_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_agent_events WHERE run_id=? ORDER BY created_at ASC", (run_id,)).fetchall()
        ]
        approval_rows = [
            _approval_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_aios_approvals WHERE run_id=? ORDER BY created_at ASC", (run_id,)).fetchall()
        ]

    return success_response({
        "run_id": run_id,
        "status": status,
        "progress": progress,
        "summary": summary,
        "goal": goal,
        "mode": plan.get("mode"),
        "focus_keyword": plan.get("focus_keyword"),
        "context_notes": plan.get("context_notes", []),
        "plan": plan,
        "steps": _aios_step_digest(plan, artifacts),
        "ui_plan": ui_plan,
        "artifacts": artifacts,
        "queue": queue,
        "events": events,
        "approvals": approval_rows,
        "final_event": final_event,
        "next_actions": ["查看资料详情", "确认检修 SOP", "联系协作人员", "提交复检或知识审核"],
    }, "天工长任务执行完成")


@yixiu_bp.get("/tasks")
def tasks():
    status = request.args.get("status", "").strip()
    with _db() as conn:
        stored = [_task_payload(row) for row in conn.execute("SELECT * FROM yixiu_tasks ORDER BY created_at DESC").fetchall()]
    items = stored + _demo_tasks(status)
    if status:
        items = [item for item in items if item.get("status") == status]
    return success_response({"tasks": items, "total": len(items)}, "检修任务获取成功")


@yixiu_bp.post("/tasks")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("tasks.create", "/api/yixiu/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    task_id = f"task-{uuid.uuid4().hex[:10]}"
    category = data.get("category") or data.get("equipment_category") or "通用设备"
    level = data.get("maintenanceLevel") or data.get("maintenance_level") or "二级检修"
    fault = data.get("faultType") or data.get("fault_type") or data.get("description") or "待确认故障"
    generated_sop, safety = _sop_for(category, level, fault)
    task = {
        "id": task_id, "workOrderNo": data.get("workOrderNo") or f"YX-{datetime.now():%Y%m%d-%H%M%S}",
        "title": data.get("title") or f"{data.get('deviceName') or data.get('equipment_name') or '设备'}检修任务",
        "equipment_name": data.get("equipment_name") or data.get("deviceName") or "待登记设备",
        "equipment_no": data.get("equipment_no", ""), "equipment_model": data.get("equipment_model") or data.get("deviceModel") or "",
        "category": category, "maintenanceLevel": level, "fault_type": fault, "description": data.get("description", ""),
        "severity": data.get("severity", "medium"), "assignee_name": data.get("assignee_name", "待分配"),
        "current_step": "作业许可与安全隔离", "progress": 0, "due_at": data.get("due_at", ""), "created_at": _now(),
        "sop": data.get("sopDetails") or generated_sop, "tools": data.get("tools", []), "parts": data.get("parts", []),
        "safety": data.get("safety") or safety, "references": data.get("references", []),
    }
    with _db() as conn:
        conn.execute("INSERT INTO yixiu_tasks VALUES (?, ?, ?, ?, ?, ?)", (task_id, json.dumps(task, ensure_ascii=False), "pending", "[]", _now(), _now()))
    task.update({"status": "pending", "completedSteps": []})
    return success_response(task, "检修任务创建成功")


@yixiu_bp.put("/tasks/<task_id>/status")
def change_task_status(task_id: str):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "pending")
    allowed = {"pending", "in_progress", "review", "completed", "paused", "rejected", "overdue"}
    if status not in allowed:
        return error_response(400, "无效的任务状态")
    with _db() as conn:
        if not _ensure_task_row(conn, task_id):
            return error_response(404, "任务不存在")
        conn.execute("UPDATE yixiu_tasks SET status=?, updated_at=? WHERE id=?", (status, _now(), task_id))
    return success_response({"task_id": task_id, "status": status, "operator": data.get("operator", "当前用户"), "operated_at": _now(), "note": data.get("note", "")}, "任务状态已更新")


@yixiu_bp.put("/tasks/<task_id>/steps/<int:step_index>")
def complete_task_step(task_id: str, step_index: int):
    data = request.get_json(silent=True) or {}
    with _db() as conn:
        row = _ensure_task_row(conn, task_id)
        if not row:
            return error_response(404, "任务不存在或不是本页面创建的任务")
        task = _task_payload(row)
        steps = task.get("sop", [])
        if step_index < 0 or step_index >= len(steps):
            return error_response(400, "作业步骤不存在")
        completed = _json(row["completed_steps"], [])
        if data.get("completed", True) and step_index not in completed:
            completed.append(step_index)
        elif not data.get("completed", True) and step_index in completed:
            completed.remove(step_index)
        completed.sort()
        progress = round(len(completed) / max(len(steps), 1) * 100)
        status = "review" if progress == 100 else "in_progress"
        conn.execute("UPDATE yixiu_tasks SET completed_steps=?, status=?, updated_at=? WHERE id=?", (json.dumps(completed), status, _now(), task_id))
    return success_response({"task_id": task_id, "completedSteps": completed, "progress": progress, "status": status, "evidence": data.get("evidence", "")}, "作业步骤已记录")


@yixiu_bp.get("/tasks/<task_id>/memory")
def task_memory(task_id: str):
    with _db() as conn:
        rows = conn.execute("SELECT * FROM yixiu_task_memory WHERE task_id=? ORDER BY created_at ASC", (task_id,)).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["value"] = _json(item.pop("value_json", "{}"), {})
        items.append(item)
    return success_response({"memory": items, "total": len(items)}, "任务记忆获取成功")


@yixiu_bp.post("/tasks/<task_id>/memory")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("task.memory", "/api/yixiu/tasks/memory")
def save_task_memory(task_id: str):
    data = request.get_json(silent=True) or {}
    key = str(data.get("key", "")).strip()
    if not key:
        return error_response(400, "记忆键名不能为空")
    value = data.get("value")
    mem_id = f"mem-{uuid.uuid4().hex[:12]}"
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_task_memory VALUES (?, ?, ?, ?, ?, ?)",
            (mem_id, task_id, key, json.dumps(value, ensure_ascii=False), str(data.get("source", "operator")), _now()),
        )
    return success_response({"id": mem_id, "task_id": task_id, "memory_key": key, "value": value, "source": data.get("source", "operator"), "created_at": _now()}, "任务记忆已保存")


@yixiu_bp.post("/recheck")
def save_recheck():
    data = request.get_json(silent=True) or {}
    passed = data.get("result", "通过") == "通过"
    status = "completed" if passed else "in_progress"
    with _db() as conn:
        conn.execute("UPDATE yixiu_tasks SET status=?, updated_at=? WHERE id=?", (status, _now(), str(data.get("task_id", ""))))
    return success_response({"task_id": data.get("task_id"), "result": data.get("result", "通过"), "next_status": status, "comment": data.get("comment", ""), "reviewer": data.get("reviewer", "复检人员"), "reviewed_at": _now()}, "复检结果已保存")


@yixiu_bp.route("/files", methods=["GET", "POST"])
def files():
    if request.method == "GET":
        keyword = request.args.get("keyword", "").strip()
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_files ORDER BY uploaded_at DESC").fetchall()
        items = [_file_dict(row) for row in rows]
        if keyword:
            items = [item for item in items if keyword in item["name"] or keyword in (item.get("equipment") or "")]
        return success_response({"files": items, "total": len(items)}, "文件列表获取成功")

    if "file" not in request.files:
        return error_response(400, "请选择需要上传的文件")
    upload = request.files["file"]
    if not upload.filename:
        return error_response(400, "文件名为空")
    original_name = Path(upload.filename).name
    ext = Path(original_name).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".md", ".mp4", ".webm"}
    if ext not in allowed:
        return error_response(400, "不支持的文件类型")
    file_id = f"file-{uuid.uuid4().hex[:12]}"
    stored_name = f"{file_id}{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "yixiu"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / secure_filename(stored_name)
    upload.save(path)
    mime = upload.mimetype or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
    kind = _file_type(original_name, mime)
    # 图片走视觉分析；PDF/Word/TXT/MD/CSV 走切片入库流水线
    parse_status = "等待解析"
    ingestion = None
    if kind == "图片":
        analysis = _analyze_image(path, mime)
        parse_status = "解析成功" if analysis.get("equipment") or analysis.get("summary") else "视觉模型不可用"
    else:
        analysis = {"summary": "文件已保存。"}
        try:
            from services.file_parser import parse_file
            from services.rag_service import insert_chunks
            chunks = parse_file(path)
            if chunks:
                ingestion = insert_chunks(chunks, source=original_name)
                analysis = {
                    "summary": f"文件已切片入库，共 {ingestion.get('inserted', 0)}/{ingestion.get('total', 0)} 块。",
                    "chunks": len(chunks),
                    "ingestion": ingestion,
                }
                parse_status = "切片入库成功" if ingestion.get("success") else f"部分入库（失败 {ingestion.get('failed', 0)} 块）"
            else:
                parse_status = "无可提取文本"
        except Exception as exc:  # noqa: BLE001
            logger.warning("文件切片入库失败 %s: %s", original_name, exc)
            parse_status = f"解析失败: {exc}"
            analysis = {"summary": f"文件已保存，但解析失败：{exc}"}
    form = request.form
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, original_name, stored_name, mime, kind, form.get("category", "现场资料"), form.get("folder", "现场资料"), path.stat().st_size, form.get("equipment", ""), form.get("model", ""), form.get("uploader", "当前用户"), _now(), "待审核", parse_status, form.get("version", "v1.0"), form.get("purpose", "knowledge"), json.dumps(analysis, ensure_ascii=False)),
        )
        row = conn.execute("SELECT * FROM yixiu_files WHERE id=?", (file_id,)).fetchone()
    return success_response(_file_dict(row), "文件上传成功")


@yixiu_bp.get("/files/<file_id>/content")
def file_content(file_id: str):
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_files WHERE id=?", (file_id,)).fetchone()
    if not row:
        return error_response(404, "文件不存在")
    path = Path(current_app.config["UPLOAD_FOLDER"]) / "yixiu" / row["stored_name"]
    if not path.exists():
        return error_response(404, "文件内容不存在")
    return send_file(path, mimetype=row["mime"], download_name=row["name"])


@yixiu_bp.post("/search")
def search():
    data = request.get_json(silent=True) or {}
    query = str(data.get("query") or data.get("description") or "").strip()
    device = str(data.get("deviceName") or data.get("device_name") or "设备").strip()
    model = str(data.get("deviceModel") or data.get("device_model") or "待确认型号").strip()
    category = str(data.get("category") or "通用设备").strip()
    fault = str(data.get("faultType") or data.get("fault_type") or "待确认故障").strip()
    level = str(data.get("maintenanceLevel") or "二级检修").strip()
    file_ids = data.get("fileIds") or []
    attachments = []
    if file_ids:
        marks = ",".join("?" for _ in file_ids)
        with _db() as conn:
            rows = conn.execute(f"SELECT * FROM yixiu_files WHERE id IN ({marks})", tuple(file_ids)).fetchall()
        attachments = [_file_dict(row) for row in rows]
    images = [item for item in attachments if item["type"] == "图片"]
    docs = [item for item in attachments if item["type"] != "图片"]
    steps, safety = _sop_for(category, level, fault)
    knowledge = _stored_knowledge() + _base_knowledge()
    terms = [term for term in [query, device, model, fault] if term]
    ranked = []
    for index, item in enumerate(knowledge):
        haystack = json.dumps(item, ensure_ascii=False)
        score = sum(1 for term in terms if term.lower() in haystack.lower())
        if score or index < 4:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    matched = [item for _, item in ranked[:6]]
    visual_findings = []
    for image in images:
        visual_findings.extend(image.get("analysis", {}).get("fault_signs", []))
    scene_text = " ".join([query, device, model, category, fault, " ".join(item.get("name", "") for item in attachments)])
    if _goal_contains(scene_text, ["车淹", "泡水", "涉水", "积水", "水淹", "轿车", "汽车", "车辆"]):
        vehicle_device = device if device and device not in {"设备", "待确认设备"} else "涉水车辆"
        vehicle_model = "" if model in {"待确认型号", "unknown", "未知"} else model
        vehicle_knowledge = [
            {
                "id": "vehicle-water-sop",
                "title": "泡水车辆检修排查 SOP",
                "type": "标准作业流程 SOP",
                "category": "汽车涉水检修",
                "equipment": vehicle_device,
                "model": vehicle_model,
                "match": 90,
                "summary": "禁止启动、拖车转移、进气检查、油液检查、电气干燥、底盘清洗防锈、车内除湿消毒和复检验收。",
                "tags": ["泡水车", "涉水", "安全确认"],
            },
            {
                "id": "vehicle-water-electric",
                "title": "汽车电气系统进水检查清单",
                "type": "维修手册",
                "category": "电气系统",
                "equipment": vehicle_device,
                "model": vehicle_model,
                "match": 84,
                "summary": "重点检查 ECU、保险盒、线束插头、传感器、启动机、发电机和绝缘状态；不确定进水深度时保持待确认。",
                "tags": ["电气系统", "进水", "复检"],
            },
        ]
        return success_response({
            "query": query,
            "device_name": vehicle_device,
            "device_model": vehicle_model,
            "category": "汽车涉水检修",
            "maintenance_level": level,
            "modalities": ["text"] + (["image"] if images else []) + (["document"] if docs else []),
            "match_score": min(94, 84 + (6 if images else 0) + (3 if docs else 0)),
            "phenomenon_summary": "根据已知图片/文字线索，车辆处于积水或涉水场景；车型、具体水深、发动机是否进水、车内是否进水均需现场复核，不做无依据推断。",
            "risk": "high",
            "stop_advice": "不要立即启动发动机；先断电、拖车转移，并检查进气系统、油液、电气线束、制动系统和底盘。",
            "causes": ["道路积水导致底盘、轮毂和制动部件浸水", "积水可能进入进气、电气插头、车门密封或车内地毯", "长时间浸泡可能造成油液乳化、电气短路、轴承锈蚀或霉变"],
            "positions": ["空气滤芯/进气管/节气门", "机油尺/油底壳", "变速箱油/差速器油", "ECU/保险盒/线束插头", "刹车盘/刹车片/ABS轮速传感器", "底盘悬挂/轴承/排气管", "车内地毯/座椅底部/安全带卷收器"],
            "tools": ["拖车设备", "内窥镜", "万用表", "绝缘检测工具", "油液检查工具", "举升机", "除湿消毒设备"],
            "visual_findings": visual_findings or ["已接入车辆涉水现场图片；仅根据当前线索判断为泡水/涉水风险，具体受损范围待拆检确认。"],
            "attachments": attachments,
            "matched_manuals": vehicle_knowledge,
            "recommended_sop": [
                {"step": 1, "action": "现场拍照记录，禁止启动发动机"},
                {"step": 2, "action": "断开电瓶负极，拖车转移到维修点"},
                {"step": 3, "action": "拆检空气滤芯、进气管和节气门"},
                {"step": 4, "action": "检查机油、变速箱油和差速器油是否乳化"},
                {"step": 5, "action": "检查 ECU、保险盒、线束插头、传感器、启动机和发电机"},
                {"step": 6, "action": "检查制动系统、底盘、轴承、防尘套和排气管"},
                {"step": 7, "action": "车内除湿、消毒、除霉味并复检"},
            ],
            "safety": ["禁止涉水后直接启动", "先断电再拆检电气系统", "试车前必须完成油液和电气复检"],
            "audit": {"risk_level": "high", "must_check": ["启动前确认", "进气系统", "油液乳化", "电气绝缘", "制动复检", "现场复拍"], "auditor": "明鉴"},
        }, "车辆泡水/涉水检索完成")
    confidence = min(96, 82 + (6 if images else 0) + (3 if docs else 0) + (3 if model != "待确认型号" else 0))
    causes = [f"{fault}相关部件存在调整、磨损或连接异常", "运行参数或装配状态偏离手册要求", "需结合检测值排除供电、润滑或压力因素"]
    return success_response({
        "query": query, "device_name": device, "device_model": model, "category": category, "maintenance_level": level,
        "modalities": ["text", "equipment_model"] + (["image"] if images else []) + (["document"] if docs else []),
        "match_score": confidence, "phenomenon_summary": f"{device}（{model}）{fault}联合检索结果",
        "risk": "high" if any(word in query for word in ["冒烟", "漏电", "起火", "严重", "高温"]) else "medium",
        "stop_advice": "先完成安全隔离和数据记录，再按引用依据检修",
        "causes": causes, "positions": ["故障关联部件", "连接与紧固位置", "供电/润滑/压力回路"],
        "tools": ["万用表", "测温仪", "扭矩工具"], "visual_findings": visual_findings,
        "attachments": attachments, "matched_manuals": matched,
        "recommended_sop": steps, "safety": safety,
        "audit": {"risk_level": "medium", "must_check": ["安全隔离", "引用依据", "检测数据", "复测记录", "现场证据"], "auditor": "明鉴"},
    }, "多模态检索完成")


@yixiu_bp.route("/knowledge", methods=["GET"])
def knowledge():
    keyword = request.args.get("keyword", "").strip()
    items = _stored_knowledge() + _base_knowledge()
    if keyword:
        items = [item for item in items if keyword.lower() in json.dumps(item, ensure_ascii=False).lower()]
    return success_response({"items": items, "total": len(items)}, "知识资料获取成功")


@yixiu_bp.post("/knowledge/upload")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("knowledge.upload", "/api/yixiu/knowledge/upload")
def upload_knowledge_file():
    """知识库文件上传 → 切片 → embedding → 入库流水线"""
    if "file" not in request.files:
        return error_response(400, "请选择需要上传的知识文件")
    upload = request.files["file"]
    if not upload.filename:
        return error_response(400, "文件名为空")
    original_name = Path(upload.filename).name
    ext = Path(original_name).suffix.lower()
    from services.file_parser import supported_suffixes
    if ext not in supported_suffixes():
        return error_response(400, f"知识库仅支持解析: {', '.join(sorted(supported_suffixes()))}")
    file_id = f"file-{uuid.uuid4().hex[:12]}"
    stored_name = f"{file_id}{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "yixiu"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / secure_filename(stored_name)
    upload.save(path)
    form = request.form

    # 切片入库
    try:
        from services.file_parser import parse_file
        from services.rag_service import insert_chunks
        chunks = parse_file(path)
        if not chunks:
            return error_response(422, "文件无可提取文本（可能是扫描版 PDF 或空文件）")
        ingestion = insert_chunks(chunks, source=original_name)
    except Exception as exc:  # noqa: BLE001
        logger.error("知识文件入库失败 %s: %s", original_name, exc)
        return error_response(500, f"知识入库失败: {exc}")

    # 写入知识候选条目，待人工审核
    item_id = f"kb-{uuid.uuid4().hex[:12]}"
    title = form.get("title") or Path(original_name).stem
    summary = f"由 {original_name} 切片入库，共 {ingestion.get('inserted', 0)}/{ingestion.get('total', 0)} 块"
    tags = form.get("tags", "知识库导入,文件切片").split(",") if form.get("tags") else ["知识库导入", "文件切片"]
    content_preview = chunks[0][:500] if chunks else ""
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_knowledge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item_id, title, form.get("type", "知识库导入"), form.get("category", "资料"),
                form.get("equipment", ""), form.get("model", ""), summary,
                f"# {title}\n\n来源文件：{original_name}\n\n## 切片预览\n{content_preview}\n\n## 切片入库统计\n- 总块数：{ingestion.get('total', 0)}\n- 成功：{ingestion.get('inserted', 0)}\n- 失败：{ingestion.get('failed', 0)}\n",
                json.dumps(tags, ensure_ascii=False), original_name, "pending", "", "", _now(), _now(),
            ),
        )
        # 同步写一条文件记录，便于后续审计
        conn.execute(
            "INSERT INTO yixiu_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, original_name, stored_name, "application/octet-stream", "知识资料", form.get("category", "知识库导入"), "知识库", path.stat().st_size, form.get("equipment", ""), form.get("model", ""), form.get("uploader", "当前用户"), _now(), "待审核", f"切片入库 {ingestion.get('inserted', 0)}/{ingestion.get('total', 0)}", form.get("version", "v1.0"), "knowledge", json.dumps({"ingestion": ingestion, "chunks": len(chunks)}, ensure_ascii=False)),
        )
    return success_response({
        "knowledge_id": item_id, "file_id": file_id,
        "original_name": original_name, "chunks": len(chunks),
        "ingestion": ingestion, "preview": content_preview,
    }, "知识文件已切片入库，等待人工审核")


@yixiu_bp.get("/knowledge/similar")
def knowledge_similar():
    """向量相似度检索：基于 LightRAG hybrid 模式检索 top 命中块"""
    query = request.args.get("query", "").strip()
    if not query:
        return error_response(400, "检索 query 不能为空")
    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5
    mode = request.args.get("mode", "hybrid")
    try:
        from services.rag_service import search_similar
        hits = search_similar(query, limit=limit, mode=mode)
    except Exception as exc:  # noqa: BLE001
        logger.error("相似度检索失败: %s", exc)
        return error_response(500, f"检索失败: {exc}")
    return success_response({"query": query, "hits": hits, "total": len(hits), "mode": mode}, "相似度检索成功")


@yixiu_bp.post("/knowledge/update")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("knowledge.update", "/api/yixiu/knowledge/update")
def update_knowledge():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    summary = str(data.get("summary", "")).strip()
    if not title or not summary:
        return error_response(400, "知识标题和沉淀摘要不能为空")
    item_id = f"kb-{uuid.uuid4().hex[:12]}"
    tags = data.get("tags") or ["设备检修", "经验总结"]
    content = data.get("content") or f"# {title}\n\n## 适用范围\n- 设备：{data.get('equipment') or '待补充'}\n- 型号：{data.get('model') or '通用'}\n\n## 故障现象与经验\n{summary}\n\n## 安全与复核\n提交内容须经人工审核，确认引用依据、适用范围和安全风险后方可入库。"
    with _db() as conn:
        conn.execute("INSERT INTO yixiu_knowledge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (item_id, title, data.get("type", "历史故障案例"), data.get("category", "案例"), data.get("equipment", ""), data.get("model", ""), summary, content, json.dumps(tags, ensure_ascii=False), data.get("source", "一线经验提交"), "pending", "", "", _now(), _now()))
        row = conn.execute("SELECT * FROM yixiu_knowledge WHERE id=?", (item_id,)).fetchone()
    item = dict(row)
    item["tags"] = _json(item["tags"], [])
    item["reviewable"] = True
    return success_response(item, "知识条目已进入人工审核队列")


@yixiu_bp.put("/knowledge/<item_id>/review")
def review_knowledge(item_id: str):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "approved")
    if status not in {"approved", "rejected", "pending"}:
        return error_response(400, "无效的审核状态")
    correction = str(data.get("correction", "")).strip()
    tags = data.get("tags")
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_knowledge WHERE id=?", (item_id,)).fetchone()
        if not row:
            return error_response(404, "知识条目不存在")
        summary = correction or row["summary"]
        tag_value = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else row["tags"]
        conn.execute("UPDATE yixiu_knowledge SET status=?, reviewer=?, correction=?, summary=?, tags=?, updated_at=? WHERE id=?", (status, data.get("reviewer", "当前审核人"), correction, summary, tag_value, _now(), item_id))
    return success_response({"id": item_id, "status": status, "summary": summary, "tags": _json(tag_value, []), "reviewer": data.get("reviewer", "当前审核人"), "updated_at": _now(), "graph_synced": status == "approved"}, "审核结果已保存并同步知识状态")


@yixiu_bp.post("/assistant/chat")
def assistant_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    file_ids = data.get("fileIds") or []
    if not message and not file_ids:
        return error_response(400, "请输入问题或上传现场资料")
    attachments = []
    if file_ids:
        marks = ",".join("?" for _ in file_ids)
        with _db() as conn:
            attachments = [_file_dict(row) for row in conn.execute(f"SELECT * FROM yixiu_files WHERE id IN ({marks})", tuple(file_ids)).fetchall()]
    findings = []
    risks = []
    for item in attachments:
        analysis = item.get("analysis") or {}
        findings.extend(analysis.get("fault_signs") or analysis.get("findings") or [])
        risks.extend(analysis.get("risk_points") or [])
    context = f"已结合 {len(attachments)} 个附件进行分析。" if attachments else ""
    evidence = f"图像线索：{'、'.join(dict.fromkeys(findings))}。" if findings else ""
    risk_text = f"风险提示：{'、'.join(dict.fromkeys(risks))}。" if risks else ""
    answer = f"{context}{evidence}{risk_text}建议先确认设备型号和安全状态，再依据故障现象检索手册与相似案例；检测结果异常时再进入拆检或更换步骤。"
    return success_response({
        "response": answer,
        "modalities": ["text"] + (["image" if any(item.get("type") == "图片" for item in attachments) else "file"] if attachments else []),
        "findings": findings, "risk_points": risks, "attachments": attachments,
        "references": ["设备维修手册", "标准作业流程", "历史故障案例"], "agent": data.get("agent", "观微"),
    }, "智能检修助手已完成多模态分析")


@yixiu_bp.post("/audit")
def audit():
    data = request.get_json(silent=True) or {}
    checks = [
        ("引用手册或知识库依据", bool(data.get("references"))),
        ("完成安全确认与断电验电", bool(data.get("safety_checked"))),
        ("记录故障现象和检测数据", bool(data.get("measurements"))),
        ("完成复测确认", bool(data.get("retested"))),
        ("提交现场证据或报告", bool(data.get("report_ready"))),
    ]
    checklist = [{"item": item, "passed": passed} for item, passed in checks]
    score = round(sum(1 for _, passed in checks if passed) / len(checks) * 100)
    return success_response({"passed": score == 100, "score": score, "checklist": checklist, "suggestion": "可归档并提交知识沉淀" if score == 100 else "请补齐未通过项目后再提交验收"}, "核查完成")


@yixiu_bp.get("/contacts")
def contacts():
    with _db() as conn:
        rows = conn.execute("SELECT * FROM yixiu_contacts ORDER BY updated_at DESC").fetchall()
    stored = []
    for row in rows:
        item = dict(row)
        item["devices"] = _json(item.pop("devices", "[]"), [])
        item["currentTask"] = item.pop("current_task", "")
        item["employeeId"] = item.pop("employee_id", "")
        stored.append(item)
    merged = list(CONTACTS)
    known = {str(item.get("id")) for item in merged}
    merged.extend(item for item in stored if str(item.get("id")) not in known)
    return success_response({"contacts": merged, "total": len(merged)}, "contacts loaded")


@yixiu_bp.put("/contacts/<contact_id>")
def upsert_contact(contact_id: str):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return error_response("contact name is required", 400)
    now = _now()
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_contacts
               (id, account, name, avatar, position, department, specialty, phone,
                status, devices, current_task, workload, employee_id, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET account=excluded.account, name=excluded.name,
               avatar=excluded.avatar, position=excluded.position, department=excluded.department,
               specialty=excluded.specialty, phone=excluded.phone, status=excluded.status,
               devices=excluded.devices, current_task=excluded.current_task,
               workload=excluded.workload, employee_id=excluded.employee_id, updated_at=excluded.updated_at""",
            (contact_id, data.get("account"), name, data.get("avatar", ""),
             data.get("position", "maintenance worker"), data.get("department", "unassigned"),
             data.get("specialty", "maintenance"), data.get("phone", ""), data.get("status", "online"),
             json.dumps(data.get("devices", []), ensure_ascii=False), data.get("currentTask", ""),
             int(data.get("workload", 0) or 0), data.get("employeeId", ""), now),
        )
    return success_response({**data, "id": contact_id, "updated_at": now}, "contact synchronized")


@yixiu_bp.get("/conversations/<conversation_id>/messages")
def conversation_messages(conversation_id: str):
    with _db() as conn:
        rows = conn.execute("SELECT * FROM yixiu_messages WHERE conversation_id=? ORDER BY created_at ASC LIMIT 500", (conversation_id,)).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["attachment"] = _json(item.pop("attachment_json", "{}"), {})
        item["card"] = _json(item.pop("card_json", "{}"), {})
        items.append(item)
    return success_response({"messages": items}, "messages loaded")


@yixiu_bp.post("/conversations/<conversation_id>/messages")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("conversation.message", "/api/yixiu/conversations/messages")
def create_conversation_message(conversation_id: str):
    data = request.get_json(silent=True) or {}
    if not str(data.get("text", "")).strip() and not data.get("attachment") and not data.get("card"):
        return error_response("message content is required", 400)
    message_id = str(data.get("id") or uuid.uuid4())
    created_at = str(data.get("created_at") or _now())
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_messages
               (id, conversation_id, sender_id, sender_name, message_type, text,
                attachment_json, card_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (message_id, conversation_id, data.get("sender_id"), data.get("sender_name"),
             data.get("message_type", "text"), data.get("text", ""),
             json.dumps(data.get("attachment") or {}, ensure_ascii=False),
             json.dumps(data.get("card") or {}, ensure_ascii=False), created_at),
        )
    return success_response({**data, "id": message_id, "conversation_id": conversation_id, "created_at": created_at}, "message created")


def _ensure_knowledge_in_db(conn: sqlite3.Connection, item_id: str):
    """确保知识条目存在于数据库中。如果来自基础JSON，则复制到数据库。"""
    row = conn.execute("SELECT * FROM yixiu_knowledge WHERE id=?", (item_id,)).fetchone()
    if row:
        return row
    for item in _base_knowledge():
        if str(item.get("id")) == str(item_id):
            raw_content = item.get("content", "")
            content_str = "\n".join(raw_content) if isinstance(raw_content, list) else str(raw_content)
            summary = item.get("summary") or content_str[:200]
            conn.execute(
                "INSERT INTO yixiu_knowledge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(item_id), item.get("title", "未命名"), item.get("type", "手册"),
                 item.get("category", "知识条目"), item.get("equipment_category") or item.get("equipment", ""),
                 item.get("equipment_model") or item.get("model", ""), summary,
                 content_str, json.dumps(item.get("tags", item.get("keywords", [])), ensure_ascii=False),
                 item.get("source", "基础知识库"), "approved", "", "", _now(), _now()),
            )
            return conn.execute("SELECT * FROM yixiu_knowledge WHERE id=?", (item_id,)).fetchone()
    return None


@yixiu_bp.put("/knowledge/<item_id>/content")
def edit_knowledge_content(item_id: str):
    """编辑保存知识条目内容，自动生成版本快照。"""
    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return error_response(400, "内容不能为空")
    with _db() as conn:
        row = _ensure_knowledge_in_db(conn, item_id)
        if not row:
            return error_response(404, "知识条目不存在")
        current_version = conn.execute(
            "SELECT MAX(version) as v FROM yixiu_knowledge_versions WHERE knowledge_id=?", (item_id,)
        ).fetchone()["v"] or 1
        new_version = current_version + 1
        title = data.get("title") or row["title"]
        tags = data.get("tags")
        tag_value = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else row["tags"]
        equipment = data.get("equipment") or row["equipment"]
        model = data.get("model") or row["model"]
        summary = data.get("summary") or (content[:200] if content else row["summary"])
        conn.execute(
            "UPDATE yixiu_knowledge SET title=?, content=?, tags=?, equipment=?, model=?, summary=?, status=?, updated_at=? WHERE id=?",
            (title, content, tag_value, equipment, model, summary, "pending", _now(), item_id),
        )
        version_id = f"ver-{uuid.uuid4().hex[:12]}"
        conn.execute(
            "INSERT INTO yixiu_knowledge_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (version_id, item_id, new_version, content, title,
             data.get("change_summary", ""), data.get("editor_id", ""),
             data.get("editor_name", "当前用户"), _now()),
        )
        updated = conn.execute("SELECT * FROM yixiu_knowledge WHERE id=?", (item_id,)).fetchone()
    item = dict(updated)
    item["tags"] = _json(item["tags"], [])
    item["version"] = new_version
    item["reviewable"] = True
    return success_response(item, "知识内容已保存，版本 v%d" % new_version)


@yixiu_bp.get("/knowledge/<item_id>/versions")
def knowledge_versions(item_id: str):
    """获取知识条目的版本历史。"""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM yixiu_knowledge_versions WHERE knowledge_id=? ORDER BY version DESC",
            (item_id,),
        ).fetchall()
    items = [dict(row) for row in rows]
    return success_response({"versions": items, "total": len(items)}, "版本历史获取成功")


@yixiu_bp.get("/knowledge/<item_id>/versions/<version_id>")
def knowledge_version_detail(item_id: str, version_id: str):
    """获取某个版本的详细内容。"""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM yixiu_knowledge_versions WHERE id=? AND knowledge_id=?",
            (version_id, item_id),
        ).fetchone()
    if not row:
        return error_response(404, "版本不存在")
    return success_response(dict(row), "版本内容获取成功")


@yixiu_bp.post("/knowledge/<item_id>/versions/<version_id>/restore")
def restore_knowledge_version(item_id: str, version_id: str):
    """恢复到指定版本。"""
    with _db() as conn:
        row = _ensure_knowledge_in_db(conn, item_id)
        if not row:
            return error_response(404, "知识条目不存在")
        ver = conn.execute(
            "SELECT * FROM yixiu_knowledge_versions WHERE id=? AND knowledge_id=?",
            (version_id, item_id),
        ).fetchone()
        if not ver:
            return error_response(404, "版本不存在")
        current_version = conn.execute(
            "SELECT MAX(version) as v FROM yixiu_knowledge_versions WHERE knowledge_id=?", (item_id,)
        ).fetchone()["v"] or 1
        new_version = current_version + 1
        conn.execute(
            "UPDATE yixiu_knowledge SET content=?, title=?, status=?, updated_at=? WHERE id=?",
            (ver["content_snapshot"], ver["title_snapshot"], "pending", _now(), item_id),
        )
        restore_id = f"ver-{uuid.uuid4().hex[:12]}"
        conn.execute(
            "INSERT INTO yixiu_knowledge_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (restore_id, item_id, new_version, ver["content_snapshot"], ver["title_snapshot"],
             "恢复到 v%d" % ver["version"], "", "当前用户", _now()),
        )
    return success_response({"id": item_id, "restored_version": ver["version"], "new_version": new_version}, "已恢复到 v%d" % ver["version"])


@yixiu_bp.get("/knowledge/<item_id>/collaborators")
def knowledge_collaborators(item_id: str):
    """获取知识条目的协作成员列表。"""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM yixiu_knowledge_collaborators WHERE knowledge_id=? ORDER BY last_active_at DESC",
            (item_id,),
        ).fetchall()
    items = [dict(row) for row in rows]
    return success_response({"collaborators": items, "total": len(items)}, "协作成员获取成功")


@yixiu_bp.post("/knowledge/<item_id>/collaborators")
def add_knowledge_collaborator(item_id: str):
    """添加协作成员。"""
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id") or data.get("userId") or data.get("name") or "guest")
    user_name = str(data.get("user_name") or data.get("userName") or data.get("name") or "新成员")
    role = str(data.get("role", "editor"))
    now = _now()
    collab_id = f"col-{uuid.uuid4().hex[:10]}"
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_knowledge_collaborators VALUES (?, ?, ?, ?, ?, ?, ?)",
            (collab_id, item_id, user_id, user_name, role, now, 1),
        )
    return success_response({
        "id": collab_id, "knowledge_id": item_id,
        "user_id": user_id, "user_name": user_name, "role": role,
    }, "协作成员添加成功")


@yixiu_bp.post("/knowledge/<item_id>/presence")
def knowledge_presence(item_id: str):
    """上报在线状态（心跳）。"""
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id") or data.get("userId") or "guest")
    user_name = str(data.get("user_name") or data.get("userName") or "当前用户")
    now = _now()
    with _db() as conn:
        existing = conn.execute(
            "SELECT * FROM yixiu_knowledge_collaborators WHERE knowledge_id=? AND user_id=?",
            (item_id, user_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE yixiu_knowledge_collaborators SET is_online=1, last_active_at=? WHERE id=?",
                (now, existing["id"]),
            )
        else:
            collab_id = f"col-{uuid.uuid4().hex[:10]}"
            conn.execute(
                "INSERT INTO yixiu_knowledge_collaborators VALUES (?, ?, ?, ?, ?, ?, ?)",
                (collab_id, item_id, user_id, user_name, "editor", now, 1),
            )
        rows = conn.execute(
            "SELECT * FROM yixiu_knowledge_collaborators WHERE knowledge_id=? AND is_online=1",
            (item_id,),
        ).fetchall()
    online = [dict(row) for row in rows]
    return success_response({"online_members": online, "count": len(online)}, "在线状态已更新")


@yixiu_bp.route("/knowledge/<item_id>/links", methods=["GET", "POST"])
def knowledge_links(item_id: str):
    """获取或添加知识条目的板块联动关联。"""
    if request.method == "GET":
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM yixiu_knowledge_links WHERE knowledge_id=? ORDER BY created_at DESC",
                (item_id,),
            ).fetchall()
        items = [dict(row) for row in rows]
        return success_response({"links": items, "total": len(items)}, "联动关联获取成功")

    data = request.get_json(silent=True) or {}
    link_type = str(data.get("link_type", "")).strip()
    target_id = str(data.get("target_id", "")).strip()
    target_title = str(data.get("target_title", "")).strip()
    if link_type not in {"task", "knowledge", "file"} or not target_id:
        return error_response(400, "关联类型和目标ID不能为空")
    link_id = f"link-{uuid.uuid4().hex[:10]}"
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_knowledge_links VALUES (?, ?, ?, ?, ?, ?)",
            (link_id, item_id, link_type, target_id, target_title, _now()),
        )
    return success_response({"id": link_id, "knowledge_id": item_id, "link_type": link_type,
                             "target_id": target_id, "target_title": target_title, "created_at": _now()}, "关联添加成功")


@yixiu_bp.route("/knowledge/<item_id>/links/<link_id>", methods=["DELETE"])
def remove_knowledge_link(item_id: str, link_id: str):
    """移除板块联动关联。"""
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_knowledge_links WHERE id=? AND knowledge_id=?", (link_id, item_id)).fetchone()
        if not row:
            return error_response(404, "关联不存在")
        conn.execute("DELETE FROM yixiu_knowledge_links WHERE id=?", (link_id,))
    return success_response({"id": link_id}, "关联已移除")


@yixiu_bp.get("/knowledge/linked/<link_type>/<target_id>")
def linked_knowledge(link_type: str, target_id: str):
    """反向查询：根据关联类型和目标ID查找关联的知识条目。"""
    with _db() as conn:
        rows = conn.execute(
            """SELECT k.*, l.target_id, l.target_title, l.id as link_id
               FROM yixiu_knowledge k
               JOIN yixiu_knowledge_links l ON k.id = l.knowledge_id
               WHERE l.link_type=? AND l.target_id=?""",
            (link_type, target_id),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["tags"] = _json(item.get("tags"), [])
        items.append(item)
    return success_response({"items": items, "total": len(items)}, "关联知识获取成功")


@yixiu_bp.route("/templates")
def list_templates():
    keyword = request.args.get("keyword", "").strip()
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM yixiu_doc_templates WHERE name LIKE ? OR category LIKE ? ORDER BY is_builtin DESC, created_at DESC",
            (f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["skeleton"] = _json(item.get("skeleton_json"), {})
        items.append(item)
    return success_response({"templates": items, "total": len(items)})


@yixiu_bp.route("/templates/<template_id>")
def get_template(template_id):
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_doc_templates WHERE id=?", (template_id,)).fetchone()
    if not row:
        return error_response(404, "模板不存在")
    item = dict(row)
    item["skeleton"] = _json(item.get("skeleton_json"), {})
    return success_response(item)


@yixiu_bp.route("/templates", methods=["POST"])
def create_template():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return error_response(400, "模板名称不能为空")
    template_id = f"tpl-{uuid.uuid4().hex[:10]}"
    skeleton = data.get("skeleton", {})
    with _db() as conn:
        conn.execute(
            "INSERT INTO yixiu_doc_templates VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (template_id, name, str(data.get("icon", "📝")),
             str(data.get("category", "通用")), str(data.get("description", "")),
             json.dumps(skeleton, ensure_ascii=False), _now()),
        )
    return success_response({"id": template_id, "name": name}, "模板创建成功")


@yixiu_bp.route("/templates/<template_id>", methods=["DELETE"])
def delete_template(template_id):
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_doc_templates WHERE id=?", (template_id,)).fetchone()
        if not row:
            return error_response(404, "模板不存在")
        if row["is_builtin"]:
            return error_response(403, "内置模板不可删除")
        conn.execute("DELETE FROM yixiu_doc_templates WHERE id=?", (template_id,))
    return success_response({"id": template_id}, "模板已删除")


@yixiu_bp.get("/aios/platform")
def aios_platform():
    return success_response(_aios_platform_snapshot(), "天工 AIOS 平台能力获取成功")


@yixiu_bp.route("/aios/agents", methods=["GET", "POST"])
def aios_agents_manage():
    if request.method == "GET":
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_agent_configs ORDER BY id").fetchall()
        return success_response({"agents": [_agent_config_dict(row) for row in rows]}, "AIOS 智能体配置获取成功")

    data = request.get_json(silent=True) or {}
    agent_id = _agent_key(str(data.get("id") or data.get("agent_id") or f"agent-{uuid.uuid4().hex[:8]}"))
    name = str(data.get("name") or _agent_by_id(agent_id).get("name") or "新智能体").strip()
    role = str(data.get("role") or data.get("description") or "").strip()
    tools = data.get("tools") if isinstance(data.get("tools"), list) else AGENT_TOOL_ALLOWLISTS.get(agent_id, [])
    knowledge_ids = data.get("knowledge_ids") if isinstance(data.get("knowledge_ids"), list) else []
    memory_keys = data.get("memory_keys") if isinstance(data.get("memory_keys"), list) else ["role", "duty", "capabilities"]
    now = _now()
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_agent_configs
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, role=excluded.role,
                 model_provider=excluded.model_provider, model_name=excluded.model_name,
                 prompt=excluded.prompt, tools_json=excluded.tools_json,
                 knowledge_ids_json=excluded.knowledge_ids_json,
                 memory_keys_json=excluded.memory_keys_json,
                 database_scope=excluded.database_scope, status=excluded.status,
                 updated_at=excluded.updated_at""",
            (
                agent_id,
                name,
                role,
                str(data.get("model_provider") or "qwen"),
                str(data.get("model_name") or "qwen-local-or-cloud"),
                str(data.get("prompt") or AGENT_PROMPTS.get(agent_id, "")),
                json.dumps(tools, ensure_ascii=False),
                json.dumps(knowledge_ids, ensure_ascii=False),
                json.dumps(memory_keys, ensure_ascii=False),
                str(data.get("database_scope") or "read_business"),
                str(data.get("status") or "enabled"),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_agent_configs WHERE id=?", (agent_id,)).fetchone()
    return success_response(_agent_config_dict(row), "AIOS 智能体配置已保存")


@yixiu_bp.route("/aios/teams", methods=["GET", "POST"])
def aios_teams():
    if request.method == "GET":
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_agent_teams ORDER BY updated_at DESC").fetchall()
        return success_response({"teams": [_team_dict(row) for row in rows]}, "AIOS Team 获取成功")

    data = request.get_json(silent=True) or {}
    team_id = str(data.get("id") or f"team-{uuid.uuid4().hex[:10]}")
    members = data.get("members") if isinstance(data.get("members"), list) else []
    workflow = data.get("workflow") if isinstance(data.get("workflow"), dict) else {}
    now = _now()
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_agent_teams
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, description=excluded.description,
                 lead_agent_id=excluded.lead_agent_id, members_json=excluded.members_json,
                 workflow_json=excluded.workflow_json, updated_at=excluded.updated_at""",
            (
                team_id,
                str(data.get("name") or "自定义 AIOS Team"),
                str(data.get("description") or ""),
                _agent_key(str(data.get("lead_agent_id") or "tiangong")),
                json.dumps(members, ensure_ascii=False),
                json.dumps(workflow, ensure_ascii=False),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_agent_teams WHERE id=?", (team_id,)).fetchone()
    return success_response(_team_dict(row), "AIOS Team 已保存")


@yixiu_bp.route("/aios/sessions", methods=["GET", "POST"])
def aios_sessions():
    if request.method == "GET":
        limit = min(int(request.args.get("limit", 30)), 100)
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_conversation_sessions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return success_response({"sessions": [_session_dict(row) for row in rows], "total": len(rows)}, "AIOS 会话获取成功")

    data = request.get_json(silent=True) or {}
    now = _now()
    session_id = str(data.get("id") or f"session-{uuid.uuid4().hex[:12]}")
    context = data.get("context") if isinstance(data.get("context"), dict) else {}
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_conversation_sessions
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 title=excluded.title, channel=excluded.channel,
                 active_agent_id=excluded.active_agent_id,
                 context_json=excluded.context_json, status=excluded.status,
                 updated_at=excluded.updated_at""",
            (
                session_id,
                str(data.get("user_id") or "current-user"),
                str(data.get("title") or "一修检修会话"),
                str(data.get("channel") or "web"),
                _agent_key(str(data.get("active_agent_id") or "tiangong")),
                json.dumps(context, ensure_ascii=False),
                str(data.get("status") or "active"),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_conversation_sessions WHERE id=?", (session_id,)).fetchone()
    return success_response(_session_dict(row), "AIOS 会话已保存")


@yixiu_bp.route("/aios/memory", methods=["GET", "POST"])
def aios_memory():
    if request.method == "GET":
        agent_id = request.args.get("agent_id", "").strip()
        where = "WHERE agent_id=?" if agent_id else ""
        params = (_agent_key(agent_id),) if agent_id else ()
        with _db() as conn:
            rows = conn.execute(f"SELECT * FROM yixiu_agent_memory {where} ORDER BY updated_at DESC", params).fetchall()
        memories = []
        for row in rows:
            item = dict(row)
            item["tags"] = _json(item.get("tags"), [])
            memories.append(item)
        return success_response({"memories": memories, "total": len(memories)}, "AIOS 长期记忆获取成功")

    data = request.get_json(silent=True) or {}
    agent_id = _agent_key(str(data.get("agent_id") or "tiangong"))
    memory_key = str(data.get("memory_key") or data.get("key") or "").strip()
    memory_value = str(data.get("memory_value") or data.get("value") or "").strip()
    if not memory_key or not memory_value:
        return error_response(400, "记忆键和值不能为空")
    memory_id = f"mem-{agent_id}-{memory_key}"
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_agent_memory VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(agent_id, memory_key) DO UPDATE SET
                 memory_value=excluded.memory_value, tags=excluded.tags, updated_at=excluded.updated_at""",
            (
                memory_id,
                agent_id,
                memory_key,
                memory_value,
                json.dumps(data.get("tags") if isinstance(data.get("tags"), list) else ["manual"], ensure_ascii=False),
                _now(),
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_agent_memory WHERE agent_id=? AND memory_key=?", (agent_id, memory_key)).fetchone()
    item = dict(row)
    item["tags"] = _json(item.get("tags"), [])
    return success_response(item, "AIOS 长期记忆已保存")


@yixiu_bp.route("/aios/approvals", methods=["GET", "POST"])
def aios_approvals():
    if request.method == "GET":
        status = request.args.get("status", "").strip()
        where = "WHERE status=?" if status else ""
        params = (status,) if status else ()
        with _db() as conn:
            rows = conn.execute(f"SELECT * FROM yixiu_aios_approvals {where} ORDER BY created_at DESC LIMIT 80", params).fetchall()
        return success_response({"approvals": [_approval_dict(row) for row in rows], "total": len(rows)}, "AIOS 审批获取成功")

    data = request.get_json(silent=True) or {}
    approval_id = str(data.get("id") or f"apr-{uuid.uuid4().hex[:12]}")
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_aios_approvals
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                approval_id,
                str(data.get("run_id") or ""),
                str(data.get("step_key") or ""),
                str(data.get("action") or ""),
                str(data.get("title") or "智能体请求执行"),
                str(data.get("detail") or ""),
                _agent_key(str(data.get("requester_agent_id") or "tiangong")),
                str(data.get("status") or "pending"),
                str(data.get("requested_by") or "AIOS"),
                "",
                "",
                _now(),
                "",
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_aios_approvals WHERE id=?", (approval_id,)).fetchone()
    return success_response(_approval_dict(row), "AIOS 审批已创建")


@yixiu_bp.post("/aios/approvals/<approval_id>/decision")
def aios_approval_decision(approval_id: str):
    data = request.get_json(silent=True) or {}
    decision = str(data.get("decision") or data.get("status") or "").strip()
    if decision not in {"approved", "rejected"}:
        return error_response(400, "审批结果必须是 approved 或 rejected")
    with _db() as conn:
        row = conn.execute("SELECT * FROM yixiu_aios_approvals WHERE id=?", (approval_id,)).fetchone()
        if not row:
            return error_response(404, "审批记录不存在")
        conn.execute(
            "UPDATE yixiu_aios_approvals SET status=?, decided_by=?, decision_note=?, decided_at=? WHERE id=?",
            (decision, str(data.get("decided_by") or "当前用户"), str(data.get("note") or ""), _now(), approval_id),
        )
        updated = conn.execute("SELECT * FROM yixiu_aios_approvals WHERE id=?", (approval_id,)).fetchone()
    return success_response(_approval_dict(updated), "AIOS 审批已处理")


@yixiu_bp.post("/aios/cancel")
def aios_cancel():
    data = request.get_json(silent=True) or {}
    run_id = str(data.get("run_id") or "").strip()
    if not run_id:
        return error_response(400, "缺少 AIOS 运行ID")
    reason = str(data.get("reason") or "用户取消长任务").strip()
    with _db() as conn:
        run = _load_aios_run(conn, run_id)
        if not run:
            return error_response(404, "AIOS 运行记录不存在")
        plan = run.get("plan") or {}
        for step in plan.get("steps", []):
            if step.get("state") not in {"done", "failed", "skipped", "compensated"}:
                step["state"] = "skipped"
                step["last_error"] = reason
                step["updated_at"] = _now()
        plan["workflow_state"] = "cancelled"
        plan["progress"] = run.get("progress", 0)
        plan["updated_at"] = _now()
        conn.execute(
            "UPDATE yixiu_aios_runs SET plan_json=?, status='cancelled', updated_at=? WHERE id=?",
            (json.dumps(plan, ensure_ascii=False), _now(), run_id),
        )
        conn.execute(
            "UPDATE yixiu_aios_queue SET state='cancelled', updated_at=? WHERE run_id=? AND state NOT IN ('done','failed')",
            (_now(), run_id),
        )
        conn.execute(
            "UPDATE yixiu_aios_approvals SET status='rejected', decision_note=?, decided_by=?, decided_at=? WHERE run_id=? AND status='pending'",
            (reason, str(data.get("decided_by") or "当前用户"), _now(), run_id),
        )
        event = _record_agent_event(
            conn,
            "tiangong",
            "AIOS 长任务已取消",
            reason,
            event_type="cancel",
            status="cancelled",
            payload={"run_id": run_id, "reason": reason},
            run_id=run_id,
        )
        updated = _load_aios_run(conn, run_id)
    return success_response({"run": updated, "event": event}, "AIOS 长任务已取消")


@yixiu_bp.route("/aios/service-accounts", methods=["GET", "POST"])
def aios_service_accounts():
    if request.method == "GET":
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_service_accounts ORDER BY created_at DESC").fetchall()
        return success_response({"service_accounts": [_service_account_dict(row) for row in rows]}, "AIOS 服务账号获取成功")

    data = request.get_json(silent=True) or {}
    account_id = str(data.get("id") or f"svc-{uuid.uuid4().hex[:10]}")
    scopes = data.get("scopes") if isinstance(data.get("scopes"), list) else ["agent:invoke", "task:read", "knowledge:read"]
    now = _now()
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_service_accounts
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, role=excluded.role,
                 scopes_json=excluded.scopes_json, enabled=excluded.enabled""",
            (
                account_id,
                str(data.get("name") or "AIOS 服务账号"),
                str(data.get("role") or "service"),
                json.dumps(scopes, ensure_ascii=False),
                1 if data.get("enabled", True) else 0,
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_service_accounts WHERE id=?", (account_id,)).fetchone()
    return success_response(_service_account_dict(row), "AIOS 服务账号已保存")


@yixiu_bp.get("/aios/trace")
def aios_trace():
    run_id = request.args.get("run_id", "").strip()
    with _db() as conn:
        if run_id:
            run = _load_aios_run(conn, run_id)
            if not run:
                return error_response(404, "AIOS 运行记录不存在")
            approvals = [
                _approval_dict(row)
                for row in conn.execute("SELECT * FROM yixiu_aios_approvals WHERE run_id=? ORDER BY created_at ASC", (run_id,)).fetchall()
            ]
            return success_response({"run": run, "approvals": approvals, "tree": _trace_tree(run, approvals)}, "AIOS Trace 获取成功")
        runs = [
            _load_aios_run(conn, row["id"])
            for row in conn.execute("SELECT id FROM yixiu_aios_runs ORDER BY updated_at DESC LIMIT 10").fetchall()
        ]
        compact = [item for item in runs if item]
    return success_response({"runs": compact, "total": len(compact)}, "AIOS Trace 列表获取成功")


@yixiu_bp.route("/aios/channels", methods=["GET", "POST"])
def aios_channels():
    if request.method == "GET":
        with _db() as conn:
            rows = conn.execute("SELECT * FROM yixiu_aios_channels ORDER BY id").fetchall()
        return success_response({"channels": [_channel_dict(row) for row in rows]}, "AIOS 渠道获取成功")

    data = request.get_json(silent=True) or {}
    channel_id = str(data.get("id") or f"channel-{uuid.uuid4().hex[:10]}")
    now = _now()
    with _db() as conn:
        conn.execute(
            """INSERT INTO yixiu_aios_channels
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, channel_type=excluded.channel_type,
                 endpoint=excluded.endpoint, enabled=excluded.enabled,
                 agent_id=excluded.agent_id, config_json=excluded.config_json,
                 updated_at=excluded.updated_at""",
            (
                channel_id,
                str(data.get("name") or "自定义渠道"),
                str(data.get("channel_type") or "web"),
                str(data.get("endpoint") or ""),
                1 if data.get("enabled", True) else 0,
                _agent_key(str(data.get("agent_id") or "tiangong")),
                json.dumps(data.get("config") if isinstance(data.get("config"), dict) else {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM yixiu_aios_channels WHERE id=?", (channel_id,)).fetchone()
    return success_response(_channel_dict(row), "AIOS 渠道已保存")


@yixiu_bp.post("/aios/plan")
@require_jwt_roles(AUDIT_ROLES)
def aios_plan():
    data = request.get_json(silent=True) or {}
    plan = _aios_plan(
        goal=str(data.get("goal") or data.get("message") or "").strip(),
        mode=str(data.get("mode") or "auto").strip(),
        task_id=str(data.get("task_id") or "").strip(),
    )
    return success_response(plan, "AIOS 执行计划已生成")


@yixiu_bp.post("/aios/execute")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("aios.execute", "/api/yixiu/aios/execute")
def aios_execute():
    data = request.get_json(silent=True) or {}
    plan = data.get("plan")
    plan_id = str(data.get("plan_id") or "").strip()
    if not plan and plan_id:
        with _db() as conn:
            row = conn.execute("SELECT * FROM yixiu_aios_runs WHERE id=?", (plan_id,)).fetchone()
        if row:
            plan = _json(row["plan_json"], {})
    if not plan:
        plan = _aios_plan(str(data.get("goal") or data.get("message") or "").strip(), str(data.get("mode") or "auto").strip(), str(data.get("task_id") or "").strip())
    if not isinstance(plan, dict) or not plan.get("steps"):
        return error_response(400, "执行计划为空，无法执行")

    plan = attach_state_machine(plan)
    transition_event = str(data.get("event") or "").strip()
    if transition_event in {"pause", "approve", "fail", "compensate"}:
        step_key = str(data.get("step_key") or "").strip()
        if not step_key:
            return error_response(400, "state transition requires step_key")
        try:
            plan, node = transition_step(
                plan,
                step_key,
                transition_event,
                error=str(data.get("error") or "").strip(),
                approvals=data.get("approvals") or {},
            )
        except ValueError as exc:
            return error_response(400, str(exc))
        steps = plan.get("steps", [])
        progress = round(sum(1 for item in steps if item.get("state") == "done") / max(len(steps), 1) * 100)
        plan["progress"] = progress
        status = plan.get("workflow_state") or "running"
        run_id = plan.get("id") or plan_id or f"aios-{uuid.uuid4().hex[:12]}"
        plan["id"] = run_id
        with _db() as conn:
            row = conn.execute("SELECT id FROM yixiu_aios_runs WHERE id=?", (run_id,)).fetchone()
            if row:
                conn.execute("UPDATE yixiu_aios_runs SET plan_json=?, status=?, progress=?, updated_at=? WHERE id=?", (json.dumps(plan, ensure_ascii=False), status, progress, _now(), run_id))
            else:
                conn.execute("INSERT INTO yixiu_aios_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (run_id, plan.get("goal", ""), plan.get("mode", "auto"), json.dumps(plan, ensure_ascii=False), status, progress, "{}", _now(), _now()))
            _sync_aios_queue(conn, run_id, plan)
            _record_agent_event(
                conn,
                (next((step.get("agent", {}) for step in plan.get("steps", []) if step.get("key") == step_key), {}) or {}).get("id", "tiangong"),
                f"AIOS 状态变更：{transition_event}",
                f"步骤 {step_key} 已切换为 {node.get('state')}。",
                event_type="transition",
                status=node.get("state", status),
                payload={"step_key": step_key, "event": transition_event, "node": node},
                run_id=run_id,
            )
        return success_response({"run_id": run_id, "status": status, "progress": progress, "plan": plan, "node": node}, "AIOS state transition completed")

    steps = plan.get("steps", [])
    approvals = data.get("approvals") or {}
    if data.get("approve_all"):
        approvals = {**{item.get("key"): True for item in steps if item.get("requires_approval")}, **approvals}
    execute_all = bool(data.get("execute_all", False))
    step_key = str(data.get("step_key") or "").strip()
    commit = data.get("commit", True) is not False
    artifacts: dict[str, dict] = {}
    selected: list[dict] = []

    while True:
        ready_steps = next_executable_steps(plan, approvals=approvals)
        if not ready_steps:
            if execute_all:
                blocked_waiting = False
                for item in plan.get("steps", []):
                    if not item.get("requires_approval") or item.get("state") in {"done", "failed", "skipped"}:
                        continue
                    if item.get("approved") or approvals.get(item.get("key")):
                        continue
                    try:
                        plan, _ = transition_step(plan, item["key"], "execute", approvals=approvals)
                        blocked_waiting = True
                        break
                    except ValueError:
                        continue
                if blocked_waiting:
                    break
            break
        if not execute_all:
            candidate = next((item for item in ready_steps if item.get("key") == step_key), None)
            if step_key and not candidate:
                return error_response(409, "请求的 AIOS 步骤暂不可执行，可能依赖未完成或需要审批")
            ready_steps = [candidate] if candidate else ready_steps[:1]
        for step in ready_steps:
            selected.append(step)
            try:
                plan, node = transition_step(plan, step["key"], "execute", approvals=approvals)
                if node.get("state") != "running":
                    artifacts[step["key"]] = {"summary": node.get("last_error", "步骤暂不可执行"), "state": node.get("state")}
                    continue
                if commit:
                    with _db() as conn:
                        _record_agent_event(
                            conn,
                            step.get("agent", {}).get("id", "tiangong"),
                            f"开始执行：{step.get('title')}",
                            step.get("tool_description") or step.get("expected_output") or "",
                            event_type="step_start",
                            status="running",
                            payload={"step_key": step.get("key"), "action": step.get("action"), "input": step.get("input")},
                            run_id=plan.get("id", ""),
                        )
                result = _aios_execute_action(step, plan.get("snapshot") or {}, commit=commit)
                step["result"] = result
                step["executed_at"] = _now()
                artifacts[step["key"]] = result
                if commit and (result.get("needs_confirmation") or step.get("requires_approval")):
                    with _db() as conn:
                        approval = _ensure_aios_approval(conn, plan.get("id", ""), step, result.get("summary", ""))
                        result["approval"] = approval
                        _record_agent_event(
                            conn,
                            step.get("agent", {}).get("id", "tiangong"),
                            f"等待人工确认：{step.get('title')}",
                            approval.get("title", ""),
                            event_type="approval_requested",
                            status="waiting_approval",
                            payload={"step_key": step.get("key"), "approval": approval},
                            run_id=plan.get("id", ""),
                        )
                plan, _ = transition_step(plan, step["key"], "complete")
                if commit:
                    with _db() as conn:
                        _record_agent_event(
                            conn,
                            step.get("agent", {}).get("id", "tiangong"),
                            f"完成执行：{step.get('title')}",
                            result.get("summary", ""),
                            event_type="step_done",
                            status="done",
                            payload={"step_key": step.get("key"), "action": step.get("action"), "result": result},
                            run_id=plan.get("id", ""),
                        )
            except Exception as exc:  # noqa: BLE001
                plan, _ = transition_step(plan, step["key"], "fail", error=str(exc))
                artifacts[step["key"]] = {"summary": "AIOS 步骤执行失败", "error": str(exc)}
                if commit:
                    with _db() as conn:
                        _record_agent_event(
                            conn,
                            step.get("agent", {}).get("id", "tiangong"),
                            f"执行失败：{step.get('title')}",
                            str(exc),
                            event_type="step_failed",
                            status="failed",
                            payload={"step_key": step.get("key"), "action": step.get("action"), "error": str(exc)},
                            run_id=plan.get("id", ""),
                        )
        if not execute_all:
            break

    if not selected:
        return error_response(409, "没有可执行的 AIOS 步骤，可能依赖未完成或需要审批")

    steps = plan.get("steps", [])
    done = sum(1 for item in steps if item.get("state") == "done")
    progress = round(done / max(len(steps), 1) * 100)
    plan["progress"] = progress
    plan["updated_at"] = _now()
    status = plan.get("workflow_state") or ("completed" if progress == 100 else "running")
    run_id = plan.get("id") or f"aios-{uuid.uuid4().hex[:12]}"
    plan["id"] = run_id
    with _db() as conn:
        row = conn.execute("SELECT id FROM yixiu_aios_runs WHERE id=?", (run_id,)).fetchone()
        payload = (json.dumps(plan, ensure_ascii=False), status, progress, json.dumps(artifacts, ensure_ascii=False), _now())
        if row:
            conn.execute("UPDATE yixiu_aios_runs SET plan_json=?, status=?, progress=?, artifacts_json=?, updated_at=? WHERE id=?", (*payload, run_id))
        else:
            conn.execute("INSERT INTO yixiu_aios_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (run_id, plan.get("goal", ""), plan.get("mode", "auto"), payload[0], status, progress, payload[3], _now(), _now()))
        queue = _sync_aios_queue(conn, run_id, plan, artifacts)
        events = [
            _agent_event_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_agent_events WHERE run_id=? ORDER BY created_at ASC", (run_id,)).fetchall()
        ]
        approval_rows = [
            _approval_dict(row)
            for row in conn.execute("SELECT * FROM yixiu_aios_approvals WHERE run_id=? ORDER BY created_at ASC", (run_id,)).fetchall()
        ]
    return success_response({"run_id": run_id, "status": status, "progress": progress, "plan": plan, "artifacts": artifacts, "queue": queue, "events": events, "approvals": approval_rows, "next_steps": [item for item in steps if item.get("state") != "done"]}, "AIOS 已执行计划步骤")


@yixiu_bp.get("/aios/status")
def aios_status():
    limit = min(int(request.args.get("limit", 10)), 50)
    with _db() as conn:
        rows = conn.execute("SELECT * FROM yixiu_aios_runs ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    runs = []
    for row in rows:
        item = dict(row)
        item["plan"] = _json(item.pop("plan_json", "{}"), {})
        item["artifacts"] = _json(item.pop("artifacts_json", "{}"), {})
        runs.append(item)
    return success_response({"runs": runs, "total": len(runs)}, "AIOS 运行记录获取成功")


@yixiu_bp.get("/aios/runs/<run_id>")
def aios_run_detail(run_id: str):
    with _db() as conn:
        run = _load_aios_run(conn, run_id)
    if not run:
        return error_response(404, "AIOS 运行记录不存在")
    return success_response(run, "AIOS 运行详情获取成功")


@yixiu_bp.get("/aios/events")
def aios_events():
    run_id = request.args.get("run_id", "").strip()
    agent_id = request.args.get("agent_id", "").strip()
    limit = min(int(request.args.get("limit", 80)), 300)
    where = []
    params = []
    if run_id:
        where.append("run_id=?")
        params.append(run_id)
    if agent_id:
        where.append("agent_id=?")
        params.append(_agent_key(agent_id))
    clause = "WHERE " + " AND ".join(where) if where else ""
    with _db() as conn:
        rows = conn.execute(
            f"SELECT * FROM yixiu_agent_events {clause} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
    return success_response({"events": [_agent_event_dict(row) for row in rows], "total": len(rows)}, "AIOS 事件流获取成功")


@yixiu_bp.post("/aios/resume")
@require_jwt_roles(WRITE_ROLES)
@require_confirmed_write("aios.resume", "/api/yixiu/aios/resume")
def aios_resume():
    data = request.get_json(silent=True) or {}
    run_id = str(data.get("run_id") or data.get("plan_id") or "").strip()
    if not run_id:
        return error_response(400, "缺少 AIOS 运行ID")
    with _db() as conn:
        run = _load_aios_run(conn, run_id)
    if not run:
        return error_response(404, "AIOS 运行记录不存在")
    plan = run.get("plan") or {}
    payload = {
        "plan": plan,
        "plan_id": run_id,
        "execute_all": data.get("execute_all", True),
        "approve_all": data.get("approve_all", False),
        "approvals": data.get("approvals") or {},
        "commit": data.get("commit", True),
        "confirmed": True,
        "idempotency_key": f"execute-{uuid.uuid4().hex[:12]}",
    }
    # 直接复用执行核心逻辑，保留同一 run_id、同一状态机和队列。
    with current_app.test_request_context(
        "/api/yixiu/aios/execute",
        method="POST",
        json=payload,
        headers={"Authorization": request.headers.get("Authorization", ""), "Idempotency-Key": payload["idempotency_key"]},
    ):
        return aios_execute()


@yixiu_bp.get("/database/status")
def database_status():
    return success_response(_database_status(), "数据库状态获取成功")


@yixiu_bp.post("/database/bootstrap")
def database_bootstrap():
    with _db() as conn:
        _seed_templates(conn)
        _seed_agent_memory(conn)
    return success_response(_database_status(), "一修业务数据库已完成初始化检查")
