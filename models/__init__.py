# models/__init__.py
"""模型模块 - 导出配置模板函数"""

from .config_templates import (
    # 传输层配置模板
    create_raw_settings,
    create_websocket_settings,
    create_xhttp_settings,
    create_grpc_settings,
    create_quic_settings,
    create_domain_socket_settings,
    create_kcp_settings,
    create_tls_settings,
    create_stream_settings,
    create_sniffing_config,
    # Xray 配置模板
    create_log_config,
    create_routing_rule,
    create_routing_config,
    create_shadowsocks_settings,
    create_inbound_config,
    # HTTP 配置模板
    create_http_request,
    create_http_response,
)

__all__ = [
    'create_raw_settings',
    'create_websocket_settings',
    'create_xhttp_settings',
    'create_grpc_settings',
    'create_quic_settings',
    'create_domain_socket_settings',
    'create_kcp_settings',
    'create_tls_settings',
    'create_stream_settings',
    'create_sniffing_config',
    'create_log_config',
    'create_routing_rule',
    'create_routing_config',
    'create_shadowsocks_settings',
    'create_inbound_config',
    'create_http_request',
    'create_http_response',
]