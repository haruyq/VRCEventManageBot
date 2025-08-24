import discord
from discord.ext import commands
from discord import app_commands

from views.login_modal import LoginModal

class LoginCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="login", description="VRChatアカウントにログインします")
    @app_commands.checks.has_permissions(administrator=True)
    async def login(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LoginModal())

async def setup(bot: commands.Bot):
    await bot.add_cog(LoginCommand(bot))