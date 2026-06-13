# encoding: utf-8
import json
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

import xray
from ui import (
    GREEN, BLUE, RED, YELLOW, RESET,
    OK, INF, ERR, WRN,
    prompt, prompt_int,
)

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
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT    NOT NULL,
            tag        TEXT    NOT NULL DEFAULT '',
            note       TEXT    NOT NULL DEFAULT '',
            file_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS files (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_id INTEGER NOT NULL REFERENCES backups(id) ON DELETE CASCADE,
            file_key  TEXT    NOT NULL,
            data      BLOB    NOT NULL,
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


def backup(tag: Optional[str] = None, note: str = "") -> Optional[int]:
    collected = _collect_files()
    if not any(key == _KEY_CONFIG for _, key, _ in collected):
        print(f" {ERR} {RED}无配置文件可备份，请先初始化配置{RESET}")
        return None

    try:
        conn = _connect()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            "INSERT INTO backups (created_at, tag, note, file_count) VALUES (?, ?, ?, ?)",
            (ts, tag or "", note, len(collected)),
        )
        backup_id = cur.lastrowid

        for _, file_key, data in collected:
            conn.execute(
                "INSERT INTO files (backup_id, file_key, data, size) VALUES (?, ?, ?, ?)",
                (backup_id, file_key, data, len(data)),
            )
            print(f" {INF}   保存: {file_key} ({_format_size(len(data))})")

        conn.commit()
        conn.close()

        tag_str = f" [{tag}]" if tag else ""
        print(f" {OK} {GREEN}备份 #{backup_id}{tag_str} 已保存到数据库{RESET}")
        print(f" {INF} {BLUE}共 {len(collected)} 个文件，数据库: {DB_PATH}{RESET}")
        return backup_id

    except Exception as e:
        print(f" {ERR} {RED}备份失败: {e}{RESET}")
        return None


def restore(backup_id: int, restart_service: bool = True) -> bool:
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT id, created_at, tag FROM backups WHERE id = ?", (backup_id,)
        ).fetchone()
        if not row:
            print(f" {ERR} {RED}备份 #{backup_id} 不存在{RESET}")
            conn.close()
            return False

        files = conn.execute(
            "SELECT file_key, data FROM files WHERE backup_id = ?", (backup_id,)
        ).fetchall()
        conn.close()

        if not any(key == _KEY_CONFIG for key, _ in files):
            print(f" {ERR} {RED}备份 #{backup_id} 中缺少 config.json{RESET}")
            return False

        if os.path.isfile(xray.CONFIG_PATH):
            print(f" {INF} {BLUE}恢复前自动备份当前配置...{RESET}")
            backup(tag="pre_restore")

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

        tag_str = f" [{row[2]}]" if row[2] else ""
        print(f" {OK} {GREEN}已从备份 #{backup_id}{tag_str} ({row[1]}) 恢复配置{RESET}")

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


def list_backups() -> List[Tuple[int, str, str, int]]:
    try:
        conn = _connect()
        rows = conn.execute(
            "SELECT b.id, b.created_at, b.tag, b.file_count, "
            "COALESCE(SUM(f.size), 0) AS total_size "
            "FROM backups b LEFT JOIN files f ON f.backup_id = b.id "
            "GROUP BY b.id ORDER BY b.id DESC"
        ).fetchall()
        conn.close()
    except Exception as e:
        print(f" {ERR} {RED}读取数据库失败: {e}{RESET}")
        return []

    if not rows:
        print(f" {INF} {BLUE}暂无备份{RESET}")
        return []

    print(f" {INF} {BLUE}共 {len(rows)} 个备份:{RESET}")
    result = []
    for row_id, ts, tag, fcount, total_size in rows:
        tag_str = f" [{tag}]" if tag else ""
        print(f"  {GREEN}#{row_id}{RESET}  {ts}{tag_str}  "
              f"{fcount} 文件  {_format_size(total_size)}")
        result.append((row_id, ts, tag, fcount))
    return result


