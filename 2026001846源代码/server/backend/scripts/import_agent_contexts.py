"""把本机 DSH / Claude Code / Codex 的会话上下文，按一休固定格式导入「上下文引擎」。

一休后端已有的 AI Import Gateway（POST /api/yixiu/integrations/imports）接受
CODEX_FIXED_UPLOAD_FIELDS 这套固定结构：
  task_goal / work_summary / changed_files / decisions / risks / todos /
  validation / memory_candidates / skill_candidates / eval_cases / next_actions
本脚本负责从三个本地会话库里把对话读出来，填进这套结构，再 POST 过去。

用法:
  python scripts/import_agent_contexts.py --dry-run        # 只打印，不写库
  python scripts/import_agent_contexts.py                  # 每个来源取最新 10 条
  python scripts/import_agent_contexts.py --limit 0        # 全量
  python scripts/import_agent_contexts.py --sources dsh,codex

环境:
  YIXIU_API_BASE  默认 http://127.0.0.1:5000
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import zstandard

HOME = Path.home()
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# ─── 会话模型 ────────────────────────────────────────────────────────────────


@dataclass
class Session:
    provider: str
    session_id: str
    title: str
    cwd: str
    started_at: str
    source: str = ""
    turns: list[tuple[str, str]] = field(default_factory=list)  # (role, text)
    tool_inputs: list[str] = field(default_factory=list)        # 工具调用原始参数

    def user_texts(self) -> list[str]:
        return [t for role, t in self.turns if role == "user" and t.strip()]

    def assistant_texts(self) -> list[str]:
        return [t for role, t in self.turns if role == "assistant" and t.strip()]


# ─── 通用小工具 ──────────────────────────────────────────────────────────────

FILE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".json", ".md", ".css",
    ".html", ".sql", ".yml", ".yaml", ".txt", ".sh", ".ps1", ".java", ".go",
    ".rs", ".toml", ".ini", ".bat", ".csv", ".env",
}
PATH_RE = re.compile(r"""[A-Za-z]:\\[^\s"'`,;)\]}|]+|(?:\.{0,2}/)?(?:[\w.@-]+/)+[\w.@-]+\.\w{1,6}""")
SENTENCE_SPLIT = re.compile(r"[。；;!?\n]+|(?<=\.)\s+")


