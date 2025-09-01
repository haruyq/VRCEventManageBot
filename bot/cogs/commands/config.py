import discord
from discord.ext import commands
from discord import app_commands

from bot.views.config_view import ConfigSelect

class ConfigCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="config", description="Botの設定を変更します。")
    async def config(self, interaction: discord.Interaction):
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message("このコマンドを使用する権限がありません。", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚙️｜設定パネル",
            description="ここではBotの設定を変更できます。\n以下のメニューから変更する設定を選択してください。",
            color=discord.Colour.blue()
        )
        await interaction.response.send_message(embed=embed, view=ConfigSelect(), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCommand(bot))