def show_backup(backup_id: int) -> None:
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT id, created_at, tag, note, file_count FROM backups WHERE id = ?",
            (backup_id,),
        ).fetchone()
        if not row:
            print(f" {ERR} {RED}备份 #{backup_id} 不存在{RESET}")
            conn.close()
            return

        files = conn.execute(
            "SELECT file_key, size FROM files WHERE backup_id = ?", (backup_id,)
        ).fetchall()
        conn.close()

        tag_str = f" [{row[2]}]" if row[2] else ""
        print(f" {INF} {BLUE}备份 #{row[0]}{tag_str}{RESET}")
        print(f"  时间: {row[1]}")
        if row[3]:
            print(f"  备注: {row[3]}")
        print(f"  文件: {row[4]} 个")
        for fkey, fsize in files:
            print(f"    - {fkey}  ({_format_size(fsize)})")

    except Exception as e:
        print(f" {ERR} {RED}查询失败: {e}{RESET}")


def delete_backup(backup_id: int) -> bool:
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT id, tag FROM backups WHERE id = ?", (backup_id,)
        ).fetchone()
        if not row:
            print(f" {ERR} {RED}备份 #{backup_id} 不存在{RESET}")
            conn.close()
            return False

        conn.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        conn.commit()
        conn.close()

        tag_str = f" [{row[1]}]" if row[1] else ""
        print(f" {OK} {GREEN}已删除备份 #{backup_id}{tag_str}{RESET}")
        return True

    except Exception as e:
        print(f" {ERR} {RED}删除失败: {e}{RESET}")
        return False


def clean_backups(keep: int = 5) -> None:
    try:
        conn = _connect()
        ids = conn.execute("SELECT id FROM backups ORDER BY id DESC").fetchall()
        to_delete = [r[0] for r in ids[keep:]]
        if not to_delete:
            print(f" {INF} {BLUE}备份数量未超过 {keep}，无需清理{RESET}")
            conn.close()
            return

        conn.execute(
            f"DELETE FROM backups WHERE id IN ({','.join('?' * len(to_delete))})",
            to_delete,
        )
        conn.commit()
        conn.close()
        print(f" {OK} {GREEN}已清理 {len(to_delete)} 个旧备份，保留最近 {keep} 个{RESET}")

    except Exception as e:
        print(f" {ERR} {RED}清理失败: {e}{RESET}")


