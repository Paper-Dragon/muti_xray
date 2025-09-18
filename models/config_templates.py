# encoding: utf-8
"""配置模板模块 - 使用函数返回字典配置而非类定义"""
from typing import List, Dict, Any, Optional


# ==================== 传输层配置模板 ====================

def create_raw_settings(accept_proxy_protocol: bool = False, header_type: str = "none",
                       request: Optional[Dict] = None, response: Optional[Dict] = None) -> Dict:
    """创建 RAW 传输设置"""
    config = {
        "acceptProxyProtocol": accept_proxy_protocol,
        "header": {"type": header_type}
    }
    if header_type == "http":
        config["header"]["request"] = request if request else create_http_request()
        config["header"]["response"] = response if response else create_http_response()
    return config


def create_http_request(version: str = "1.1", method: str = "GET",
                       path: Optional[List[str]] = None,
                       headers: Optional[Dict[str, List[str]]] = None) -> Dict:
    """创建 HTTP 请求配置"""
    return {
        "version": version,
        "method": method,
        "path": path if path else ["/"],
        "headers": headers if headers else {
            "Host": ["www.baidu.com", "www.bing.com"],
            "User-Agent": [
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46"
            ],
            "Accept-Encoding": ["gzip, deflate"],
            "Connection": ["keep-alive"],
            "Pragma": ["no-cache"]
        }
    }


def create_http_response(version: str = "1.1", status: str = "200", reason: str = "OK",
                        headers: Optional[Dict[str, List[str]]] = None) -> Dict:
    """创建 HTTP 响应配置"""
    return {
        "version": version,
        "status": status,
        "reason": reason,
        "headers": headers if headers else {
            "Content-Type": ["application/octet-stream", "video/mpeg"],
            "Transfer-Encoding": ["chunked"],
            "Connection": ["keep-alive"],
            "Pragma": ["no-cache"]
        }
    }


def create_websocket_settings(accept_proxy_protocol: bool = False, path: str = "/",
                             headers: Optional[Dict[str, str]] = None,
                             max_early_data: int = 1024,
                             use_browser_forwarding: bool = False,
                             early_data_header_name: str = "") -> Dict:
    """创建 WebSocket 设置"""
    return {
        "acceptProxyProtocol": accept_proxy_protocol,
        "path": path,
        "headers": headers if headers else {"Host": "v2ray.com"},
        "maxEarlyData": max_early_data,
        "useBrowserForwarding": use_browser_forwarding,
        "earlyDataHeaderName": early_data_header_name
    }


def create_xhttp_settings(host: str = "example.com", path: str = "/yourpath",
                         mode: str = "auto", extra: Optional[Dict[str, Any]] = None) -> Dict:
    """创建 XHTTP 设置"""
    return {
        "host": host,
        "path": path,
        "mode": mode,
        "extra": extra if extra else {"headers": {}}
    }


def create_grpc_settings(service_name: str = "GunService") -> Dict:
    """创建 gRPC 设置"""
    return {"serviceName": service_name}


def create_quic_settings(header_type: str = "none") -> Dict:
    """创建 QUIC 设置"""
    return {"type": header_type}


def create_domain_socket_settings(path: str = "/path/to/ds/file",
                                 abstract: bool = False, padding: bool = False) -> Dict:
    """创建 Domain Socket 设置"""
    return {"path": path, "abstract": abstract, "padding": padding}


def create_kcp_settings(mtu: int = 1350, tti: int = 20,
                       uplink_capacity: int = 5, downlink_capacity: int = 20,
                       congestion: bool = False, read_buffer_size: int = 1,
                       write_buffer_size: int = 1, header_type: str = "none",
                       seed: Optional[str] = "Password") -> Dict:
    """创建 KCP 设置"""
    return {
        "mtu": mtu,
        "tti": tti,
        "uplinkCapacity": uplink_capacity,
        "downlinkCapacity": downlink_capacity,
        "congestion": congestion,
        "readBufferSize": read_buffer_size,
        "writeBufferSize": write_buffer_size,
        "header": {"type": header_type},
        "seed": seed
    }


def create_tls_settings(server_name: str = "v2ray.com",
                       alpn: Optional[List[str]] = None,
                       allow_insecure: bool = False,
                       disable_system_root: bool = False,
                       certificates: Optional[List[Dict]] = None,
                       verify_client_certificate: bool = False,
                       pinned_peer_certificate_chain_sha256: str = "") -> Dict:
    """创建 TLS 设置"""
    return {
        "serverName": server_name,
        "alpn": alpn if alpn else ["h2", "http/1.1"],
        "allowInsecure": allow_insecure,
        "disableSystemRoot": disable_system_root,
        "certificates": certificates if certificates else [],
        "verifyClientCertificate": verify_client_certificate,
        "pinnedPeerCertificateChainSha256": pinned_peer_certificate_chain_sha256
    }


