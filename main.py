# encoding: utf-8
import argparse
import os
import random
import string
import sys
import time
import uuid
from typing import List, Optional, AnyStr

from simple_term_menu import TerminalMenu

from models import ShadowSocksSettings, RAWSettingsConfig, StreamSettingsConfig, InboundConfig
from utils import *


xray = Xray()
publish = Publish()


def uninstall(args):
    xray.uninstall()


def install(args):
    xray.install()

def upgrade(args):
    xray.upgrade()

def install_geo(args):
    xray.install_geo()

def create_vmess_node(transport_layer, listen_ip, client_ip, port, tag, name, random_port=False):
    """
    Create Single Vmess Inbound Node

    :param transport_layer: 传输层协议 raw(即tcp模式),ws,xhttp(支持HTTP/1.1、HTTP/2、HTTP/3)
    :param listen_ip: 配置文件中监听的IP地址（内网IP）
    :param client_ip: 客户端连接使用的IP地址（公网IP）
    :param port: server port
    :param name: node name
    :param random_port: Bool random port
    :param tag: tag[0]: in-192-168-23-129   tag[1] out-192-168-23-129 tag[2]
    """
    uuids = str(uuid.uuid4())
    if random_port:
        port = random.randint(10000, 30000)

    path = f"/c{''.join(random.sample(string.ascii_letters + string.digits, 5))}c/"
    # 配置文件使用内网IP监听
    xray.insert_inbounds_vmess_config(ipaddr=listen_ip, port=port, inbounds_tag=tag[0],
                                      uuids=uuids, alert_id=0, path=path, name=name, transport_layer=transport_layer)
    # VMess链接使用公网IP供客户端连接
    publish.create_vmess_quick_link(ps=name, address=client_ip, uuid=uuids,
                                        port=port, alert_id=0, mode=transport_layer, path=path)


def create_sk5_node(network_layer, ip, port, tag, name, advanced_configuration, sk5_order_ports_mode,
                    sk5_pin_passwd_mode):
    # print("DEBUG check mode sock5")
    # 端口等熵变大
    if advanced_configuration == "y":
        if sk5_order_ports_mode == "N":
            port = random.randint(10000, 30000)
    # 随机用户预先生成，决定是否覆盖
    user = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    passwd = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    # 部署高级配置 固定用户名密码
    if advanced_configuration == "y":
        if sk5_pin_passwd_mode == "y":
            # 客户增加需求，固定用户名密码端口号？？？？？？？？？
            user = '147258'
            passwd = '147258'

    if network_layer == "tcp":
        xray.insert_inbounds_sk5_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                            name=name)
    elif network_layer == "tcp,udp":
        xray.insert_inbounds_sk5_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                                name=name, network_layer_support_udp=True)
    else:
        print(
            f"{Warning} {RED}{BLACK_BG}作者还没写这个模式{FONT} {network_layer} "
            f"请联系作者 {GREEN}{BLACK_BG}{author_email}{FONT}"
        )
        exit(2)

    # 整理生成快捷链接的数据，并记录在 publish.config
    raw_link = f"ip:{ip} 用户名:{user} 密码:{passwd} 端口：{port} 节点名称:{name}"
    publish.raw_config_list.append(raw_link)
    quick_link = f"socks://{publish.encode_b64(f'{user}:{passwd}')}@{ip}:{port}#{name}"
    publish.quick_config_link_list.append(quick_link)


