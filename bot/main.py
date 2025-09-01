import discord
from discord.ext import commands

import json
import os
import aiofiles.os
from cryptography.fernet import Fernet

from modules.db import GroupsDB, UserGroupsDB

from utils.logger import Logger
from utils.core import CONFIG_DIR

Log = Logger()
cwd = os.getcwd()

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents, help_command=None)
    
    async def setup_hook(self):
        await GroupsDB().init_db()
        await UserGroupsDB().init_db()
        
        for folder in ("cogs/commands", "cogs/events"):
            for filename in await aiofiles.os.listdir(f"{cwd}/bot/{folder}"):
                if not filename.endswith(".py"):
                    continue
                ext = f"{folder}.{filename[:-3]}"
                try:
                    await self.load_extension(ext)
                    Log.info(f"[{ext}] ロード成功")
                except Exception as e:
                    Log.error(f"[{ext}] ロード失敗: {e}")

bot = Bot()

config_path = f"{CONFIG_DIR}/config.json"
with open(config_path, "r+", encoding="utf-8") as f:
    data = json.load(f)
    if not data.get("secret"):
        data["secret"] = Fernet.generate_key().decode()
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.truncate()

bot.run(data["token"], log_handler=None)