def create_stream_settings(network: str = "raw", security: str = "none",
                          raw_settings: Optional[Dict] = None,
                          ws_settings: Optional[Dict] = None,
                          xhttp_settings: Optional[Dict] = None,
                          tls_settings: Optional[Dict] = None,
                          kcp_settings: Optional[Dict] = None,
                          quic_settings: Optional[Dict] = None,
                          ds_settings: Optional[Dict] = None,
                          grpc_settings: Optional[Dict] = None,
                          sockopt: Optional[Dict] = None) -> Dict:
    """创建流设置配置"""
    config = {"network": network, "security": security}
    
    # 根据网络类型添加对应的设置
    network_settings_map = {
        "raw": ("rawSettings", raw_settings),
        "kcp": ("kcpSettings", kcp_settings),
        "ws": ("wsSettings", ws_settings),
        "xhttp": ("xhttpSettings", xhttp_settings),
        "quic": ("quicSettings", quic_settings),
        "domainsocket": ("dsSettings", ds_settings),
        "grpc": ("grpcSettings", grpc_settings)
    }
    
    settings_key, settings_value = network_settings_map.get(network, (None, None))
    if settings_key and settings_value:
        config[settings_key] = settings_value
    
    if tls_settings and security == "tls":
        config["tlsSettings"] = tls_settings
    
    if sockopt:
        config["sockopt"] = sockopt
    
    return config


def create_sniffing_config(enabled: bool = True,
                          dest_override: Optional[List[str]] = None,
                          metadata_only: bool = False) -> Dict:
    """创建流量嗅探配置"""
    return {
        "enabled": enabled,
        "destOverride": dest_override if dest_override else ["http", "tls"],
        "metadataOnly": metadata_only
    }


# ==================== Xray 配置模板 ====================

def create_log_config(loglevel: str = "info",
                     access: Optional[str] = None,
                     error: Optional[str] = None) -> Dict:
    """创建日志配置"""
    config = {"loglevel": loglevel}
    if access:
        config["access"] = access
    if error:
        config["error"] = error
    return config


def create_routing_rule(domain_matcher: str = "mph", rule_type: str = "field",
                       domains: Optional[List[str]] = None,
                       ip: Optional[List[str]] = None,
                       port: str = "53,443,1000-2000",
                       source_port: str = "53,443,1000-2000",
                       network: str = "tcp",
                       source: Optional[List[str]] = None,
                       user: Optional[List[str]] = None,
                       inbound_tag: Optional[List[str]] = None,
                       protocol: Optional[List[str]] = None,
                       attrs: str = "attrs[':method'] == 'GET'",
                       outbound_tag: str = "direct",
                       balancer_tag: str = "balancer") -> Dict:
    """创建路由规则"""
    rule = {"type": rule_type}
    if domains:
        rule["domain"] = domains
    if ip:
        rule["ip"] = ip
    if port:
        rule["port"] = port
    if source_port:
        rule["sourcePort"] = source_port
    if network:
        rule["network"] = network
    if source:
        rule["source"] = source
    if user:
        rule["user"] = user
    if inbound_tag:
        rule["inboundTag"] = inbound_tag
    if protocol:
        rule["protocol"] = protocol
    if attrs:
        rule["attrs"] = attrs
    if outbound_tag:
        rule["outboundTag"] = outbound_tag
    if balancer_tag:
        rule["balancerTag"] = balancer_tag
    return rule


def create_routing_config(domain_strategy: str = "AsIs",
                         domain_matcher: str = "mph",
                         rules: Optional[List[Dict]] = None,
                         balancers: Optional[List[Dict]] = None) -> Dict:
    """创建路由配置"""
    config = {
        "domainStrategy": domain_strategy,
        "domainMatcher": domain_matcher,
        "rules": rules if rules else [],
        "balancers": balancers if balancers else []
    }
    return config


def create_shadowsocks_settings(method: str = "plain", password: str = "password",
                               email: Optional[str] = None, level: int = 0,
                               network: str = "tcp,udp", iv_check: bool = False) -> Dict:
    """创建 Shadowsocks 设置"""
    settings = {
        "method": method,
        "password": password,
        "level": level,
        "network": network,
        "ivCheck": iv_check
    }
    if email:
        settings["email"] = email
    return settings


def create_inbound_config(listen: str = "127.0.0.1", port: int = 1080,
                         protocol: str = "vmess",
                         settings: Optional[Dict] = None,
                         stream_settings: Optional[Dict] = None,
                         tag: str = "identifier",
                         sniffing: Optional[Dict] = None,
                         allocate: Optional[Dict] = None,
                         ps: Optional[str] = None) -> Dict:
    """创建入站配置"""
    config = {
        "listen": listen,
        "port": port,
        "protocol": protocol,
        "settings": settings if settings else {},
        "streamSettings": stream_settings if stream_settings else {},
        "tag": tag,
        "sniffing": sniffing if sniffing else create_sniffing_config()
    }
    if ps:
        config["ps"] = ps
    if allocate:
        config["allocate"] = allocate
    return config
