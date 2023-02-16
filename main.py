# encoding: utf-8
import argparse
import random
import string
import time
import uuid
import os

from utils.controllerFactory import Xray, get_net_card, is_root
from utils.color import *
from utils.publishFactory import Publish, encode_b64

quick_link_list = []
xray = Xray()
publish = Publish(config=quick_link_list)
origin_link_list = []
origin_publish = Publish(config=origin_link_list)

def uninstall(args):
    xray.uninstall()

def install(args):
    xray.install()

def create_vmess_node(transport_layer, ip, port, tag, name, random_port=False):
    """
    transport_layer: 传输层协议
    tag: tag[0]: in-192-168-23-129   tag[1] out-192-168-23-129
    """
    uuids = str(uuid.uuid4())
    if random_port:
        port = random.randint(30000, 50000)

    if transport_layer == "ws":
        path = "/c" + \
            ''.join(random.sample(string.ascii_letters + string.digits, 5)) + "c/"
        # print("DEBUG path is", path)
        xray.insert_inbounds_vmess_ws_config(
            ipaddr=ip, port=port, inbounds_tag=tag[0], uuids=uuids, alert_id=0, path=path, name=name)
        
        publish.create_vmess_ws_quick_link(
            ps=name, address=ip, uuid=uuids, port=port, alert_id=0, path=path)

    elif transport_layer == "tcp":
        xray.insert_inbounds_vmess_tcp_config(
            ipaddr=ip, port=port, inbounds_tag=tag[0], uuids=uuids, alert_id=0, name=name)
        
        publish.create_vmess_tcp_quick_link(
            ps=name, address=ip, uuid=uuids, port=port, alert_id=0)

def create_sk5_node(transport_layer, ip, port, tag, name, advanced_configuration, sk5_order_ports_mode, sk5_pin_passwd_mode):
    # print("DEBUG check mode sock5")
    # 端口等熵变大
    if advanced_configuration == "y":
        if sk5_order_ports_mode == "N":
            port = random.randint(30000, 50000)
    # 随机用户预先生成，决定是否覆盖
    user = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    passwd = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    # 部署高级配置 固定用户名密码
    if advanced_configuration == "y":
        if sk5_pin_passwd_mode == "y":
            # 客户增加需求，固定用户名密码？？？？？？？？？端口号
            user = '147258'
            passwd = '147258'

    if transport_layer == "tcp":
        xray.insert_inbounds_sk5_tcp_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                            name=name)
    elif transport_layer == "tcp+udp":
        xray.insert_inbounds_sk5_tcp_udp_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                                name=name)
    else:
        print(
            f"{Warning} {Red}作者还没写这个模式 {transport_layer} 请联系作者 {Green} {author_email} {Font}")
        exit(2)

    # 整理生成快捷链接的数据，并记录在orgin_link_list
    # origin_link_list 记录raw数据
    # quick_link_list 记录快速加入链接
    b64 = encode_b64(f"{user}:{passwd}")
    origin_link = f"ip:{ip} 用户名:{user} 密码:{passwd} 端口：{port} 节点名称:{name}"
    origin_link_list.append(origin_link)
    quick_link = f"socks://{b64}@{ip}:{port}#{name}"
    quick_link_list.append(quick_link)

def create_v2_sk5_node(v2_transport_layer, sk5_transport_layer, ip, port, tag, name, advanced_configuration, order_ports_mode, sk5_pin_passwd_mode):
    """
    # tag: ['in-192-168-23-131', 'out-192-168-23-131', '192-168-23-131'],
    # name: Name-192-168-23-131
    # ip: 192.168.23.131
    """
    tag[0] = f"v2-{tag[0]}"
    tag[1] = f"v2-{tag[1]}"
    name = f"v2-{name}"
    # print(f"tag: {tag},name: {name}")
    xray.insert_routing_config(tag[0], tag[1])
    xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
    random_port = True
    if order_ports_mode == 'y':
        random_port = False
    create_vmess_node(transport_layer=v2_transport_layer,
                      ip=ip, port=port, tag=tag, name=name, random_port=random_port)

    tag[0] = tag[0].replace('v2', 'sk5')
    tag[1] = tag[1].replace('v2', 'sk5')
    name = name.replace('v2', 'sk5')
    xray.insert_routing_config(tag[0], tag[1])
    xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
    port += 1
    create_sk5_node(transport_layer=sk5_transport_layer, ip=ip, port=port, tag=tag, name=name, advanced_configuration=advanced_configuration,
                    sk5_order_ports_mode=order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)

def compatible_Kitsunebi():
    xray_config_file_path =  "/etc/systemd/system/xray.service"

    if os.system(f'cat {xray_config_file_path} | grep Xray_VMESS_AEAD_DISABLED'):
        os.system(f"sed -i '/\[Service\]/a\\Environment=\"Xray_VMESS_AEAD_DISABLED=true\"' {xray_config_file_path}")
        xray.restart
    else:
        print("经过查询，已经优化过了！")

