from vrchatapi.exceptions import ApiException

import discord

from typing import Dict, Any

from bot.modules.db import GroupsDB

from bot.services.vrchat.group import Group
from bot.services.vrchat.store import Store

class AddGroupModal(discord.ui.Modal, title="グループ追加"):
    def __init__(self):
        super().__init__()
        self.group_id = discord.ui.TextInput(label="グループID", placeholder="grp_00000000-0000-0000...", required=True)
        self.add_item(self.group_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        result, api_client = Store.load(str(interaction.user.id))
        if not result:
            embed = discord.Embed(description="認証情報の取得に失敗しました。/login コマンドで再度ログインしてください。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        group_id: str = self.group_id.value
        grp = Group(api_client)
        db = GroupsDB()
        
        try:
            groups = await db.get_groups(interaction.guild.id)
            if any(group.get("id") == group_id for group in groups.values()):
                embed = discord.Embed(description="このグループは既に追加されています。", color=discord.Colour.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            resp_raw = await grp.fetch(group_id)
            resp: Dict[str, Any] = filter(dict(resp_raw))
            
            check = await grp.validate_user(group_id)
            if check:
                await db.add_group(interaction.guild.id, resp)
                embed = discord.Embed(
                    title="グループ追加成功", 
                    description=f"**{resp['name']}** `({resp['short_code']}.{resp['discriminator']})` を追加しました。", 
                    color=discord.Colour.green()
                )
            else:
                embed = discord.Embed(description="あなたはこのグループのメンバーではありません。グループの追加に失敗しました。", color=discord.Colour.red())
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except ApiException:
            embed = discord.Embed(description="グループの取得に失敗しました。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)