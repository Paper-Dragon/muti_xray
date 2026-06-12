# encoding: utf-8
"""
Xray 系统控制模块。

提供纯函数接口：权限检查、网卡扫描、服务管理、安装/卸载。
不依赖全局状态，不继承任何配置类。
"""
import ipaddress
import os
import platform
import socket
import subprocess
from typing import Dict, List, Optional

import psutil

# ── ANSI 颜色（内联，不依赖旧 utils）────────────────────────────────────────

_G = '\033[92m'   # green
_B = '\033[94m'   # blue
_R = '\033[91m'   # red
_Y = '\033[93m'   # yellow
_BG = '\033[40m'  # black bg
_F = '\033[0m'    # reset
_OK  = f"{_G}{_BG}[成功]{_F}"
_INF = f"{_B}{_BG}[信息]{_F}"
_ERR = f"{_R}{_BG}[错误]{_F}"
_WRN = f"{_Y}{_BG}[警告]{_F}"

# ── 常量 ──────────────────────────────────────────────────────────────────────

CONFIG_PATH    = "/usr/local/etc/xray/config.json"
SERVICE_FILE   = "/etc/systemd/system/xray.service"
INSTALL_SCRIPT = "common/install-release.sh"


# ── 权限检查 ──────────────────────────────────────────────────────────────────

def is_root() -> bool:
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (ImportError, AttributeError):
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


# ── 命令执行 ──────────────────────────────────────────────────────────────────

def _run(cmd: str) -> None:
    """执行 shell 命令，失败时打印错误并抛异常。"""
    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f" {_ERR} {_R}命令执行失败: {cmd}\n{e}{_F}")
        raise


# ── 服务管理 ──────────────────────────────────────────────────────────────────

def start()   -> None: _run("systemctl start xray")
def stop()    -> None: _run("systemctl stop xray")
def restart() -> None: _run("systemctl restart xray")
def status()  -> None: _run("systemctl status xray")


# ── 安装 / 卸载 ───────────────────────────────────────────────────────────────

def _ensure_install_script() -> None:
    if not os.path.exists(INSTALL_SCRIPT):
        print(f" {_INF} {_B}安装脚本不存在，开始下载...{_F}")
        _run(
            f"wget -N --no-check-certificate "
            f"https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh "
            f"-O {INSTALL_SCRIPT}"
        )
        if not os.path.exists(INSTALL_SCRIPT):
            raise FileNotFoundError("安装脚本下载失败，请检查网络")


def _remove_config() -> None:
    if os.path.exists(CONFIG_PATH):
        print("检测到旧配置，正在删除...")
        os.remove(CONFIG_PATH)


def install() -> None:
    _ensure_install_script()
    _remove_config()
    _run(f"/bin/bash {INSTALL_SCRIPT} install")


def uninstall() -> None:
    _ensure_install_script()
    _remove_config()
    _run(f"/bin/bash {INSTALL_SCRIPT} remove --purge")


def upgrade() -> None:
    _ensure_install_script()
    _run(f"/bin/bash {INSTALL_SCRIPT} install")


def install_geo() -> None:
    _ensure_install_script()
    _run(f"/bin/bash {INSTALL_SCRIPT} install-geodata")


# ── 配置文件操作 ──────────────────────────────────────────────────────────────

