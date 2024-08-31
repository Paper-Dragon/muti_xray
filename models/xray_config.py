from typing import List, Dict, Any, Optional, Literal
from transport_config import *
from log_config import *
from api_config import *
from policy_config import *
from dns_config import *

class RoutingRuleConfig:
    def __init__(self,
                 domain_matcher: str = "mph",
                 type: str = "field",
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
                 balancer_tag: str = "balancer"):
        self.domain_matcher = domain_matcher
        self.type = type
        self.domains = domains if domains else []
        self.ip = ip if ip else []
        self.port = port
        self.source_port = source_port
        self.network = network
        self.source = source if source else []
        self.user = user if user else []
        self.inbound_tag = inbound_tag if inbound_tag else []
        self.protocol = protocol if protocol else []
        self.attrs = attrs
        self.outbound_tag = outbound_tag
        self.balancer_tag = balancer_tag

class RoutingConfig:
    def __init__(self, 
                 domain_strategy: str = "AsIs", 
                 domain_matcher: str = "mph", 
                 rules: Optional[List[RoutingRuleConfig]] = None,
                 balancers: Optional[List[Dict[str, Any]]] = None):
        self.domain_strategy = domain_strategy
        self.domain_matcher = domain_matcher
        self.rules = rules if rules else []
        self.balancers = balancers if balancers else []

class InboundConfig:
    def __init__(self, 
                 listen: str = "127.0.0.1", 
                 port: int = 1080, 
                 protocol: Literal["trojan", "socks", "dokodemo-door",
                                    "http", "shadowsocks", "vless"] =  "vmess", 
                 settings: Dict[str, Any] = None, 
                 stream_settings: StreamSettingsConfig = None, 
                 tag: str = "identifier", 
                 sniffing: SniffingConfig = SniffingConfig(), 
                 allocate: AllocateConfig = AllocateConfig()):
        """
        Initialize Inbound configuration.

        :param listen: IP address to listen on, default is "127.0.0.1".
        :param port: Port number to listen on, default is 1080.
        :param protocol: Protocol name, default is "protocol_name".
        :param settings: Protocol-specific settings.
        :param stream_settings: Stream settings.
        :param tag: Tag for this inbound connection.
        :param sniffing: Sniffing configuration.
        :param allocate: Allocate configuration.
        """
        self.listen = listen
        self.port = port
        self.protocol = protocol
        self.settings = settings if settings else {}
        self.stream_settings = stream_settings if stream_settings else StreamSettingsConfig()
        self.tag = tag
        self.sniffing = sniffing
        self.allocate = allocate

class ProxySettingsConfig:
    def __init__(self,
                 tag: str = "another-outbound-tag",
                 transportLayer: str = "false"):
        self.tag = tag
        self.transportLayer = transportLayer

class MuxConfig:
    def __init__(self,
                 enabled: str = "false",
                 concurrency: int = 8
                 ):
        self.enabled = enabled
        self.concurrency = concurrency

class OutboundConfig:
    
    """
    出站连接用于向远程网站或下一级代理服务器发送数据

    :param send_through: 用于发送数据的 IP 地址，当主机有多个 IP 地址时有效，默认值为 "0.0.0.0"

    """
    def __init__(self, 
                 send_through: str = "0.0.0.0",
                 protocol: Literal["blackhole", "dns", "freedom", "http",
                                    "socks", "vmess", "shadowsocks", "trojan",
                                    "vless", "loopback"] = "freedom", 
                 # settings: Dict[str, Any] = None,
                 tag: str = "identifier",
                 stream_settings: Dict[str, Any] = None,
                 proxy_settings: ProxySettingsConfig = ProxySettingsConfig(),
                 mux: MuxConfig = MuxConfig()):
        self.send_through = send_through
        self.protocol = protocol
        # self.settings = settings if settings else {}
        self.tag = tag
        self.stream_settings = stream_settings if stream_settings else StreamSettingsConfig()
        self.proxy_settings = proxy_settings
        self.mux = mux

class StatsConfig:
    def __init__(self):
        pass  # Implement as needed

class ReverseConfig:
    def __init__(self):
        pass  # Implement as needed

class FakeDNSConfig:
    def __init__(self, ip_pool: str = "198.18.0.0/16", pool_size: int = 65535):
        self.ip_pool = ip_pool
        self.pool_size = pool_size

class BrowserForwarderConfig:
    def __init__(self):
        pass  # Implement as needed

class ObservatoryConfig:
    def __init__(self):
        pass  # Implement as needed

class XrayConfig:
    def __init__(self, 
                 log: Optional[LogConfig] = LogConfig(),
                 api: Optional[APIConfig] = APIConfig(),
                 dns: Optional[DNSConfig] = DNSConfig(),
                 routing: Optional[RoutingConfig] = {},
                 policy: Optional[PolicyConfig] = {},
                 inbounds: Optional[List[InboundConfig]] = None,
                 outbounds: Optional[List[OutboundConfig]] = None,
                 transport: Optional[TransportConfig] = {},
                 stats: StatsConfig = StatsConfig(),
                 reverse: ReverseConfig = ReverseConfig(),
                 fakedns: Optional[List[FakeDNSConfig]] = None,
                 browser_forwarder: BrowserForwarderConfig = BrowserForwarderConfig(),
                 observatory: ObservatoryConfig = ObservatoryConfig()):
        
        self.log = log
        self.api = api
        self.dns = dns
        self.routing = routing if routing else {}
        self.policy = policy if policy else {}
        self.inbounds = inbounds if inbounds else []
        self.outbounds = outbounds if outbounds else []
        self.transport = transport if transport else {}
        self.stats = stats
        self.reverse = reverse
        self.fakedns = fakedns if fakedns else []
        self.browser_forwarder = browser_forwarder
        self.observatory = observatory

    def to_dict(self) -> Dict[str, Any]:
        """Converts the configuration to a dictionary."""
        return {
            "log": vars(self.log) if self.log else {},
            "api": vars(self.api) if self.api else {},
            "dns": vars(self.dns) if self.dns else {},
            "routing": vars(self.routing) if self.routing else {},
            "policy": self.policy if self.policy else {},
            "inbounds": [vars(inbound) for inbound in self.inbounds],
            "outbounds": [vars(outbound) for outbound in self.outbounds],
            "transport": vars(self.transport) if self.transport else {},
            "stats": vars(self.stats),
            "reverse": vars(self.reverse),
            "fakedns": [vars(fakedns) for fakedns in self.fakedns],
            "browserForwarder": vars(self.browser_forwarder),
            "observatory": vars(self.observatory),
        }

    def save_to_json(self, filepath: str) -> None:
        """Saves the configuration to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)


import json
def __test():
    xray_config = XrayConfig()
    xray_config_dict = xray_config.to_dict()
    format_json = json.dumps(xray_config_dict, indent=4)
    print(format_json)
    xray_config.save_to_json("./config.json")

__test()
