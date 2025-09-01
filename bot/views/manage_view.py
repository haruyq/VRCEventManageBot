import discord

from modules.db import GroupsDB

from manage.add_group import AddGroupModal
from manage.delete_group import DeleteGroupView
from manage.select_group import SelectGroupView

class ManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ManageSelect())

class ManageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="グループ一覧表示", description="現在のグループの一覧を表示します。", value="list_group"),
            discord.SelectOption(label="グループ追加", description="新しいグループを追加します。", value="add_group"),
            discord.SelectOption(label="グループ削除", description="既存のグループを削除します。", value="delete_group"),
            discord.SelectOption(label="グループ選択", description="管理するグループを選択します。", value="select_group"),
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        value: str = self.values[0]
        db = GroupsDB()
        
        if value == "list_group":
            await self._list_groups(interaction, db)
        elif value == "add_group":
            await interaction.response.send_modal(AddGroupModal())
        elif value == "delete_group":
            await self._manage_groups(interaction, db, "削除", discord.Colour.orange(), DeleteGroupView)
        elif value == "select_group":
            await self._manage_groups(interaction, db, "選択", discord.Colour.purple(), SelectGroupView)
    
    async def _list_groups(self, interaction: discord.Interaction, db: GroupsDB):
        await interaction.response.defer(ephemeral=True)
        groups = await db.get_groups(interaction.guild.id)
        
        if not groups:
            embed = discord.Embed(description="グループが存在しません。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        group_list = "\n".join(f"- {g['name']} `({g['short_code']}.{g['discriminator']})`" for g in groups.values())
        embed = discord.Embed(title="グループ一覧", description=group_list, color=discord.Colour.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _manage_groups(self, interaction: discord.Interaction, db: GroupsDB, action: str, color: discord.Colour, view_class):
        await interaction.response.defer(ephemeral=True)
        groups = await db.get_groups(interaction.guild.id)
        
        if not groups:
            embed = discord.Embed(description="グループが存在しません。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(title=f"グループ{action}", description=f"{action}するグループを選択してください。", color=color)
        await interaction.followup.send(embed=embed, view=view_class(groups), ephemeral=True)