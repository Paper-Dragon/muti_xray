# encoding: utf-8
"""交互式配置模块"""
import time
from typing import List, Dict, Any

from utils import xray, publish, GREEN, RED, FONT, Info, OK, BLUE, YELLOW, Error, GREEN_BG
from utils.color import Warning
from .constants import PROTOCOLS, DEFAULT_START_PORT
from .utils import show_menu, exit_with_error
from .protocols import configure_protocol
from .nodes import create_vmess_node, create_sk5_node, create_v2_sk5_node, create_shadowsocks_node


def collect_black_domains() -> List[str]:
    """收集黑名单域名"""
    black_domains = []
    try:
        while True:
            black_domain_v = input(f"{GREEN}请输入被封禁的域名{FONT}（{RED}输入END结束{FONT}）: ")
            if black_domain_v == "END":
                break
            if black_domain_v.strip():
                black_domains.append(black_domain_v.strip())
                print(f" {OK} {BLUE}已添加域名: {black_domain_v.strip()}{FONT}")
    except (EOFError, KeyboardInterrupt):
        # 非交互式环境或用户中断，返回已收集的域名
        print(f"\n {Info} {YELLOW}输入结束，已收集 {len(black_domains)} 个域名{FONT}")
    return black_domains


def configure_black_domains():
    """配置黑名单域名"""
    print(f" {Info} {GREEN}正在配置黑名单域名...{FONT}")
    black_domains = collect_black_domains()
    
    if black_domains:
        print(f" {Info} {GREEN}正在添加 {len(black_domains)} 个域名到黑名单...{FONT}")
        for domain in black_domains:
            xray.insert_black_domain(domain)
        print(f" {OK} {GREEN}黑名单域名配置完成{FONT}")
    else:
        print(f" {Info} {YELLOW}未添加任何黑名单域名{FONT}")


def select_protocol() -> str:
    """选择协议类型"""
    try:
        protocol_menu = show_menu(PROTOCOLS, "请选择你要制作的协议(按上下键移动，回车选择)")
        return PROTOCOLS[protocol_menu]
    except (EOFError, KeyboardInterrupt, SystemExit) as e:
        # 非交互式环境，默认选择第一个协议
        print(f"\n {Warning} {YELLOW}非交互式环境，使用默认协议: {PROTOCOLS[0]}{FONT}")
        return PROTOCOLS[0]


def create_node_for_interface(card_info: Dict, protocol: str, protocol_config: Dict[str, Any], 
                             base_port: int, node_name_prefix: str) -> int:
    """为单个网卡接口创建节点"""
    listen_ip = card_info['listen_ip']
    client_ip = card_info['client_ip']
    interface_name = card_info['interface']
    
    print(f" {Info} {GREEN}正在处理网卡 {BLUE}{interface_name}{FONT}: {YELLOW}监听IP {listen_ip}{FONT} | {BLUE}客户端IP {client_ip}{FONT}")
    
    try:
        tag = xray.gen_tag(ipaddr=listen_ip)
    except Exception as e:
        print(f"{Error} {RED}没安装xray，请先执行 python3 main.py install 命令安装xray{FONT}")
        print(f"报错是 {RED}{e}{FONT}")
        return base_port
    
    port = base_port + 1
    time.sleep(0.1)
    
    xray.insert_routing_config(tag[0], tag[1])
    xray.insert_outbounds_config(ipaddr=listen_ip, outbound_tag=tag[1])
    name = f"{node_name_prefix}-{tag[2]}"
    
    if protocol == "socks5":
        create_sk5_node(
            network_layer=protocol_config["network_layer"],
            ip=listen_ip, port=port, tag=tag, name=name,
            advanced_configuration=protocol_config["advanced_configuration"],
            sk5_order_ports_mode=protocol_config["sk5_order_ports_mode"],
            sk5_pin_passwd_mode=protocol_config["sk5_pin_passwd_mode"],
            client_ip=client_ip
        )
    elif protocol == "vmess":
        create_vmess_node(
            transport_layer=protocol_config["transport_mode"],
            listen_ip=listen_ip, client_ip=client_ip,
            port=port, tag=tag, name=name
        )
    elif protocol == "vmess-socks5":
        port += 1
        create_v2_sk5_node(
            v2_transport_layer=protocol_config["vmess_transport_mode"],
            sk5_network_layer=protocol_config["socks5_network_layer"],
            listen_ip=listen_ip, client_ip=client_ip, port=port, tag=tag, name=name,
            advanced_configuration=protocol_config["advanced_configuration"],
            order_ports_mode=protocol_config["sk5_order_ports_mode"],
            sk5_pin_passwd_mode=protocol_config["sk5_pin_passwd_mode"]
        )
    elif protocol == "shadowsocks":
        create_shadowsocks_node(
            method=protocol_config["method"],
            password=protocol_config["password"],
            network_layer=protocol_config["network_layer"],
            ip=listen_ip, port=port, tag=tag, name=name,
            ss_order_ports_mode=protocol_config["ss_order_ports_mode"],
            client_ip=client_ip
        )
    else:
        exit_with_error("", protocol)
    
    return port


def finalize_config(protocol: str, publish_flag: str):
    """完成配置并保存"""
    xray.write_2_file()
    print(f"{OK} {GREEN}配置生成完毕!{FONT}")
    xray.restart()
    print(f"{OK} {GREEN}内核重载配置完毕!{FONT}")
    
    if protocol in ["socks5", "vmess-socks5"]:
        publish.save_2_file(config_list=publish.raw_config_list)
    publish.save_2_file()
    
    if publish_flag == 'true':
        publish.publish_2_web()


def config_init(args):
    """初始化配置并创建节点"""
    net_card = xray.get_net_card()
    print(f" {Info} {GREEN}网卡信息获取完成{FONT}")
    print(f" {Info} {GREEN}正在生成网络黑洞，用于制作ip和域名封禁功能...{FONT}")

    xray.init_config()
    print(f" {OK} {RED}{GREEN_BG}网络黑洞生成成功...{FONT}")

    configure_black_domains()

    protocol = select_protocol()
    protocol_config = configure_protocol(protocol)

    port = DEFAULT_START_PORT
    for card_info in net_card:
        port = create_node_for_interface(card_info, protocol, protocol_config, port, args.name)
    
    finalize_config(protocol, args.publish)