def create_v2_sk5_node(v2_transport_layer, sk5_network_layer, listen_ip, client_ip, port, tag, name, advanced_configuration,
                       order_ports_mode, sk5_pin_passwd_mode):
    """
    创建VMess+Socks5组合节点
    
    :param v2_transport_layer: VMess传输层协议
    :param sk5_network_layer: Socks5网络层协议
    :param listen_ip: 配置文件中监听的IP地址（内网IP）
    :param client_ip: 客户端连接使用的IP地址（公网IP）
    :param port: 端口号
    :param tag: 标签列表
    :param name: 节点名称
    :param advanced_configuration: 高级配置选项
    :param order_ports_mode: 顺序端口模式
    :param sk5_pin_passwd_mode: Socks5固定密码模式
    """
    v2_tag = [f"v2-{t}" if i < 2 else t for i, t in enumerate(tag)]
    name = f"v2-{name}"

    xray.insert_routing_config(v2_tag[0], v2_tag[1])
    xray.insert_outbounds_config(ipaddr=listen_ip, outbound_tag=v2_tag[1])
    random_port = True
    if order_ports_mode == 'y':
        random_port = False
    create_vmess_node(transport_layer=v2_transport_layer,
                      listen_ip=listen_ip, client_ip=client_ip, port=port, tag=tag, name=name, random_port=random_port)

    sk5_tag = [f"sk5-{t}" if i < 2 else t for i, t in enumerate(tag)]
    name = f"sk5-{name}"

    xray.insert_routing_config(sk5_tag[0], sk5_tag[1])
    xray.insert_outbounds_config(ipaddr=listen_ip, outbound_tag=sk5_tag[1])
    port += 1
    create_sk5_node(network_layer=sk5_network_layer, ip=listen_ip, port=port, tag=tag, name=name,
                    advanced_configuration=advanced_configuration,
                    sk5_order_ports_mode=order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)


def create_shadowsocks_node(method, password,
                            network_layer = "tcp,udp",
                            transport_layer = "raw",
                            ip: str = "127.0.0.1", port: int = 1080, tag: str = "identifier",
                            name: Optional[AnyStr] = None):
    """
    创建并插入一个 Shadowsocks 节点配置。

    :param transport_layer:
    :type network_layer: 'tcp', 'udp', 'tcp,udp'
    :param network_layer:  网络层协议 tcp,udp, tcp+udp
    :param method: (str) 加密方法（未指定时默认为 "plain"）。
    :param password: (str) 连接密码（未提供时会生成一个随机密码）。
    :param ip: (str) 监听的 IP 地址。
    :param port: (int) 监听的端口号。
    :param tag: (list) 标签列表（使用第一个元素）。
    :param name: (str) Shadowsocks 节点的名称。

    :return: None

    :note: 当前仅支持 RAW 模式。
    """

    if not password:
        password = f"c{''.join(random.sample(string.ascii_letters + string.digits, 5))}c"
    if not method:
        method = "plain"
    shadowsocks_settings = ShadowSocksSettings(
        network=network_layer,
        method=method,
        password=password
    )
    raw_transport_layer_settings = RAWSettingsConfig()
    # TODO: 传输层临时先用raw模式吧，后面再支持其他的

    stream_settings = StreamSettingsConfig(
        network=transport_layer,
        raw_settings=raw_transport_layer_settings
    )
    config = InboundConfig(listen=ip, port=port,protocol="shadowsocks",
                                  settings=shadowsocks_settings,
                                  tag=tag[0],
                                  streamSettings=stream_settings,
                                  ps=name)
    xray.insert_inbounds_config(config)

    publish.create_shadowsocks_quick_link(method=shadowsocks_settings.method,
                                          password=shadowsocks_settings.password,
                                          ip=config.listen, port = config.port,
                                          network_layer_type=shadowsocks_settings.network,
                                          name=config.ps)

    # 也许调试用？
    return config


def compatible_kitsunebi():
    if os.system(f'grep XRAY_VMESS_AEAD_FORCED {xray.service_config_file} >/dev/null'):
        os.system(f"sed -i '/\\[Service\\]/a\\\\Environment=\"XRAY_VMESS_AEAD_FORCED=false\"' {xray.service_config_file}")
        os.system("systemctl daemon-reload")
        xray.restart()
    else:
        print("经过查询，Kitsunebi 已经优化过了！")


