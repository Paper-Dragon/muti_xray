# encoding: utf-8
"""
交互向导。

整合原 protocols.py + interactive.py + core/utils.py 的菜单逻辑。
所有函数仅负责"问用户"，不直接操作配置或网卡，
返回纯数据结构供 main.py / builder.py 使用。
"""
import os
import platform
import sys
from typing import Dict, List

# ── ANSI 颜色 ─────────────────────────────────────────────────────────────────

_G = '\033[92m'
_B = '\033[94m'
_R = '\033[91m'
_Y = '\033[93m'
_BG = '\033[40m'
_F = '\033[0m'
_OK  = f"{_G}{_BG}[成功]{_F}"
_WRN = f"{_Y}{_BG}[警告]{_F}"

# ── 协议与选项常量 ────────────────────────────────────────────────────────────

PROTOCOLS          = ["socks5", "vmess", "vless", "shadowsocks"]
SOCKS5_NETWORKS    = ["tcp", "tcp,udp"]
VMESS_TRANSPORTS   = ["raw", "ws", "xhttp"]
SS_NETWORKS        = ["tcp", "udp", "tcp,udp"]
SS_METHODS         = ["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305", "plain"]

# ── 跨平台菜单 ────────────────────────────────────────────────────────────────

_IS_WIN = platform.system() == "Windows"
_HAS_MENU = False

if not _IS_WIN:
    try:
        from simple_term_menu import TerminalMenu
        _HAS_MENU = True
    except (ImportError, NotImplementedError):
        pass


