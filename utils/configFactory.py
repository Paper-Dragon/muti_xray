import json
import os
import time
from typing import AnyStr

from .color import *
import models

class Config:
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        self.service_config_file="/etc/systemd/system/xray.service"
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

    def insert_inbounds_config(self, inbound_config: models.InboundConfig):
        inbound_dict = vars(inbound_config)
        # 直接将字典追加到 inbounds 列表中
        self.myconfig['inbounds'].append(inbound_dict)

    @staticmethod
    def gen_tag(ipaddr: AnyStr = "127.0.0.1") -> list:
        """
        生成标签

        :param ipaddr: server ip address
        :type ipaddr: AnyStr
        :return list[inbound_tag, outbound_tag, suffix]
        """
        # 如果ps字段有用，保留；否则考虑是否有必要返回ps
        inbound_tag = f"in-{ipaddr.replace('.', '-')}"
        outbound_tag = f"out-{ipaddr.replace('.', '-')}"
        suffix = ipaddr.replace(".", "-")
        return [inbound_tag, outbound_tag, suffix]

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

    def insert_inbounds_vmess_ws_config(self, ipaddr, port, inbounds_tag, uuids, alert_id, path, name):
        self.myconfig["inbounds"].append(
            {
                    "port": port,
                    "listen": ipaddr,
                    "tag": inbounds_tag,
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

    def insert_inbounds_vmess_tcp_config(self, ipaddr, port, inbounds_tag, uuids, alert_id, name):
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
                    "tag": inbounds_tag
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

    def insert_inbounds_sk5_tcp_udp_config(self, ipaddr, port, inbounds_tag, user, passwd, name):
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
                    "udp": True,
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
        """将内存中的配置写入文件"""
        print("正在将内存中的配置写入文件中...")
        with open(self.config_path_file, 'w', encoding='utf-8') as f:
            json.dump(self.myconfig, f, indent=4, separators=(',', ': '))
        print("配置已写入文件。")


    def list_node(self):
        """列出配置文件中的节点信息"""
        if os.path.exists(self.config_path_file):
            print(f"{OK} {colored(f'找到配置文件 {self.config_path_file}', 'green')} ")
            try:
                with open(self.config_path_file, "r", encoding='utf-8') as file:
                    config_data = json.load(file)
                    nodes = config_data.get("inbounds", [])
                    for node in nodes:
                        print(node.get("ps", "无名称"))
            except Exception as e:
                print(f"{Error} {colored(f'解析配置文件出错: {e}', 'red')}")
        else:
            print(f"{Error} {colored('没有找到配置文件', 'red')} ")
    
    def old_config_check(self):
        if os.path.exists(self.config_path_file):
            print("检测到老的配置，正在执行删除过程")
            time.sleep(2)
            os.system(f"rm -rf {self.config_path_file}")
            return True
        else:
            return False
