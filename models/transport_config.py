from typing import List, Dict, Any, Optional, Literal


class HTTPRequestConfig:
    def __init__(self,
                 version: str = "1.1",
                 method: str = "GET",
                 path: Optional[List[str]] = None,
                 headers: Optional[Dict[str, List[str]]] = None):
        self.version = version
        self.method = method
        self.path = path if path else ["/"]
        self.headers = headers if headers else {
            "Host": ["www.baidu.com", "www.bing.com"],
            "User-Agent": [
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46"
            ],
            "Accept-Encoding": ["gzip, deflate"],
            "Connection": ["keep-alive"],
            "Pragma": ["no-cache"]
        }

class HTTPResponseConfig:
    def __init__(self,
                 version: str = "1.1",
                 status: str = "200",
                 reason: str = "OK",
                 headers: Optional[Dict[str, List[str]]] = None):
        self.version = version
        self.status = status
        self.reason = reason
        self.headers = headers if headers else {
            "Content-Type": ["application/octet-stream", "video/mpeg"],
            "Transfer-Encoding": ["chunked"],
            "Connection": ["keep-alive"],
            "Pragma": ["no-cache"]
        }

class TCPSettingsConfig:
    def __init__(self, acceptProxyProtocol: bool = False, header_type: str = "none",
                 request: Optional[HTTPRequestConfig] = None, response: Optional[HTTPResponseConfig] = None):
        self.acceptProxyProtocol = acceptProxyProtocol
        self.header = {"type": header_type}
        if header_type == "http":
            self.header["request"] = request if request else HTTPRequestConfig()
            self.header["response"] = response if response else HTTPResponseConfig()

class KCPSettingsConfig:
    def __init__(self, 
                 mtu: int = 1350, 
                 tti: int = 20, 
                 uplink_capacity: int = 5, 
                 downlink_capacity: int = 20,
                 congestion: bool = False, 
                 read_buffer_size: int = 1, 
                 write_buffer_size: int = 1,
                 header_type: str = "none", 
                 seed: Optional[str] = "Password"):
        """
        Initialize KCP settings.

        :param mtu: Maximum Transmission Unit size, default is 1350.
        :param tti: Transmission Time Interval, default is 20.
        :param uplink_capacity: Uplink capacity in MB, default is 5.
        :param downlink_capacity: Downlink capacity in MB, default is 20.
        :param congestion: Enable congestion control, default is False.
        :param read_buffer_size: Size of the read buffer, default is 1.
        :param write_buffer_size: Size of the write buffer, default is 1.
        :param header_type: Type of packet header for obfuscation, default is "none". 
                            Available options: "none", "srtp", "utp", "wechat-video", 
                            "dtls", "wireguard".
        :param seed: Encryption seed, optional, default is "Password".
        """
        self.mtu = mtu
        self.tti = tti
        self.uplink_capacity = uplink_capacity
        self.downlink_capacity = downlink_capacity
        self.congestion = congestion
        self.read_buffer_size = read_buffer_size
        self.write_buffer_size = write_buffer_size
        self.header = {"type": header_type}
        self.seed = seed

class WebSocketSettingsConfig:
    def __init__(self,
                 acceptProxyProtocol: bool = False,
                 path: str = "/",
                 headers: Optional[Dict[str, str]] = None,
                 max_early_data: int = 1024,
                 use_browser_forwarding: bool = False,
                 early_data_header_name: str = ""):
        self.acceptProxyProtocol = acceptProxyProtocol
        self.path = path
        self.headers = headers if headers else {"Host": "v2ray.com"}
        self.max_early_data = max_early_data
        self.use_browser_forwarding = use_browser_forwarding
        self.early_data_header_name = early_data_header_name

class HTTPSettingsConfig:
    def __init__(self,
                 host: Optional[List[str]] = None,
                 path: str = "/random/path",
                 method: str = "PUT",
                 headers: Optional[Dict[str, List[str]]] = None):
        self.host = host if host else ["v2ray.com"]
        self.path = path
        self.method = method
        self.headers = headers if headers else {}

class GRPCSettingsConfig:
    def __init__(self, service_name: str = "GunService"):
        self.service_name = service_name

class QUICSettingsConfig:
    def __init__(self, header_type: str = "none"):
        """
        Initialize QUIC settings.

        :param header_type: Type of packet header for obfuscation, default is "none".
                            Available options: "none", "srtp", "utp", "wechat-video", 
                            "dtls", "wireguard".
        """
        self.type = header_type

