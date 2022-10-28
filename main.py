# encoding: utf-8
import argparse
import random
import time

from utils.controllerFactory import Xray, get_net_card, is_root
from utils.color import *

xray = Xray()


def uninstall(args):
    xray.uninstall()


def install(args):
    xray.install()


def config_init(args):
    net_card = get_net_card()
    print(f" {Info} {Green} 正常获取网卡信息.... {Font}")
    print(f" {Info} {Green} 你的网卡信息是：{net_card} {Font}")
    print(f" {Info} {Green} 正在生成网络黑洞，用于制作ip和域名封禁功能... {Font}")
    xray.init_config()
    print(f" {OK} {GreenBG} {Red} 网络黑洞生成成功... {Font}")
    while True:
        black_domain = input(f"请输入被封禁的域名{Red}输入END结束{Font}")
        if black_domain == "END":
            break
        xray.insert_black_domain(black_domain)
    top_mode = input("请输入你要制作的协议：【sock5/vmess】")
    if top_mode == "sock5":
        second_mode = input("请输入你要创建传输层模式【tcp】")
    # elif top_mode == "vmess":
    #     second_mode = input("请输入你要创建的模式【ws/tcp】")
    else:
        print(f"{Warning} {Red}作者还没写这个模式 {top_mode} 请联系作者 {Green} {author_email} {Font}")
        exit(2)
    for ip in net_card:
        tag = []
        print(f"{Info} 正在处理 {ip} {Font}")
        tag = xray.gen_tag(ipaddr=ip)
        # print(f"{tag[0]}  {tag[1]}")
        xray.insert_routing_config(tag[0], tag[1])
        xray.insert_outbounds_config(ipaddr=ip, outbound_tag=tag[1])
        time.sleep(1)
        if top_mode == "sock5":
            xray.insert_inbounds_sk5_tcp_config(ipaddr=ip, port=random.randint(30000, 50000), inbounds_tag=tag[0])

    xray.write_2_file()
    print(f"{OK} {Green} 配置生成完毕! {Font}")
    xray.restart()
    print(f"{OK} {Green} 内核重载配置完毕! {Font}")
    # xray.print_file_config()


def list_node(args):
    xray.list_node()


def status(args):
    xray.status()


if __name__ == '__main__':
    if not is_root():
        print(f"{Error} {Red}请使用root运行{Font}")
        exit(1)

    parser = argparse.ArgumentParser(description='Mutilation IP Cluster Server Management Script')
    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="list all nodes in this Cluster server")
    parser.set_defaults(func=list_node)
    subparsers = parser.add_subparsers(help='choose into sub menu')

    parser_install = subparsers.add_parser('install', help='Full Install xray')
    parser_install.set_defaults(func=install)

    parser_config_init = subparsers.add_parser('config_init', help='Init Config')
    # parser_config_init.add_argument('--name', type=str, help='Prefix name of the generated node')
    # parser_config_init.add_argument('--mode', type=str, help='Transport Layer Protocol')
    parser_config_init.set_defaults(func=config_init)

    parser_uninstall = subparsers.add_parser('uninstall', help='Remove From This Computer')
    parser_uninstall.set_defaults(func=uninstall)

    parser_status = subparsers.add_parser('status', help="show xray status")
    parser_status.set_defaults(func=status)

    # parser_s = subparsers.add_parser('modify', help='Edit the name of a node')
    # parser_s.add_argument('--name', type=str, help='NodeName')
    # parser_s.add_argument('--port', type=int, help='Port')
    # parser_s.add_argument('--network', type=str, help='Network')
    # parser_s.add_argument('--path', type=str, help='path')
    # parser_s.set_defaults(func=modify)

    args = parser.parse_args()
    # execute function
    args.func(args)
