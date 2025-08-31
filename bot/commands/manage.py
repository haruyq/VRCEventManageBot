import discord
from discord.ext import commands
from discord import app_commands

import aiofiles.os
import os
import json

from views.manage import ManageView
from modules.config import check_mode, BotMode

cwd = os.getcwd()
CONFIG_DIR = f"{cwd}/bot/configs"
LOGINDATA_DIR = f"{cwd}/bot/logins"

class ManageCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="manage", description="VRChatのグループを管理します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def manage(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        mode = check_mode()
        if mode != BotMode.USER and interaction.user.id != data.get("owner_id"):
            embed = discord.Embed(description="このコマンドはBot管理者のみ使用できます。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if not await aiofiles.os.path.exists(f"{LOGINDATA_DIR}/{interaction.user.id}.enc"):
            embed = discord.Embed(description="認証情報が存在しません。/login コマンドでログインしてください。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(title="グループ管理", description="以下のオプションから選択してください。", color=discord.Colour.green())
        await interaction.followup.send(embed=embed, view=ManageView(), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCommand(bot))