class DomainSocketConfig:
    def __init__(self, path: str = "/path/to/ds/file", abstract: bool = False, padding: bool = False):
        """
        Initialize DomainSocket settings.

        :param path: The file system path to the domain socket.
        :param abstract: Whether to use an abstract namespace socket, default is False.
        :param padding: Whether to pad the data, default is False.
        """
        self.path = path
        self.abstract = abstract
        self.padding = padding

class SniffingConfig:
    def __init__(self, 
                 enabled: bool = True, 
                 destOverride: Optional[List[str]] = None, 
                 metadataOnly: bool = False):
        """
        Initialize Sniffing configuration.

        :param enabled: Whether sniffing is enabled, default is True.
        :param destOverride: List of protocols to override, default is ["http", "tls"].
        :param metadataOnly: Whether to use only metadata, default is False.
        """
        self.enabled = enabled
        self.destOverride = destOverride if destOverride else ["http", "tls"]
        self.metadataOnly = metadataOnly

class AllocateConfig:
    def __init__(self, 
                 strategy: str = "always", 
                 refresh: int = 5, 
                 concurrency: int = 3):
        """
        Initialize Allocate configuration.

        :param strategy: Allocation strategy, default is "always".
        :param refresh: Refresh time in seconds, default is 5.
        :param concurrency: Number of concurrent connections, default is 3.
        """
        self.strategy = strategy
        self.refresh = refresh
        self.concurrency = concurrency

class SockoptConfig:
    def __init__(self, 
                 mark: int = 0, 
                 tcp_fast_open: bool = False, 
                 tcp_fast_open_queue_length: int = 4096, 
                 tproxy: str = "off", 
                 tcp_keep_alive_interval: int = 0):
        """
        Initialize Socket options configuration.

        :param mark: Mark for routing, default is 0.
        :param tcp_fast_open: Enable TCP Fast Open, default is False.
        :param tcp_fast_open_queue_length: Length of the TCP Fast Open queue, default is 4096.
        :param tproxy: Transparent proxy setting, default is "off".
        :param tcp_keep_alive_interval: Interval for TCP keep-alive, default is 0.
        """
        self.mark = mark
        self.tcp_fast_open = tcp_fast_open
        self.tcp_fast_open_queue_length = tcp_fast_open_queue_length
        self.tproxy = tproxy
        self.tcp_keep_alive_interval = tcp_keep_alive_interval

class CertificateConfig:
    def __init__(self, 
                 usage: str = "encipherment", 
                 certificate_file: str = "/path/to/certificate.crt", 
                 key_file: str = "/path/to/key.key", 
                 certificate: Optional[List[str]] = None, 
                 key: Optional[List[str]] = None):
        """
        Initialize Certificate configuration.

        :param usage: Usage type, default is "encipherment".
        :param certificate_file: Path to the certificate file, default is "/path/to/certificate.crt".
        :param key_file: Path to the key file, default is "/path/to/key.key".
        :param certificate: List of certificate strings.
        :param key: List of key strings.
        """
        self.usage = usage
        self.certificate_file = certificate_file
        self.key_file = key_file
        self.certificate = certificate if certificate else []
        self.key = key if key else []

class TLSSettingsConfig:
    def __init__(self, 
                 server_name: str = "v2ray.com", 
                 alpn: Optional[List[str]] = None, 
                 allow_insecure: bool = False, 
                 disable_system_root: bool = False, 
                 certificates: Optional[List[Dict[str, Any]]] = None, 
                 verify_client_certificate: bool = False, 
                 pinned_peer_certificate_chain_sha256: str = ""):
        """
        Initialize TLS settings configuration.

        :param server_name: Server name for TLS, default is "v2ray.com".
        :param alpn: Application-Layer Protocol Negotiation strings, e.g., ["h2", "http/1.1"].
        :param allow_insecure: Allow insecure connections, default is False.
        :param disable_system_root: Disable using system root certificates, default is False.
        :param certificates: List of certificates for TLS, default is an empty list.
        :param verify_client_certificate: Verify client certificate, default is False.
        :param pinned_peer_certificate_chain_sha256: SHA256 hash of pinned peer certificate chain, default is an empty string.
        """
        self.server_name = server_name
        self.alpn = alpn if alpn else ["h2", "http/1.1"]
        self.allow_insecure = allow_insecure
        self.disable_system_root = disable_system_root
        self.certificates = certificates if certificates else CertificateConfig()
        self.verify_client_certificate = verify_client_certificate
        self.pinned_peer_certificate_chain_sha256 = pinned_peer_certificate_chain_sha256

