# config.py
# This file holds the configuration for the application, like color codes.

import os

# This line helps enable ANSI color codes on Windows terminals
if os.name == 'nt':
    os.system("")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'