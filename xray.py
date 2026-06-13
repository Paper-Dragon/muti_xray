# encoding: utf-8
import ipaddress
import os
import platform
import socket
import subprocess
from typing import Dict, List, Optional

import psutil

from ui import GREEN, BLUE, RED, YELLOW, RESET, OK, INF, ERR, WRN

CONFIG_PATH    = "/usr/local/etc/xray/config.json"
SERVICE_FILE   = "/etc/systemd/system/xray.service"
INSTALL_SCRIPT = "common/install-release.sh"


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


def _run(cmd: str) -> None:
    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f" {ERR} {RED}命令执行失败: {cmd}\n{e}{RESET}")
        raise


def start()   -> None: _run("systemctl start xray")
def stop()    -> None: _run("systemctl stop xray")
def restart() -> None: _run("systemctl restart xray")
def status()  -> None: _run("systemctl status xray")


def _ensure_install_script() -> None:
    if not os.path.exists(INSTALL_SCRIPT):
        print(f" {INF} {BLUE}安装脚本不存在，开始下载...{RESET}")
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


def generate_self_signed_cert(
    cert_dir: str = "/usr/local/etc/xray/tls",
    domain: str = "xray.local",
) -> tuple:
    os.makedirs(cert_dir, mode=0o700, exist_ok=True)
    cert_path = os.path.join(cert_dir, f"{domain}.crt")
    key_path  = os.path.join(cert_dir, f"{domain}.key")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f" {INF} {BLUE}已存在自签证书: {cert_path}{RESET}")
        return cert_path, key_path

    print(f" {INF} {BLUE}正在生成自签名 TLS 证书（域名: {domain}）...{RESET}")
    cmd = (
        f"openssl req -x509 -newkey rsa:2048 -nodes "
        f"-keyout {key_path} -out {cert_path} -days 3650 "
        f"-subj '/CN={domain}' 2>/dev/null"
    )
    try:
        subprocess.run(cmd, shell=True, check=True)
        os.chmod(key_path, 0o600)
        print(f" {OK} {GREEN}自签证书已生成: {cert_path}{RESET}")
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
        print(f" {ERR} {RED}未找到配置文件{RESET}")
        return
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        nodes = data.get("inbounds", [])
        if not nodes:
            print("配置文件中没有节点")
            return
        print(f" {OK} {GREEN}共 {len(nodes)} 个节点:{RESET}")
        for node in nodes:
            print(f"  {node.get('ps', '无名称')}")
    except Exception as e:
        print(f" {ERR} {RED}解析配置文件出错: {e}{RESET}")


def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def _get_public_ip(interface_ip: Optional[str] = None) -> Optional[str]:
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
        print(f" {WRN} {YELLOW}{label}获取到无效 IP: {ip}{RESET}")
        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f" {ERR} {RED}curl 获取公网 IP 失败: {e}{RESET}")
        return None
    except Exception as e:
        print(f" {ERR} {RED}获取公网 IP 时发生错误: {e}{RESET}")
        return None


def get_net_cards() -> List[Dict]:
    print(f" {INF} {BLUE}开始扫描网卡信息...{RESET}")
    result = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family != socket.AF_INET or addr.address == "127.0.0.1":
                continue
            private_ip = addr.address
            if _is_private(private_ip):
                print(f" {INF} {GREEN}网卡 {BLUE}{iface}{RESET}: {YELLOW}内网IP {private_ip}{RESET}")
                public_ip = _get_public_ip(private_ip)
                if public_ip:
                    client_ip = public_ip
                    print(f" {OK} {GREEN}  └─ 公网IP: {BLUE}{public_ip}{RESET}")
                else:
                    client_ip = private_ip
                    print(f" {WRN} {YELLOW}  └─ 无法获取公网IP，使用内网IP{RESET}")
            else:
                client_ip = private_ip
                print(f" {INF} {GREEN}网卡 {BLUE}{iface}{RESET}: {GREEN}直接公网IP {BLUE}{private_ip}{RESET}")

            result.append({
                "interface": iface,
                "listen_ip": private_ip,
                "client_ip": client_ip,
            })

    if not result:
        print(f" {ERR} {RED}未获取到任何可用 IP 地址{RESET}")
    return result
