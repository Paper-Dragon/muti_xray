# Muti-Xray

> 如果有功能还不能用，那是因为开发者还没写完，欢迎提交 Issue 催更。

## 什么是 Muti-Xray

Muti-Xray 是一个支持多操作系统、高度兼容的大规模节点管理和抗网络审查的站群服务器管理工具。针对当前 GFW（防火长城）引入的人工智能深度包检测机制，本工具采用多 IP 策略来提高抗审查能力。

### 适用场景

- 全球 IP 代理池
- 在线直播
- 爬虫 IP 池
- 大型机场的抗网络审查

---

## 安装

### 第一步：安装 Git

```bash
source '/etc/os-release' ; [[ "${ID}" == "centos" || "${ID}" == "rhel" ]] && yum install git -y || (apt-get update && apt-get install git -y)
```

### 第二步：克隆代码库

```bash
git clone https://github.com/Paper-Dragon/muti_xray.git
cd muti_xray
```

### 第三步：准备操作系统

```bash
bash prepare.sh run
```

> 此脚本会安装 Python3、pip、openssl 等基础依赖，并通过 pip 安装项目所需的 Python 包。Trojan 协议需要 openssl 生成自签证书，已包含在内。

### 第四步：启动管理工具

```bash
python3 main.py
```

进入交互式主菜单，按数字选择操作：

```
══════════════════════════════════════════════════
 Muti-Xray 站群服务器隧道管理
══════════════════════════════════════════════════
  1. 安装 Xray 内核
  2. 升级 Xray 内核
  3. 安装/更新 GeoIP GeoSite
  4. 初始化配置并创建节点
  5. 查看服务状态
  6. 显示当前配置
  7. 列出所有节点
  8. 备份配置
  9. 恢复配置
 10. 卸载 Xray
  0. 退出
──────────────────────────────────────────────────
 请选择 (0-10):
```

---

## 使用流程

### 安装 Xray

选择 `1. 安装 Xray 内核`。

> **注意**：安装会删除 `/usr/local/etc/xray/config.json`，即所有现有节点配置。

### 初始化配置

选择 `4. 初始化配置并创建节点`，按提示依次完成：

1. 输入节点名称前缀（默认 Node）
2. 选择是否发布链接到 dpaste.com
3. 输入要封禁的域名（可选，直接回车跳过）
4. 多选要创建的协议（空格/逗号分隔）
5. 按协议分别配置参数
6. 自动为每张网卡生成节点、写入配置、重启 Xray

### 备份与恢复

- 选择 `8. 备份配置` 将当前配置（config.json、TLS 证书、分享链接）保存到 SQLite 数据库
- 选择 `9. 恢复配置` 从备份恢复，每次备份会覆盖上一次

---

## 多协议组合选择

初始化配置时支持同时为每张网卡创建多种协议的节点，一次运行即可生成所有组合。

协议选择时可多选（TerminalMenu 环境下空格选中回车确认，普通终端下输入逗号分隔的数字，如 `1,3`）：

```
请选择要创建的协议（可多选）
（可多选，逗号分隔，如 1,3）
--------------------------------------------------
  1. socks5
  2. vmess
  3. vless
  4. shadowsocks
  5. trojan
--------------------------------------------------
请选择 (1-5, 逗号分隔): 1,4
```

选择后按协议逐一配置参数。每张网卡的每种协议使用独立的路由标签（tag），相互隔离，各自的流量通过对应网卡的 IP 出站。

### 节点命名规则

```
{前缀}-{公网IP}-{协议}

示例（前缀 Node，公网 IP 1.2.3.4，同时选了 socks5 + vmess + trojan）：
  Node-1-2-3-4-socks5
  Node-1-2-3-4-vmess
  Node-1-2-3-4-trojan
```

---

## 生成文件

初始化配置后会生成以下文件：

| 文件 | 说明 |
| --- | --- |
| `/usr/local/etc/xray/config.json` | Xray 配置文件（自动重载） |
| `quick_link.txt` | 所有节点的分享链接，生成在执行命令时的工作目录（即仓库根目录） |

`quick_link.txt` 内容示例（各协议格式）：

```
# Socks5（含明文和快速链接两行）
ip:1.2.3.4 用户名:abc 密码:xyz 端口:10001 节点名称:Node-1-2-3-4-socks5
socks://base64@1.2.3.4:10001#Node-1-2-3-4-socks5

# VMess
vmess://base64

# VLess
vless://uuid@1.2.3.4:10002?type=raw&encryption=none#Node-1-2-3-4-vless

# Shadowsocks
ss://base64@1.2.3.4:10003?type=tcp,udp#Node-1-2-3-4-shadowsocks

# Trojan（自签证书，客户端需开启 allowInsecure）
trojan://password@1.2.3.4:10004?security=tls&type=raw&allowInsecure=1#Node-1-2-3-4-trojan
```

