# encoding: utf-8
import argparse
import os
import random
import string
import sys
import time
import uuid
from typing import List, Literal, Optional, AnyStr

from simple_term_menu import TerminalMenu
from termcolor import colored

from models import ShadowSocksSettings, TCPSettingsConfig, StreamSettingsConfig, InboundConfig
from utils import *


xray = Xray()
publish = Publish()


def uninstall(args):
    xray.uninstall()


def install(args):
    xray.install()

def create_vmess_node(transport_layer, ip, port, tag, name, random_port=False):
    """
    Create Single Vmess Inbound Node

    :param transport_layer: 传输层协议 tcp,http
    :param ip: ip address
    :param port: server port
    :param name: node name
    :param random_port: Bool random port
    :param tag: tag[0]: in-192-168-23-129   tag[1] out-192-168-23-129 tag[2]
    """
    uuids = str(uuid.uuid4())
    if random_port:
        port = random.randint(10000, 30000)

    path = f"/c{''.join(random.sample(string.ascii_letters + string.digits, 5))}c/"
    xray.insert_inbounds_vmess_config(ipaddr=ip, port=port, inbounds_tag=tag[0],
                                      uuids=uuids, alert_id=0, path=path, name=name, transport_layer=transport_layer)
    publish.create_vmess_quick_link(ps=name, address=ip, uuid=uuids,
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
            f"{Warning} {colored('作者还没写这个模式', 'red')} {network_layer} "
            f"请联系作者 {colored(f'{author_email}', 'green')}")
        exit(2)

    # 整理生成快捷链接的数据，并记录在 publish.config
    raw_link = f"ip:{ip} 用户名:{user} 密码:{passwd} 端口：{port} 节点名称:{name}"
    publish.raw_config_list.append(raw_link)
    quick_link = f"socks://{publish.encode_b64(f'{user}:{passwd}')}@{ip}:{port}#{name}"
    publish.quick_config_link_list.append(quick_link)


def create_v2_sk5_node(v2_transport_layer, sk5_network_layer, ip, port, tag, name, advanced_configuration,
                       order_ports_mode, sk5_pin_passwd_mode):
    """
    # tag: ['in-192-168-23-131', 'out-192-168-23-131', '192-168-23-131'],
    # name: Name-192-168-23-131
    # ip: 192.168.23.131
    """
    v2_tag = [f"v2-{t}" if i < 2 else t for i, t in enumerate(tag)]
    name = f"v2-{name}"

    xray.insert_routing_config(v2_tag[0], v2_tag[1])
    xray.insert_outbounds_config(ipaddr=ip, outbound_tag=v2_tag[1])
    random_port = True
    if order_ports_mode == 'y':
        random_port = False
    create_vmess_node(transport_layer=v2_transport_layer,
                      ip=ip, port=port, tag=tag, name=name, random_port=random_port)

    sk5_tag = [f"sk5-{t}" if i < 2 else t for i, t in enumerate(tag)]
    name = f"sk5-{name}"

    xray.insert_routing_config(sk5_tag[0], sk5_tag[1])
    xray.insert_outbounds_config(ipaddr=ip, outbound_tag=sk5_tag[1])
    port += 1
    create_sk5_node(network_layer=sk5_network_layer, ip=ip, port=port, tag=tag, name=name,
                    advanced_configuration=advanced_configuration,
                    sk5_order_ports_mode=order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)


