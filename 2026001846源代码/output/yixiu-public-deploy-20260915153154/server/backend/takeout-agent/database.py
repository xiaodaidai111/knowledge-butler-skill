# -*- coding: utf-8 -*-
"""
数据库层：SQLite，用于预留扩展。当前仍从 data/*.json 加载知识库与样本店铺，
若表中已有数据则优先从数据库读取，便于前端对接后做增删改查。
"""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# 使用 config 中的路径
try:
    from config import DATA_DIR, DATABASE_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "agent.db"))


def get_connection() -> sqlite3.Connection:
    """获取 SQLite 连接（每次调用新建，便于多线程/请求隔离）。"""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    初始化数据库表结构。
    - restaurants: 店铺原始数据与扩展字段
    - knowledge_base: 知识库条目
    """
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                rating REAL,
                monthly_orders INTEGER,
                price_range TEXT,
                last_inspection_score INTEGER,
                violations INTEGER,
                complaint_count INTEGER,
                total_reviews INTEGER,
                negative_reviews INTEGER,
                packaging_flags TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                keywords TEXT,
                content TEXT,
                created_at TEXT,
                updated_at TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()


def load_json(filename: str, default: Any) -> Any:
    """从 data 目录读取 JSON 文件。"""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(filename: str, payload: Any) -> None:
    """写入 JSON 到 data 目录。"""
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def get_restaurants_from_db() -> List[Dict[str, Any]]:
    """从数据库读取店铺列表；若表为空则返回空列表（由调用方回退到 JSON）。"""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, name, category, rating, monthly_orders, price_range, "
            "last_inspection_score, violations, complaint_count, total_reviews, "
            "negative_reviews, packaging_flags FROM restaurants"
        )
        rows = cur.fetchall()
        out = []
        for row in rows:
            d = dict(row)
            flags = d.get("packaging_flags")
            if isinstance(flags, str):
                try:
                    d["packaging_flags"] = json.loads(flags) if flags else []
                except Exception:
                    d["packaging_flags"] = []
            out.append(d)
        return out
    finally:
        conn.close()


def get_knowledge_base_from_db() -> List[Dict[str, Any]]:
    """从数据库读取知识库；若表为空则返回空列表。"""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, title, keywords, content FROM knowledge_base"
        )
        rows = cur.fetchall()
        out = []
        for row in rows:
            d = dict(row)
            for key in ("keywords", "content"):
                val = d.get(key)
                if isinstance(val, str):
                    try:
                        d[key] = json.loads(val) if val else ([] if key == "content" else [])
                    except Exception:
                        d[key] = [] if key == "content" else []
            out.append(d)
        return out
    finally:
        conn.close()


def seed_restaurants_from_json() -> int:
    """从 data/sample_restaurants.json 导入到数据库；返回插入条数。"""
    data = load_json("sample_restaurants.json", [])
    if not data:
        return 0
    conn = get_connection()
    try:
        cur = conn.cursor()
        for r in data:
            flags = r.get("packaging_flags", [])
            flags_str = json.dumps(flags, ensure_ascii=False) if flags else "[]"
            cur.execute(
                """INSERT OR REPLACE INTO restaurants (
                    id, name, category, rating, monthly_orders, price_range,
                    last_inspection_score, violations, complaint_count, total_reviews,
                    negative_reviews, packaging_flags, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    str(r.get("id", "")),
                    str(r.get("name", "")),
                    str(r.get("category", "")),
                    r.get("rating"),
                    r.get("monthly_orders"),
                    str(r.get("price_range", "")),
                    r.get("last_inspection_score"),
                    r.get("violations"),
                    r.get("complaint_count"),
                    r.get("total_reviews"),
                    r.get("negative_reviews"),
                    flags_str,
                ),
            )
        conn.commit()
        return len(data)
    finally:
        conn.close()


def seed_knowledge_base_from_json() -> int:
    """从 data/knowledge_base.json 导入到数据库；返回插入条数。"""
    data = load_json("knowledge_base.json", [])
    if not data:
        return 0
    conn = get_connection()
    try:
        cur = conn.cursor()
        for r in data:
            kw = r.get("keywords", [])
            content = r.get("content", [])
            cur.execute(
                """INSERT OR REPLACE INTO knowledge_base (id, title, keywords, content, updated_at)
                 VALUES (?, ?, ?, ?, datetime('now'))""",
                (
                    str(r.get("id", "")),
                    str(r.get("title", "")),
                    json.dumps(kw, ensure_ascii=False),
                    json.dumps(content, ensure_ascii=False),
                ),
            )
        conn.commit()
        return len(data)
    finally:
        conn.close()


def ensure_seed() -> None:
    """确保数据库已初始化并有数据：若 restaurants 或 knowledge_base 为空，则从 JSON 导入。"""
    init_db()
    if not get_restaurants_from_db():
        seed_restaurants_from_json()
    if not get_knowledge_base_from_db():
        seed_knowledge_base_from_json()
