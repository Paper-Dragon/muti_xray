# encoding: utf-8
import os
import platform
from typing import Dict, List

from ui import GREEN, BLUE, RED, YELLOW, RESET, OK, WRN

PROTOCOLS          = ["socks5", "vmess", "vless", "shadowsocks", "trojan"]
SOCKS5_NETWORKS    = ["tcp", "tcp,udp"]
VMESS_TRANSPORTS   = ["raw", "ws", "xhttp"]
SS_NETWORKS        = ["tcp", "udp", "tcp,udp"]
SS_METHODS         = ["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305", "plain"]

_IS_WIN = platform.system() == "Windows"
_HAS_MENU = False

if not _IS_WIN:
    try:
        from simple_term_menu import TerminalMenu
        _HAS_MENU = True
    except (ImportError, NotImplementedError):
        pass


def _show_menu(options: List[str], title: str) -> int:
    if _HAS_MENU:
        try:
            idx = TerminalMenu(options, title=title).show()
            if idx is not None:
                return idx
        except (NotImplementedError, OSError):
            pass

    print(f"\n{GREEN}{title}{RESET}")
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
            print(f"{WRN} {RED}请输入 1 到 {len(options)} 之间的数字{RESET}")
        except ValueError:
            print(f"{WRN} {RED}请输入有效数字{RESET}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{WRN} {YELLOW}使用默认选项: {options[0]}{RESET}")
            return 0


def _show_multi_menu(options: List[str], title: str) -> List[str]:
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

    print(f"\n{GREEN}{title}{RESET}")
    print(f"{YELLOW}（可多选，逗号分隔，如 1,3）{RESET}")
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
                print(f" {OK} {GREEN}已选择: {', '.join(selected)}{RESET}")
                return selected
            print(f"{WRN} {RED}请输入有效范围{RESET}")
        except ValueError:
            print(f"{WRN} {RED}请输入有效数字{RESET}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{WRN} {YELLOW}使用默认选项: {options[0]}{RESET}")
            return [options[0]]


def _yes_no(title: str) -> bool:
    return _show_menu(["是", "否"], title) == 0


DEFAULT_PORT_LO = 10000
DEFAULT_PORT_HI = 30000


def ask_port_range() -> tuple:
    try:
        raw = input(
            f" 随机端口范围（格式 起始-结束，直接回车使用默认 "
            f"{DEFAULT_PORT_LO}-{DEFAULT_PORT_HI}）: "
        ).strip()
        if not raw:
            return DEFAULT_PORT_LO, DEFAULT_PORT_HI
        parts = raw.split("-")
        lo, hi = int(parts[0].strip()), int(parts[1].strip())
        if lo < 1 or hi > 65535 or lo >= hi:
            print(f"{WRN} {RED}范围无效，使用默认 {DEFAULT_PORT_LO}-{DEFAULT_PORT_HI}{RESET}")
            return DEFAULT_PORT_LO, DEFAULT_PORT_HI
        return lo, hi
    except (ValueError, IndexError):
        print(f"{WRN} {YELLOW}格式错误，使用默认 {DEFAULT_PORT_LO}-{DEFAULT_PORT_HI}{RESET}")
        return DEFAULT_PORT_LO, DEFAULT_PORT_HI
    except (EOFError, KeyboardInterrupt):
        print()
        return DEFAULT_PORT_LO, DEFAULT_PORT_HI


def _ask_start_port(proto_name: str) -> int:
    try:
        raw = input(f" {proto_name} 起始端口（如 20001，直接回车从 10001 开始）: ").strip()
        if not raw:
            return 0
        port = int(raw)
        if 1 <= port <= 65535:
            return port
        print(f"{WRN} {RED}端口需在 1-65535 之间，将使用默认值{RESET}")
        return 0
    except (ValueError, EOFError, KeyboardInterrupt):
        return 0


def _ask_socks5() -> dict:
    network = SOCKS5_NETWORKS[_show_menu(SOCKS5_NETWORKS, "Socks5 网络层协议")]
    adv = _yes_no("开启高级配置？（可自定义端口和密码）")
    pin_passwd = False
    order_ports = False
    start_port = 0
    if adv:
        pin_passwd  = _yes_no("使用固定默认密码（放弃随机密码）？")
        order_ports = _yes_no("顺序分配端口（放弃随机端口）？")
        if order_ports:
            start_port = _ask_start_port("Socks5")
    return {
        "network_layer": network,
        "advanced_configuration": "y" if adv else "N",
        "sk5_pin_passwd_mode":   "y" if pin_passwd  else "N",
        "sk5_order_ports_mode":  "y" if order_ports else "N",
        "start_port": start_port,
    }