def _clip(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _uniq(items: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _is_prose(line: str) -> bool:
    """排掉 markdown 标题、表格行和代码行，只留能当结论读的句子。"""
    stripped = line.strip()
    if len(stripped) < 10:
        return False
    if stripped.startswith(("#", "|", ">", "```", "---", "===")):
        return False
    if stripped.count("|") >= 2 or stripped.count("{") + stripped.count("}") >= 2:
        return False
    return True


def _note(text: str, max_len: int = 14) -> list[str]:
    """把一段话切成适合放进列表的短句。"""
    picked = []
    for part in SENTENCE_SPLIT.split(text):
        part = _clip(part, 200)
        if _is_prose(part):
            picked.append(part)
        if len(picked) >= max_len:
            break
    return picked


def _scan(lines: list[str], keywords: tuple[str, ...], limit: int = 5) -> list[str]:
    hits = []
    for line in lines:
        if not _is_prose(line):
            continue
        if any(k.lower() in line.lower() for k in keywords):
            hits.append(_clip(line, 200))
        if len(hits) >= limit:
            break
    return hits


def _walk_lines(texts: list[str]) -> list[str]:
    out: list[str] = []
    for text in texts:
        for line in text.splitlines():
            line = line.strip().lstrip("-*•0123456789. ").strip()
            if line:
                out.append(line)
    return out


def extract_files(tool_inputs: list[str], project_root: Path, limit: int = 10) -> list[str]:
    """从工具调用参数里捞文件路径。

    只认两种：命中项目根的绝对路径（剥掉根），以及本来就是相对路径的写法。
    其它绝对路径（`/raw.githubusercontent.com/...`、别的盘符）一律丢掉，
    否则日志里的 URL 会被当成「改动文件」写进一休。
    """
    found: list[str] = []
    root = str(project_root).replace("\\", "/").lower()
    for raw in tool_inputs:
        for match in PATH_RE.findall(raw):
            path = match.strip().strip("\"'").rstrip(".,;:")
            if Path(path).suffix.lower() not in FILE_EXT:
                continue
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            index = lower.find(root)
            if index != -1:
                normalized = normalized[index + len(root):]
            elif re.match(r"^[A-Za-z]:", normalized) or normalized.startswith(("/", "~")):
                continue
            normalized = normalized.strip("/").removeprefix("./")
            if not normalized or normalized.count("/") > 8:
                continue
            found.append(normalized)
    return _uniq(found, limit)


# ─── 会话读取：DSH ───────────────────────────────────────────────────────────


def _dsh_records(path: Path) -> list[dict]:
    """DSH 的 session.v3.jsonl.zstd 是「一段一条」的多帧 zstd，必须跨帧读。"""
    with path.open("rb") as handle:
        with zstandard.ZstdDecompressor().stream_reader(handle, read_across_frames=True) as reader:
            text = reader.read().decode("utf-8", "replace")
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def read_dsh_sessions(project_root: Path) -> list[Session]:
    root = HOME / ".dsh-desktop" / "sessions"
    if not root.is_dir():
        return []
    sessions: list[Session] = []
    for path in sorted(root.rglob("session.v3.jsonl*")):
        if not path.name.startswith("session.v3.jsonl"):
            continue
        try:
            records = _dsh_records(path)
        except Exception as exc:  # 单个会话损坏不该拖垮整批
            print(f"  [skip] {path.parent.name}: {exc}", file=sys.stderr)
            continue
        header = next((r for r in records if r.get("type") == "session"), {})
        cwd = str(header.get("cwd") or "")
        if not cwd:
            continue
        session = Session(
            provider="dsh",
            session_id=str(header.get("id") or path.parent.name),
            title="",
            cwd=cwd,
            started_at=_iso(header.get("createdAt")),
            source=str(path),
        )
        for record in records:
            kind, data = record.get("type"), record.get("data") or {}
            if kind == "session/title":
                session.title = str(data.get("title") or session.title)
            elif kind == "user/message":
                if (data.get("source") or {}).get("kind") == "plugin":
                    continue  # 注入的策略提示，不是用户输入
                text = "\n".join(
                    part.get("text", "") for part in data.get("content", []) if part.get("type") == "text"
                )
                if text.strip():
                    session.turns.append(("user", text))
            elif kind == "assistant/message":
                message = data.get("message") or {}
                text = "\n".join(
                    part.get("text", "") for part in message.get("content", []) if part.get("type") == "text"
                )
                if text.strip():
                    session.turns.append(("assistant", text))
            elif kind == "tool/call":
                session.tool_inputs.append(str(data.get("arguments") or ""))
        if session.turns:
            sessions.append(session)
    return sessions


# ─── 会话读取：Claude Code ───────────────────────────────────────────────────


def _is_injected_user_text(text: str) -> bool:
    """判断一条 role=user 的记录是不是工具注入的指令块，而不是用户真的说的话。

    Codex 会把 `<recommended_plugins>`、`<app-context>` 和整份 AGENTS.md
    （`# AGENTS.md instructions\\n\\n<INSTRUCTIONS>…`）都记成用户消息，
    直接拿来当任务目标会变成一堆无意义的标题。
    """
    head = text.lstrip()[:400]
    if head.startswith(("<", "{", "[", "# AGENTS.md")):
        return True
    if head.startswith("The following is the Codex agent history"):  # 压缩后的历史回灌
        return True
    return any(marker in head for marker in ("<INSTRUCTIONS>", "<recommended_plugins>", "<app-context>"))


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def read_claude_sessions(project_root: Path) -> list[Session]:
    root = HOME / ".claude" / "projects"
    if not root.is_dir():
        return []
    sessions: list[Session] = []
    for path in sorted(root.rglob("*.jsonl")):
        records = _read_jsonl(path)
        if not records:
            continue
        cwd = next((str(r.get("cwd")) for r in records if r.get("cwd")), "")
        if not cwd:
            continue
        session = Session(
            provider="claude",
            session_id=path.stem,
            title="",
            cwd=cwd,
            started_at="",
            source=str(path),
        )
        for record in records:
            kind = record.get("type")
            if record.get("timestamp") and not session.started_at:
                session.started_at = str(record["timestamp"])
            if kind == "ai-title":
                session.title = str(record.get("title") or record.get("aiTitle") or session.title)
            elif kind == "user":
                text = _content_text((record.get("message") or {}).get("content"))
                if text.strip() and not _is_injected_user_text(text):
                    session.turns.append(("user", text))
            elif kind == "assistant":
                content = (record.get("message") or {}).get("content")
                text = _content_text(content)
                if text.strip():
                    session.turns.append(("assistant", text))
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "tool_use":
                            session.tool_inputs.append(json.dumps(part.get("input"), ensure_ascii=False))
        if session.turns:
            sessions.append(session)
    return sessions


# ─── 会话读取：Codex ─────────────────────────────────────────────────────────


def read_codex_sessions(project_root: Path) -> list[Session]:
    root = HOME / ".codex" / "sessions"
    if not root.is_dir():
        return []
    sessions: list[Session] = []
    for path in sorted(root.rglob("rollout-*.jsonl")):
        records = _read_jsonl(path)
        if not records:
            continue
        meta = next((r.get("payload") or {} for r in records if r.get("type") == "session_meta"), {})
        cwd = str(meta.get("cwd") or "")
        if not cwd:
            continue
        session = Session(
            provider="codex",
            session_id=str(meta.get("session_id") or path.stem),
            title="",
            cwd=cwd,
            started_at=str(meta.get("timestamp") or ""),
            source=str(path),
        )
        for record in records:
            if record.get("type") != "response_item":
                continue
            payload = record.get("payload") or {}
            if payload.get("type") != "message":
                continue
            role = payload.get("role")
            text = "\n".join(
                part.get("text", "")
                for part in payload.get("content", [])
                if isinstance(part, dict) and part.get("type") in ("input_text", "output_text")
            )
            if not text.strip():
                continue
            if role == "user":
                if _is_injected_user_text(text):
                    continue
                session.turns.append(("user", text))
            elif role == "assistant":
                session.turns.append(("assistant", text))
        if session.turns:
            sessions.append(session)
    return sessions


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _iso(value) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    return str(value or "")


# ─── 摘要：填入一休固定结构 ──────────────────────────────────────────────────


def build_report(session: Session, project_root: Path, project_name: str) -> dict:
    users = session.user_texts()
    assistants = session.assistant_texts()
    assistant_lines = _walk_lines(assistants)

    goal_source = users[0] if users else (assistants[0] if assistants else session.title)
    if not users:
        # 有些 Codex 续聊文件里第一条「助手消息」是审批结果 JSON，拿它当标题没意义。
        goal_source = next((t for t in assistants if len(t) > 40 and _is_prose(t[:120])), goal_source)
    task_goal = _clip(" ".join(_note(goal_source, 2)) or goal_source, 200)

    work_summary = _uniq(
        _note(assistants[-1], 4) + _note(assistants[0], 2) if assistants else [],
        5,
    )
    if not work_summary and session.title:
        work_summary = [session.title]

    files = extract_files(session.tool_inputs, project_root)

    decisions = _scan(assistant_lines, ("决策", "决定", "采用", "选择", "改为", "改用", "方案", "根因"), 5)
    risks = _scan(assistant_lines, ("风险", "注意", "局限", "限制", "未验证", "阻塞", "失败", "待确认"), 5)
    todos = _scan(assistant_lines, ("待办", "todo", "下一步", "需要", "建议", "待补", "后续"), 5)
    validation = _scan(assistant_lines, ("通过", "验证", "测试", "build", "exit code", "0 error", "built in"), 5)

    title = session.title.strip() or _clip(task_goal, 40) or f"{session.provider} 会话"
    stamp = session.started_at or "未知时间"
    short_id = re.sub(r"[^a-zA-Z0-9]", "", session.session_id.removeprefix("session-"))[:8] or "unknown"
    rounds = len(users)

    memory_candidates = [
        f"{title}｜目标：{task_goal}",
        f"来源 {session.provider} 会话 {short_id}（{stamp}，{rounds} 轮），"
        f"关键结论：{work_summary[0] if work_summary else '待补充'}",
    ]
    if decisions:
        memory_candidates.append(f"可复用决策：{decisions[0]}")

    skill_candidates = [
        f"{session.provider} 会话任务复现路径：{'; '.join(todos[:3]) if todos else task_goal}",
    ]
    eval_cases = [
        f"校验 {session.provider} 会话 {short_id} 导入质量："
        f"目标是否可复现、改动文件是否完整（{len(files)} 个）、风险是否被记录（{len(risks)} 条）、待办是否闭环（{len(todos)} 条）。",
    ]
    next_actions = _uniq(todos[:3] + (assistants[-1:] and _note(assistants[-1], 2) or []), 4)

    return {
        "provider": session.provider,
        "project_name": project_name,
        "title": f"[{session.provider}] {title}",
        "content_type": "chat",
        "task_goal": task_goal,
        "work_summary": work_summary or ["会话内容已归档，等待人工补全总结。"],
        "changed_files": files,
        "decisions": decisions or ["保留会话中的关键方案，等待人工审核后沉淀为团队决策。"],
        "risks": risks or ["需人工确认对话是否包含敏感信息、错误结论或不适用上下文。"],
        "todos": todos or ["关联到项目进展，并决定是否生成 Memory、Skill 或 Eval 用例。"],
        "validation": validation or [f"会话共 {rounds} 轮用户输入、{len(assistants)} 条助手回复，已结构化导入。"],
        "memory_candidates": memory_candidates,
        "skill_candidates": skill_candidates,
        "eval_cases": eval_cases,
        "next_actions": next_actions or ["人工审核候选资产。"],
    }


# ─── 导入 ────────────────────────────────────────────────────────────────────


def same_project(cwd: str, project_root: Path) -> bool:
    if not cwd:
        return False
    try:
        return Path(cwd).resolve() == project_root.resolve()
    except OSError:
        return cwd.replace("\\", "/").lower() == str(project_root).replace("\\", "/").lower()


def existing_import_ids(client: httpx.Client, base: str) -> set[str]:
    try:
        resp = client.get(f"{base}/api/yixiu/integrations/imports", timeout=15)
        rows = (resp.json().get("data") or {}).get("imports") or []
        return {str(row.get("id")) for row in rows}
    except Exception as exc:
        print(f"  警告：读取已有导入失败（将按全量导入）: {exc}", file=sys.stderr)
        return set()


def make_client(base: str, timeout: float = 60) -> httpx.Client:
    """本机地址绕开系统代理。

    这台机器上同时存在大小写重复的 *_proxy 变量，httpx 读进 `all_proxy` 会
    直接 InvalidURL（`:1]`），导入本地 5000 端口根本不需要代理。
    """
    local = "127.0.0.1" in base or "localhost" in base
    return httpx.Client(timeout=timeout, trust_env=not local)


def main() -> int:
    parser = argparse.ArgumentParser(description="把 DSH / Claude / Codex 会话上下文导入一休上下文引擎")
    parser.add_argument("--api", default=os.getenv("YIXIU_API_BASE", "http://127.0.0.1:5000"))
    parser.add_argument("--project", default=str(PROJECT_ROOT), help="过滤会话的工作目录（默认本仓库）")
    parser.add_argument("--project-name", default="一休 Team Memory OS", help="写入一休的项目名")
    parser.add_argument("--sources", default="dsh,claude,codex")
    parser.add_argument("--limit", type=int, default=10, help="每个来源取最新几条，0 表示全部")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写库")
    args = parser.parse_args()

    project_root = Path(args.project)
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    readers = {
        "dsh": read_dsh_sessions,
        "claude": read_claude_sessions,
        "codex": read_codex_sessions,
    }

    collected: list[Session] = []
    for name in sources:
        reader = readers.get(name)
        if reader is None:
            print(f"未知来源: {name}", file=sys.stderr)
            continue
        found = [s for s in reader(project_root) if same_project(s.cwd, project_root)]
        found.sort(key=lambda s: (s.started_at, s.source), reverse=True)
        # Codex 续聊会为同一个 session_id 再写一个 rollout 文件，内容是同一段对话的延续。
        # 一休那边 id 是主键，重复导入要么 500 要么堆噪音，只保留最新那一份。
        unique: list[Session] = []
        seen_ids: set[str] = set()
        for session in found:
            key = f"{session.provider}:{session.session_id}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            unique.append(session)
        found = unique
        if args.limit > 0:
            found = found[: args.limit]
        print(f"{name:7} 命中 {len(found)} 条会话（工作目录 = {project_root}）")
        collected.extend(found)

    if not collected:
        print("没有找到任何会话。用 --project 指定其它工作目录试试。")
        return 0

    if args.dry_run:
        for session in collected:
            report = build_report(session, project_root, args.project_name)
            print("\n" + "=" * 78)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\n[dry-run] 共 {len(collected)} 条，未写库。")
        return 0

    sent = skipped = failed = 0
    with make_client(args.api) as client:
        known = existing_import_ids(client, args.api)
        for session in collected:
            import_id = f"imp-{session.provider}-{re.sub(r'[^a-zA-Z0-9]', '', session.session_id.removeprefix('session-'))[:16]}"
            if import_id in known:
                skipped += 1
                continue
            payload = build_report(session, project_root, args.project_name)
            payload["id"] = import_id
            payload["source_id"] = f"src-{session.provider}"
            payload["imported_by"] = "agent-context-importer"
            try:
                resp = client.post(f"{args.api}/api/yixiu/integrations/imports", json=payload)
                body = resp.json()
            except Exception as exc:
                failed += 1
                print(f"  ✗ {import_id}: {exc}", file=sys.stderr)
                continue
            if resp.status_code == 200 and body.get("code") == 200:
                artifacts = len((body.get("data") or {}).get("import", {}).get("artifacts") or [])
                sent += 1
                print(f"  ✓ {session.provider:6} {import_id}  artifacts={artifacts}  {payload['title'][:52]}")
            else:
                failed += 1
                print(f"  ✗ {import_id}: {body.get('message') or body}", file=sys.stderr)

    print(f"\n完成：导入 {sent} 条，跳过已存在 {skipped} 条，失败 {failed} 条。")
    print(f"查看：{args.api}/api/yixiu/integrations/imports")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
