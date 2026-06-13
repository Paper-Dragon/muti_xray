# encoding: utf-8
from typing import Dict, List, Tuple

import links as lk
import xray as xray_ctrl
from models import (
    ShadowsocksInbound,
    Socks5Inbound,
    TrojanInbound,
    VlessInbound,
    VmessInbound,
    XrayConfig,
    _rand_port,
    _rand_str,
    _ip_suffix,
    new_uuid,
    new_path,
)


def _tag(proto: str, ip: str, role: str = "in") -> str:
    return f"{proto.replace('-', '_')}-{role}-{_ip_suffix(ip)}"


def _freedom_outbound(ip: str, tag: str) -> dict:
    return {"sendThrough": ip, "protocol": "freedom", "tag": tag}


def _routing_rule(inbound_tag: str, outbound_tag: str) -> dict:
    return {"type": "field", "inboundTag": [inbound_tag], "outboundTag": outbound_tag}


def _add_vmess(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    transport = proto_cfg["transport_mode"]
    if proto_cfg.get("order_ports") != "y":
        port = _rand_port()

    in_tag  = _tag(tag_prefix, listen_ip, "in")
    out_tag = _tag(tag_prefix, listen_ip, "out")
    path = new_path()

    node = VmessInbound(
        listen=listen_ip, port=port, tag=in_tag,
        uuid=new_uuid(), transport=transport,
        path=path, name=name,
    )
    cfg.inbounds.append(node)
    cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
    cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

    return port, [lk.vmess_link(node, client_ip)]


def _add_vless(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    transport = proto_cfg["transport_mode"]
    if proto_cfg.get("order_ports") != "y":
        port = _rand_port()

    in_tag  = _tag(tag_prefix, listen_ip, "in")
    out_tag = _tag(tag_prefix, listen_ip, "out")
    path = new_path()

    node = VlessInbound(
        listen=listen_ip, port=port, tag=in_tag,
        uuid=new_uuid(), transport=transport,
        path=path, name=name,
    )
    cfg.inbounds.append(node)
    cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
    cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

    return port, [lk.vless_link(node, client_ip)]


def _add_socks5(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    adv = proto_cfg.get("advanced_configuration") == "y"
    if adv and proto_cfg.get("sk5_order_ports_mode") != "y":
        port = _rand_port()

    if adv and proto_cfg.get("sk5_pin_passwd_mode") == "y":
        user, passwd = "147258", "147258"
    else:
        user   = _rand_str(16)
        passwd = _rand_str(16)

    udp = proto_cfg.get("network_layer") == "tcp,udp"
    in_tag  = _tag(tag_prefix, listen_ip, "in")
    out_tag = _tag(tag_prefix, listen_ip, "out")

    node = Socks5Inbound(
        listen=listen_ip, port=port, tag=in_tag,
        user=user, passwd=passwd, name=name, udp=udp,
    )
    cfg.inbounds.append(node)
    cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
    cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

    return port, [lk.socks5_link(node, client_ip), lk.socks5_plain(node, client_ip)]


def _add_trojan(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    transport = proto_cfg.get("transport_mode", "raw")
    if proto_cfg.get("order_ports") != "y":
        port = _rand_port()

    password = proto_cfg.get("password") or f"c{_rand_str(12)}c"

    cert_file = proto_cfg.get("cert_file", "")
    key_file  = proto_cfg.get("key_file", "")
    if not cert_file or not key_file:
        cert_file, key_file = xray_ctrl.generate_self_signed_cert(domain=listen_ip)

    in_tag  = _tag(tag_prefix, listen_ip, "in")
    out_tag = _tag(tag_prefix, listen_ip, "out")
    path = new_path() if transport in ("ws", "xhttp") else ""

    node = TrojanInbound(
        listen=listen_ip, port=port, tag=in_tag,
        password=password, cert_file=cert_file, key_file=key_file,
        transport=transport, path=path, name=name,
    )
    cfg.inbounds.append(node)
    cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
    cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

    return port, [lk.trojan_link(node, client_ip)]


def _add_shadowsocks(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    if proto_cfg.get("ss_order_ports_mode") != "y":
        port = _rand_port()

    password = proto_cfg.get("password") or f"c{_rand_str(8)}c"
    method   = proto_cfg.get("method") or "plain"
    network  = proto_cfg.get("network_layer", "tcp,udp")

    in_tag  = _tag(tag_prefix, listen_ip, "in")
    out_tag = _tag(tag_prefix, listen_ip, "out")

    node = ShadowsocksInbound(
        listen=listen_ip, port=port, tag=in_tag,
        method=method, password=password,
        network=network, name=name,
    )
    cfg.inbounds.append(node)
    cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
    cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

    return port, [lk.ss_link(node, client_ip)]


def _add_protocol_node(
    cfg: XrayConfig,
    card: dict,
    proto: str,
    proto_cfg: dict,
    port: int,
    name: str,
) -> Tuple[int, List[str]]:
    listen_ip = card["listen_ip"]
    client_ip = card["client_ip"]

    if proto == "vmess":
        return _add_vmess(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "vless":
        return _add_vless(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "trojan":
        return _add_trojan(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "socks5":
        return _add_socks5(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "shadowsocks":
        return _add_shadowsocks(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    raise ValueError(f"未知协议: {proto}")


def build_config(
    cards: List[dict],
    protocols: List[str],
    proto_configs: Dict[str, dict],
    blocked_domains: List[str],
    name_prefix: str = "Node",
    start_port: int = 10000,
) -> Tuple[XrayConfig, List[str]]:
    cfg = XrayConfig(blocked_domains=blocked_domains)
    all_links: List[str] = []
    port = start_port

    for card in cards:
        listen_ip = card["listen_ip"]
        client_ip = card["client_ip"]
        name_suffix = client_ip.replace(".", "-")

        for proto in protocols:
            port += 1
            name = f"{name_prefix}-{name_suffix}-{proto}"
            try:
                port, node_links = _add_protocol_node(
                    cfg, card, proto, proto_configs[proto], port, name
                )
                all_links.extend(node_links)
            except Exception as e:
                print(f"[警告] 创建节点 {name} 失败: {e}，跳过")

    return cfg, all_links
