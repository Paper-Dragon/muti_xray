# encoding: utf-8
"""主入口文件"""
import sys

if sys.version_info < (3, 6):
    sys.exit("本程序需要 Python 3.6 或更高版本，当前版本: {0}。请使用 python3 运行。".format(sys.version.split()[0]))

import argparse
import platform

from utils import is_root, xray, Error, RED, FONT
from core.interactive import config_init
from core.utils import call_xray_method


if __name__ == '__main__':
    # Windows 上不强制要求管理员权限（某些操作可能需要）
    if platform.system() != "Windows" and not is_root():
        print("{0} {1}请使用root运行{2}".format(Error, RED, FONT))
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="{0}站群服务器隧道管理脚本{1}\n\n"
                   "用于管理和配置 Xray 代理节点，支持多网卡、多 IP 的站群服务器场景。\n"
                   "支持 VMess、Shadowsocks、Socks5 等多种协议。".format(RED, FONT),
        add_help=False,
        epilog="使用示例:\n"
               "  {0} install                    # 首次安装 Xray 内核\n"
               "  {0} config_init --name Node-1  # 初始化配置并创建节点\n"
               "  {0} --list                     # 列出所有已配置的节点\n"
               "  {0} status                     # 查看 Xray 服务运行状态\n"
               "  {0} show_config                # 查看当前配置文件内容\n"
               "\n更多信息请查看: https://github.com/Paper-Dragon/muti_xray".format(sys.argv[0]),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-h', '--help', action='help',
                        default=argparse.SUPPRESS, 
                        help='显示此帮助消息并退出。'
                             ' 也可使用 "命令 -h" 查看特定命令的详细帮助，'
                             ' 例如: python main.py install -h')

    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="列出站群服务器内的所有节点。"
                             " 显示所有已配置的入站节点及其名称。")

    subparsers = parser.add_subparsers(
        help='可用命令（使用 "命令 -h" 查看详细帮助）',
        dest='command',
        metavar='命令'
    )

    parser_install = subparsers.add_parser(
        'install', 
        help='安装或升级 Xray 内核',
        description='安装或升级 Xray 内核。'
                   ' ⚠️  警告: 执行此命令会删除所有现有配置文件！'
                   ' 建议在首次使用或确认要重置配置时执行。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python main.py install    # 安装最新版本的 Xray 内核'
    )
    parser_install.set_defaults(func=call_xray_method('install'))

    parser_upgrade = subparsers.add_parser(
        'upgrade', 
        help='升级 Xray 内核（与 install 相同）',
        description='升级 Xray 内核到最新版本。此命令与 install 功能相同。'
                   ' ⚠️  警告: 会删除现有配置！'
    )
    parser_upgrade.set_defaults(func=call_xray_method('upgrade'))

    parser_install_geo = subparsers.add_parser(
        'install_geo', 
        help='安装或升级 Geo 数据库',
        description='安装或更新 GeoIP 和 GeoSite 数据库。'
                   ' 这些数据库用于路由规则和域名匹配。'
                   ' 建议定期更新以获得最新的地理位置和域名数据。',
        epilog='示例:\n'
               '  python main.py install_geo    # 更新 Geo 数据库'
    )
    parser_install_geo.set_defaults(func=call_xray_method('install_geo'))

    parser_config_init = subparsers.add_parser(
        'config_init', 
        help='初始化配置并创建节点',
        description='初始化 Xray 配置并创建代理节点。'
                   ' 此命令会交互式地引导您完成以下步骤:\n'
                   '  1. 扫描并识别所有网卡和 IP 地址\n'
                   '  2. 配置黑名单域名（可选）\n'
                   '  3. 选择协议类型（VMess、Shadowsocks、Socks5 等）\n'
                   '  4. 为每个网卡自动创建节点\n'
                   '  5. 生成配置文件并重启 Xray 服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python main.py config_init --name MyNode              # 创建节点，名称为 MyNode-IP\n'
               '  python main.py config_init --name Node-1 --publish false  # 创建节点但不发布到网络'
    )
    parser_config_init.add_argument(
        '--name', 
        type=str,
        default='Node',
        help='节点名称的前缀。每个节点将自动添加 IP 后缀，'
             ' 例如: --name Node 会生成 Node-192-168-1-1 这样的节点名。'
             ' 默认值: Node。'
    )
    parser_config_init.add_argument(
        '--publish', 
        type=str, 
        default='true',
        choices=['true', 'false'],
        help='是否将节点配置发布到 dpaste.com 网站（用于分享配置链接）。'
             ' 默认值: true（发布）。'
             ' 设置为 false 时仅保存到本地文件。'
    )
    parser_config_init.set_defaults(func=config_init)

    parser_uninstall = subparsers.add_parser(
        'uninstall', 
        help='卸载 Xray 服务',
        description='从系统中完全移除 Xray 服务和所有相关文件。'
                   ' ⚠️  警告: 此操作不可逆，会删除所有配置文件、日志和程序文件！'
                   ' 执行前请确保已备份重要配置。',
        epilog='示例:\n'
               '  python main.py uninstall    # 卸载 Xray（会删除配置文件）'
    )
    parser_uninstall.set_defaults(func=call_xray_method('uninstall'))

    parser_status = subparsers.add_parser(
        'status', 
        help='查看 Xray 服务运行状态',
        description='显示 Xray 服务的当前运行状态。'
                   ' 包括服务是否正在运行、进程信息等。'
                   ' 类似 systemctl status xray 命令的输出。',
        epilog='示例:\n'
               '  python main.py status    # 查看服务状态'
    )
    parser_status.set_defaults(func=call_xray_method('status'))

    parser_config = subparsers.add_parser(
        'show_config', 
        help='查看当前配置文件内容',
        description='显示当前 Xray 配置文件（/usr/local/etc/xray/config.json）的内容。'
                   ' 用于检查当前配置是否正确，或用于调试问题。'
                   ' 输出为 JSON 格式，可能较长。',
        epilog='示例:\n'
               '  python main.py show_config    # 显示配置文件内容'
    )
    parser_config.set_defaults(func=call_xray_method('print_file_config'))

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # 执行函数
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse 在显示帮助信息后会正常退出（SystemExit(code=0)）
        # 只有在非正常退出时才报错
        if e.code != 0:
            print("解析参数出错！")
        sys.exit(e.code if e.code is not None else 0)
    
    # 处理--list参数
    if args.list:
        xray.list_node()
    elif hasattr(args, 'func'):
        args.func(args)
