from typing import Dict



class PolicyLevelConfig:
    def __init__(self,
                 handshake: int = 4,
                 conn_idle: int = 300,
                 uplink_only: int = 2,
                 downlink_only: int = 5,
                 stats_user_uplink: bool = False,
                 stats_user_downlink: bool = False,
                 buffer_size: int = 10240):
        self.handshake = handshake
        self.conn_idle = conn_idle
        self.uplink_only = uplink_only
        self.downlink_only = downlink_only
        self.stats_user_uplink = stats_user_uplink
        self.stats_user_downlink = stats_user_downlink
        self.buffer_size = buffer_size

class PolicySystemConfig:
    def __init__(self,
                 stats_inbound_uplink: bool = False,
                 stats_inbound_downlink: bool = False,
                 stats_outbound_uplink: bool = False,
                 stats_outbound_downlink: bool = False):
        self.stats_inbound_uplink = stats_inbound_uplink
        self.stats_inbound_downlink = stats_inbound_downlink
        self.stats_outbound_uplink = stats_outbound_uplink
        self.stats_outbound_downlink = stats_outbound_downlink

class PolicyConfig:
    def __init__(self, 
                 levels: Dict[str, PolicyLevelConfig] = {},
                 system: PolicySystemConfig = PolicySystemConfig()):
        self.levels = levels if levels else {"0": PolicyLevelConfig()}
        self.system = system
