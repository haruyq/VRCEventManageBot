from discord.ext import commands

from utils.logger import Logger

Log = Logger()

class OnReadyEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        Log.info("-------------------")
        Log.info(f"ログインしました。")
        Log.info(f"ユーザー: {self.bot.user.name} (ID: {self.bot.user.id})")
        Log.info(f"レイテンシ: {round(self.bot.latency * 1000)}ms")
        Log.info(f"サーバー数: {len(self.bot.guilds)}")
        Log.info("-------------------")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnReadyEvent(bot))