---

## 兼容性

- **Python 最低版本**：3.6

### 操作系统兼容性

推荐使用 Ubuntu 22.04 / 24.04。

| 操作系统 | 兼容性 | 备注 |
| --- | --- | --- |
| Ubuntu/Debian/Deepin/Mint | 支持 | 版本需大于 16 |
| CentOS/RHEL 7 | 支持 | |
| ~~Fedora~~ | 未支持 | prepare.sh 无此发行版分支 |
| ~~Rocky Linux~~ | 未支持 | prepare.sh 无此发行版分支 |
| ~~MacOS~~ | 未支持 | prepare.sh 无此发行版分支，systemctl 依赖限制 |
| ~~Windows~~ | 未支持 | systemctl 依赖限制 |

### 支持的协议

| 协议 | 网络层 | 传输层 | 备注 |
| --- | --- | --- | --- |
| **Socks5** | TCP | RAW | 支持密码认证 |
| **Socks5** | TCP+UDP | RAW | UDP 绑定本网卡 IP |
| **VMess** | TCP | RAW | alterId=0（AEAD 模式） |
| **VMess** | TCP | WebSocket | |
| **VMess** | TCP | XHTTP | 支持 HTTP/1.1、HTTP/2、HTTP/3 |
| **VLess** | TCP | RAW | decryption=none，无加密开销 |
| **VLess** | TCP | WebSocket | |
| **VLess** | TCP | XHTTP | 支持 HTTP/1.1、HTTP/2、HTTP/3 |
| **Trojan** | TCP | RAW+TLS | 自动生成自签证书，客户端开启 allowInsecure |
| **Trojan** | TCP | WebSocket+TLS | |
| **Trojan** | TCP | XHTTP+TLS | |
| **Shadowsocks** | TCP | RAW | |
| **Shadowsocks** | UDP | RAW | |
| **Shadowsocks** | TCP+UDP | RAW | |

#### Shadowsocks 加密方法

| 方法 | 说明 |
| --- | --- |
| `aes-128-gcm` | 推荐，性能与安全均衡 |
| `aes-256-gcm` | 更高安全强度 |
| `chacha20-poly1305` | 适合低端 CPU |
| `plain` | 无加密，仅用于测试 |

---

## 为什么选择 Muti-Xray？

- **多协议组合**：一次初始化可同时创建 Socks5、VMess、Shadowsocks 等任意组合
- **多 IP 支持**：自动扫描所有网卡，每个 IP 独立出站，流量严格隔离
- **自动获取公网 IP**：内网 IP 自动通过 curl 探测对应公网 IP，节点链接直接使用公网地址
- **批量操作**：10 张网卡一次交互全部完成
- **备份恢复**：一键备份/恢复，SQLite 数据库存储
- **链接即用**：生成标准 vmess:// / vless:// / trojan:// / ss:// / socks:// 格式，直接导入客户端
- **发布分享**：可一键发布到 dpaste.com 生成分享链接

---

## 致谢

- [Project X Community](https://github.com/XTLS)
- [Xray-core](https://github.com/XTLS/Xray-core)

---

## 注意

该脚本仅供学习交流使用，请勿用于非法活动。网络并非法外之地，违法必究。

---

## 有关作者你不知道的一切

- 宇宙中的光速本来是35km/h，PaperDragon花了两天优化。
- 有一次PaperDragon咬了一只猫，这只猫获得了超能力并且学会了Python。
- 当贝尔发明电话的时候，他在电话上看到一个PaperDragon的未接来电。
- 解释器不警告PaperDragon，PaperDragon警告解释器。
- PaperDragon可以心算MD5。
- PaperDragon抄袭的代码从来没人看出过，他还总是在抄的时候骂骂咧咧，谁也不知道他在骂什么。
- 如果你的代码被SIGPAPERDRAGON杀死，这段代码将永远不能再被运行。
- 在ENIAC诞生的那一天，工程师们在桌上发现一份写满了它无法运行的程序的笔记，落款是PaperDragon，多年后人们发现这份代码是一个手写的AI模型。
- PaperDragon没有提出过博弈论，因为没有人能和他博弈。
- PaperDragon找不到人写笑话，因为PaperDragon写完了所有的。
