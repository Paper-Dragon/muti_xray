# 生成 README 图片资源

本文档说明如何生成 `README.assets/` 目录下的演示图片和动图。

## 环境准备

使用 Docker 容器生成，需要安装以下依赖：

```bash
docker run -d --privileged --name xray-test -v "$(pwd):/app" jockerdragon/docker-systemd:ubuntu-24.04

docker exec xray-test bash -c '
apt-get update -qq && apt-get install -y -qq python3 python3-pip fonts-noto-cjk-extra > /dev/null 2>&1
pip3 install --break-system-packages Pillow
'
```

关键依赖：
- **Pillow**：Python 图像处理库，用于渲染终端画面
- **fonts-noto-cjk-extra**：Noto Sans CJK 中文字体，路径为 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`

## 核心渲染逻辑

### 基础参数

```python
FONT_PATH  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SIZE  = 16
LINE_H     = 22      # 行高
PAD_X      = 14      # 左边距
PAD_Y      = 10      # 上下边距
IMG_W      = 720     # 图片宽度
BG_COLOR   = (30, 30, 30)   # 深灰背景
DEFAULT_FG = (204, 204, 204) # 默认前景色
```

### ANSI 颜色映射

```python
ANSI_COLORS = {
    "92": (80, 250, 123),    # 绿色
    "94": (139, 180, 250),   # 蓝色
    "91": (255, 85, 85),     # 红色
    "93": (241, 250, 140),   # 黄色
}
```

### 解析 ANSI 色彩并渲染文本

```python
import re
from PIL import Image, ImageDraw, ImageFont

def parse_spans(text):
    """将带 ANSI 转义码的文本解析为 (文本, 颜色) 列表。"""
    parts = re.split(r'(\033\[[0-9;]*m)', text)
    spans = []
    fg = DEFAULT_FG
    for p in parts:
        m = re.match(r'\033\[([0-9;]*)m', p)
        if m:
            codes = m.group(1).split(';')
            for c in codes:
                if c == '0' or c == '':
                    fg = DEFAULT_FG
                elif c in ANSI_COLORS and ANSI_COLORS[c]:
                    fg = ANSI_COLORS[c]
        elif p:
            spans.append((p, fg))
    return spans
```

## 生成静态 PNG

适用于只需展示单个界面状态的场景（如主菜单）。

```python
G  = "\033[92m"
R  = "\033[91m"
Y  = "\033[93m"
RS = "\033[0m"

lines = [
    "root@server:~/muti_xray# python3 main.py",
    "",
    f"{G}{'═' * 50}{RS}",
    f" {R}Muti-Xray 站群服务器隧道管理{RS}",
    f"{G}{'═' * 50}{RS}",
    f"  {G} 1.{RS} 安装 Xray 内核",
    # ... 更多菜单项
    f"  {Y} 0.{RS} 退出",
    f"{G}{'─' * 50}{RS}",
    f" 请选择 (0-11): ",
]

# 计算图片高度（根据行数自适应）
height = PAD_Y * 2 + LINE_H * len(lines)
img = Image.new("RGB", (IMG_W, height), BG_COLOR)
draw = ImageDraw.Draw(img)
font = ImageFont.truetype(FONT_PATH, FONT_SIZE, index=2)

for i, line in enumerate(lines):
    y = PAD_Y + i * LINE_H
    x = PAD_X
    for text, color in parse_spans(line):
        draw.text((x, y), text, fill=color, font=font)
        bbox = font.getbbox(text)
        x += bbox[2] - bbox[0]

img.save("README.assets/main_menu.png")
```

## 生成动态 GIF

适用于需要展示交互过程的场景（如初始化配置、追加协议）。

### 原理

GIF 动画由多帧组成，每帧是一张固定尺寸的图片。通过逐步添加终端行内容并渲染为帧，模拟终端交互过程。

### Recorder 类

```python
FIXED_ROWS = 28  # GIF 显示区域固定行数

class Recorder:
    def __init__(self):
        self.lines = []    # 当前终端所有行
        self.frames = []   # (Image, duration_ms) 列表

    def add(self, duration=800):
        """将当前状态渲染为一帧。"""
        visible = self.lines[-FIXED_ROWS:]  # 只显示最后 N 行
        img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE, index=2)
        for i, line in enumerate(visible):
            y = PAD_Y + i * LINE_H
            x = PAD_X
            for text, color in parse_spans(line):
                draw.text((x, y), text, fill=color, font=font)
                bbox = font.getbbox(text)
                x += bbox[2] - bbox[0]
        self.frames.append((img, duration))

    def println(self, text="", duration=400):
        """添加一行并生成帧。"""
        self.lines.append(text)
        self.add(duration)

    def print_lines(self, texts, duration=300):
        """一次性添加多行，只生成一帧。"""
        for t in texts:
            self.lines.append(t)
        self.add(duration)

    def type_input(self, text, delay_per_char=55, pause_after=400):
        """模拟逐字符输入效果。"""
        for i in range(1, len(text) + 1):
            tmp = self.lines[:-1] + [self.lines[-1] + text[:i]]
            # 渲染临时状态
            ...
            self.frames.append((img, delay_per_char))
        self.lines[-1] = self.lines[-1] + text
        self.add(pause_after)

    def save_gif(self, path):
        """保存为 GIF 动画。"""
        imgs = [f[0] for f in self.frames]
        durs = [f[1] for f in self.frames]
        imgs[0].save(
            path,
            save_all=True,
            append_images=imgs[1:],
            duration=durs,
            loop=0,          # 无限循环
            optimize=False,
        )
```

### 使用示例

```python
r = Recorder()

# 命令提示符
r.println("root@server:~/muti_xray# ", 800)

# 模拟输入命令
r.type_input("python3 main.py", delay_per_char=50, pause_after=500)

# 显示菜单（多行一帧）
r.print_lines(menu_lines, 800)

# 模拟选择
r.type_input("4", delay_per_char=80, pause_after=500)

# 输出结果
r.println(f" {OK_S} {G}配置已写入{RS}", 400)

# 保存
r.save_gif("README.assets/config_init.gif")
```

## 当前资源文件

| 文件 | 类型 | 用途 |
|------|------|------|
| `main_menu.png` | 静态截图 | 主菜单展示 |
| `config_init.gif` | 动图 | 初始化配置完整流程 |
| `append_protocol.gif` | 动图 | 追加协议流程 |
| `backup_restore.gif` | 动图 | 备份与恢复流程 |
| `install_xray.gif` | 动图 | 安装 Xray 流程 |

## 注意事项

1. **字体索引**：`ImageFont.truetype(FONT_PATH, FONT_SIZE, index=2)` 中 `index=2` 对应 Noto Sans CJK SC（简体中文），不同系统可能需要调整
2. **GIF 帧率**：`delay_per_char` 建议 50-80ms 模拟打字速度，`duration` 用于控制停留时间
3. **固定行数**：GIF 使用 `FIXED_ROWS` 固定显示区域，超出部分自动滚动（只取最后 N 行）
4. **PNG 自适应**：静态图高度根据 `len(lines)` 自动计算
