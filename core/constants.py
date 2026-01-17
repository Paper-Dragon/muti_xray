# encoding: utf-8
"""常量定义模块"""

# 端口相关常量
DEFAULT_PORT_START = 10000
DEFAULT_PORT_END = 30000
DEFAULT_START_PORT = 10000

# 默认值常量
DEFAULT_HOST = "bilibili.com"
DEFAULT_SK5_USER = '147258'
DEFAULT_SK5_PASSWD = '147258'
RANDOM_STRING_LENGTH = 5
SK5_CREDENTIAL_LENGTH = 16

# 协议选项
PROTOCOLS = ["socks5", "vmess", "trojan", "shadowsocks", "vmess-socks5"]
SOCKS5_NETWORK_LAYERS = ["tcp", "tcp,udp"]
VMESS_TRANSPORT_MODES = ["ws", "raw", "xhttp"]
SHADOWSOCKS_NETWORK_LAYERS = ['tcp', 'udp', 'tcp,udp']
SHADOWSOCKS_METHODS = ["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305", "plain"]
YES_NO_OPTIONS = ["y", "N"]
