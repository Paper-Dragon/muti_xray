## Muti-Xray

> 如果有功能还不能用，那是因为开发者还没写完，欢迎提交 Issue 催更。

## 什么是 Muti-Xray

Muti-Xray 是一个支持多操作系统、高度兼容的大规模节点管理和抗网络审查的站群服务器管理工具。针对当前 GFW（防火长城）引入的人工智能深度包检测机制，本工具采用多 IP 策略来提高抗审查能力。

### 适用场景：

- 全球 IP 代理池
- 在线直播
- 爬虫 IP 池
- 大型机场的抗网络审查

## 安装

### 第一步：安装 Git

#### RHEL/CentOS 7/Debian/Ubuntu:

```bash
source '/etc/os-release' ; [[ "${ID}" == "centos" || "${ID}" == "rhel" ]] && yum install git -y || (apt-get update && apt-get install git -y)
```

#### MacOS:

请参考 Git 官方网站的安装指南：[https://git-scm.com/](https://git-scm.com/)。

### 第二步：克隆代码库

```bash
git clone https://github.com/Paper-Dragon/muti_xray.git
```

### 第三步：准备操作系统

```bash
cd muti_xray && bash prepare.sh run
```

### 第四步：安装 Xray

```bash
python3 main.py install
```

### 配置

![config_init](README.assets/config_init.gif)

```bash
python3 main.py config_init --name CCC-Node
```

## 升级

> 注意：升级将删除所有现有的配置。

```bash
python3 main.py install
```

## 调整参数

使用 `--help` 查看可用选项。

```bash
(venv01) [root@monther project]# python3 main.py --help
usage: main.py [-h] [--list]
               {install,config_init,uninstall,status,show_config} ...

站群服务器隧道管理脚本

位置参数：
  {install,config_init,uninstall,status,show_config}
                        选择子菜单功能
    install             安装或升级 Xray 核心。注意：所有配置将被丢失。
    config_init         初始化配置并重载核心设置。
    uninstall           完全移除此计算机上的管理服务。
    status              查看 Xray 运行状态。
    show_config         显示配置文件内容。

可选参数：
  -h, --help            显示此帮助信息并退出。
  --list, -L            列出站群服务器中的所有节点。
```

## 兼容性

- Python 最低版本要求：3.6

### 操作系统兼容性

- 建议使用 Ubuntu 22.04

| 操作系统                  | 兼容性                   | 备注           |
| ------------------------- | ------------------------ | -------------- |
| CentOS/RHEL 7             | 支持                     | 现在已支持     |
| Fedora                    | 支持                     |                |
| Ubuntu/Debian/Deepin/Mint | 支持                     | 版本需大于 16  |
| ~~Windows 7/8/10/11~~     | ~~理论上可行，尚未实现~~ | 需要联系开发者 |
| MacOS                     | 支持                     | 完全支持       |

### 支持的协议

#### V2Ray

| 协议      | 支持情况                                             |
| --------- | ---------------------------------------------------- |
| VMess     | RAW, RAW+TLS/XTLS, WS, WS+TLS/XTLS, XHTTP           |
| VMessAEAD | RAW, RAW+TLS/XTLS, WS, WS+TLS/XTLS, XHTTP           |
| VLess     | RAW, RAW+TLS/XTLS, WS, WS+TLS/XTLS, XHTTP           |
| VLite     | √                                                    |

**注意**: XHTTP 协议支持 HTTP/1.1、HTTP/2 和 HTTP/3 等多种 HTTP 版本，提供更好的性能和兼容性。

#### Trojan

| 协议   | 支持情况 |
| ------ | -------- |
| Trojan | √        |

#### Shadowsocks

| 协议            | 支持情况 | 网络层协议 | 传输层协议   | 加密方法                                    |
| --------------- | -------- | ---------- | ------------ | ------------------------------------------- |
| ShadowsocksAEAD | √        | TCP        | RAW          | plain                                       |
|                 | √        | TCP        | RAW          | aes-128-gcm                                 |
|                 | √        | TCP        | RAW          | aes-256-gcm                                 |
|                 | √        | TCP        | RAW          | chacha20-poly1305 或 chacha20-ietf-poly1305 |
|                 | √        | UDP        | RAW          | plain                                       |
|                 | √        | UDP        | RAW          | aes-128-gcm                                 |
|                 | √        | UDP        | RAW          | aes-256-gcm                                 |
|                 | √        | UDP        | RAW          | chacha20-poly1305 或 chacha20-ietf-poly1305 |
|                 | √        | TCP+UDP    | RAW          | plain                                       |
|                 | √        | TCP+UDP    | RAW          | aes-128-gcm                                 |
|                 | √        | TCP+UDP    | RAW          | aes-256-gcm                                 |
|                 | √        | TCP+UDP    | RAW          | chacha20-poly1305 或 chacha20-ietf-poly1305 |
|                 | 未来支持 | ?          | mkcp         | ?                                           |
|                 | 未来支持 | ?          | WebSocket    | ?                                           |
|                 | 未来支持 | ?          | HTTP         | ?                                           |
|                 | 未来支持 | ?          | GRPC         | ?                                           |
|                 | 未来支持 | ?          | QUIC         | ?                                           |
|                 | 未来支持 | ?          | DomainSocket | ?                                           |

#### Socks5

| 协议   | 支持协议     | 支持情况 |
| ------ | ------------ | -------- |
| Socks5 | TCP, TCP+UDP | √        |

### 多路复用 (Mux)

支持多路复用技术，可以有效提升网络连接性能和资源利用率。
默认已经开启多路复用技术

#### 多路复用特性

| 功能           | 支持情况 | 默认值 | 说明                                     |
| -------------- | -------- | ------ | ---------------------------------------- |
| RAW 隧道复用   | √        | 启用   | 将多个TCP连接复用到单个物理连接上        |
| 并发连接数     | √        | 8      | 同时复用的连接数量，可根据需要调整       |
| XUDP 聚合隧道  | √        | 启用   | 支持UDP协议的聚合传输                    |
| XUDP 并发数    | √        | 16     | XUDP协议的并发连接数                     |
| UDP443 处理    | √        | reject | 对UDP 443端口的处理方式（reject/allow）  |


### 数字证书

| 功能     | 支持情况 | 需要的参数                             | 是否必需                    |
| -------- | -------- | -------------------------------------- | --------------------------- |
| 证书加密 | 未来支持 | 服务器端证书的域名                     | 可选                        |
|          |          | ALPN 数值                              | 客户端和服务端一致          |
|          |          | allowInsecure 允许不安全连接（客户端） | 是/否                       |
|          |          | disableSystemRoot 禁用系统根 CA        |                             |
|          |          | verifyClientCertificate 验证客户端证书 | 是/否                       |
| 数字证书 |          | certificate/certificateFile            |                             |
|          |          | key/keyFile                            |                             |
|          |          | 验证方式                               | encipherment, verify, issue |

## 为什么选择 Muti-Xray？

- 多协议支持
- 多 IP 支持
- 高级传输配置选项
- 批量操作多个公网 IP
- 生成快捷链接并发布到网页
- 保存快捷链接配置到文本文件

## 致谢：

- [Project X Community](https://github.com/XTLS)
- [Xray](https://github.com/XTLS/Xray-core)

## 注意

该脚本仅供学习交流使用，请勿用于非法活动。网络并非法外之地，违法必究。

## 有关作者你不知道的一切

- 宇宙中的光速本来是35km/h,PaperDragon花了两天优化。
- 有一次PaperDragon咬了一只猫,这只猫获得了超能力并且学会了Python。
- 当贝尔发明电话的时候,他在电话上看到一个PaperDragon的未接来电。
- 解释器不警告PaperDragon,PaperDragon警告解释器。
- PaperDragon可以心算MD5
- PaperDragon抄袭的代码从来没人看出过,他还总是在抄的时候骂骂咧咧,谁也不知道他在骂什么
- 如果你的代码被SIGPAPERFRAGON杀死,这段代码将永远不能再被运行。
- 在ENIAC诞生的那一天,工程师们在桌上发现一份写满了它无法运行的程序的笔记,落款是PaperDragon,多年后人们发现这份代码是一个手写的AI模型。
- PaperDragon没有提出过博弈论,因为没有人能和他博弈。
- PaperDragon找不到人写笑话,因为PaperDragon写完了所有的。