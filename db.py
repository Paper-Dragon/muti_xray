# encoding: utf-8
import json
import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Optional

DB_PATH     = "/usr/local/etc/xray/xray.db"
BACKUP_FILE = "xray.db"


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, mode=0o700, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cards (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            interface  TEXT NOT NULL,
            listen_ip  TEXT NOT NULL UNIQUE,
            client_ip  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS nodes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id     INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
            protocol    TEXT NOT NULL,
            port        INTEGER NOT NULL,
            tag         TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            params      TEXT NOT NULL DEFAULT '{}',
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_nodes_card ON nodes(card_id);
    """)
    return conn


def save_cards(cards: List[dict]) -> List[dict]:
    conn = _connect()
    result = []
    for c in cards:
        conn.execute(
            "INSERT INTO cards (interface, listen_ip, client_ip) VALUES (?, ?, ?) "
            "ON CONFLICT(listen_ip) DO UPDATE SET interface=excluded.interface, client_ip=excluded.client_ip",
            (c["interface"], c["listen_ip"], c["client_ip"]),
        )
        row = conn.execute("SELECT id FROM cards WHERE listen_ip = ?", (c["listen_ip"],)).fetchone()
        result.append({**c, "id": row[0]})
    conn.commit()
    conn.close()
    return result


def get_cards() -> List[dict]:
    conn = _connect()
    rows = conn.execute("SELECT id, interface, listen_ip, client_ip FROM cards ORDER BY id").fetchall()
    conn.close()
    return [{"id": r[0], "interface": r[1], "listen_ip": r[2], "client_ip": r[3]} for r in rows]


def add_node(card_id: int, protocol: str, port: int, tag: str, name: str, params: dict) -> int:
    conn = _connect()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO nodes (card_id, protocol, port, tag, name, params, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (card_id, protocol, port, tag, name, json.dumps(params, ensure_ascii=False), ts),
    )
    node_id = cur.lastrowid
    conn.commit()
    conn.close()
    return node_id


def get_nodes() -> List[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT n.id, n.card_id, n.protocol, n.port, n.tag, n.name, n.params, "
        "c.interface, c.listen_ip, c.client_ip "
        "FROM nodes n JOIN cards c ON n.card_id = c.id ORDER BY n.id"
    ).fetchall()
    conn.close()
    return [{
        "id": r[0], "card_id": r[1], "protocol": r[2], "port": r[3],
        "tag": r[4], "name": r[5], "params": json.loads(r[6]),
        "interface": r[7], "listen_ip": r[8], "client_ip": r[9],
    } for r in rows]


def get_protocols() -> List[str]:
    conn = _connect()
    rows = conn.execute("SELECT DISTINCT protocol FROM nodes ORDER BY protocol").fetchall()
    conn.close()
    return [r[0] for r in rows]


def clear_nodes() -> None:
    conn = _connect()
    conn.execute("DELETE FROM nodes")
    conn.commit()
    conn.close()


def clear_all() -> None:
    conn = _connect()
    conn.execute("DELETE FROM nodes")
    conn.execute("DELETE FROM cards")
    conn.execute("DELETE FROM settings")
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    conn = _connect()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key: str, value: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_max_port() -> int:
    conn = _connect()
    row = conn.execute("SELECT MAX(port) FROM nodes").fetchone()
    conn.close()
    return row[0] if row[0] is not None else 10000


def has_data() -> bool:
    conn = _connect()
    row = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()
    conn.close()
    return row[0] > 0


def backup() -> str:
    if not os.path.isfile(DB_PATH):
        return ""
    shutil.copy2(DB_PATH, BACKUP_FILE)
    return os.path.abspath(BACKUP_FILE)


def restore() -> bool:
    if not os.path.isfile(BACKUP_FILE):
        return False
    shutil.copy2(BACKUP_FILE, DB_PATH)
    return True