def generate_self_signed_cert(
    cert_dir: str = "/usr/local/etc/xray/tls",
    domain: str = "xray.local",
) -> tuple:
    """
    用 openssl 生成自签名 TLS 证书，返回 (cert_path, key_path)。

    证书放在 cert_dir 下，文件名为 {domain}.crt / {domain}.key。
    已存在则直接返回路径，不重复生成。
    """
    os.makedirs(cert_dir, mode=0o700, exist_ok=True)
    cert_path = os.path.join(cert_dir, f"{domain}.crt")
    key_path  = os.path.join(cert_dir, f"{domain}.key")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f" {_INF} {_B}已存在自签证书: {cert_path}{_F}")
        return cert_path, key_path

    print(f" {_INF} {_B}正在生成自签名 TLS 证书（域名: {domain}）...{_F}")
    cmd = (
        f"openssl req -x509 -newkey rsa:2048 -nodes "
        f"-keyout {key_path} -out {cert_path} -days 3650 "
        f"-subj '/CN={domain}' 2>/dev/null"
    )
    try:
        subprocess.run(cmd, shell=True, check=True)
        os.chmod(key_path, 0o600)
        print(f" {_OK} {_G}自签证书已生成: {cert_path}{_F}")
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "openssl 生成证书失败，请确认已安装 openssl：apt install openssl"
        )
    return cert_path, key_path


def print_config() -> None:
    if os.path.exists(CONFIG_PATH):
        print("当前配置文件内容：")
        with open(CONFIG_PATH, encoding="utf-8") as f:
            print(f.read())
    else:
        print("未找到配置文件")


def list_nodes() -> None:
    import json
    if not os.path.exists(CONFIG_PATH):
        print(f" {_ERR} {_R}未找到配置文件{_F}")
        return
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        nodes = data.get("inbounds", [])
        if not nodes:
            print("配置文件中没有节点")
            return
        print(f" {_OK} {_G}共 {len(nodes)} 个节点:{_F}")
        for node in nodes:
            print(f"  {node.get('ps', '无名称')}")
    except Exception as e:
        print(f" {_ERR} {_R}解析配置文件出错: {e}{_F}")


# ── 网络信息 ──────────────────────────────────────────────────────────────────

def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def _get_public_ip(interface_ip: Optional[str] = None) -> Optional[str]:
    """通过 curl 获取指定网卡出口的公网 IP，失败返回 None。"""
    if interface_ip:
        cmd = f"curl -s --interface {interface_ip} --connect-timeout 10 http://ifconfig.icu/ip"
    else:
        cmd = "curl -s --connect-timeout 10 http://ifconfig.icu/ip"
    try:
        result = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=15, check=True,
        )
        ip = result.stdout.strip()
        if ip and not _is_private(ip):
            return ip
        label = f"接口 {interface_ip} " if interface_ip else ""
        print(f" {_WRN} {_Y}{label}获取到无效 IP: {ip}{_F}")
        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f" {_ERR} {_R}curl 获取公网 IP 失败: {e}{_F}")
        return None
    except Exception as e:
        print(f" {_ERR} {_R}获取公网 IP 时发生错误: {e}{_F}")
        return None


def get_net_cards() -> List[Dict]:
    """
    扫描所有非回环 IPv4 网卡，返回列表。

    每项格式：
    {
        'interface': str,    # 网卡名
        'listen_ip': str,    # 入站监听 IP（内网 IP）
        'client_ip': str,    # 客户端连接 IP（公网 IP 或内网 IP）
    }
    """
    print(f" {_INF} {_B}开始扫描网卡信息...{_F}")
    result = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family != socket.AF_INET or addr.address == "127.0.0.1":
                continue
            private_ip = addr.address
            if _is_private(private_ip):
                print(f" {_INF} {_G}网卡 {_B}{iface}{_F}: {_Y}内网IP {private_ip}{_F}")
                public_ip = _get_public_ip(private_ip)
                if public_ip:
                    client_ip = public_ip
                    print(f" {_OK} {_G}  └─ 公网IP: {_B}{public_ip}{_F}")
                else:
                    client_ip = private_ip
                    print(f" {_WRN} {_Y}  └─ 无法获取公网IP，使用内网IP{_F}")
            else:
                client_ip = private_ip
                print(f" {_INF} {_G}网卡 {_B}{iface}{_F}: {_G}直接公网IP {_B}{private_ip}{_F}")

            result.append({
                "interface": iface,
                "listen_ip": private_ip,
                "client_ip": client_ip,
            })

    if not result:
        print(f" {_ERR} {_R}未获取到任何可用 IP 地址{_F}")
    return result
