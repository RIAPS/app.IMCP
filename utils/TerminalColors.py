import platform

# code to color terminal text color

if platform.system().upper() == 'WINDOWS':
    Red = "\033[38;2;128;0;0m"
    LightRed = "\033[38;2;255;0;0m"
    Green = "\033[38;2;0;255;0m"
    DarkGreen = "\033[38;2;0;128;0m"
    Yellow = "\033[38;2;255,215,0m"
    Orange = "\033[38;2;255;153;51m"
    LightPurple = "\033[38;2;204,0,204m"
    Purple = "\033[38;2;153,0,153m"
    Cyan = "\033[38;2;0,255,255m"
    LightGray = "\033[38;2;192,192,192m"
    White = "\033[38;2;255,255,255m"
    Black = "\033[38;2;0,0,0m"
    RESET = "\033[0m"
elif platform.system().upper() == 'LINUX':
    Red = "\033[31m"
    LightRed = "\033[91m"
    Green = "\033[92m"
    DarkGreen = "\033[32m"
    Yellow = "\033[93m"
    Orange = "\033[33m"
    LightPurple = "\033[94m"
    Purple = "\033[95m"
    Cyan = "\033[96m"
    LightGray = "\033[97m"
    White = "\033[37m"
    Black = "\033[98m"
    RESET = "\033[00m"
else:
    Red = ""
    LightRed = ""
    Green = ""
    DarkGreen = ""
    Yellow = ""
    Orange = ""
    LightPurple = ""
    Purple = ""
    Cyan = ""
    LightGray = ""
    White = ""
    Black = ""
    RESET = ""


def debugMessage(msg, color="", logger=None):
    if logger:
        if color == "":
            logger.info(f"{msg}")
        else:
            logger.info(f"{color}{msg}{RESET}")
    else:
        if color == "":
            print(f"{msg}")
        else:
            print(f"{color}{msg}{RESET}")