def config_init(args):
    # 获取网卡信息
    net_card = get_net_card()
    print(f" {Info} {Green} 正常获取网卡信息.... {Font}")
    print(f" {Info} {Green} 你的网卡信息是：{net_card} {Font}")
    print(f" {Info} {Green} 正在生成网络黑洞，用于制作ip和域名封禁功能... {Font}")

    # 初始化配置对象和生成网络黑洞
    xray.init_config()
    print(f" {OK} {GreenBG} {Red} 网络黑洞生成成功... {Font}")

    # 增加黑化域名
    while True:
        black_domain = []
        black_domain_v = input(f"请输入被封禁的域名{Red}输入END结束{Font}")
        if black_domain_v == "END":
            break
        black_domain.append(black_domain_v)
    if black_domain != '':
        xray.insert_black_domain(black_domain)

    disable_aead_verify = "N"
    # 选择传输层协议
    top_mode = input("请输入你要制作的协议：【sock5/vmess/trojan/shadowsocks/v2-sk5】")
    if top_mode == "sock5":
        second_mode = str(input("请输入你要创建传输层模式【tcp/tcp+udp】"))
        advanced_configuration = str(input("是否要进入高级配置，定制功能【y/N】"))
        if advanced_configuration == "y":
            sk5_pin_passwd_mode = input("是否启动默认密码放弃随机密码？【y/N】")
            sk5_order_ports_mode = str(input("是否顺序生成端口？默认随机生成【y/N】"))
    elif top_mode == "vmess":
        second_mode = input("请输入你要创建的模式【ws/tcp/http/h2c】")
        disable_aead_verify = input("是否开启面向Kitsunebi优化【y/N】")
    elif top_mode == "v2-sk5":
        second_mode_v2 = input("请输入你要创建的v2模式【ws/tcp/http/h2c】")
        second_mode_sk5 = str(input("请输入你要创建sk5传输层模式【tcp/tcp+udp】"))
        disable_aead_verify = input("是否开启面向Kitsunebi优化【y/N】")
        advanced_configuration = str(input("是否要进入高级配置，定制功能【y/N】"))
        order_ports_mode = 'N'
        sk5_pin_passwd_mode = 'N'
        if advanced_configuration == "y":
            sk5_pin_passwd_mode = input("是否启动sk5默认密码放弃随机密码？【y/N】")
            order_ports_mode = str(input("是否顺序生成端口？默认随机生成【y/N】"))
    else:
        print(
            f"{Warning} {Red}作者还没写这个模式 {top_mode} 请联系作者 {Green} {author_email} {Font}")
        exit(2)

    # 若为顺序生成端口模式，从这个端口开始顺序生成
    port = 10000
    if disable_aead_verify == "y":
        compatible_Kitsunebi()
    # 以网卡为index生成配置
    for ip in net_card:
        print(f"{Info} 正在处理 {ip} {Font}")
        tag = xray.gen_tag(ipaddr=ip)
        port += 1

        time.sleep(0.1)
        name = f"{args.name}-{tag[2]}"
        if top_mode == "sock5":
            xray.insert_routing_config(tag[0], tag[1])
            xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
            create_sk5_node(transport_layer=second_mode, ip=ip, port=port, tag=tag, name=name, advanced_configuration=advanced_configuration,
                            sk5_order_ports_mode=sk5_order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        elif top_mode == "vmess":
            xray.insert_routing_config(tag[0], tag[1])
            xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
            create_vmess_node(transport_layer=second_mode,
                              ip=ip, port=port, tag=tag, name=name)
        elif top_mode == "v2-sk5":
            port += 1
            create_v2_sk5_node(v2_transport_layer=second_mode_v2, sk5_transport_layer=second_mode_sk5,
                               ip=ip, port=port, tag=tag, name=name, advanced_configuration=advanced_configuration, order_ports_mode=order_ports_mode,
                               sk5_pin_passwd_mode=sk5_pin_passwd_mode)
        else:
            print(
                f"{Warning} {Red}作者还没写这个模式 {top_mode} 请联系作者 {Green} {author_email} {Font}")
            exit(2)
    # print(quick_link_list)
    xray.write_2_file()
    print(f"{OK} {Green} 配置生成完毕! {Font}")
    xray.restart()
    print(f"{OK} {Green} 内核重载配置完毕! {Font}")
    origin_publish.publish_2_txt()
    publish.publish_2_web()


def list_node(args):
    xray.list_node()


def status(args):
    xray.status()


def show_file_config(args):
    xray.print_file_config()


if __name__ == '__main__':
    if not is_root():
        print(f"{Error} {Red}请使用root运行{Font}")
        exit(1)

    parser = argparse.ArgumentParser(description=f'{Red}站群服务器隧道管理脚本{Font}')
    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="列出站群服务器内的所有节点")
    parser.set_defaults(func=list_node)
    subparsers = parser.add_subparsers(help='选择进入子菜单功能')

    parser_install = subparsers.add_parser('install', help='完整安装Xray【不包含配置】')
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

    args = parser.parse_args()
    # execute function
    args.func(args)
