# encoding: utf-8
"""协议配置模块"""
import os
from typing import Dict, Any

from utils import xray
from .constants import (
    SOCKS5_NETWORK_LAYERS, VMESS_TRANSPORT_MODES, 
    SHADOWSOCKS_NETWORK_LAYERS, SHADOWSOCKS_METHODS
)
from .utils import show_menu, get_yes_no_choice, exit_with_error
from utils.color import Warning, YELLOW, FONT


def compatible_kitsunebi():
    """为Kitsunebi客户端优化配置"""
    if os.system(f'grep XRAY_VMESS_AEAD_FORCED {xray.service_config_file} >/dev/null'):
        os.system(f"sed -i '/\\[Service\\]/a\\\\Environment=\"XRAY_VMESS_AEAD_FORCED=false\"' {xray.service_config_file}")
        os.system("systemctl daemon-reload")
        xray.restart()
    else:
        print("经过查询，Kitsunebi 已经优化过了！")


def configure_socks5_protocol() -> Dict[str, Any]:
    """配置socks5协议参数"""
    socks5_network_layer = SOCKS5_NETWORK_LAYERS[show_menu(SOCKS5_NETWORK_LAYERS, "你想要什么socks5网络层协议")]
    
    advanced_configuration = get_yes_no_choice("socks5高级配置")
    sk5_pin_passwd_mode = "N"
    sk5_order_ports_mode = "N"
    
    if advanced_configuration == "y":
        sk5_pin_passwd_mode = get_yes_no_choice("启动默认密码并且放弃随机密码")
        sk5_order_ports_mode = get_yes_no_choice("是否顺序生成端口？默认随机生成")
    
    return {
        "network_layer": socks5_network_layer,
        "advanced_configuration": advanced_configuration,
        "sk5_pin_passwd_mode": sk5_pin_passwd_mode,
        "sk5_order_ports_mode": sk5_order_ports_mode
    }


def configure_vmess_protocol() -> Dict[str, Any]:
    """配置vmess协议参数"""
    vmess_transport_mode = VMESS_TRANSPORT_MODES[show_menu(
        VMESS_TRANSPORT_MODES, 
        "输入要创建的传输层模式（raw即tcp模式，xhttp支持HTTP/1.1、HTTP/2、HTTP/3）"
    )]
    
    disable_aead_verify = get_yes_no_choice("是否开启面向Kitsunebi优化(默认开启）")
    if disable_aead_verify != "N":
        compatible_kitsunebi()
    
    return {"transport_mode": vmess_transport_mode}


def configure_vmess_socks5_protocol() -> Dict[str, Any]:
    """配置vmess-socks5组合协议参数"""
    socks5_network_layer = ["tcp", "tcp+udp"][show_menu(["tcp", "tcp+udp"], "你想要什么socks5网络层协议")]
    vmess_transport_mode = VMESS_TRANSPORT_MODES[show_menu(
        VMESS_TRANSPORT_MODES,
        "输入要创建vmess的传输层模式（raw即tcp模式，xhttp支持HTTP/1.1、HTTP/2、HTTP/3）"
    )]
    
    disable_aead_verify = get_yes_no_choice("是否开启面向Kitsunebi优化(默认开启）")
    if disable_aead_verify != "N":
        compatible_kitsunebi()
    
    advanced_configuration = get_yes_no_choice("是否要进入高级配置，定制功能")
    sk5_pin_passwd_mode = "N"
    sk5_order_ports_mode = "N"
    
    if advanced_configuration == "y":
        sk5_pin_passwd_mode = get_yes_no_choice("启动sk5默认密码放弃随机密码？")
        sk5_order_ports_mode = get_yes_no_choice("是否顺序生成端口？默认随机生成")
    
    return {
        "socks5_network_layer": socks5_network_layer,
        "vmess_transport_mode": vmess_transport_mode,
        "advanced_configuration": advanced_configuration,
        "sk5_pin_passwd_mode": sk5_pin_passwd_mode,
        "sk5_order_ports_mode": sk5_order_ports_mode
    }


def configure_shadowsocks_protocol() -> Dict[str, Any]:
    """配置shadowsocks协议参数"""
    network_layer = SHADOWSOCKS_NETWORK_LAYERS[show_menu(SHADOWSOCKS_NETWORK_LAYERS, "你想要什么网络层协议")]
    method = SHADOWSOCKS_METHODS[show_menu(SHADOWSOCKS_METHODS, "加密方法")]
    try:
        password = input("请输入密码(回车则随机生成密码):")
    except (EOFError, KeyboardInterrupt):
        # 非交互式环境，使用空密码（将随机生成）
        password = ""
        print(f" {Warning} {YELLOW}非交互式环境，将使用随机密码{FONT}")
    
    return {
        "network_layer": network_layer,
        "method": method,
        "password": password
    }


def configure_protocol(protocol: str) -> Dict[str, Any]:
    """根据协议类型配置参数"""
    configs = {
        "socks5": configure_socks5_protocol,
        "vmess": configure_vmess_protocol,
        "vmess-socks5": configure_vmess_socks5_protocol,
        "shadowsocks": configure_shadowsocks_protocol
    }
    
    if protocol not in configs:
        exit_with_error("", protocol)
    
    return configs[protocol]()
