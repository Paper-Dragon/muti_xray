# encoding: utf-8
import platform
import sys

if sys.version_info < (3, 6):
    sys.exit(
        "本程序需要 Python 3.6 或更高版本，当前版本: {}。"
        "请使用 python3 运行。".format(sys.version.split()[0])
    )

import xray
import backup as bk
from builder import build_config
from wizard import ask_black_domains, ask_proto_configs, ask_protocols
import links as lk
from ui import (
    GREEN, BLUE, RED, YELLOW, RESET,
    OK, INF, ERR,
    prompt, prompt_int,
)


def _do_install() -> None:
    xray.install()


def _do_upgrade() -> None:
    xray.upgrade()


def _do_install_geo() -> None:
    xray.install_geo()


def _do_uninstall() -> None:
    if prompt(f" {RED}确认完全卸载 Xray？(y/N): {RESET}").lower() != "y":
        print(f" {INF} {BLUE}已取消{RESET}")
        return
    xray.uninstall()


def _do_status() -> None:
    xray.status()


def _do_show_config() -> None:
    xray.print_config()


def _do_list_nodes() -> None:
    xray.list_nodes()


def _do_config_init() -> None:
    name = prompt(" 节点名称前缀（默认 Node）: ", "Node")
    publish = prompt(" 发布链接到 dpaste.com？(Y/n): ", "y")

    cards = xray.get_net_cards()
    if not cards:
        print(f" {ERR} {RED}未找到可用网卡，退出{RESET}")
        return
    print(f" {OK} {GREEN}共发现 {len(cards)} 张网卡{RESET}")

    blocked_domains = ask_black_domains()

    protocols = ask_protocols()
    print(f"\n {OK} {GREEN}已选择协议: {BLUE}{', '.join(protocols)}{RESET}")

    proto_configs = ask_proto_configs(protocols)

    cfg, all_links = build_config(
        cards=cards,
        protocols=protocols,
        proto_configs=proto_configs,
        blocked_domains=blocked_domains,
        name_prefix=name,
    )

    cfg.save(xray.CONFIG_PATH)
    print(f" {OK} {GREEN}配置已写入 {xray.CONFIG_PATH}{RESET}")

    xray.restart()
    print(f" {OK} {GREEN}Xray 服务已重启{RESET}")

    plain_links = [l for l in all_links if l.startswith("ip:")]
    quick_links = [l for l in all_links if not l.startswith("ip:")]

    if plain_links:
        lk.save_links(plain_links, append=False)
        lk.save_links(quick_links, append=True)
    else:
        lk.save_links(quick_links, append=False)

    if publish.lower() != "n":
        lk.publish_to_web()


def _do_backup() -> None:
    bk.interactive_menu()


_MENU = [
    ("安装 Xray 内核",          _do_install),
    ("升级 Xray 内核",          _do_upgrade),
    ("安装/更新 GeoIP GeoSite", _do_install_geo),
    ("初始化配置并创建节点",    _do_config_init),
    ("查看服务状态",            _do_status),
    ("显示当前配置",            _do_show_config),
    ("列出所有节点",            _do_list_nodes),
    ("备份管理",                _do_backup),
    ("卸载 Xray",               _do_uninstall),
]


def main_menu() -> None:
    while True:
        print(f"\n{GREEN}{'═' * 50}{RESET}")
        print(f" {RED}Muti-Xray 站群服务器隧道管理{RESET}")
        print(f"{GREEN}{'═' * 50}{RESET}")
        for i, (label, _) in enumerate(_MENU, 1):
            print(f"  {GREEN}{i}.{RESET} {label}")
        print(f"  {YELLOW}0.{RESET} 退出")
        print(f"{GREEN}{'─' * 50}{RESET}")

        choice = prompt_int(f" 请选择 (0-{len(_MENU)}): ")
        if choice is None or choice == 0:
            print(f" {INF} {BLUE}再见{RESET}")
            return
        if 1 <= choice <= len(_MENU):
            print()
            try:
                _MENU[choice - 1][1]()
            except Exception as e:
                print(f" {ERR} {RED}{e}{RESET}")
        else:
            print(f" {ERR} {RED}无效选项{RESET}")


if __name__ == "__main__":
    if platform.system() != "Windows" and not xray.is_root():
        print(f" {ERR} {RED}请使用 root 权限运行{RESET}")
        sys.exit(1)

    main_menu()
