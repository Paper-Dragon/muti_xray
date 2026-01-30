from ipaddress import IPv4Address, IPv6Address
import os
import platform
import subprocess
import psutil
import ipaddress
import socket
from utils import configFactory
from utils.color import *

def is_root():
    """检查是否有 root/管理员权限（跨平台）"""
    system = platform.system()
    
    if system == "Windows":
        # Windows 上检查是否为管理员
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (ImportError, AttributeError):
            # 降级方案：检查是否有管理员权限的其他方式
            return os.name == 'nt'  # Windows 上默认为 False，需要手动检查
    else:
        # Linux/Mac 使用 geteuid
        try:
            return os.geteuid() == 0
        except AttributeError:
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
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
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
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
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
        
        :return: 包含内网IP和公网IP映射关系的字典列表
        """
        net_card_info = []
        interface_mapping = {}  # 存储网卡名到IP的映射
        
        # 获取所有网卡信息
        info = psutil.net_if_addrs()
        print(f" {Info} {BLUE}开始扫描网卡信息...{FONT}")
        
        for interface_name, addresses in info.items():
            for addr in addresses:
                if addr[0] == 2 and addr[1] != '127.0.0.1':  # IPv4且非环回地址
                    private_ip = addr[1]
                    interface_mapping[interface_name] = private_ip
                    
                    if Xray.is_private_ip(private_ip):
                        print(f" {Info} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}内网IP {private_ip}{FONT}")
                        
                        # 对于内网IP，尝试获取对应的公网IP
                        public_ip = Xray.get_public_ip_via_interface(private_ip)
                        if public_ip and not Xray.is_private_ip(public_ip):
                            # 返回包含内网IP和公网IP的映射
                            net_card_info.append({
                                'interface': interface_name,
                                'private_ip': private_ip,
                                'public_ip': public_ip,
                                'listen_ip': private_ip,  # 配置文件中listen的IP
                                'client_ip': public_ip    # 客户端连接使用的IP
                            })
                            print(f" {OK} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}{private_ip}{FONT} {GREEN}-> 公网IP {BLUE}{public_ip}{FONT}")
                        else:
                            # 如果无法获取公网IP，使用内网IP
                            net_card_info.append({
                                'interface': interface_name,
                                'private_ip': private_ip,
                                'public_ip': None,
                                'listen_ip': private_ip,  # 配置文件中listen的IP
                                'client_ip': private_ip   # 客户端连接也使用内网IP
                            })
                            print(f" {Warning} {YELLOW}网卡 {BLUE}{interface_name}{FONT}: {YELLOW}无法获取公网IP，使用内网IP {private_ip}{FONT}")
                    else:
                        # 直接是公网IP的情况
                        net_card_info.append({
                            'interface': interface_name,
                            'private_ip': private_ip,
                            'public_ip': private_ip,
                            'listen_ip': private_ip,   # 配置文件中listen的IP
                            'client_ip': private_ip    # 客户端连接使用的IP
                        })
                        print(f" {Info} {GREEN}网卡 {BLUE}{interface_name}{FONT}: {GREEN}直接公网IP {BLUE}{private_ip}{FONT}")
        
        if net_card_info:
            print(f" {OK} {GREEN}最终获取到的网卡映射关系:{FONT}")
            for i, card in enumerate(net_card_info, 1):
                if card['public_ip']:
                    print(f" {Info} {BLUE}[{i}] {GREEN}网卡: {card['interface']}{FONT} | {YELLOW}监听: {card['listen_ip']}{FONT} | {BLUE}公网: {card['client_ip']}{FONT}")
                else:
                    print(f" {Info} {BLUE}[{i}] {GREEN}网卡: {card['interface']}{FONT} | {YELLOW}IP: {card['listen_ip']}{FONT}")
        else:
            print(f" {Error} {RED}未获取到任何可用的IP地址{FONT}")
            
        return net_card_info
