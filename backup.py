# encoding: utf-8
import db
import xray
from builder import generate_from_db
import links as lk
from ui import GREEN, BLUE, RED, YELLOW, RESET, OK, INF, ERR, WRN


def backup() -> bool:
    if not db.has_data():
        print(f" {ERR} {RED}数据库中没有节点数据，请先初始化配置{RESET}")
        return False

    path = db.backup()
    if path:
        print(f" {OK} {GREEN}数据库已备份到当前目录: {path}{RESET}")
        return True

    print(f" {ERR} {RED}备份失败{RESET}")
    return False


def restore(restart_service: bool = True) -> bool:
    if not db.restore():
        print(f" {ERR} {RED}没有可用的备份{RESET}")
        return False

    print(f" {OK} {GREEN}数据库已恢复{RESET}")

    try:
        cfg, all_links = generate_from_db()
        cfg.save(xray.CONFIG_PATH)
        print(f" {OK} {GREEN}配置已从数据库重新生成{RESET}")

        plain_links = [l for l in all_links if l.startswith("ip:")]
        quick_links = [l for l in all_links if not l.startswith("ip:")]
        if plain_links:
            lk.save_links(plain_links, append=False)
            lk.save_links(quick_links, append=True)
        else:
            lk.save_links(quick_links, append=False)

        if restart_service:
            try:
                xray.restart()
                print(f" {OK} {GREEN}Xray 服务已重启{RESET}")
            except Exception:
                print(f" {WRN} {YELLOW}服务重启失败，请手动执行: systemctl restart xray{RESET}")

        return True

    except Exception as e:
        print(f" {ERR} {RED}恢复失败: {e}{RESET}")
        return False
