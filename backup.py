# encoding: utf-8
import os
import sqlite3
from typing import List, Tuple

import xray
from ui import GREEN, BLUE, RED, YELLOW, RESET, OK, INF, ERR, WRN

DB_PATH    = "/usr/local/etc/xray/backups.db"
TLS_DIR    = "/usr/local/etc/xray/tls"
LINKS_FILE = "quick_link.txt"

_KEY_CONFIG = "config.json"
_KEY_LINKS  = "quick_link.txt"
_KEY_TLS    = "tls/"


def _format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, mode=0o700, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS backups (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            created_at TEXT    NOT NULL,
            file_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS files (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_id INTEGER NOT NULL DEFAULT 1 REFERENCES backups(id) ON DELETE CASCADE,
            file_key  TEXT    NOT NULL,
            data      BLOB   NOT NULL,
            size      INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_files_backup ON files(backup_id);
    """)
    return conn


def _collect_files() -> List[Tuple[str, str, bytes]]:
    result: List[Tuple[str, str, bytes]] = []

    if os.path.isfile(xray.CONFIG_PATH):
        with open(xray.CONFIG_PATH, "rb") as f:
            result.append((xray.CONFIG_PATH, _KEY_CONFIG, f.read()))
    else:
        print(f" {WRN} {YELLOW}配置文件不存在: {xray.CONFIG_PATH}{RESET}")

    if os.path.isfile(LINKS_FILE):
        with open(LINKS_FILE, "rb") as f:
            result.append((LINKS_FILE, _KEY_LINKS, f.read()))

    if os.path.isdir(TLS_DIR):
        for name in os.listdir(TLS_DIR):
            full = os.path.join(TLS_DIR, name)
            if os.path.isfile(full):
                with open(full, "rb") as f:
                    result.append((full, _KEY_TLS + name, f.read()))

    return result


def backup() -> bool:
    collected = _collect_files()
    if not any(key == _KEY_CONFIG for _, key, _ in collected):
        print(f" {ERR} {RED}无配置文件可备份，请先初始化配置{RESET}")
        return False

    try:
        conn = _connect()
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("DELETE FROM files WHERE backup_id = 1")
        conn.execute("DELETE FROM backups WHERE id = 1")
        conn.execute(
            "INSERT INTO backups (id, created_at, file_count) VALUES (1, ?, ?)",
            (ts, len(collected)),
        )

        for _, file_key, data in collected:
            conn.execute(
                "INSERT INTO files (backup_id, file_key, data, size) VALUES (1, ?, ?, ?)",
                (file_key, data, len(data)),
            )
            print(f" {INF}   保存: {file_key} ({_format_size(len(data))})")

        conn.commit()
        conn.close()

        print(f" {OK} {GREEN}备份已保存 ({ts}){RESET}")
        print(f" {INF} {BLUE}共 {len(collected)} 个文件，数据库: {DB_PATH}{RESET}")
        return True

    except Exception as e:
        print(f" {ERR} {RED}备份失败: {e}{RESET}")
        return False


def restore(restart_service: bool = True) -> bool:
    try:
        conn = _connect()
        row = conn.execute("SELECT created_at, file_count FROM backups WHERE id = 1").fetchone()
        if not row:
            print(f" {ERR} {RED}没有可用的备份{RESET}")
            conn.close()
            return False

        files = conn.execute("SELECT file_key, data FROM files WHERE backup_id = 1").fetchall()
        conn.close()

        if not files:
            print(f" {ERR} {RED}备份数据为空{RESET}")
            return False

        print(f" {INF} {BLUE}备份时间: {row[0]}，共 {row[1]} 个文件{RESET}")

        for file_key, data in files:
            if file_key == _KEY_CONFIG:
                os.makedirs(os.path.dirname(xray.CONFIG_PATH), exist_ok=True)
                with open(xray.CONFIG_PATH, "wb") as f:
                    f.write(data)
                print(f" {OK}   恢复: {_KEY_CONFIG}")

            elif file_key == _KEY_LINKS:
                with open(LINKS_FILE, "wb") as f:
                    f.write(data)
                print(f" {OK}   恢复: {_KEY_LINKS}")

            elif file_key.startswith(_KEY_TLS):
                os.makedirs(TLS_DIR, mode=0o700, exist_ok=True)
                cert_name = file_key[len(_KEY_TLS):]
                dest = os.path.join(TLS_DIR, cert_name)
                with open(dest, "wb") as f:
                    f.write(data)
                if cert_name.endswith(".key"):
                    os.chmod(dest, 0o600)
                print(f" {OK}   恢复: {file_key}")

        print(f" {OK} {GREEN}配置已恢复{RESET}")

        if restart_service:
            try:
                xray.restart()
                print(f" {OK} {GREEN}Xray 服务已重启{RESET}")
            except Exception:
                print(f" {WRN} {YELLOW}服务重启失败，请手动执行: systemctl restart xray{RESET}")

        return True

    except Exception as e:
        print(f" {ERR} {RED}恢复失败: {e}{RESET}")
        return False
