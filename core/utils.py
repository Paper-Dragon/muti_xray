# encoding: utf-8
"""工具函数模块"""
import platform
import random
import string
import sys
from typing import List

from utils import author_email, xray
from utils.color import Warning, RED, BLACK_BG, FONT, GREEN, YELLOW
from .constants import RANDOM_STRING_LENGTH, DEFAULT_PORT_START, DEFAULT_PORT_END, YES_NO_OPTIONS

# 跨平台菜单支持
_IS_WINDOWS = platform.system() == "Windows"

if not _IS_WINDOWS:
    try:
        from simple_term_menu import TerminalMenu
        _HAS_TERMINAL_MENU = True
    except (ImportError, NotImplementedError):
        _HAS_TERMINAL_MENU = False
else:
    _HAS_TERMINAL_MENU = False


def call_xray_method(method_name):
    """通用包装函数，用于调用xray对象的方法"""
    def wrapper(args):
        method = getattr(xray, method_name)
        method()
    return wrapper


def generate_random_string(length: int = RANDOM_STRING_LENGTH) -> str:
    """生成随机字符串"""
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


def generate_random_port() -> int:
    """生成随机端口"""
    return random.randint(DEFAULT_PORT_START, DEFAULT_PORT_END)


def show_menu(options: List[str], title: str) -> int:
    """显示终端菜单并返回选择的索引（跨平台支持）"""
    if _HAS_TERMINAL_MENU:
        try:
            menu = TerminalMenu(options, title=title)
            return menu.show()
        except (NotImplementedError, OSError):
            # 非交互式环境或终端不可用，回退到降级方案
            pass
    
    # Windows 或 TerminalMenu 不可用时的降级方案
    print(f"\n{GREEN}{title}{FONT}")
    print("-" * 50)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    print("-" * 50)
    
    while True:
        try:
            choice = input(f"请选择 (1-{len(options)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(options):
                return index
            else:
                print(f"{Warning} {RED}请输入 1 到 {len(options)} 之间的数字{FONT}")
        except ValueError:
            print(f"{Warning} {RED}请输入有效的数字{FONT}")
        except (KeyboardInterrupt, EOFError):
            # 非交互式环境，返回默认值（第一个选项）
            print(f"\n{Warning} {YELLOW}非交互式环境，使用默认选项: {options[0]}{FONT}")
            return 0


def get_yes_no_choice(title: str) -> str:
    """获取是/否选择"""
    return YES_NO_OPTIONS[show_menu(YES_NO_OPTIONS, title)]


def exit_with_error(message: str, protocol: str = ""):
    """统一错误退出函数"""
    protocol_text = f" {protocol}" if protocol else ""
    print(
        f"{Warning} {RED}作者还没写这个模式{FONT}{protocol_text} "
        f"请联系作者 {GREEN}{BLACK_BG}{author_email}{FONT}"
    )
    sys.exit(2)
