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

#### RHEL/CentOS 7/Debian/Ubuntu

```bash
source '/etc/os-release' ; [[ "${ID}" == "centos" || "${ID}" == "rhel" ]] && yum install git -y || (apt-get update && apt-get install git -y)
```

#### MacOS

请参考 Git 官方网站的安装指南：[https://git-scm.com/](https://git-scm.com/)。

### 第二步：克隆代码库

```bash
git clone https://github.com/Paper-Dragon/muti_xray.git
cd muti_xray
```

### 第三步：准备操作系统

```bash
bash prepare.sh run
```

### 第四步：安装 Xray 内核

> **注意**：此命令会删除 `/usr/local/etc/xray/config.json`，即所有现有节点配置。

```bash
python3 main.py install
```

### 第五步：初始化配置

```bash
python3 main.py config_init --name 节点前缀
```

运行后进入交互向导，按提示依次完成：

1. 输入要封禁的域名（可选，直接回车跳过）
2. 多选要创建的协议（空格/逗号分隔）
3. 按协议分别配置参数
4. 自动为每张网卡生成节点、写入配置、重启 Xray

---

## 命令参考

```
usage: python3 main.py [-h] [--list] 命令 ...

站群服务器隧道管理脚本

命令:
  install       安装或重置 Xray 内核（会删除现有配置）
  upgrade       升级 Xray 内核
  install_geo   安装/更新 GeoIP 和 GeoSite 数据库
  config_init   交互式初始化配置并创建节点
  uninstall     完全卸载 Xray 服务和配置
  status        查看 Xray 服务运行状态
  show_config   显示当前配置文件内容

可选参数:
  -h, --help    显示帮助信息并退出
  --list, -L    列出配置文件中所有节点
```

### config_init 选项

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--name NAME` | 节点名称前缀，自动追加公网 IP 后缀 | `Node` |
| `--publish true\|false` | 是否将链接发布到 dpaste.com | `true` |

### 使用示例

```bash
# 安装 Xray（⚠️ 会删除现有配置文件）
python3 main.py install

# 创建节点，前缀为 CCC-Node，不发布到网络
python3 main.py config_init --name CCC-Node --publish false

# 列出所有已配置节点
python3 main.py --list

# 查看 Xray 服务状态
python3 main.py status

# 查看当前配置文件内容
python3 main.py show_config

# 升级 Xray 内核（保留现有配置）
python3 main.py upgrade

# 更新 Geo 数据库
python3 main.py install_geo
```

---

## 多协议组合选择

`config_init` 支持同时为每张网卡创建多种协议的节点，一次运行即可生成所有组合。

协议选择时可多选（TerminalMenu 环境下空格选中回车确认，普通终端下输入逗号分隔的数字，如 `1,3`）：

```
请选择要创建的协议（可多选）
（可多选，逗号分隔，如 1,3）
--------------------------------------------------
  1. socks5
  2. vmess
  3. vless
  4. shadowsocks
--------------------------------------------------
请选择 (1-4, 逗号分隔): 1,4
```

选择后按协议逐一配置参数。每张网卡的每种协议使用独立的路由标签（tag），相互隔离，各自的流量通过对应网卡的 IP 出站。

### 节点命名规则

```
{前缀}-{公网IP}-{协议}

示例（前缀 Node，公网 IP 1.2.3.4）：
  Node-1-2-3-4-socks5
  Node-1-2-3-4-vmess
  Node-1-2-3-4-shadowsocks
  v2-Node-1-2-3-4-vmess-socks5    （vmess-socks5 复合协议中的 VMess 节点）
  sk5-Node-1-2-3-4-vmess-socks5   （vmess-socks5 复合协议中的 Socks5 节点）
```

---

## 生成文件

运行 `config_init` 后会生成以下文件：

| 文件 | 说明 |
| --- | --- |
| `/usr/local/etc/xray/config.json` | Xray 配置文件（自动重载） |
| `quick_link.txt` | 所有节点的分享链接，生成在执行命令时的工作目录（即仓库根目录） |

`quick_link.txt` 内容示例：

```
ip:1.2.3.4 用户名:abc 密码:xyz 端口:10001 节点名称:Node-1-2-3-4-socks5
socks://base64@1.2.3.4:10001#Node-1-2-3-4-socks5
vmess://base64
ss://base64@1.2.3.4:10002?type=tcp,udp#Node-1-2-3-4-shadowsocks
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

- **多协议组合**：一次 `config_init` 可同时创建 Socks5、VMess、Shadowsocks 等任意组合
- **多 IP 支持**：自动扫描所有网卡，每个 IP 独立出站，流量严格隔离
- **自动获取公网 IP**：内网 IP 自动通过 curl 探测对应公网 IP，节点链接直接使用公网地址
- **批量操作**：10 张网卡一条命令全部完成
- **链接即用**：生成标准 vmess:// / ss:// / socks:// 格式，直接导入客户端
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