def _ask_vmess() -> dict:
    transport = VMESS_TRANSPORTS[_show_menu(VMESS_TRANSPORTS, "VMess 传输层模式（raw=TCP，xhttp 支持 HTTP/1~3）")]
    order_ports = _yes_no("顺序分配端口（放弃随机端口）？")
    start_port = 0
    if order_ports:
        start_port = _ask_start_port("VMess")
    kitsunebi = _yes_no("开启 Kitsunebi 兼容优化（AEAD 强制关闭）？")
    if kitsunebi:
        _apply_kitsunebi()
    return {"transport_mode": transport, "order_ports": "y" if order_ports else "N", "start_port": start_port}


def _ask_trojan() -> dict:
    transport = VMESS_TRANSPORTS[_show_menu(VMESS_TRANSPORTS, "Trojan 传输层模式（raw=TCP，xhttp 支持 HTTP/1~3）")]
    order_ports = _yes_no("顺序分配端口（放弃随机端口）？")
    start_port = 0
    if order_ports:
        start_port = _ask_start_port("Trojan")
    try:
        password = input("请输入 Trojan 密码（直接回车随机生成）: ").strip()
    except (EOFError, KeyboardInterrupt):
        password = ""
        print(f"{WRN} {YELLOW}将使用随机密码{RESET}")

    use_custom_cert = _yes_no("使用已有证书？（否则自动生成自签证书）")
    cert_file = key_file = ""
    if use_custom_cert:
        try:
            cert_file = input("证书文件路径（fullchain.crt）: ").strip()
            key_file  = input("私钥文件路径（private.key）: ").strip()
        except (EOFError, KeyboardInterrupt):
            cert_file = key_file = ""
            print(f"{WRN} {YELLOW}将使用自签证书{RESET}")

    return {
        "transport_mode": transport,
        "order_ports":    "y" if order_ports else "N",
        "start_port":     start_port,
        "password":       password,
        "cert_file":      cert_file,
        "key_file":       key_file,
    }


def _ask_vless() -> dict:
    transport = VMESS_TRANSPORTS[_show_menu(VMESS_TRANSPORTS, "VLess 传输层模式（raw=TCP，xhttp 支持 HTTP/1~3）")]
    order_ports = _yes_no("顺序分配端口（放弃随机端口）？")
    start_port = 0
    if order_ports:
        start_port = _ask_start_port("VLess")
    return {"transport_mode": transport, "order_ports": "y" if order_ports else "N", "start_port": start_port}


def _ask_shadowsocks() -> dict:
    network     = SS_NETWORKS[_show_menu(SS_NETWORKS, "Shadowsocks 网络层")]
    method      = SS_METHODS[_show_menu(SS_METHODS, "加密方法")]
    order_ports = _yes_no("顺序分配端口（放弃随机端口）？")
    start_port = 0
    if order_ports:
        start_port = _ask_start_port("Shadowsocks")
    try:
        password = input("请输入密码（直接回车随机生成）: ").strip()
    except (EOFError, KeyboardInterrupt):
        password = ""
        print(f"{WRN} {YELLOW}将使用随机密码{RESET}")
    return {
        "network_layer": network,
        "method": method,
        "password": password,
        "ss_order_ports_mode": "y" if order_ports else "N",
        "start_port": start_port,
    }


def _apply_kitsunebi() -> None:
    svc = "/etc/systemd/system/xray.service"
    if not os.path.exists(svc):
        print(f"{WRN} {YELLOW}服务文件不存在，跳过 Kitsunebi 优化{RESET}")
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
    print(f" {OK} {GREEN}Kitsunebi 优化已写入服务文件{RESET}")


def ask_protocols() -> List[str]:
    try:
        return _show_multi_menu(PROTOCOLS, "请选择要创建的协议（可多选）")
    except (EOFError, KeyboardInterrupt, SystemExit):
        print(f"\n{WRN} {YELLOW}使用默认协议: {PROTOCOLS[0]}{RESET}")
        return [PROTOCOLS[0]]


def ask_proto_configs(protocols: List[str]) -> Dict[str, dict]:
    _funcs = {
        "socks5":      _ask_socks5,
        "vmess":       _ask_vmess,
        "vless":       _ask_vless,
        "shadowsocks": _ask_shadowsocks,
        "trojan":      _ask_trojan,
    }
    result: Dict[str, dict] = {}
    for proto in protocols:
        print(f"\n{GREEN}{'─' * 50}{RESET}")
        print(f" {OK} {BLUE}配置协议: {GREEN}{proto}{RESET}")
        print(f"{GREEN}{'─' * 50}{RESET}")
        if proto not in _funcs:
            print(f"{WRN} {YELLOW}协议 {proto} 尚未实现，跳过{RESET}")
            continue
        result[proto] = _funcs[proto]()
    return result


def ask_black_domains() -> List[str]:
    domains: List[str] = []
    print(f" {BLUE}请输入要封禁的域名（输入 END 结束，直接回车跳过）:{RESET}")
    try:
        while True:
            d = input(f"{GREEN}域名> {RESET}").strip()
            if d.upper() == "END" or d == "":
                break
            domains.append(d)
            print(f" {OK} {BLUE}已添加: {d}{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass
    return domains
