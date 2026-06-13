# encoding: utf-8
import json
import os
import random
import string
import uuid as _uuid
from dataclasses import dataclass, field
from typing import List, Optional


def _rand_str(length: int = 8) -> str:
    return ''.join(random.sample(string.ascii_letters + string.digits, length))

def _rand_port(lo: int = 10000, hi: int = 30000) -> int:
    return random.randint(lo, hi)

def _ip_suffix(ip: str) -> str:
    return ip.replace(".", "-")

def new_uuid() -> str:
    return str(_uuid.uuid4())

def new_path() -> str:
    return f"/c{_rand_str(5)}c/"


@dataclass
class VmessInbound:
    listen: str
    port: int
    tag: str
    uuid: str
    transport: str
    path: str = ""
    host: str = "bilibili.com"
    name: str = ""

    def to_dict(self) -> dict:
        stream: dict = {"network": self.transport}
        if self.transport == "ws":
            stream["wsSettings"] = {
                "path": self.path,
                "headers": {"Host": self.host},
            }
        elif self.transport == "xhttp":
            stream["xhttpSettings"] = {
                "host": self.host,
                "path": self.path,
                "mode": "auto",
                "extra": {"headers": {}},
            }
        return {
            "listen": self.listen,
            "port": self.port,
            "ps": self.name,
            "protocol": "vmess",
            "settings": {"clients": [{"id": self.uuid, "alterId": 0}]},
            "streamSettings": stream,
            "tag": self.tag,
        }


@dataclass
class Socks5Inbound:
    listen: str
    port: int
    tag: str
    user: str
    passwd: str
    name: str = ""
    udp: bool = False

    def to_dict(self) -> dict:
        return {
            "listen": self.listen,
            "port": self.port,
            "ps": self.name,
            "protocol": "socks",
            "settings": {
                "auth": "password",
                "accounts": [{"user": self.user, "pass": self.passwd}],
                "udp": self.udp,
                "ip": self.listen,
            },
            "streamSettings": {
                "network": "raw",
                "security": "none",
                "rawSettings": {"header": {"type": "none"}},
            },
            "tag": self.tag,
            "sniffing": {},
        }


@dataclass
class ShadowsocksInbound:
    listen: str
    port: int
    tag: str
    method: str
    password: str
    network: str = "tcp,udp"
    name: str = ""

    def to_dict(self) -> dict:
        return {
            "listen": self.listen,
            "port": self.port,
            "ps": self.name,
            "protocol": "shadowsocks",
            "settings": {
                "method": self.method,
                "password": self.password,
                "network": self.network,
                "level": 0,
                "ivCheck": False,
            },
            "streamSettings": {
                "network": "raw",
                "security": "none",
                "rawSettings": {"acceptProxyProtocol": False, "header": {"type": "none"}},
            },
            "tag": self.tag,
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"],
                "metadataOnly": False,
            },
        }


@dataclass
class VlessInbound:
    listen: str
    port: int
    tag: str
    uuid: str
    transport: str
    path: str = ""
    host: str = "bilibili.com"
    name: str = ""
    flow: str = ""

    def to_dict(self) -> dict:
        client: dict = {"id": self.uuid, "level": 0}
        if self.flow:
            client["flow"] = self.flow

        stream: dict = {"network": self.transport}
        if self.transport == "ws":
            stream["wsSettings"] = {
                "path": self.path,
                "headers": {"Host": self.host},
            }
        elif self.transport == "xhttp":
            stream["xhttpSettings"] = {
                "host": self.host,
                "path": self.path,
                "mode": "auto",
                "extra": {"headers": {}},
            }
        return {
            "listen": self.listen,
            "port": self.port,
            "ps": self.name,
            "protocol": "vless",
            "settings": {
                "clients": [client],
                "decryption": "none",
            },
            "streamSettings": stream,
            "tag": self.tag,
        }


@dataclass
class TrojanInbound:
    listen: str
    port: int
    tag: str
    password: str
    cert_file: str
    key_file: str
    transport: str = "raw"
    path: str = ""
    host: str = ""
    name: str = ""

    def to_dict(self) -> dict:
        tls_settings: dict = {
            "certificates": [
                {"certificateFile": self.cert_file, "keyFile": self.key_file}
            ]
        }
        stream: dict = {"network": self.transport, "security": "tls", "tlsSettings": tls_settings}
        if self.transport == "ws":
            stream["wsSettings"] = {"path": self.path, "headers": {"Host": self.host}}
        elif self.transport == "xhttp":
            stream["xhttpSettings"] = {
                "host": self.host, "path": self.path,
                "mode": "auto", "extra": {"headers": {}},
            }
        return {
            "listen": self.listen,
            "port": self.port,
            "ps": self.name,
            "protocol": "trojan",
            "settings": {
                "clients": [{"password": self.password, "level": 0}]
            },
            "streamSettings": stream,
            "tag": self.tag,
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"],
                "metadataOnly": False,
            },
        }


@dataclass
class XrayConfig:
    inbounds: list = field(default_factory=list)
    outbounds: list = field(default_factory=list)
    routing_rules: list = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    log_level: str = "warning"
    log_path: str = "/var/log/xray/"

    def build(self) -> dict:
        rules = []

        if self.blocked_domains:
            rules.append({
                "type": "field",
                "domain": self.blocked_domains,
                "outboundTag": "out-block",
            })

        rules.extend(self.routing_rules)

        outbounds = list(self.outbounds)
        if self.blocked_domains:
            outbounds.insert(0, {"protocol": "blackhole", "tag": "out-block"})

        return {
            "log": {
                "loglevel": self.log_level,
                "access": f"{self.log_path}access.log",
                "error": f"{self.log_path}error.log",
            },
            "routing": {
                "domainStrategy": "AsIs",
                "domainMatcher": "mph",
                "rules": rules,
            },
            "inbounds": [
                (ib.to_dict() if hasattr(ib, "to_dict") else ib)
                for ib in self.inbounds
            ],
            "outbounds": outbounds,
        }

    def save(self, path: str = "/usr/local/etc/xray/config.json") -> None:
        config_dir = os.path.dirname(path)
        if config_dir:
            os.makedirs(config_dir, mode=0o755, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.build(), f, indent=4, separators=(",", ": "))
