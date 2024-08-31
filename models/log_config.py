from typing import Optional

class LogConfig:
    # https://www.v2fly.org/config/overview.html#logobject
    def __init__(self, loglevel: str = "info", access: Optional[str] = None, error: Optional[str] = None):
        self.loglevel = loglevel
        self.access = access
        self.error = error