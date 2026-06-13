# encoding: utf-8
from typing import Optional

GREEN  = '\033[92m'
BLUE   = '\033[94m'
RED    = '\033[91m'
YELLOW = '\033[93m'
BG     = '\033[40m'
RESET  = '\033[0m'

OK  = f"{GREEN}{BG}[成功]{RESET}"
INF = f"{BLUE}{BG}[信息]{RESET}"
ERR = f"{RED}{BG}[错误]{RESET}"
WRN = f"{YELLOW}{BG}[警告]{RESET}"


def prompt(text: str, default: str = "") -> str:
    try:
        val = input(text).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def prompt_int(text: str) -> Optional[int]:
    try:
        val = input(text).strip()
        return int(val) if val else None
    except (ValueError, EOFError, KeyboardInterrupt):
        print()
        return None
