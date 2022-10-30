import base64
import os
from utils.color import *


def encode_b64(strings):
    bb = str(strings).encode()
    cc = base64.b64encode(bb)
    strings = str(cc, 'utf-8')
    return strings


class Publish(object):
    def __init__(self, config):
        """
        发布一个列表到网页端或者文件内
        :param config: list
        """
        self.config = config
        self.quick_file = "quick_link.txt"
        self.p_web = "dpaste.com"

    def publish_2_web(self):
        self.publish_2_txt()
        print(f"发布的链接是： {Green}  ")
        os.system(f"./common/pastebinit-1.5/pastebinit -i {self.quick_file} -b {self.p_web}")
        print(Font)

    def publish_2_txt(self):
        f = open(self.quick_file, 'a')
        for i in self.config:
            f.write(i)
            f.write("\n")
        print(f"{OK} {Green} 我们已经帮你记在了 {Red} {self.quick_file} {Green} 文件里 {Font}")
        f.close()


def __test_b64e(strings):
    b64 = encode_b64(strings)
    print(b64)
    os.system(f"echo {b64} | base64 -d")


# test
if __name__ == '__main__':
    __test_b64e(f"{author_email}")
