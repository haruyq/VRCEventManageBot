import logging
import sys
import json
import os

from bot.utils.core import CONFIG_DIR

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[90m",   # グレー
        logging.INFO: "\033[92m",    # 緑
        logging.WARNING: "\033[93m", # 黄色
        logging.ERROR: "\033[91m",   # 赤
        logging.CRITICAL: "\033[95m" # 紫
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.RESET)
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)

cwd = os.getcwd()

def set_Loglevel(level: str, logger: logging.Logger):
    if level == "DEBUG":
        return logger.setLevel(logging.DEBUG)
    elif level == "INFO":
        return logger.setLevel(logging.INFO)
    elif level == "WARNING":
        return logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        return logger.setLevel(logging.ERROR)

def Logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))

    with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
        LOGLEVEL = json.load(f)["loglevel"]
    
    logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(level=set_Loglevel(level=LOGLEVEL, logger=logger), handlers=[handler])
    return logger