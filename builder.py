# encoding: utf-8
import json
from typing import Dict, List, Tuple

import db
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


def _make_vmess(listen_ip: str, port: int, in_tag: str, name: str, params: dict) -> VmessInbound:
    return VmessInbound(
        listen=listen_ip, port=port, tag=in_tag,
        uuid=params["uuid"], transport=params["transport"],
        path=params.get("path", ""), name=name,
    )


def _make_vless(listen_ip: str, port: int, in_tag: str, name: str, params: dict) -> VlessInbound:
    return VlessInbound(
        listen=listen_ip, port=port, tag=in_tag,
        uuid=params["uuid"], transport=params["transport"],
        path=params.get("path", ""), name=name,
    )


def _make_socks5(listen_ip: str, port: int, in_tag: str, name: str, params: dict) -> Socks5Inbound:
    return Socks5Inbound(
        listen=listen_ip, port=port, tag=in_tag,
        user=params["user"], passwd=params["passwd"],
        name=name, udp=params.get("udp", False),
    )


def _make_trojan(listen_ip: str, port: int, in_tag: str, name: str, params: dict) -> TrojanInbound:
    import os
    cert_file = params["cert_file"]
    key_file = params["key_file"]
    if not os.path.isfile(cert_file) or not os.path.isfile(key_file):
        cert_file, key_file = xray_ctrl.generate_self_signed_cert(domain=listen_ip)
    return TrojanInbound(
        listen=listen_ip, port=port, tag=in_tag,
        password=params["password"],
        cert_file=cert_file, key_file=key_file,
        transport=params.get("transport", "raw"),
        path=params.get("path", ""), name=name,
    )


def _make_shadowsocks(listen_ip: str, port: int, in_tag: str, name: str, params: dict) -> ShadowsocksInbound:
    return ShadowsocksInbound(
        listen=listen_ip, port=port, tag=in_tag,
        method=params["method"], password=params["password"],
        network=params.get("network", "tcp,udp"), name=name,
    )


_MAKERS = {
    "vmess": _make_vmess,
    "vless": _make_vless,
    "socks5": _make_socks5,
    "trojan": _make_trojan,
    "shadowsocks": _make_shadowsocks,
}


def _build_node_params(proto: str, proto_cfg: dict, listen_ip: str, port_range: Tuple[int, int] = (10000, 30000)) -> Tuple[int, dict]:
    lo, hi = port_range

    if proto == "vmess":
        transport = proto_cfg["transport_mode"]
        port = _rand_port(lo, hi) if proto_cfg.get("order_ports") != "y" else 0
        return port, {"uuid": new_uuid(), "transport": transport, "path": new_path()}

    if proto == "vless":
        transport = proto_cfg["transport_mode"]
        port = _rand_port(lo, hi) if proto_cfg.get("order_ports") != "y" else 0
        return port, {"uuid": new_uuid(), "transport": transport, "path": new_path()}

    if proto == "socks5":
        adv = proto_cfg.get("advanced_configuration") == "y"
        port = 0
        if adv and proto_cfg.get("sk5_order_ports_mode") != "y":
            port = _rand_port(lo, hi)
        elif not adv:
            port = _rand_port(lo, hi)

        if adv and proto_cfg.get("sk5_pin_passwd_mode") == "y":
            user, passwd = "147258", "147258"
        else:
            user, passwd = _rand_str(16), _rand_str(16)
        udp = proto_cfg.get("network_layer") == "tcp,udp"
        return port, {"user": user, "passwd": passwd, "udp": udp}

    if proto == "trojan":
        transport = proto_cfg.get("transport_mode", "raw")
        port = _rand_port(lo, hi) if proto_cfg.get("order_ports") != "y" else 0
        password = proto_cfg.get("password") or f"c{_rand_str(12)}c"
        cert_file = proto_cfg.get("cert_file", "")
        key_file = proto_cfg.get("key_file", "")
        if not cert_file or not key_file:
            cert_file, key_file = xray_ctrl.generate_self_signed_cert(domain=listen_ip)
        path = new_path() if transport in ("ws", "xhttp") else ""
        return port, {
            "password": password, "cert_file": cert_file, "key_file": key_file,
            "transport": transport, "path": path,
        }

    if proto == "shadowsocks":
        port = _rand_port(lo, hi) if proto_cfg.get("ss_order_ports_mode") != "y" else 0
        password = proto_cfg.get("password") or f"c{_rand_str(8)}c"
        method = proto_cfg.get("method") or "plain"
        network = proto_cfg.get("network_layer", "tcp,udp")
        return port, {"method": method, "password": password, "network": network}

    raise ValueError(f"未知协议: {proto}")


