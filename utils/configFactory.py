import json
import os.path
import time
from .color import *


class Config:
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        # self.fp = open(self.config_path_file, "w", encoding='utf-8')
        self.myconfig = {"log": {}, "routing": {"rules": []}, "inbounds": [], "outbounds": []}
        self.log_level = "warning"
        self.log_path = "/var/log/xray/"
        self.name = "PaperDragon"

    def init_config(self):
        """
        初始化配置，插入黑洞路由
        :return:
        """
        self.myconfig["log"]["access"] = f"{self.log_path}access.log"
        self.myconfig["log"]["error"] = f"{self.log_path}error.log"
        self.myconfig["log"]["loglevel"] = self.log_level

        # self.myconfig["routing"].get("rules").append(
        #     {
        #         "type": "field",
        #         "ip": [
        #             "geoip:private"
        #         ],
        #         "outboundTag": "out-block"
        #     })
        self.myconfig["routing"].get("rules").append({
            "type": "field",
            "domain": [
            ],
            "outboundTag": "out-block"
        })

    def insert_block_config(self):
        self.myconfig["outbounds"].append(
            {
                "protocol": "blackhole",
                "tag": "out-block"
            })

    def gen_tag(self, ipaddr):
        tag = []
        inboundTag = "in-" + ipaddr.replace(".", "-")
        outboundTag = "out-" + ipaddr.replace(".", "-")
        ps = ipaddr.replace(".", "-")
        tag.append(inboundTag)
        tag.append(outboundTag)
        tag.append(ps)
        return tag

    def insert_black_domain(self, black_domain):
        self.myconfig["routing"]["rules"][0].get("domain").append(
            f"{black_domain}"
        )

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
        if mode == "vmess_tcp":
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
        elif mode == "vmess_ws":
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

    def insert_inbounds_sk5_tcp_config(self, ipaddr, port, inbounds_tag, user, passwd, name):
        self.myconfig["inbounds"].append(
            {
                "listen": ipaddr,
                "port": port,
                "ps": name,
                "protocol": "socks",
                "settings": {
                    "auth": "password",
                    "accounts": [
                        {
                            "user": user,
                            "pass": passwd
                        }
                    ],
                    "udp": False,
                    "ip": "127.0.0.1"
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "none",
                    "tcpSettings": {
                        "header": {
                            "type": "none"
                        }
                    }
                },
                "tag": inbounds_tag,
                "sniffing": {}
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
        print("正在清除所有配置并将内存中的配置写进文件中")
        print("...........")
        json_data = json.dumps(self.myconfig, indent=4, separators=(',', ': '))
        f = open(self.config_path_file, 'w')
        f.write(json_data)
        f.close()

    def list_node(self):
        if os.path.exists(self.config_path_file):
            print(f"{OK} {Green} 找到文件配置文件 {self.config_path_file} {Font}")
            myconfig = open(self.config_path_file, "r", encoding='utf-8')
            print("现在有如下节点")
            try:
                for v in myconfig["routing"].get("inbounds"):
                    print(v["ps"])
            except Exception as e:
                print(f"{Error} {Red} 在这个配置文件中没找到节点{Font}: {e}")
            myconfig.close()

    def old_config_check(self):
        if os.path.exists(self.config_path_file):
            print("检测到老的配置，正在执行删除过程")
            time.sleep(2)
            os.system(f"rm -rf {self.config_path_file}")
            return True
        else:
            return False
