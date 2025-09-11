from typing import Optional, Dict, Union, List, Any
class DNSConfig:
    """
    DNSConfig 类用于表示 DNS 配置，包含多个 DNS 相关参数。
    
    属性:
    - hosts: 一个字典，定义域名到 IP 地址的映射，可以是单个 IP 地址或 IP 地址的列表。
    - servers: 一个列表，定义 DNS 服务器，可以是字符串（表示简单的 DNS 服务器地址）或复杂的服务器配置字典。
    - clientIp: 当前网络的 IP 地址。用于 DNS 查询时通知 DNS 服务器，客户端所在的地理位置（不能是私有 IP 地址）。
    - queryStrategy: DNS 查询策略（例如优先使用 IPv4）。
    - disableCache: 是否禁用 DNS 缓存。
    - disableFallback: 是否禁用 DNS 回退机制。
    - tag: 一个标签，用于标识此 DNS 配置的来源或用途。
    """
    
    def __init__(self,
                 hosts: Dict[str, Union[str, List[str]]] = {},
                 servers: List[Union[str, Dict[str, Any]]] = ["localhost", "https://dns.google/dns-query","1.0.0.1"],
                 clientIp: str = "",
                 queryStrategy: str = "UseIPv4",
                 disableCache: bool = True,
                 disableFallback: bool = True,
                 tag: str = "dns_inbound"):
        """
        初始化 DNSConfig 类的实例。

        参数:
        - hosts: 字典，定义域名到 IP 地址的映射。
        - servers: 列表，包含 DNS 服务器的配置。
        - clientIp: 字符串，客户端 IP 地址。
        - queryStrategy: 字符串，定义 DNS 查询策略。
        - disableCache: 布尔值，是否禁用 DNS 缓存。
        - disableFallback: 布尔值，是否禁用 DNS 回退。
        - tag: 字符串，配置的标签。
        """
        self.hosts = hosts if hosts else {}
        self.servers = servers if servers else []
        if clientIp:
            self.clientIp = clientIp
        self.queryStrategy = queryStrategy
        self.disableCache = disableCache
        self.disableFallback = disableFallback
        self.tag = tag

    def to_dict(self) -> Dict[str, Any]:
        """
        将 DNSConfig 实例转换为字典。

        返回:
        - 字典，包含 DNSConfig 的所有配置项。
        """
        return {
            "hosts": self.hosts,
            "servers": self.servers,
            "clientIp": self.clientIp,
            "queryStrategy": self.queryStrategy,
            "disableCache": self.disableCache,
            "disableFallback": self.disableFallback,
            "tag": self.tag
        }