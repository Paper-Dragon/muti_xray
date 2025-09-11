from ipaddress import IPv4Address, IPv6Address
import os
import subprocess
from subprocess import CompletedProcess
import psutil
import ipaddress
import socket
from utils import configFactory
from utils.color import *

def is_root():
    if not os.geteuid():
        return True
    return False

class Xray(configFactory.Config):
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        self.service_config_file="/etc/systemd/system/xray.service"
        self.install_script_path = "common/install-release.sh"
        self.log_path = "/var/log/xray/"
        self.myconfig = {"log": {}, "routing": {"rules": []}, "inbounds": [], "outbounds": []}
        self.log_level = "warning"

    @staticmethod
    def _execute_command(cmd):
        """封装执行命令的方法，增加错误处理"""
        try:
            subprocess.run(cmd, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(f" {Error} {RED}命令执行失败: {cmd}, 错误信息: {e}{FONT}")
            raise

    def start(self):
        self._execute_command("systemctl start xray")

    def stop(self):
        self._execute_command("systemctl stop xray")

    def restart(self):
        self._execute_command("systemctl restart xray")

    def status(self):
        self._execute_command("systemctl status xray")

    def _download_install_script(self):
        """下载安装脚本，并检查是否成功"""
        if not os.path.exists(self.install_script_path):
            print(f" {Info} {BLUE}安装脚本不存在，开始下载...{FONT}")
            download_cmd = f"wget -N --no-check-certificate https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh -O {self.install_script_path}"
            self._execute_command(download_cmd)
            if not os.path.exists(self.install_script_path):
                print(f" {Error} {RED}安装脚本下载失败，请检查网络或URL。{FONT}")
                raise FileNotFoundError("安装脚本下载失败")

    def install(self):
        self._download_install_script()
        self.old_config_remove()
        install_cmd = f"/bin/bash {self.install_script_path} install"
        self._execute_command(install_cmd)

    def uninstall(self):
        self._download_install_script()
        self.old_config_remove()
        uninstall_cmd = f"/bin/bash {self.install_script_path} remove --purge"
        self._execute_command(uninstall_cmd)

    def upgrade(self):
        self._download_install_script()
        install_cmd = f"/bin/bash {self.install_script_path} install"
        self._execute_command(install_cmd)

    def install_geo(self):
        self._download_install_script()
        install_cmd = f"/bin/bash {self.install_script_path} install-geodata"
        self._execute_command(install_cmd)

    @staticmethod
    def is_private_ip(ip_str):
        """
        判断IP地址是否为内网地址
        
        :param ip_str: IP地址字符串
        :return: True为内网地址，False为公网地址
        """
        try:
            ip: IPv4Address | IPv6Address = ipaddress.ip_address(ip_str)
            return ip.is_private
        except ValueError:
            return True

    @staticmethod
    def get_public_ip_via_interface(interface_ip=None):
        """
        通过指定网卡获取公网IP地址
        
        :param interface_ip: 网卡的内网IP地址，用于绑定出站接口
        :return: 公网IP地址字符串，获取失败返回None
        """
        try:
            if interface_ip:
                # 使用curl命令绑定源IP获取公网IP
                cmd = f"curl -s --interface {interface_ip} --connect-timeout 10 http://ifconfig.icu/ip"
                try:
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=15,
                        check=True
                    )
                    public_ip = result.stdout.strip()
                    if public_ip and not Xray.is_private_ip(public_ip):
                        print(f" {OK} {GREEN}接口绑定: {BLUE}{interface_ip}{FONT} {GREEN}获取公网IP: {BLUE}{public_ip}{FONT}")
                        return public_ip
                    else:
                        print(f" {Warning} {YELLOW}接口 {BLUE}{interface_ip}{FONT} {YELLOW}获取到无效IP: {RED}{public_ip}{FONT}")
                        return None
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    print(f" {Error} {RED}通过curl获取公网IP失败: {e}{FONT}")
                    return None
            else:
                # 不指定接口时使用默认路由
                cmd = "curl -s --connect-timeout 10 http://ifconfig.icu/ip"
                try:
                    result: CompletedProcess[str] = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=15,
                        check=True
                    )
                    public_ip = result.stdout.strip()
                    if public_ip and not Xray.is_private_ip(public_ip):
                        print(f" {OK} {GREEN}获取到公网IP: {BLUE}{public_ip}{FONT}")
                        return public_ip
                    else:
                        print(f" {Warning} {YELLOW}获取到无效IP: {RED}{public_ip}{FONT}")
                        return None
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    print(f" {Error} {RED}通过curl获取公网IP失败: {e}{FONT}")
                    return None
                
        except Exception as e:
            print(f" {Error} {RED}获取公网IP时发生错误: {e}{FONT}")
            return None

    @staticmethod
    def get_net_card():
        """
        获取网卡信息，针对站群服务器多网卡多IP场景优化
        为每个内网IP尝试获取对应的公网IP
        
        :return: IP地址列表，包含公网IP或内网IP
        """
        net_card_info = []
        interface_mapping = {}  # 存储网卡名到IP的映射
        
        # 获取所有网卡信息
        info = psutil.net_if_addrs()
        print(f" {Info} {BLUE}开始扫描网卡信息...{FONT}")
        
        for interface_name, addresses in info.items():
            for addr in addresses:
                if addr[0] == 2 and addr[1] != '127.0.0.1':  # IPv4且非环回地址
                    ip_addr = addr[1]
                    interface_mapping[interface_name] = ip_addr
                    
                    if Xray.is_private_ip(ip_addr):
                        print(f" {Info} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}内网IP {ip_addr}{FONT}")
                        
                        # 对于内网IP，尝试获取对应的公网IP
                        public_ip = Xray.get_public_ip_via_interface(ip_addr)
                        if public_ip and not Xray.is_private_ip(public_ip):
                            net_card_info.append(public_ip)
                            print(f" {OK} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}{ip_addr}{FONT} {GREEN}-> 公网IP {BLUE}{public_ip}{FONT}")
                        else:
                            # 如果无法获取公网IP，使用内网IP
                            net_card_info.append(ip_addr)
                            print(f" {Warning} {YELLOW}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}无法获取公网IP，使用内网IP {ip_addr}{FONT}")
                    else:
                        # 直接是公网IP
                        net_card_info.append(ip_addr)
                        print(f" {Info} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {GREEN}直接公网IP {BLUE}{ip_addr}{FONT}")
        
        # 去重但保持顺序
        unique_ips = list(dict.fromkeys(net_card_info))
        
        if unique_ips:
            print(f" {OK} {GREEN}最终获取到的IP地址列表: {BLUE}{unique_ips}{FONT}")
        else:
            print(f" {Error} {RED}未获取到任何可用的IP地址{FONT}")
            
        return unique_ips
