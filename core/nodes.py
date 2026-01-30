# encoding: utf-8
"""节点创建模块"""
import uuid
from typing import Optional

from models.config_templates import (
    create_shadowsocks_settings, create_raw_settings, 
    create_stream_settings, create_inbound_config
)
from utils import xray, publish

from .constants import (
    DEFAULT_HOST, DEFAULT_SK5_USER, DEFAULT_SK5_PASSWD, SK5_CREDENTIAL_LENGTH
)
from .utils import generate_random_string, generate_random_port, exit_with_error


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
        port = generate_random_port()

    path = f"/c{generate_random_string()}c/"
    host = DEFAULT_HOST

    xray.insert_inbounds_vmess_config(
        ipaddr=listen_ip, port=port, inbounds_tag=tag[0],
        uuids=uuids, alert_id=0, host=host, path=path, name=name, transport_layer=transport_layer
    )
    publish.create_vmess_quick_link(ps=name, address=client_ip, uuid=uuids,
                                        port=port, alert_id=0, mode=transport_layer, host=host, path=path)


def create_sk5_node(network_layer, ip, port, tag, name, advanced_configuration, sk5_order_ports_mode,
                    sk5_pin_passwd_mode, client_ip=None):
    """创建Socks5节点。ip 为入站监听地址（内网），client_ip 为客户端连接地址（公网，用于生成链接）。"""
    if client_ip is None:
        client_ip = ip
    if advanced_configuration == "y":
        if sk5_order_ports_mode == "N":
            port = generate_random_port()
    
    if advanced_configuration == "y" and sk5_pin_passwd_mode == "y":
        user = DEFAULT_SK5_USER
        passwd = DEFAULT_SK5_PASSWD
    else:
        user = generate_random_string(SK5_CREDENTIAL_LENGTH)
        passwd = generate_random_string(SK5_CREDENTIAL_LENGTH)

    if network_layer == "tcp":
        xray.insert_inbounds_sk5_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                            name=name)
    elif network_layer == "tcp,udp":
        xray.insert_inbounds_sk5_config(ipaddr=ip, port=port, inbounds_tag=tag[0], user=user, passwd=passwd,
                                                name=name, network_layer_support_udp=True)
    else:
        exit_with_error("", network_layer)

    raw_link = f"ip:{client_ip} 用户名:{user} 密码:{passwd} 端口：{port} 节点名称:{name}"
    publish.raw_config_list.append(raw_link)
    quick_link = f"socks://{publish.encode_b64(f'{user}:{passwd}')}@{client_ip}:{port}#{name}"
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
                    sk5_order_ports_mode=order_ports_mode, sk5_pin_passwd_mode=sk5_pin_passwd_mode,
                    client_ip=client_ip)


def create_shadowsocks_node(method, password,
                            network_layer="tcp,udp",
                            transport_layer="raw",
                            ip: str = "127.0.0.1", port: int = 1080, tag=None,
                            name: Optional[str] = None,
                            ss_order_ports_mode: str = "N",
                            client_ip: Optional[str] = None):
    """
    创建并插入一个 Shadowsocks 节点配置。

    :param ip: (str) 入站监听的 IP 地址（内网）。
    :param client_ip: (str) 客户端连接地址（公网），用于生成分享链接；未传时使用 ip。
    :param ss_order_ports_mode: 'N' 为随机端口，'y' 为顺序使用传入的 port。
    :note: 当前仅支持 RAW 模式。
    """
    if client_ip is None:
        client_ip = ip
    if ss_order_ports_mode == "N":
        port = generate_random_port()

    if not password:
        password = f"c{generate_random_string()}c"
    if not method:
        method = "plain"
    shadowsocks_settings = create_shadowsocks_settings(
        network=network_layer,
        method=method,
        password=password
    )
    raw_settings = create_raw_settings()
    stream_settings = create_stream_settings(
        network=transport_layer,
        raw_settings=raw_settings
    )
    tag_value = tag[0] if tag and isinstance(tag, list) else str(tag) if tag else "identifier"
    config = create_inbound_config(
        listen=ip,
        port=port,
        protocol="shadowsocks",
        settings=shadowsocks_settings,
        stream_settings=stream_settings,
        tag=tag_value,
        ps=name
    )
    xray.insert_inbounds_config(config)

    publish.create_shadowsocks_quick_link(method=shadowsocks_settings["method"],
                                          password=shadowsocks_settings["password"],
                                          ip=client_ip, port=config["port"],
                                          network_layer_type=shadowsocks_settings["network"],
                                          name=config.get("ps"))
    return config
