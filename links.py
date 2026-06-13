# encoding: utf-8
import base64
import json
import subprocess
from typing import List

from models import VmessInbound, VlessInbound, Socks5Inbound, ShadowsocksInbound, TrojanInbound


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def vmess_link(node: VmessInbound, client_ip: str) -> str:
    cfg: dict = {
        "v": "2",
        "ps": node.name,
        "add": client_ip,
        "port": node.port,
        "id": node.uuid,
        "aid": 0,
        "scy": "auto",
        "net": node.transport,
        "type": "none",
        "host": "",
        "path": "",
        "tls": "",
        "sni": "",
        "alpn": "",
    }
    if node.transport == "ws":
        cfg["path"] = node.path
        cfg["host"] = node.host
    elif node.transport == "xhttp":
        cfg["path"] = node.path
        cfg["host"] = node.host
    return f"vmess://{_b64(json.dumps(cfg, separators=(',', ': ')))}"


def vless_link(node: VlessInbound, client_ip: str) -> str:
    params = f"type={node.transport}&encryption=none"
    if node.transport == "ws":
        params += f"&path={node.path}&host={node.host}"
    elif node.transport == "xhttp":
        params += f"&path={node.path}&host={node.host}"
    if node.flow:
        params += f"&flow={node.flow}"
    return f"vless://{node.uuid}@{client_ip}:{node.port}?{params}#{node.name}"


def trojan_link(node: TrojanInbound, client_ip: str) -> str:
    params = f"security=tls&type={node.transport}&allowInsecure=1"
    if node.transport == "ws":
        params += f"&path={node.path}&host={node.host}"
    elif node.transport == "xhttp":
        params += f"&path={node.path}&host={node.host}"
    return f"trojan://{node.password}@{client_ip}:{node.port}?{params}#{node.name}"


def socks5_link(node: Socks5Inbound, client_ip: str) -> str:
    return f"socks://{_b64(f'{node.user}:{node.passwd}')}@{client_ip}:{node.port}#{node.name}"


def socks5_plain(node: Socks5Inbound, client_ip: str) -> str:
    return (
        f"ip:{client_ip} 用户名:{node.user} 密码:{node.passwd} "
        f"端口:{node.port} 节点名称:{node.name}"
    )


def ss_link(node: ShadowsocksInbound, client_ip: str) -> str:
    encoded = _b64(f"{node.method}:{node.password}")
    return f"ss://{encoded}@{client_ip}:{node.port}?type={node.network}#{node.name}"


def save_links(links: List[str], path: str = "quick_link.txt", append: bool = False) -> None:
    if not links:
        return
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")
    label = "追加" if append else "写入"
    print(f"已{label} {len(links)} 条链接到 {path}")


def publish_to_web(path: str = "quick_link.txt", site: str = "dpaste.com") -> None:
    pastebinit = "./common/pastebinit-1.6.2/pastebinit"
    try:
        result = subprocess.run(
            [pastebinit, "-i", path, "-b", site],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=30,
        )
        if result.returncode == 0:
            print(f"发布成功，分享链接: {result.stdout.strip()}")
        else:
            print(f"发布失败: {result.stderr.strip()}")
    except FileNotFoundError:
        print(f"发布工具不存在: {pastebinit}")
    except subprocess.TimeoutExpired:
        print("发布超时，请检查网络连接")
    except Exception as e:
        print(f"发布时发生错误: {e}")
