import os

import psutil

from utils import configFactory


def is_root():
    if not os.geteuid():
        return True
    return False


def get_net_card():
    net_card_info = []
    info = psutil.net_if_addrs()
    for k, v in info.items():
        for item in v:
            if item[0] == 2 and not item[1] == '127.0.0.1':
                net_card_info.append((item[1]))
    return net_card_info


class Xray(configFactory.Config):
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        self.install_script_path = "common/install-release.sh"
        self.log_path = "/var/log/xray/"
        self.myconfig = {"log": {}, "routing": {"rules": []}, "inbounds": [], "outbounds": []}
        self.log_level = "warning"

    def start(self):
        os.system("systemctl start xray")

    def stop(self):
        os.system("systemctl stop xray")

    def restart(self):
        os.system("systemctl restart xray")

    def status(self):
        os.system("systemctl status xray")

    def install(self):
        while not os.path.exists(self.install_script_path):
            print("电脑上没有找到xray安装脚本，正在执行重新最新脚本获取")
            os.system(
                f"wget -N --no-check-certificate https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh -O {self.install_script_path}")
        self.old_config_check()
        os.system(f"/bin/bash {self.install_script_path} install")

    def uninstall(self):
        if not os.path.isfile(self.install_script_path):
            print("电脑上没有找到xray安装脚本，正在执行重新最新脚本获取")
            os.system(
                f"wget -N --no-check-certificate https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh -O {self.install_script_path}")
        self.old_config_check()
        os.system(f"/bin/bash {self.install_script_path} remove --purge")
