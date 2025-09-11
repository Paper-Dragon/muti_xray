from dis import hasconst
import json
import os
import time

from .color import *
import models
from models.transport_config import XHTTPSettingsConfig, WebSocketSettingsConfig
from models.log_config import LogConfig
from models.xray_config import RoutingConfig, RoutingRuleConfig

class Config:
    def __init__(self):
        self.config_path_file = "/usr/local/etc/xray/config.json"
        self.service_config_file="/etc/systemd/system/xray.service"
        # self.fp = open(self.config_path_file, "w", encoding='utf-8')
        self.myconfig = {"log": {}, "routing": {"rules": []}, "inbounds": [], "outbounds": []}
        self.log_level = "warning"
        self.log_path = "/var/log/xray/"
        self.name = "Paper-Dragon"

    def init_config(self):
        """
        初始化配置，插入黑洞路由
        :return:
        """
        log_config = LogConfig(
            loglevel=self.log_level,
            access=f"{self.log_path}access.log",
            error=f"{self.log_path}error.log"
        )
        self.myconfig["log"] = vars(log_config)

        # 使用 RoutingConfig 类生成路由配置
        routing_config = RoutingConfig(
            domain_strategy="AsIs",
            domain_matcher="mph",
            rules=[]
        )
        
        self.myconfig["routing"] = {
            "domainStrategy": routing_config.domain_strategy,
            "domainMatcher": routing_config.domain_matcher,
            "rules": [],
            "balancers": routing_config.balancers
        }

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
    def gen_tag(ipaddr: str = "127.0.0.1") -> list:
        """
        生成标签

        :param ipaddr: server ip address
        :type ipaddr: str
        :return list[inbound_tag, outbound_tag, suffix]
        """
        # 如果ps字段有用，保留；否则考虑是否有必要返回ps
        inbound_tag = f"in-{ipaddr.replace('.', '-')}"
        outbound_tag = f"out-{ipaddr.replace('.', '-')}"
        suffix = ipaddr.replace(".", "-")
        return [inbound_tag, outbound_tag, suffix]

    def insert_black_domain(self, black_domain):
        """
        将域名添加到黑洞规则中，如果黑洞规则不存在则创建
        :param black_domain: 要封禁的域名字符串
        """
        if not self.myconfig.get("routing") or "rules" not in self.myconfig["routing"]:
            print(f" {Error} {RED}路由配置不存在，请先初始化配置{FONT}")
            return
        
        # 查找现有的黑洞规则
        black_rule_index = -1
        for i, rule in enumerate(self.myconfig["routing"]["rules"]):
            if rule.get("outboundTag") == "out-block":
                black_rule_index = i
                break
        
        # 如果没有黑洞规则，创建一个
        if black_rule_index == -1:
            print(f" {Info} {BLUE}正在创建黑洞规则...{FONT}")
            
            # 确保黑洞出站配置存在
            self.insert_block_config()
            
            # 使用 RoutingRuleConfig 创建黑洞规则
            block_rule = RoutingRuleConfig(
                type="field",
                domains=[black_domain],
                outbound_tag="out-block"
            )
            
            # 转换为字典格式，只包含必要字段
            rule_dict = {
                "type": block_rule.type,
                "domain": block_rule.domains,
                "outboundTag": block_rule.outbound_tag
            }
            
            # 将黑洞规则插入到第一个位置
            self.myconfig["routing"]["rules"].insert(0, rule_dict)
            print(f" {OK} {GREEN}已创建黑洞规则并添加域名 '{black_domain}'{FONT}")
        else:
            # 如果黑洞规则已存在，直接添加域名
            black_rule = self.myconfig["routing"]["rules"][black_rule_index]
            if "domain" not in black_rule:
                black_rule["domain"] = []
            black_rule["domain"].append(black_domain)
            print(f" {OK} {GREEN}已将域名 '{black_domain}' 添加到黑洞规则{FONT}")

    def insert_routing_config(self, inbound_tag, outbound_tag):
        rule_dict = {
            "type": "field",
            "inboundTag": [inbound_tag],
            "outboundTag": outbound_tag
        }
        self.myconfig["routing"]["rules"].append(rule_dict)

    def insert_outbounds_config(self, ipaddr, outbound_tag):
        self.myconfig["outbounds"].append(
            {
                "sendThrough": ipaddr,
                "protocol": "freedom",
                "tag": outbound_tag
            })
    def insert_inbounds_vmess_config(self, ipaddr, port, inbounds_tag, uuids, alert_id, path, name,
                                     transport_layer = "raw", host = "iqiyi.com"):
        config = {
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
                "network": transport_layer
            },
            "tag": inbounds_tag
        }

        if transport_layer == "ws":
            ws_settings = WebSocketSettingsConfig(path=path)
            config["streamSettings"]["wsSettings"] = vars(ws_settings)
        elif transport_layer == "xhttp":
            xhttp_settings = XHTTPSettingsConfig(path=path, host=host)
            config["streamSettings"]["xhttpSettings"] = vars(xhttp_settings)
        self.myconfig["inbounds"].append(config)

    def insert_inbounds_sk5_config(self, ipaddr, port, inbounds_tag, user, passwd, name,
                                   network_layer_support_udp:bool = False ):
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
                    "udp": network_layer_support_udp,
                    "ip": "127.0.0.1"
                },
                "streamSettings": {
                    "network": "raw",
                    "security": "none",
                    "rawSettings": {
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
        print("内存中的配置是...")
        print(json.dumps(self.myconfig, indent=4, separators=(',', ': ')))

    def print_file_config(self):
        if os.path.exists(self.config_path_file):
            print("文件中的配置是...")
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
            print(f"{OK} {GREEN}找到配置文件 {self.config_path_file}{FONT}")
            try:
                with open(self.config_path_file, "r", encoding='utf-8') as file:
                    config_data = json.load(file)
                    nodes = config_data.get("inbounds", [])
                    for node in nodes:
                        print(f"  {node.get('ps', '无名称')}")
            except Exception as e:
                print(f"{Error} {RED}解析配置文件出错: {e}{FONT}")
        else:
            print(f"{Error} {RED}没有找到配置文件{FONT}")
    
    def old_config_remove(self):
        if os.path.exists(self.config_path_file):
            print("检测到老的配置，正在执行删除过程")
            time.sleep(2)
            os.system(f"rm -rf {self.config_path_file}")
            return True
        else:
            return False