def _node_to_link(proto: str, node, client_ip: str) -> List[str]:
    if proto == "vmess":
        return [lk.vmess_link(node, client_ip)]
    if proto == "vless":
        return [lk.vless_link(node, client_ip)]
    if proto == "trojan":
        return [lk.trojan_link(node, client_ip)]
    if proto == "socks5":
        return [lk.socks5_link(node, client_ip), lk.socks5_plain(node, client_ip)]
    if proto == "shadowsocks":
        return [lk.ss_link(node, client_ip)]
    return []


def generate_from_db() -> Tuple[XrayConfig, List[str]]:
    blocked_raw = db.get_setting("blocked_domains", "[]")
    try:
        blocked = json.loads(blocked_raw)
    except (json.JSONDecodeError, TypeError):
        blocked = []

    cfg = XrayConfig(blocked_domains=blocked)
    all_links: List[str] = []

    for row in db.get_nodes():
        proto = row["protocol"]
        in_tag = row["tag"]
        out_tag = in_tag.replace("-in-", "-out-")
        listen_ip = row["listen_ip"]
        client_ip = row["client_ip"]
        params = row["params"]

        maker = _MAKERS.get(proto)
        if not maker:
            continue

        node = maker(listen_ip, row["port"], in_tag, row["name"], params)
        cfg.inbounds.append(node)
        cfg.outbounds.append(_freedom_outbound(listen_ip, out_tag))
        cfg.routing_rules.append(_routing_rule(in_tag, out_tag))

        all_links.extend(_node_to_link(proto, node, client_ip))

    return cfg, all_links


def _is_order_mode(proto: str, proto_cfg: dict) -> bool:
    if proto == "socks5":
        return proto_cfg.get("advanced_configuration") == "y" and proto_cfg.get("sk5_order_ports_mode") == "y"
    if proto == "shadowsocks":
        return proto_cfg.get("ss_order_ports_mode") == "y"
    return proto_cfg.get("order_ports") == "y"


def build_config(
    cards: List[dict],
    protocols: List[str],
    proto_configs: Dict[str, dict],
    blocked_domains: List[str],
    name_prefix: str = "Node",
    start_port: int = 10000,
    port_range: Tuple[int, int] = (10000, 30000),
) -> Tuple[XrayConfig, List[str]]:
    db.clear_all()
    db_cards = db.save_cards(cards)
    db.set_setting("name_prefix", name_prefix)
    db.set_setting("blocked_domains", json.dumps(blocked_domains, ensure_ascii=False))

    proto_port_counters: Dict[str, int] = {}
    for proto in protocols:
        cfg = proto_configs[proto]
        if _is_order_mode(proto, cfg):
            sp = cfg.get("start_port", 0)
            proto_port_counters[proto] = (sp - 1) if sp > 0 else start_port

    for card in db_cards:
        name_suffix = card["client_ip"].replace(".", "-")
        for proto in protocols:
            rand_port, params = _build_node_params(proto, proto_configs[proto], card["listen_ip"], port_range)
            if rand_port > 0:
                port = rand_port
            else:
                proto_port_counters[proto] = proto_port_counters.get(proto, start_port) + 1
                port = proto_port_counters[proto]
            in_tag = _tag(proto, card["listen_ip"], "in")
            name = f"{name_prefix}-{name_suffix}-{proto}"
            try:
                db.add_node(card["id"], proto, port, in_tag, name, params)
            except Exception as e:
                print(f"[警告] 创建节点 {name} 失败: {e}，跳过")

    return generate_from_db()


def append_protocol(
    protocols: List[str],
    proto_configs: Dict[str, dict],
    port_range: Tuple[int, int] = (10000, 30000),
) -> Tuple[XrayConfig, List[str]]:
    cards = db.get_cards()
    if not cards:
        raise RuntimeError("数据库中没有网卡记录，请先初始化配置")

    name_prefix = db.get_setting("name_prefix", "Node")
    max_port = db.get_max_port()

    proto_port_counters: Dict[str, int] = {}
    for proto in protocols:
        cfg = proto_configs[proto]
        if _is_order_mode(proto, cfg):
            sp = cfg.get("start_port", 0)
            proto_port_counters[proto] = (sp - 1) if sp > 0 else max_port

    for card in cards:
        name_suffix = card["client_ip"].replace(".", "-")
        for proto in protocols:
            rand_port, params = _build_node_params(proto, proto_configs[proto], card["listen_ip"], port_range)
            if rand_port > 0:
                port = rand_port
            else:
                proto_port_counters[proto] = proto_port_counters.get(proto, max_port) + 1
                port = proto_port_counters[proto]
            in_tag = _tag(proto, card["listen_ip"], "in")
            name = f"{name_prefix}-{name_suffix}-{proto}"
            try:
                db.add_node(card["id"], proto, port, in_tag, name, params)
            except Exception as e:
                print(f"[警告] 创建节点 {name} 失败: {e}，跳过")

    cfg, all_links = generate_from_db()
    return cfg, all_links
