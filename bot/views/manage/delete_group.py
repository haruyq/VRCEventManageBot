import discord

from typing import Dict, Any

from modules.db import GroupsDB

class DeleteGroupView(discord.ui.View):
    def __init__(self, groups: Dict[str, Any]):
        super().__init__(timeout=None)
        self.add_item(DeleteGroupSelect(groups))

class DeleteGroupSelect(discord.ui.Select):
    def __init__(self, groups: Dict[str, Any]):
        options = [
            discord.SelectOption(
                label=f"{group['name']} ({group['short_code']}.{group['discriminator']})", 
                description=f"{group['id']}", 
                value=group['id']
            )
            for group in groups.values()
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        group_id: str = self.values[0]
        db = GroupsDB()
        success = await db.remove_group(interaction.guild.id, group_id)
        
        if success:
            embed = discord.Embed(title="グループ削除成功", description=f"グループID `{group_id}` を削除しました。", color=discord.Colour.green())
        else:
            embed = discord.Embed(description=f"グループID `{group_id}` の削除に失敗しました。", color=discord.Colour.red())
        
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)