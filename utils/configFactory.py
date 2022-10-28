import os.path
import time
import json


class Config:
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        # self.fp = open(self.config_path_file, "w", encoding='utf-8')
        self.myconfig = {"log": {}, "routing": {"rules": []}, "inbounds": [], "outbounds": []}
        self.log_level = "warning"
        self.log_path = "/var/log/xray/"

    def init_config(self):
        """
        初始化配置，插入黑洞路由
        :return:
        """
        self.myconfig["log"]["access"] = f"{self.log_path}access.log"
        self.myconfig["log"]["error"] = f"{self.log_path}error.log"
        self.myconfig["log"]["loglevel"] = self.log_level

        self.myconfig["routing"].get("rules").append(
            {
                "type": "field",
                "ip": [
                    "geoip:private"
                ],
                "outboundTag": "out-block"
            })
        self.myconfig["routing"].get("rules").append({
            "type": "field",
            "domain": [
                "baidu.com",
                "www.baidu.com"
            ],
            "outboundTag": "out-block"
        })
        self.myconfig["outbounds"].append(
            {
                "protocol": "blackhole",
                "tag": "out-block"
            })

    def insert_routing_config(self, inbound_tag, outbound_tag):
        self.myconfig["routing"]["rules"].append(
            {
                "type": "field",
                "inboundTag": [
                    inbound_tag
                ],
                "outboundTag": outbound_tag
            })

    def insert_outbounds_config(self, ipaddr, outbound_tag):
        self.myconfig["outbounds"].append(
            {
                "sendThrough": ipaddr,
                "protocol": "freedom",
                "tag": outbound_tag
            })

    def insert_inbounds_config(self, ipaddr, inbound_tag, mode="tcp", path="/aaa/", uuids=" ", alert_id=2,
                               name="default", port=8443):
        if mode == "tcp":
            self.myconfig["inbounds"].append(
                {
                    "listen": ipaddr,
                    "port": port,
                    "ps": name,
                    "protocol": "vmess",
                    "settings": {
                        "clients": [
                            {
                                "id": uuids,
                                "alert_id": alert_id
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp"
                    },
                    "tag": inbound_tag
                }
            )
        elif mode == "ws":
            self.myconfig["inbounds"].append(
                {
                    "port": port,
                    "listen": ipaddr,
                    "tag": inbound_tag,
                    "ps": name,
                    "protocol": "vmess",
                    "settings": {
                        "clients": [
                            {
                                "id": uuids,
                                "alterId": alert_id
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "ws",
                        "wsSettings": {
                            "path": path
                        }
                    }
                }
            )

    def print_ram_config(self):
        print("内存中的配置是。。。")
        print(json.dumps(self.myconfig, indent=4, separators=(',', ': ')))

    def print_file_config(self):
        if os.path.exists(self.config_path_file):
            print("文件中的配置是。。。")
            os.system(f"cat {self.config_path_file}")
        else:
            print("没有配置文件")
            time.sleep(3)

    def write_2_file(self):
        print("正在清除所有配置并k将内存中的配置写进文件中")
        print("...........")
        json_data = json.dumps(self.myconfig, indent=4, separators=(',', ': '))
        f = open(self.config_path_file, 'w')
        f.write(json_data)
        f.close()

    def list_node(self):
        myconfig = open(self.config_path_file, "r", encoding='utf-8')
        print("现在有如下节点")
        # for v in myconfig["routing"].get("inbounds"):
        #     print(v["ps"])
        print("111")
        myconfig.close()

    def old_config_check(self):
        if os.path.exists(self.config_path_file):
            print("检测到老的配置，正在执行删除过程")
            time.sleep(2)
            os.system(f"rm -rf {self.config_path_file}")
            return True
        else:
            return False
