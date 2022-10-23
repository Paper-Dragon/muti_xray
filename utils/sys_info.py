import psutil


class SysInfo(object):
    def __init__(self):
        self.netCard_info = []

    def get_net_card(self):
        info = psutil.net_if_addrs()
        for k, v in info.items():
            for item in v:
                if item[0] == 2 and not item[1] == '127.0.0.1':
                    self.netCard_info.append((item[1]))


if __name__ == '__main__':
    sysinfo = SysInfo()
    sysinfo.get_net_card()
    print(sysinfo.netCard_info)
