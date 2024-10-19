GREEN = '\033[92m'
BLUE = '\033[94m'
RED = '\033[91m'
YELLOW = '\033[93m'

BLACK_BG = '\033[40m'
GREEN_BG = '\033[42m'

FONT = '\033[0m'

OK = f"{GREEN}{BLACK_BG}[成功]{FONT}"
Info = f"{BLUE}{BLACK_BG}[信息]{FONT}"
Error = f"{RED}{BLACK_BG}[错误]{FONT}"
Warning = f"{YELLOW}{BLACK_BG}[警告]{FONT}"

def _test_color():
    print(OK)
    print(Info)
    print(Error)
    print(Warning)