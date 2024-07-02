import base64
import os
import json
from .color import *


def encode_b64(strings):
    """编码一个字符串到base64."""
    return base64.b64encode(strings.encode()).decode('utf-8')


class Publish(object):
    def __init__(self, config=None):
        """
        发布一个配置列表到网络服务或者文件内
        :param config: list
        """
        self.config = config if config is not None else []
        self.quick_file = "quick_link.txt"
        self.p_web = "dpaste.com"

    def publish_2_web(self):
        """将当前的配置列表发布到一个网络服务上"""
        self.publish_2_txt()
        print(f"{Green}发布的链接是： ")
        os.system(f"./common/pastebinit-1.5/pastebinit -i {self.quick_file} -b {self.p_web}")
        print(Font)

    def publish_2_txt(self):
        """将当前的配置列表写入到一个文本文件中"""
        with open(self.quick_file, 'a') as f:
            for config_item in self.config:
                f.write(config_item + "\n")
        print(f"{OK}{Green} 我们已经帮你记在了 {Red}{self.quick_file}{Green} 文件里 {Font}")

    def create_vmess_ws_quick_link(self, ps, address, uuid, port, alert_id, path):
        """
        :param ps: 节点名称
        :param address: 节点地址
        :param uuid: 设备id
        :param port: 端口
        :param alert_id: 加密id
        :param mode: 模式 ws，tcp
        :param path: 路径
        :return: None
        """
        mode = "ws"
        user_config = {
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
            "path": path,
            "tls": "",
            "sni": "",
            "alpn": ""
        }
        self.create_vmess_code(user_config=user_config)

    def create_vmess_tcp_quick_link(self, ps, address, uuid, port, alert_id):
        """
        :param ps: 节点名称
        :param address: 节点地址
        :param uuid: 设备id
        :param port: 端口
        :param alert_id: 加密id
        :param mode: 模式 ws，tcp
        :param path: 路径
        :return: None
        """
        mode = "tcp"
        user_config = {
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
        self.create_vmess_code(user_config=user_config)

    def create_vmess_code(self, user_config):
        aaa = json.dumps(user_config, indent=4, separators=(',', ': '))

        bb = str(aaa).encode()
        cc = base64.b64encode(bb)
        vmess_link = f"vmess://{str(cc, 'utf-8')}"
        self.config.append(vmess_link)
        # f = open(self.quick_file, 'a')
        # f.write(vmess_link)
        # f.write("\n")
        # f.close()
        # print("DEBUG quicklink is", vmess_link)
    
    
    def __test_base64_encoding(self, strings):
        encoded = encode_b64(strings)
        print(encoded)
        os.system(f"echo {encoded} | base64 -d")


def _test_base64_encoding():
    publish_instance = Publish()
    publish_instance.__test_base64_encoding(author_email)


if __name__ == '__main__':
    _test_base64_encoding()