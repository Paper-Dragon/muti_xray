import os

from utils import configFactory


class Xray(configFactory.Config):
    def __init__(self):
        self.install_script_path = "common/install-release.sh"

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
        os.system(f"/bin/bash {self.install_script_path} uninstall")