def _show_menu(options: List[str], title: str) -> int:
    """单选菜单，返回所选索引。"""
    if _HAS_MENU:
        try:
            idx = TerminalMenu(options, title=title).show()
            if idx is not None:
                return idx
        except (NotImplementedError, OSError):
            pass

    print(f"\n{_G}{title}{_F}")
    print("-" * 50)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("-" * 50)
    while True:
        try:
            choice = input(f"请选择 (1-{len(options)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return idx
            print(f"{_WRN} {_R}请输入 1 到 {len(options)} 之间的数字{_F}")
        except ValueError:
            print(f"{_WRN} {_R}请输入有效数字{_F}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{_WRN} {_Y}使用默认选项: {options[0]}{_F}")
            return 0


def _show_multi_menu(options: List[str], title: str) -> List[str]:
    """多选菜单，返回所选选项列表。"""
    if _HAS_MENU:
        try:
            menu = TerminalMenu(
                options, title=title,
                multi_select=True,
                show_multi_select_hint=True,
                multi_select_empty_ok=False,
            )
            indices = menu.show()
            if indices is None:
                return [options[0]]
            if isinstance(indices, int):
                return [options[indices]]
            return [options[i] for i in indices]
        except (NotImplementedError, OSError, TypeError):
            pass

    print(f"\n{_G}{title}{_F}")
    print(f"{_Y}（可多选，逗号分隔，如 1,3）{_F}")
    print("-" * 50)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("-" * 50)
    while True:
        try:
            raw = input(f"请选择 (1-{len(options)}, 逗号分隔): ").strip()
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            indices = [int(p) - 1 for p in parts]
            if all(0 <= i < len(options) for i in indices) and indices:
                selected = [options[i] for i in indices]
                print(f" {_OK} {_G}已选择: {', '.join(selected)}{_F}")
                return selected
            print(f"{_WRN} {_R}请输入有效范围{_F}")
        except ValueError:
            print(f"{_WRN} {_R}请输入有效数字{_F}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{_WRN} {_Y}使用默认选项: {options[0]}{_F}")
            return [options[0]]


def _yes_no(title: str) -> bool:
    """是/否菜单，返回 True(是) / False(否)。"""
    return _show_menu(["是", "否"], title) == 0


# ── 协议参数询问 ──────────────────────────────────────────────────────────────

def _ask_socks5() -> dict:
    network = SOCKS5_NETWORKS[_show_menu(SOCKS5_NETWORKS, "Socks5 网络层协议")]
    adv = _yes_no("开启高级配置？（可自定义端口和密码）")
    pin_passwd = False
    order_ports = False
    if adv:
        pin_passwd  = _yes_no("使用固定默认密码（放弃随机密码）？")
        order_ports = _yes_no("顺序分配端口（默认随机端口）？")
    return {
        "network_layer": network,
        "advanced_configuration": "y" if adv else "N",
        "sk5_pin_passwd_mode":   "y" if pin_passwd  else "N",
        "sk5_order_ports_mode":  "y" if order_ports else "N",
    }


def _ask_vmess() -> dict:
    transport = VMESS_TRANSPORTS[_show_menu(VMESS_TRANSPORTS, "VMess 传输层模式（raw=TCP，xhttp 支持 HTTP/1~3）")]
    kitsunebi = _yes_no("开启 Kitsunebi 兼容优化（AEAD 强制关闭）？")
    if kitsunebi:
        _apply_kitsunebi()
    return {"transport_mode": transport, "order_ports": "N"}


def _ask_vless() -> dict:
    transport = VMESS_TRANSPORTS[_show_menu(VMESS_TRANSPORTS, "VLess 传输层模式（raw=TCP，xhttp 支持 HTTP/1~3）")]
    order_ports = _yes_no("顺序分配端口（默认随机端口）？")
    return {"transport_mode": transport, "order_ports": "y" if order_ports else "N"}


def _ask_shadowsocks() -> dict:
    network     = SS_NETWORKS[_show_menu(SS_NETWORKS, "Shadowsocks 网络层")]
    method      = SS_METHODS[_show_menu(SS_METHODS, "加密方法")]
    order_ports = _yes_no("顺序分配端口（默认随机端口）？")
    try:
        password = input("请输入密码（直接回车随机生成）: ").strip()
    except (EOFError, KeyboardInterrupt):
        password = ""
        print(f"{_WRN} {_Y}将使用随机密码{_F}")
    return {
        "network_layer": network,
        "method": method,
        "password": password,
        "ss_order_ports_mode": "y" if order_ports else "N",
    }



def _apply_kitsunebi() -> None:
    """在 xray.service 中写入 XRAY_VMESS_AEAD_FORCED=false。"""
    svc = "/etc/systemd/system/xray.service"
    if not os.path.exists(svc):
        print(f"{_WRN} {_Y}服务文件不存在，跳过 Kitsunebi 优化{_F}")
        return
    with open(svc, encoding="utf-8") as f:
        content = f.read()
    if "XRAY_VMESS_AEAD_FORCED" in content:
        print("Kitsunebi 优化已生效，无需重复设置")
        return
    new_content = content.replace(
        "[Service]",
        '[Service]\nEnvironment="XRAY_VMESS_AEAD_FORCED=false"',
        1,
    )
    with open(svc, "w", encoding="utf-8") as f:
        f.write(new_content)
    os.system("systemctl daemon-reload")
    print(f" {_OK} {_G}Kitsunebi 优化已写入服务文件{_F}")


# ── 公开接口 ──────────────────────────────────────────────────────────────────

def ask_protocols() -> List[str]:
    """多选协议，至少选一个，返回协议名列表。"""
    try:
        return _show_multi_menu(PROTOCOLS, "请选择要创建的协议（可多选）")
    except (EOFError, KeyboardInterrupt, SystemExit):
        print(f"\n{_WRN} {_Y}使用默认协议: {PROTOCOLS[0]}{_F}")
        return [PROTOCOLS[0]]


def ask_proto_configs(protocols: List[str]) -> Dict[str, dict]:
    """
    按协议列表顺序交互式询问参数。
    返回 {协议名: 参数dict} 映射。
    """
    _funcs = {
        "socks5":      _ask_socks5,
        "vmess":       _ask_vmess,
        "vless":       _ask_vless,
        "shadowsocks": _ask_shadowsocks,
    }
    result: Dict[str, dict] = {}
    for proto in protocols:
        print(f"\n{_G}{'─' * 50}{_F}")
        print(f" {_OK} {_B}配置协议: {_G}{proto}{_F}")
        print(f"{_G}{'─' * 50}{_F}")
        if proto not in _funcs:
            print(f"{_WRN} {_Y}协议 {proto} 尚未实现，跳过{_F}")
            continue
        result[proto] = _funcs[proto]()
    return result


def ask_black_domains() -> List[str]:
    """交互式收集要封禁的域名列表，输入 END 结束。"""
    domains: List[str] = []
    print(f" {_B}请输入要封禁的域名（输入 END 结束，直接回车跳过）:{_F}")
    try:
        while True:
            d = input(f"{_G}域名> {_F}").strip()
            if d.upper() == "END" or d == "":
                break
            domains.append(d)
            print(f" {_OK} {_B}已添加: {d}{_F}")
    except (EOFError, KeyboardInterrupt):
        pass
    return domains
