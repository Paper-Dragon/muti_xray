import os.path
import time


class Config:
    def __init__(self, name):
        self.name = name

    def inbounds_config(self):
        pass

    def outbounds_config(self):
        pass

    def router_config(self):
        pass

    def old_config_check(self):
        if os.path.exists("/usr/local/etc/xray/config.json"):
            print("检测到老的配置，正在执行删除过程")
            time.sleep(2)
            os.system("rm -rf /usr/local/etc/xray/config.json")
            return True
        else:
            return False