class StreamSettingsConfig:
    def __init__(self, 
                 network: Literal["tcp", "kcp", "ws", "http", "domainsocket", "quic", "grpc"] = "tcp", 
                 security: Literal["none", "tls"] = "none", 
                 tls_settings: Optional[TLSSettingsConfig] = None, 
                 tcp_settings: Optional[TCPSettingsConfig] = None, 
                 kcp_settings: Optional[KCPSettingsConfig] = None, 
                 ws_settings: Optional[WebSocketSettingsConfig] = None, 
                 http_settings: Optional[HTTPSettingsConfig] = None, 
                 quic_settings: Optional[QUICSettingsConfig] = None, 
                 ds_settings: Optional[DomainSocketConfig] = None, 
                 grpc_settings: Optional[GRPCSettingsConfig] = None, 
                 sockopt: Optional[SockoptConfig] = None):
        """
        Initialize StreamSettings configuration.

        :param network: Network type, determines the underlying transport protocol.
                        Can be "tcp", "kcp", "ws" (WebSocket), "http", "domainsocket", "quic", or "grpc".
        :param security: Security protocol used for the connection. Can be "none" or "tls".
        :param tls_settings: TLS settings for securing the connection. Only relevant if security is set to "tls".
                            Represented by an instance of TLSSettingsConfig.
        :param tcp_settings: Configuration for TCP connections. Represented by an instance of TCPSettingsConfig.
        :param kcp_settings: Configuration for KCP connections. Represented by an instance of KCPSettingsConfig.
        :param ws_settings: Configuration for WebSocket (ws) connections. Represented by an instance of WebSocketSettingsConfig.
        :param http_settings: Configuration for HTTP/2 connections. Represented by an instance of HTTPSettingsConfig.
        :param quic_settings: Configuration for QUIC connections. Represented by an instance of QUICSettingsConfig.
        :param ds_settings: Configuration for Domain Socket connections. Represented by an instance of DomainSocketConfig.
        :param grpc_settings: Configuration for gRPC connections. Represented by an instance of GRPCSettingsConfig.
        :param sockopt: Socket options, such as TCP Fast Open, marking, and keep-alive intervals.
                       Represented by an instance of SockoptConfig.
        """
        self.network = network
        self.security = security
        
        network_settings_map = {
            "tcp": tcp_settings,
            "kcp": kcp_settings,
            "ws": ws_settings,
            "http": http_settings,
            "quic": quic_settings,
            "domainsocket": ds_settings,
            "grpc": grpc_settings
        }
        # print(f"Network: @{network}@")
        # print(f"Available settings: {network_settings_map}")
        # print(f"Selected setting: {network_settings_map.get(network)}")

        if network in network_settings_map:
            settings = network_settings_map[network]
            if settings:
                setattr(self, f"{network}Settings", vars(settings))
        if tls_settings and security == "tls":
            self.tls_settings = vars(tls_settings)
        if sockopt:
            self.sockopt = sockopt


class TransportConfig:
    def __init__(self, tcpSettings=None, kcpSettings=None, wsSettings=None, httpSettings=None, quicSettings=None, dsSettings=None, grpcSettings=None):
        self.tcpSettings = vars(tcpSettings) if tcpSettings else vars(TCPSettingsConfig())
        self.kcpSettings = vars(kcpSettings) if kcpSettings else vars(KCPSettingsConfig())
        self.wsSettings = vars(wsSettings) if wsSettings else vars(WebSocketSettingsConfig())
        self.httpSettings = vars(httpSettings) if httpSettings else vars(HTTPSettingsConfig())
        self.quicSettings = vars(quicSettings) if quicSettings else vars(QUICSettingsConfig())
        self.dsSettings = vars(dsSettings) if dsSettings else vars(DomainSocketConfig())
        self.grpcSettings = vars(grpcSettings) if grpcSettings else vars(GRPCSettingsConfig())


    def to_dict(self) -> Dict[str, Any]:
        """Converts the configuration to a dictionary."""
        return {
            "tcpSettings": self.tcpSettings,
            "kcpSettings": self.kcpSettings,
            "wsSettings": self.wsSettings,
            "httpSettings": self.httpSettings,
            "quicSettings": self.quicSettings,
            "dsSettings": self.dsSettings,
            "grpcSettings": self.grpcSettings,
        }
    def save_to_json(self, filepath: str) -> None:
        """Saves the configuration to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)


import json
def __test():
    config = TransportConfig()
    config_dict = config.to_dict()
    format_json = json.dumps(config_dict, indent=4)
    print(format_json)
    config.save_to_json("./config.json")

# __test()