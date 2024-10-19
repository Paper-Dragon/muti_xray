from typing import Optional
class APIConfig:
    # https://www.v2fly.org/config/api.html
    # 一般用不到
    def __init__(self, tag: str = "api", services = None):
        self.tag = tag
        self.services = services if services else []
