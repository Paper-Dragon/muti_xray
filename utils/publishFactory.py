import os
import json
import base64
from typing import List, Optional

class Publish:
    def __init__(self, raw_config_list: Optional[List[str]] = None):
        """
        初始化 Publish 类
        :param config: 配置列表，默认为空列表
        :type config: Optional[List[str]]
        """
        self.raw_config_list = raw_config_list if raw_config_list else []
        self.quick_file = "quick_link.txt"
        self.p_web = "dpaste.com"
        self.quick_config_link_list = []

    @staticmethod
    def encode_b64(strings: str) -> str:
        """
        编码一个字符串为base64格式
        :param strings: 需要编码的字符串
        :type strings: str
        :return: 编码后的base64字符串
        :rtype: str
        """
        return base64.b64encode(strings.encode()).decode('utf-8')

    def publish_2_web(self):
        """
        将当前的配置列表发布到一个网络服务上
        :return: None
        """
        try:
            print("发布的链接是： ")
            os.system(f"./common/pastebinit-1.6.2/pastebinit -i {self.quick_file} -b {self.p_web}")
        except Exception as e:
            print(f"发布到网络时发生错误: {e}")

    def save_2_file(self, config_list: List[str] = None):
        """
        将当前的配置列表写入到一个文本文件中
        """
        print_info = f"我们已经帮你把 {'节点信息' if config_list else '快速链接'} 记在了 {self.quick_file} 文件里"
        config_list = config_list if config_list else self.quick_config_link_list

        try:
            with open(self.quick_file, 'a') as f:
                for config_item in config_list:
                    f.write(config_item + "\n")
            print(print_info)
        except IOError as e:
            print(f"写入文件 {self.quick_file} 时发生错误: {e}")


    def create_vmess_quick_link(self, ps: str = "NodeName", address: str = "127.0.0.1",
                                uuid: str = "2ddf920d-2eca-4c94-b496-83e9a634dc1d",
                                port: int = 10086, alert_id: int = 0,
                                mode: str = "raw", 
                                host: Optional[str] = None,
                                path: Optional[str] = None) -> None:
        """
        创建一个vmess配置并加入到配置列表中，支持raw、websocket和xhttp模式
        """
        vmess_config = {
            "v": "2",
            "ps": ps,
            "add": address,
            "port": port,
            "id": uuid,
            "aid": alert_id,
            "scy": "auto",
            "net": mode,
            "type": "none",
            "host": "",
            "tls": "",
            "sni": "",
            "alpn": ""
        }

        if mode == "ws":
            vmess_config["path"] = path if path else ""
        elif mode == "http":
            vmess_config["path"] = path if path else "/yourpath"
            vmess_config["host"] = "example.com"
        try:
            config_json = json.dumps(vmess_config, indent=4, separators=(',', ': '))
            vmess_link = f"vmess://{self.encode_b64(config_json)}"
            self.quick_config_link_list.append(vmess_link)
        except (TypeError, ValueError) as e:
            print(f"编码 vmess 配置时发生错误: {e}")


    def create_shadowsocks_quick_link(self, method: str, password: str, ip: str, port: int,
                                      network_layer_type: str, name: str):
        try:
            encode_code = self.encode_b64(f"{method}:{password}")
            quick_link = f"ss://{encode_code}@{ip}:{port}?type={network_layer_type}#{name}"
            self.quick_config_link_list.append(quick_link)
        except Exception as e:
            print(f"创建 Shadowsocks 链接时发生错误: {e}")