def config_init(args):
    # 获取网卡信息
    net_card = xray.get_net_card()
    print(f" {Info} {GREEN}网卡信息获取完成{FONT}")
    print(f" {Info} {GREEN}正在生成网络黑洞，用于制作ip和域名封禁功能...{FONT}")

    # 初始化配置对象和生成网络黑洞
    xray.init_config()
    print(f" {OK} {RED}{GREEN_BG}网络黑洞生成成功...{FONT}")

    # 增加黑名单域名
    while True:
        black_domain = []
        black_domain_v = input(f"{GREEN}请输入被封禁的域名{FONT}{RED}输入END结束{FONT}")
        if black_domain_v == "END":
            break
        black_domain.append(black_domain_v)
    if black_domain != '':
        xray.insert_black_domain(black_domain)

    disable_aead_verify = "N"
    # 选择传输层协议
    protocol_options = ["socks5", "vmess", "trojan", "shadowsocks", "vmess-socks5"]
    protocol_menu = TerminalMenu(protocol_options, title="请选择你要制作的协议(按上下键移动，回车选择)").show()
    protocol = protocol_options[protocol_menu]

    advanced_configuration = "N"
    sk5_pin_passwd_mode = "N"
    sk5_order_ports_mode = "N"

    if protocol == "socks5":
        # socks5 network layer protocol
        socks5_network_layer_options = ["tcp", "tcp,udp"]
        socks5_network_layer_menu = TerminalMenu(socks5_network_layer_options, title="你想要什么socks5网络层协议")
        socks5_network_layer = socks5_network_layer_options[socks5_network_layer_menu.show()]

        advanced_configuration_options: List[str] = ["y", "N"]
        advanced_configuration_menu = TerminalMenu(advanced_configuration_options, title="socks5高级配置").show()
        advanced_configuration = advanced_configuration_options[advanced_configuration_menu]
        if advanced_configuration == "y":
            sk5_pin_passwd_mode_options: List[str] = ["y", "N"]
            sk5_pin_passwd_mode_menu = TerminalMenu(sk5_pin_passwd_mode_options, title="启动默认密码并且放弃随机密码").show()
            sk5_pin_passwd_mode = sk5_pin_passwd_mode_options[sk5_pin_passwd_mode_menu]

            sk5_order_ports_mode_options: List[str] = ["y", "N"]
            sk5_order_ports_mode_menu = TerminalMenu(sk5_order_ports_mode_options, title="是否顺序生成端口？默认随机生成").show()
            sk5_order_ports_mode = sk5_order_ports_mode_options[sk5_order_ports_mode_menu]
    elif protocol == "vmess":
        vmess_transport_mode_options: List[str] = ["ws", "raw", "xhttp"]
        vmess_transport_mode_menu = TerminalMenu(vmess_transport_mode_options, title="输入要创建的传输层模式（raw即tcp模式，xhttp支持HTTP/1.1、HTTP/2、HTTP/3）").show()
        vmess_transport_mode = vmess_transport_mode_options[vmess_transport_mode_menu]
        disable_aead_verify_options = ["y", "N"]
        disable_aead_verify_menu = TerminalMenu(disable_aead_verify_options, title="是否开启面向Kitsunebi优化(默认开启）").show()
        disable_aead_verify = disable_aead_verify_options[disable_aead_verify_menu]
        if disable_aead_verify != "N":
            compatible_kitsunebi()
    elif protocol == "vmess-socks5":
        # socks5 network layer protocol
        socks5_network_layer_options = ["tcp", "tcp+udp"]
        socks5_network_layer_menu = TerminalMenu(socks5_network_layer_options, title="你想要什么socks5网络层协议")
        socks5_network_layer = socks5_network_layer_options[socks5_network_layer_menu.show()]

        vmess_transport_mode_options: List[str] = ["ws", "raw", "xhttp"]
        vmess_transport_mode_menu = TerminalMenu(vmess_transport_mode_options, title="输入要创建vmess的传输层模式（raw即tcp模式，xhttp支持HTTP/1.1、HTTP/2、HTTP/3）").show()
        vmess_transport_mode = vmess_transport_mode_options[vmess_transport_mode_menu]
        disable_aead_verify_options = ["y", "N"]
        disable_aead_verify_menu = TerminalMenu(disable_aead_verify_options,title="是否开启面向Kitsunebi优化(默认开启）").show()
        disable_aead_verify = disable_aead_verify_options[disable_aead_verify_menu]
        advanced_configuration_options: List[str] = ["y", "N"]
        advanced_configuration_menu = TerminalMenu(advanced_configuration_options, title="是否要进入高级配置，定制功能").show()
        advanced_configuration = advanced_configuration_options[advanced_configuration_menu]
        sk5_pin_passwd_mode = "N"
        sk5_order_ports_mode_menu = "N"
        if advanced_configuration == "y":
            sk5_pin_passwd_mode_options: List[str] = ["y", "N"]
            sk5_pin_passwd_mode_menu = TerminalMenu(sk5_pin_passwd_mode_options, title="启动sk5默认密码放弃随机密码？").show()
            sk5_pin_passwd_mode = sk5_pin_passwd_mode_options[sk5_pin_passwd_mode_menu]
            sk5_order_ports_mode_options: List[str] = ["y", "N"]
            sk5_order_ports_mode_menu = TerminalMenu(sk5_order_ports_mode_options,
                                                     title="是否顺序生成端口？默认随机生成").show()
            sk5_order_ports_mode = sk5_order_ports_mode_options[sk5_order_ports_mode_menu]
        if disable_aead_verify != "N":
            compatible_kitsunebi()
    elif protocol == "shadowsocks":
        shadowsocks_network_layer_options = ['tcp', 'udp', 'tcp,udp']
        shadowsocks_network_layer_menu = TerminalMenu(shadowsocks_network_layer_options, title="你想要什么网络层协议")
        shadowsocks_network_layer = shadowsocks_network_layer_options[shadowsocks_network_layer_menu.show()]

        method_options = ["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305", "plain"]
        method_menu = TerminalMenu(method_options,title="加密方法").show()
        method = method_options[method_menu]
        password = input("请输入密码(回车则随机生成密码):")
    else:
        print(
            f"{Warning} {RED}作者还没写这个模式{FONT} {protocol} "
            f"请联系作者 {GREEN}{author_email}{FONT}"
        )
        exit(2)

    # 若为顺序生成端口模式，从这个端口开始顺序生成
    port = 10000

    # 以网卡为index生成配置
    for card_info in net_card:
        listen_ip = card_info['listen_ip']  # 配置文件监听的IP（内网IP）
        client_ip = card_info['client_ip']  # 客户端连接的IP（公网IP）
        interface_name = card_info['interface']
        
        print(f" {Info} {GREEN}正在处理网卡 {BLUE}{interface_name}{FONT}: {YELLOW}监听IP {listen_ip}{FONT} | {BLUE}客户端IP {client_ip}{FONT}")
        tag: List[str] = []
        try:
            tag = xray.gen_tag(ipaddr=listen_ip)  # 使用监听IP生成tag
        except Exception as e:
            print(f"{Error} {RED}没安装xray，请先执行 python3 main.py install 命令安装xray{FONT}")
            print(f"报错是 {RED}{e}{FONT}")
        port += 1

        time.sleep(0.1)

        # 插入路由配置
        xray.insert_routing_config(tag[0], tag[1])

        # 插入出口配置，使用监听IP作为出站IP
        xray.insert_outbounds_config(ipaddr=listen_ip, outbound_tag=tag[1])
        name = f"{args.name}-{tag[2]}"
        if protocol == "socks5":
            create_sk5_node(network_layer=socks5_network_layer, ip=listen_ip, port=port, tag=tag, name=name,
                            advanced_configuration=advanced_configuration,
                            sk5_order_ports_mode=sk5_order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        elif protocol == "vmess":
            create_vmess_node(transport_layer=vmess_transport_mode, listen_ip=listen_ip, client_ip=client_ip, 
                             port=port, tag=tag, name=name)
        elif protocol == "vmess-socks5":
            port += 1
            create_v2_sk5_node(v2_transport_layer=vmess_transport_mode, sk5_network_layer=socks5_network_layer,
                               listen_ip=listen_ip, client_ip=client_ip, port=port, tag=tag, name=name, 
                               advanced_configuration=advanced_configuration,
                               order_ports_mode=sk5_order_ports_mode,
                               sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        elif protocol == "shadowsocks":
            create_shadowsocks_node(method=method, password=password, network_layer=shadowsocks_network_layer, ip=listen_ip,
                                    port=port, tag=tag, name=name)
        else:
            print(
                f"{Warning} {RED}作者还没写这个模式{FONT} {protocol} "
                f"请联系作者 {GREEN}{author_email}{FONT}"
            )
            exit(2)
    
    xray.write_2_file()
    print(f"{OK} {GREEN}配置生成完毕!{FONT}")
    xray.restart()
    print(f"{OK} {GREEN}内核重载配置完毕!{FONT}")
    if protocol == "socks5" or protocol == "vmess-socks5":
        publish.save_2_file(config_list=publish.raw_config_list)
    publish.save_2_file()
    if args.publish == 'true':
        publish.publish_2_web()


def list_node(args):
    xray.list_node()


def status(args):
    xray.status()


def show_file_config(args):
    xray.print_file_config()


if __name__ == '__main__':
    if not is_root():
        print(f"{Error} {RED}请使用root运行{FONT}")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description=f"{RED}站群服务器隧道管理脚本{FONT}",
        add_help=False
    )

    parser.add_argument('-h', '--help', action='help',
                        default=argparse.SUPPRESS, help='显示此帮助消息并退出')

    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="列出站群服务器内的所有节点")

    subparsers = parser.add_subparsers(help='选择进入子菜单功能')

    parser_install = subparsers.add_parser(
        'install', help='安装/升级xray内核,注意！执行升级全部配置将会丢失')
    parser_install.set_defaults(func=install)

    parser_upgrade = subparsers.add_parser('upgrade', help="升级内核")
    parser_upgrade.set_defaults(func=upgrade)

    parser_install_geo = subparsers.add_parser('install_geo', help="安装/升级 geo数据库")
    parser_install_geo.set_defaults(func=install_geo)

    parser_config_init = subparsers.add_parser(
        'config_init', help='进行配置初始化并重载内核设置')
    parser_config_init.add_argument('--name', type=str, help='节点名称的前缀')
    parser_config_init.add_argument('--publish', type=str, default='true', help='将节点配置发布到dpaste（值为false则不发布,为true则发布，默认为true')
    # parser_config_init.add_argument('--mode', type=str, help='Transport Layer Protocol')
    parser_config_init.set_defaults(func=config_init)

    parser_uninstall = subparsers.add_parser(
        'uninstall', help='从这个电脑上完全移除站群管理服务')
    parser_uninstall.set_defaults(func=uninstall)

    parser_status = subparsers.add_parser('status', help="查看xray运行状态")
    parser_status.set_defaults(func=status)

    parser_config = subparsers.add_parser('show_config', help="查看文件中的配置")
    parser_config.set_defaults(func=show_file_config)

    # parser_s = subparsers.add_parser('modify', help='Edit the name of a node')
    # parser_s.add_argument('--name', type=str, help='NodeName')
    # parser_s.add_argument('--port', type=int, help='Port')
    # parser_s.add_argument('--network', type=str, help='Network')
    # parser_s.add_argument('--path', type=str, help='path')
    # parser_s.set_defaults(func=modify)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # execute function
    try:
        # 解析命令行参数
        args = parser.parse_args()
    except SystemExit:
        print("解析参数出错！")
        exit(0)
    args.func(args)
