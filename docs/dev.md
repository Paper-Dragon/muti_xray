# 开发测试指南

本项目依赖 `systemctl`、Linux 文件系统路径等真实环境，无法在 Windows / macOS 上直接运行。开发和测试时使用 [jockerdragon/docker-systemd](https://hub.docker.com/r/jockerdragon/docker-systemd) 镜像提供完整的 systemd 容器环境，模拟真实用户操作。

---

## 前置条件

- 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 或 Docker Engine
- 已克隆本仓库到本地

---

## 快速开始

### 1. 启动容器并进入

```bash
# 启动（Linux / macOS）
docker run -d --privileged --name xray-test -v $(pwd):/app jockerdragon/docker-systemd:ubuntu-24.04

# 启动（Windows，替换为实际路径）
docker run -d --privileged --name xray-test -v E:/muti_xray:/app jockerdragon/docker-systemd:ubuntu-24.04

# 进入容器
docker exec -it xray-test bash
```

以下所有操作均在容器内交互式执行。

### 2. 安装依赖

```bash
apt-get update -qq
apt-get install -y -qq python3 python3-pip openssl curl > /dev/null 2>&1
pip3 install --break-system-packages -q -r /app/requirements.txt
```

### 3. 准备测试数据

```bash
mkdir -p /usr/local/etc/xray/tls /var/log/xray

cat > /usr/local/etc/xray/config.json << "EOF"
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {"listen": "10.0.0.1", "port": 10800, "ps": "Socks5-Node-1", "protocol": "socks",
     "settings": {"auth": "password", "accounts": [{"user": "admin", "pass": "test123"}]}, "tag": "in-0"},
    {"listen": "10.0.0.2", "port": 10801, "ps": "VMess-Node-2", "protocol": "vmess",
     "settings": {"clients": [{"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}]}, "tag": "in-1"}
  ],
  "outbounds": [
    {"protocol": "freedom", "tag": "out-0", "sendThrough": "10.0.0.1"},
    {"protocol": "freedom", "tag": "out-1", "sendThrough": "10.0.0.2"}
  ],
  "routing": {"rules": []}
}
EOF

openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout /usr/local/etc/xray/tls/xray.local.key \
    -out /usr/local/etc/xray/tls/xray.local.crt \
    -days 3650 -subj "/CN=xray.local" 2>/dev/null
chmod 600 /usr/local/etc/xray/tls/xray.local.key

cat > /app/quick_link.txt << "EOF"
socks://YWRtaW46dGVzdDEyMw==@1.2.3.4:10800#Socks5-Node-1
vmess://eyJ2IjoiMiIsInBzIjoiVk1lc3MtTm9kZS0yIn0=
EOF
```

---

## 测试

```bash
cd /app
python3 main.py
```

进入主菜单后，按提示操作：

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

### 测试备份功能

1. 主菜单选 `8` 备份配置，确认保存成功
2. 选 `0` 退出，手动删除配置模拟丢失：

```bash
rm -f /usr/local/etc/xray/config.json
rm -rf /usr/local/etc/xray/tls/*
rm -f quick_link.txt
```

3. 重新 `python3 main.py` → `9` 恢复配置
4. 验证恢复结果：

```bash
cat /usr/local/etc/xray/config.json | python3 -m json.tool | head -10
ls -la /usr/local/etc/xray/tls/
cat quick_link.txt
```

---

## 退出并清理

```bash
# 退出容器
exit

# 销毁容器
docker rm -f xray-test
```

---

## 可用镜像标签

[jockerdragon/docker-systemd](https://hub.docker.com/r/jockerdragon/docker-systemd) 提供以下发行版镜像，均支持 systemd：

| 标签 | 说明 |
| --- | --- |
| `ubuntu-24.04` | **推荐**，轻量约 70MB |
| `ubuntu-22.04` | Ubuntu 22.04 |
| `ubuntu-20.04` | Ubuntu 20.04 |
| `ubuntu-18.04` | Ubuntu 18.04 |
| `debian-12` | Debian 12 (Bookworm) |
| `debian-11` | Debian 11 (Bullseye) |
| `debian-10` | Debian 10 (Buster) |
| `centos-7-cgroupv1` | CentOS 7 (cgroup v1) |
| `centos-7-cgroupv2` | CentOS 7 (cgroup v2) |
| `rockylinux-8` | Rocky Linux 8 |
| `rockylinux-9` | Rocky Linux 9 |

如需测试多发行版兼容性，替换标签即可：

```bash
docker run -d --privileged --name xray-test-debian -v $(pwd):/app jockerdragon/docker-systemd:debian-12
docker exec -it xray-test-debian bash
```

---

## 注意事项

1. 容器需使用 `--privileged` 或 `--cap-add SYS_ADMIN` 以支持 systemd
2. macOS 的 Docker Desktop 需启用 cgroup v2（编辑 `~/.docker/daemon.json` 添加 `{"features": {"cgroupv2": true}}`）
3. 恢复备份时菜单会询问是否重启服务，未安装 Xray 的测试环境选择不重启即可
4. 项目目录通过 `-v` 挂载，容器内修改代码会实时生效，无需重建
