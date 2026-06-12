# encoding: utf-8
"""
Muti-Xray 主入口。

CLI 子命令分发，调用 xray.py / wizard.py / builder.py / links.py。
"""
import argparse
import platform
import sys

if sys.version_info < (3, 6):
    sys.exit(
        "本程序需要 Python 3.6 或更高版本，当前版本: {}。"
        "请使用 python3 运行。".format(sys.version.split()[0])
    )

import xray
from builder import build_config
from wizard import ask_black_domains, ask_proto_configs, ask_protocols
import links as lk

_R = '\033[91m'
_G = '\033[92m'
_B = '\033[94m'
_BG = '\033[40m'
_F = '\033[0m'
_ERR = f"{_R}{_BG}[错误]{_F}"
_OK  = f"{_G}{_BG}[成功]{_F}"
_INF = f"{_B}{_BG}[信息]{_F}"


# ── config_init 主流程 ────────────────────────────────────────────────────────

def config_init(args) -> None:
    """交互式初始化：扫网卡 → 选协议 → 建节点 → 写配置 → 重启服务 → 保存链接。"""
    cards = xray.get_net_cards()
    if not cards:
        print(f" {_ERR} {_R}未找到可用网卡，退出{_F}")
        sys.exit(1)
    print(f" {_OK} {_G}共发现 {len(cards)} 张网卡{_F}")

    blocked_domains = ask_black_domains()

    protocols = ask_protocols()
    print(f"\n {_OK} {_G}已选择协议: {_B}{', '.join(protocols)}{_F}")

    proto_configs = ask_proto_configs(protocols)

    cfg, all_links = build_config(
        cards=cards,
        protocols=protocols,
        proto_configs=proto_configs,
        blocked_domains=blocked_domains,
        name_prefix=args.name,
    )

    cfg.save(xray.CONFIG_PATH)
    print(f" {_OK} {_G}配置已写入 {xray.CONFIG_PATH}{_F}")

    xray.restart()
    print(f" {_OK} {_G}Xray 服务已重启{_F}")

    # 分离 socks5 明文信息（以 "ip:" 开头的行）与快速链接
    plain_links = [l for l in all_links if l.startswith("ip:")]
    quick_links = [l for l in all_links if not l.startswith("ip:")]

    if plain_links:
        lk.save_links(plain_links, append=False)
        lk.save_links(quick_links, append=True)
    else:
        lk.save_links(quick_links, append=False)

    if args.publish == "true":
        lk.publish_to_web()


# ── CLI 参数定义 ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{_R}站群服务器隧道管理脚本{_F}\n\n"
                    "支持 VMess、Shadowsocks、Socks5 等多种协议，多网卡多 IP 场景。",
        add_help=False,
        epilog=(
            "使用示例:\n"
            "  python main.py install               # 安装 Xray 内核\n"
            "  python main.py config_init --name N  # 初始化配置\n"
            "  python main.py --list                # 列出所有节点\n"
            "  python main.py status                # 查看服务状态\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-h", "--help", action="help",
        default=argparse.SUPPRESS,
        help="显示帮助信息并退出",
    )
    parser.add_argument(
        "--list", "-L", action="store_true", default=False,
        help="列出配置文件中所有节点",
    )

    sub = parser.add_subparsers(dest="command", metavar="命令")

    # install
    p = sub.add_parser("install", help="安装或重置 Xray 内核（会删除现有配置）")
    p.set_defaults(func=lambda _: xray.install())

    # upgrade
    p = sub.add_parser("upgrade", help="升级 Xray 内核")
    p.set_defaults(func=lambda _: xray.upgrade())

    # install_geo
    p = sub.add_parser("install_geo", help="安装/更新 GeoIP 和 GeoSite 数据库")
    p.set_defaults(func=lambda _: xray.install_geo())

    # uninstall
    p = sub.add_parser("uninstall", help="完全卸载 Xray 服务和配置")
    p.set_defaults(func=lambda _: xray.uninstall())

    # status
    p = sub.add_parser("status", help="查看 Xray 服务运行状态")
    p.set_defaults(func=lambda _: xray.status())

    # show_config
    p = sub.add_parser("show_config", help="显示当前配置文件内容")
    p.set_defaults(func=lambda _: xray.print_config())

    # config_init
    p = sub.add_parser("config_init", help="交互式初始化配置并创建节点")
    p.add_argument(
        "--name", type=str, default="Node",
        help="节点名称前缀，自动追加 IP 后缀（默认: Node）",
    )
    p.add_argument(
        "--publish", type=str, default="true", choices=["true", "false"],
        help="是否发布链接到 dpaste.com（默认: true）",
    )
    p.set_defaults(func=config_init)

    return parser


# ── 入口 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if platform.system() != "Windows" and not xray.is_root():
        print(f" {_ERR} {_R}请使用 root 权限运行{_F}")
        sys.exit(1)

    parser = _build_parser()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print("参数解析出错")
        sys.exit(e.code if e.code is not None else 0)

    if args.list:
        xray.list_nodes()
    elif hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)
