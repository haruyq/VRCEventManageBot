import os
import json

CWD = os.getcwd()
CONFIG_DIR = f"{CWD}/configs"
DATA_DIR = f"{CWD}/data"
LOGINDATA_DIR = f"{CWD}/logins"

with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
    config_data = json.load(f)

TOKEN = config_data.get("token")
OWNER_ID = config_data.get("owner_id")
SECRET = config_data.get("secret")