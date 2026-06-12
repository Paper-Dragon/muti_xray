# encoding: utf-8
"""
配置构建器。

build_config() 接收网卡列表、选中协议及各协议参数，
直接构造 dataclass 实例，填入 XrayConfig，同时收集分享链接。
不再有 insert_xxx 系列方法或模板函数层。
"""
from typing import Dict, List, Tuple

import links as lk
from models import (
    ShadowsocksInbound,
    Socks5Inbound,
    VmessInbound,
    XrayConfig,
    _rand_port,
    _rand_str,
    _ip_suffix,
    new_uuid,
    new_path,
)

# vmess-socks5 是复合协议，占用 2 个端口位；其余各占 1 个
_PORT_COST = {"vmess-socks5": 2}


def _tag(proto: str, ip: str, role: str = "in") -> str:
    """生成唯一 tag：{proto}-{role}-{ip_suffix}"""
    return f"{proto.replace('-', '_')}-{role}-{_ip_suffix(ip)}"


def _freedom_outbound(ip: str, tag: str) -> dict:
    return {"sendThrough": ip, "protocol": "freedom", "tag": tag}


def _routing_rule(inbound_tag: str, outbound_tag: str) -> dict:
    return {"type": "field", "inboundTag": [inbound_tag], "outboundTag": outbound_tag}


# ── 单协议节点添加 ────────────────────────────────────────────────────────────

def _add_vmess(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    """添加 VMess 入站，返回 (最终端口, 链接列表)。"""
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


def _add_socks5(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    """添加 Socks5 入站，返回 (最终端口, 链接列表)。"""
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


def _add_shadowsocks(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str, tag_prefix: str,
) -> Tuple[int, List[str]]:
    """添加 Shadowsocks 入站，返回 (最终端口, 链接列表)。"""
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


def _add_vmess_socks5(
    cfg: XrayConfig,
    listen_ip: str, client_ip: str,
    port: int, proto_cfg: dict,
    name: str,
) -> Tuple[int, List[str]]:
    """
    添加 VMess+Socks5 复合节点（各自独立 tag，占用 2 个连续端口）。

    VMess 先确定实际端口（可能随机），sk5 紧跟其后用 vmess_port+1。
    返回 (sk5 端口, 所有链接列表)。
    """
    all_links: List[str] = []

    vmess_port, v_links = _add_vmess(
        cfg, listen_ip, client_ip, port, proto_cfg,
        name=f"v2-{name}", tag_prefix=f"v2_{_ip_suffix(listen_ip)}",
    )
    all_links.extend(v_links)

    # sk5 紧接 vmess 实际端口，保证两者相差 1
    sk5_port, s_links = _add_socks5(
        cfg, listen_ip, client_ip, vmess_port + 1, proto_cfg,
        name=f"sk5-{name}", tag_prefix=f"sk5_{_ip_suffix(listen_ip)}",
    )
    all_links.extend(s_links)

    return sk5_port, all_links


# ── 单张网卡，单个协议 ────────────────────────────────────────────────────────

def _add_protocol_node(
    cfg: XrayConfig,
    card: dict,
    proto: str,
    proto_cfg: dict,
    port: int,
    name: str,
) -> Tuple[int, List[str]]:
    """
    为一张网卡添加一个协议节点。
    返回 (本轮最终端口, 分享链接列表)。
    """
    listen_ip = card["listen_ip"]
    client_ip = card["client_ip"]

    if proto == "vmess":
        return _add_vmess(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "socks5":
        return _add_socks5(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "shadowsocks":
        return _add_shadowsocks(cfg, listen_ip, client_ip, port, proto_cfg, name, proto)
    if proto == "vmess-socks5":
        return _add_vmess_socks5(cfg, listen_ip, client_ip, port, proto_cfg, name)

    raise ValueError(f"未知协议: {proto}")


# ── 顶层入口 ──────────────────────────────────────────────────────────────────

def build_config(
    cards: List[dict],
    protocols: List[str],
    proto_configs: Dict[str, dict],
    blocked_domains: List[str],
    name_prefix: str = "Node",
    start_port: int = 10000,
) -> Tuple[XrayConfig, List[str]]:
    """
    组装完整 XrayConfig 并收集所有分享链接。

    返回 (XrayConfig, 所有节点的链接列表)。
    """
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
                # 补偿端口偏移，避免下一个节点端口冲突
                port += _PORT_COST.get(proto, 1) - 1

    return cfg, all_links