def export_backup(backup_id: int, output_dir: str = ".") -> Optional[str]:
    import base64

    try:
        conn = _connect()
        row = conn.execute(
            "SELECT id, created_at, tag, note FROM backups WHERE id = ?",
            (backup_id,),
        ).fetchone()
        if not row:
            print(f" {ERR} {RED}备份 #{backup_id} 不存在{RESET}")
            conn.close()
            return None

        files = conn.execute(
            "SELECT file_key, data FROM files WHERE backup_id = ?", (backup_id,)
        ).fetchall()
        conn.close()

        export_data = {
            "backup_id": row[0],
            "created_at": row[1],
            "tag": row[2],
            "note": row[3],
            "files": {fkey: base64.b64encode(data).decode() for fkey, data in files},
        }

        ts = row[1].replace("-", "").replace(":", "").replace(" ", "_")
        output_path = os.path.join(output_dir, f"xray_export_{ts}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f" {OK} {GREEN}已导出: {output_path}{RESET}")
        return output_path

    except Exception as e:
        print(f" {ERR} {RED}导出失败: {e}{RESET}")
        return None


def import_backup(json_path: str) -> Optional[int]:
    import base64

    if not os.path.isfile(json_path):
        print(f" {ERR} {RED}文件不存在: {json_path}{RESET}")
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            export_data = json.load(f)

        files_dict = export_data.get("files", {})
        if _KEY_CONFIG not in files_dict:
            print(f" {ERR} {RED}导入文件中缺少 config.json{RESET}")
            return None

        conn = _connect()
        ts = export_data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        tag = export_data.get("tag", "")
        note = export_data.get("note", f"从 {os.path.basename(json_path)} 导入")

        cur = conn.execute(
            "INSERT INTO backups (created_at, tag, note, file_count) VALUES (?, ?, ?, ?)",
            (ts, tag, note, len(files_dict)),
        )
        new_id = cur.lastrowid

        for file_key, b64data in files_dict.items():
            data = base64.b64decode(b64data)
            conn.execute(
                "INSERT INTO files (backup_id, file_key, data, size) VALUES (?, ?, ?, ?)",
                (new_id, file_key, data, len(data)),
            )

        conn.commit()
        conn.close()

        print(f" {OK} {GREEN}已导入为备份 #{new_id}，共 {len(files_dict)} 个文件{RESET}")
        return new_id

    except json.JSONDecodeError:
        print(f" {ERR} {RED}文件不是有效的 JSON: {json_path}{RESET}")
        return None
    except Exception as e:
        print(f" {ERR} {RED}导入失败: {e}{RESET}")
        return None


def _select_backup_id() -> Optional[int]:
    backups = list_backups()
    if not backups:
        return None
    id_list = [b[0] for b in backups]
    bid = prompt_int(f"\n 请输入备份 ID（如 {id_list[0]}），输入 0 取消: ")
    if bid is None or bid == 0:
        print(f" {INF} {BLUE}已取消{RESET}")
        return None
    if bid not in id_list:
        print(f" {ERR} {RED}无效 ID{RESET}")
        return None
    return bid


def _action_backup() -> None:
    tag = prompt(" 备份标签（直接回车跳过）: ")
    note = prompt(" 备份备注（直接回车跳过）: ")
    backup(tag=tag or None, note=note)


def _action_restore() -> None:
    bid = _select_backup_id()
    if bid is None:
        return
    if prompt(" 确认恢复？当前配置将被覆盖 (y/N): ").lower() != "y":
        print(f" {INF} {BLUE}已取消{RESET}")
        return
    restart = prompt(" 恢复后是否重启 Xray 服务？(Y/n): ").lower() != "n"
    restore(bid, restart_service=restart)


def _action_show() -> None:
    bid = _select_backup_id()
    if bid is not None:
        show_backup(bid)


def _action_delete() -> None:
    bid = _select_backup_id()
    if bid is None:
        return
    if prompt(f" 确认删除备份 #{bid}？(y/N): ").lower() != "y":
        print(f" {INF} {BLUE}已取消{RESET}")
        return
    delete_backup(bid)


def _action_clean() -> None:
    val = prompt(" 保留最近几个备份？（默认 5）: ", "5")
    try:
        keep = int(val)
    except ValueError:
        keep = 5
    clean_backups(keep=keep)


def _action_export() -> None:
    bid = _select_backup_id()
    if bid is None:
        return
    output_dir = prompt(" 导出目录（默认当前目录）: ", ".")
    export_backup(bid, output_dir=output_dir)


def _action_import() -> None:
    path = prompt(" 请输入 JSON 导出文件路径: ")
    if not path:
        print(f" {ERR} {RED}未输入路径{RESET}")
        return
    import_backup(path)


_MENU_ITEMS = [
    ("创建备份",     _action_backup),
    ("恢复备份",     _action_restore),
    ("查看备份列表", lambda: list_backups()),
    ("查看备份详情", _action_show),
    ("删除备份",     _action_delete),
    ("清理旧备份",   _action_clean),
    ("导出备份",     _action_export),
    ("导入备份",     _action_import),
]


def interactive_menu() -> None:
    while True:
        print(f"\n{GREEN}{'═' * 50}{RESET}")
        print(f" {BLUE}备份管理{RESET}")
        print(f"{GREEN}{'═' * 50}{RESET}")
        for i, (label, _) in enumerate(_MENU_ITEMS, 1):
            print(f"  {GREEN}{i}.{RESET} {label}")
        print(f"  {YELLOW}0.{RESET} 返回")
        print(f"{GREEN}{'─' * 50}{RESET}")

        choice = prompt_int(f" 请选择 (0-{len(_MENU_ITEMS)}): ")
        if choice is None or choice == 0:
            return
        if 1 <= choice <= len(_MENU_ITEMS):
            print()
            _MENU_ITEMS[choice - 1][1]()
        else:
            print(f" {ERR} {RED}无效选项{RESET}")
