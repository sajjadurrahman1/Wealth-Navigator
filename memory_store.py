# memory_store.py
# SQLite-backed memory store:
# - Short-term memory: chat messages per conversation/session
# - Long-term memory: user-level facts/preferences + optional summaries

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MEMORY_DIR = Path(".memory")
USER_ID_FILE = MEMORY_DIR / ".user_id"
DB_PATH = MEMORY_DIR / "memory.db"


def ensure_memory_dir() -> None:
    MEMORY_DIR.mkdir(exist_ok=True)


def _connect() -> sqlite3.Connection:
    ensure_memory_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Create DB tables if they don't exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                title TEXT,
                profile_snapshot TEXT,
                summary TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS long_memory (
                user_id TEXT NOT NULL,
                mem_key TEXT NOT NULL,
                mem_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                PRIMARY KEY(user_id, mem_key)
            )
            """
        )
        conn.commit()


def get_or_create_user_id() -> str:
    """
    Persist a stable user_id locally so the same user returns across restarts.
    """
    ensure_memory_dir()
    if USER_ID_FILE.exists():
        try:
            existing = USER_ID_FILE.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        except OSError:
            pass

    new_id = str(uuid.uuid4())
    try:
        USER_ID_FILE.write_text(new_id, encoding="utf-8")
    except OSError:
        # If write fails, still return an ID for this run
        pass
    return new_id


# ---------------------------
# Short-term memory (sessions)
# ---------------------------

def create_conversation(user_id: str, profile_snapshot: Optional[Dict[str, Any]] = None, title: Optional[str] = None) -> str:
    init_db()
    conversation_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    snapshot_json = json.dumps(profile_snapshot or {}, ensure_ascii=False)

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO conversations (conversation_id, user_id, created_at, title, profile_snapshot, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, user_id, created_at, title, snapshot_json, "")
        )
        conn.commit()

    return conversation_id


def list_conversations(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT conversation_id, created_at, title
            FROM conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        ).fetchall()

    out = []
    for cid, created_at, title in rows:
        out.append({
            "conversation_id": cid,
            "created_at": created_at,
            "title": title or "Untitled"
        })
    return out


def load_conversation_messages(conversation_id: str) -> List[Dict[str, str]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

    return [{"role": r, "content": c} for (r, c) in rows]


def append_message(conversation_id: str, role: str, content: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, role, content, datetime.utcnow().isoformat())
        )
        conn.commit()


def set_conversation_summary(conversation_id: str, summary: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE conversations
            SET summary = ?
            WHERE conversation_id = ?
            """,
            (summary, conversation_id)
        )
        conn.commit()


def get_conversation_summary(conversation_id: str) -> str:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT summary FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        ).fetchone()
    return (row[0] or "") if row else ""


def set_conversation_title(conversation_id: str, title: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET title = ? WHERE conversation_id = ?",
            (title[:80], conversation_id)
        )
        conn.commit()


# ---------------------------
# Long-term memory (user facts)
# ---------------------------

def upsert_long_memory(user_id: str, mem_key: str, mem_value: str, ttl_days: Optional[int] = None) -> None:
    """
    Store long-term facts/preferences.
    ttl_days: if provided, memory expires after ttl_days.
    """
    init_db()
    updated_at = datetime.utcnow().isoformat()
    expires_at = None
    if ttl_days is not None:
        expires_at = (datetime.utcnow() + timedelta(days=ttl_days)).isoformat()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO long_memory (user_id, mem_key, mem_value, updated_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, mem_key)
            DO UPDATE SET mem_value=excluded.mem_value, updated_at=excluded.updated_at, expires_at=excluded.expires_at
            """,
            (user_id, mem_key, mem_value, updated_at, expires_at)
        )
        conn.commit()


def get_long_memory(user_id: str) -> Dict[str, str]:
    init_db()
    now = datetime.utcnow().isoformat()

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT mem_key, mem_value, expires_at
            FROM long_memory
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

    out: Dict[str, str] = {}
    for k, v, expires_at in rows:
        if expires_at and expires_at < now:
            continue
        out[k] = v
    return out


def cleanup_expired_long_memory(user_id: Optional[str] = None) -> None:
    init_db()
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        if user_id:
            conn.execute(
                "DELETE FROM long_memory WHERE user_id = ? AND expires_at IS NOT NULL AND expires_at < ?",
                (user_id, now)
            )
        else:
            conn.execute(
                "DELETE FROM long_memory WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,)
            )
        conn.commit()


# ---------------------------
# Compatibility helpers
# (so your existing code won't break)
# ---------------------------

def load_user_state(user_id: str) -> Dict[str, Any]:
    """
    Compatibility: return latest conversation messages + stored long-term profile snapshot if needed.
    This keeps your app.py from crashing if it expects {profile, chat}.
    """
    init_db()
    convs = list_conversations(user_id, limit=1)
    if not convs:
        return {"profile": {}, "chat": []}

    cid = convs[0]["conversation_id"]
    chat = load_conversation_messages(cid)

    # Long-term "profile" is stored as LTM keys; we’ll return them as a dict.
    profile = get_long_memory(user_id)
    return {"profile": profile, "chat": chat, "conversation_id": cid}


def save_user_state(user_id: str, profile_data: Dict[str, Any], chat: List[Dict[str, str]]) -> None:
    """
    Compatibility: upsert long-term memory based on current profile_data.
    Chat is NOT stored here anymore (we store message-by-message in append_message).
    This is kept only because your app.py currently calls it.
    """
    # Save long-term user preferences/facts
    if profile_data.get("currency"):
        upsert_long_memory(user_id, "currency", str(profile_data["currency"]))
    if profile_data.get("selected_tax_class"):
        upsert_long_memory(user_id, "selected_tax_class", str(profile_data["selected_tax_class"]))
    if "goal_amount" in profile_data:
        upsert_long_memory(user_id, "goal_amount", str(profile_data["goal_amount"]))
    if "goal_months" in profile_data:
        upsert_long_memory(user_id, "goal_months", str(profile_data["goal_months"]))


def clear_user_state(user_id: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM long_memory WHERE user_id = ?", (user_id,))
        conn.commit()

def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation and all its messages."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.commit()

def get_profile_snapshot(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional helper – store a snapshot of the profile inside a conversation.
    """
    return {
        "gross_income": profile_data.get("gross_income"),
        "selected_tax_class": profile_data.get("selected_tax_class"),
        "goal_amount": profile_data.get("goal_amount"),
        "goal_months": profile_data.get("goal_months"),
        "currency": profile_data.get("currency"),
        "expenses": profile_data.get("expenses", {}),
    }
