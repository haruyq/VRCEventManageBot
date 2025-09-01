import json

from enum import Enum

from utils.core import CONFIG_DIR

class BotMode(Enum):
    """Botの動作モードを定義する列挙型

    Args:
        GUILD: 動作モードがGuildModeの場合
        USER: 動作モードがUserModeの場合
    """
    GUILD = "guild"
    USER =  "user"

def check_mode():
    with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("mode") not in ["guild", "user"]:
        data["mode"] = "guild"
        with open(f"{CONFIG_DIR}/config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    if data["mode"] == "guild":
        return BotMode.GUILD
    elif data["mode"] == "user":
        return BotMode.USER