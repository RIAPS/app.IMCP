#code to color terminal text color

# grey = "\x1b[38;21m"
# yellow = "\x1b[33;21m"
# red = "\x1b[31;21m"
# bold_red = "\x1b[31;1m"
# reset = "\x1b[0m"

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
# 3 and 4 bit colors
Black = "\033[30m"
Red = "\033[31m"
Green = "\033[32m"
Yellow = "\033[33m"
Blue = "\033[34m"
Magenta = "\033[35m"
Cyan = "\033[36m"
White = "\033[37m"
Gray = "\033[90m"
BrightRed = "\033[91m"
BrightGreen = "\033[92m"
BrightYellow = "\033[93m"
BrightBlue = "\033[94m"
BrightMagenta = "\033[95m"
BrightCyan = "\033[96m"
BrightWhite = "\033[97m"
RESET = "\033[00m"

# 8 bit colors "\033[38;5;#m "
DarkGreen = "\033[38;5;34m"

localBrightCyan = "\033[96m\033[44m"
qryBlack = "\033[30m\033[46m"
ansBlack = "\033[30m\033[101m"

debugMode = True
msgcounterLimit = 10