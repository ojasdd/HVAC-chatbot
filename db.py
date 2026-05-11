import sqlite3
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
import time
import uuid

DB_PATH = Path(__file__).parent / "app.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
        ''')
        conn.commit()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> Optional[int]:
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password))
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def verify_user(username: str, password: str) -> Optional[int]:
    with get_db() as conn:
        user = conn.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_password(password))
        ).fetchone()
        if user:
            return user["id"]
        return None

def create_chat(user_id: int, title: str) -> str:
    chat_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chats (id, user_id, title, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, title, int(time.time()))
        )
        conn.commit()
    return chat_id

def get_user_chats(user_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        chats = conn.execute(
            "SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(chat) for chat in chats]

def add_message(chat_id: str, role: str, content: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, int(time.time()))
        )
        conn.commit()

def get_chat_messages(chat_id: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        messages = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,)
        ).fetchall()
        return [dict(msg) for msg in messages]

# Initialize DB on load
init_db()
