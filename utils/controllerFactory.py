import os
import subprocess
import psutil
from utils import configFactory
import logging

def is_root():
    if not os.geteuid():
        return True
    return False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.error(f"命令执行失败: {cmd}, 错误信息: {e}")
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
            logger.info("安装脚本不存在，开始下载...")
            download_cmd = f"wget -N --no-check-certificate https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh -O {self.install_script_path}"
            self._execute_command(download_cmd)
            if not os.path.exists(self.install_script_path):
                logger.error("安装脚本下载失败，请检查网络或URL。")
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
    def get_net_card():
        net_card_info = []
        info = psutil.net_if_addrs()
        for k, v in info.items():
            for item in v:
                if item[0] == 2 and not item[1] == '127.0.0.1':
                    net_card_info.append((item[1]))
        return net_card_info
