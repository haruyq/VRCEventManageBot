import discord
from discord.ext import commands

import json
import os
import aiofiles.os
from cryptography.fernet import Fernet

from modules.logger import Logger

Log = Logger()
cwd = os.getcwd()

CONFIG_DIR = f"{cwd}/bot/configs"

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents, help_command=None)
    
    async def setup_hook(self):
        for folder in ("commands", "events"):
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

with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if not data.get("secret"):
    data["secret"] = Fernet.generate_key().decode()
    with open(f"{CONFIG_DIR}/config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

bot.run(data["token"], log_handler=None)