def create_shadowsocks_node(method, password,
                            network_layer: Literal['tcp', 'udp', 'tcp,udp'] = "tcp,udp",
                            transport_layer: Literal["tcp", "kcp", "ws", "http", "domainsocket", "quic", "grpc"] = "tcp",
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

    :note: 当前仅支持 TCP 模式。
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
    tcp_transport_layer_settings = TCPSettingsConfig()
    # TODO: 传输层临时先用tcp模式吧，后面再支持其他的

    stream_settings = StreamSettingsConfig(
        network=transport_layer,
        tcp_settings=tcp_transport_layer_settings
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
        os.system(f"sed -i '/\[Service\]/a\\Environment=\"XRAY_VMESS_AEAD_FORCED=false\"' {xray.service_config_file}")
        os.system("systemctl daemon-reload")
        xray.restart()
    else:
        print("经过查询，Kitsunebi 已经优化过了！")


def config_init(args):
    # 获取网卡信息
    net_card = xray.get_net_card()
    print(f" {Info} {colored('正常获取网卡信息....', 'green')}")
    print(f" {Info} {colored('你的网卡信息是：', 'green')} {net_card}")
    print(f" {Info} {colored('正在生成网络黑洞，用于制作ip和域名封禁功能...', 'green')} ")

    # 初始化配置对象和生成网络黑洞
    xray.init_config()
    print(f" {OK} {colored('网络黑洞生成成功...', 'red', 'on_green')}")

    # 增加黑化域名
    while True:
        black_domain = []
        black_domain_v = input(f"{colored('请输入被封禁的域名', 'green')}{colored('输入END结束', 'red')}")
        if black_domain_v == "END":
            break
        black_domain.append(black_domain_v)
    if black_domain != '':
        xray.insert_black_domain(black_domain)

    disable_aead_verify = "N"
    # 选择传输层协议
    protocol_options = ["socks5", "vmess", "trojan", "shadowsocks", "vmess-socks5"]
    protocol_menu = TerminalMenu(protocol_options, title="请选择你要制作的协议").show()
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
        vmess_transport_mode_options: List[str] = ["ws", "tcp", "http", "h2c"]
        vmess_transport_mode_menu = TerminalMenu(vmess_transport_mode_options, title="输入要创建的传输层模式").show()
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

        vmess_transport_mode_options: List[str] = ["ws", "tcp", "http", "h2c"]
        vmess_transport_mode_menu = TerminalMenu(vmess_transport_mode_options, title="输入要创建vmess的传输层模式").show()
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
        shadowsocks_network_layer_options: List[Literal['tcp', 'udp', 'tcp,udp']] = ['tcp', 'udp', 'tcp,udp']
        shadowsocks_network_layer_menu = TerminalMenu(shadowsocks_network_layer_options, title="你想要什么网络层协议")
        shadowsocks_network_layer = shadowsocks_network_layer_options[shadowsocks_network_layer_menu.show()]

        method_options = ["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305", "plain"]
        method_menu = TerminalMenu(method_options,title="加密方法").show()
        method = method_options[method_menu]
        password = input("请输入密码(回车则随机生成密码):")
    else:
        print(
            f"{Warning} {colored('作者还没写这个模式', 'red')} {protocol} "
            f"请联系作者 {colored(f'{author_email}', 'green')}")
        exit(2)

    # 若为顺序生成端口模式，从这个端口开始顺序生成
    port = 10000

    # 以网卡为index生成配置
    for ip in net_card:
        print(f"{Info} {colored(f'正在处理{ip}', 'green')}")
        tag: List[str] = []
        try:
            tag = xray.gen_tag(ipaddr=ip)
        except Exception as e:
            print(f"{Error} {colored('没安装xray，请先执行 python3 main.py install 命令安装xray', 'green')}")
            print(f"报错是 {e}")
        port += 1

        time.sleep(0.1)

        # 插入路由配置
        xray.insert_routing_config(tag[0], tag[1])

        # 插入出口配置，默认任凭流量自由出去
        xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
        name = f"{args.name}-{tag[2]}"
        if protocol == "socks5":
            create_sk5_node(network_layer=socks5_network_layer, ip=ip, port=port, tag=tag, name=name,
                            advanced_configuration=advanced_configuration,
                            sk5_order_ports_mode=sk5_order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        elif protocol == "vmess":
            create_vmess_node(transport_layer=vmess_transport_mode, ip=ip, port=port, tag=tag, name=name)
        elif protocol == "vmess-socks5":
            port += 1
            create_v2_sk5_node(v2_transport_layer=vmess_transport_mode, sk5_network_layer=socks5_network_layer,
                               ip=ip, port=port, tag=tag, name=name, advanced_configuration=advanced_configuration,
                               order_ports_mode=sk5_order_ports_mode,
                               sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        elif protocol == "shadowsocks":
            create_shadowsocks_node(method=method, password=password, network_layer=shadowsocks_network_layer, ip=ip,
                                    port=port, tag=tag, name=name)
        else:
            print(
            f"{Warning} {colored('作者还没写这个模式', 'red')} {protocol} "
            f"请联系作者 {colored(f'{author_email}', 'green')}")
            exit(2)
    
    xray.write_2_file()
    print(f"{OK} {colored(' 配置生成完毕!', 'green')}")
    xray.restart()
    print(f"{OK} {colored('内核重载配置完毕! ', 'green')}")
    if protocol == "socks5" or protocol == "vmess-socks5":
        publish.save_2_file(config_list=publish.raw_config_list)
    publish.save_2_file()
    publish.publish_2_web()


def list_node(args):
    xray.list_node()


def status(args):
    xray.status()


def show_file_config(args):
    xray.print_file_config()


if __name__ == '__main__':
    if not is_root():
        print(f"{Error} {colored('请使用root运行','red')}")
        exit(1)

    parser = argparse.ArgumentParser(
        description=f"{colored('站群服务器隧道管理脚本', 'red')}",
        add_help=False  # 不添加默认的帮助信息
    )

    parser.add_argument('-h', '--help', action='help',
                        default=argparse.SUPPRESS, help='显示此帮助消息并退出')

    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="列出站群服务器内的所有节点")

    subparsers = parser.add_subparsers(help='选择进入子菜单功能')

    parser_install = subparsers.add_parser(
        'install', help='安装/升级xray内核,注意！执行升级全部配置将会丢失')
    parser_install.set_defaults(func=install)

    parser_config_init = subparsers.add_parser(
        'config_init', help='进行配置初始化并重载内核设置')
    parser_config_init.add_argument('--name', type=str, help='节点名称的前缀')
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
