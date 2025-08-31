import discord

from vrchatapi.exceptions import ApiException

from modules.logger import Logger
from modules.db import GroupsDB, filter
from modules.vrchat import Group, Store

Log = Logger()

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
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        if selected_value == "list_group":
            await interaction.response.defer(ephemeral=True)
            db = GroupsDB()
            groups = await db.get_groups(interaction.guild.id)
            if not groups:
                await interaction.followup.send("グループが存在しません。", ephemeral=True)
                return
            
            group_list = "\n".join(f"- {g['name']} (ID: {g['id']})" for g in groups.values())
            embed = discord.Embed(title="グループ一覧", description=group_list, color=discord.Colour.blue())
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif selected_value == "add_group":
            await interaction.response.send_modal(AddGroupModal())
            
        elif selected_value == "delete_group":
            await interaction.response.defer(ephemeral=True)
            db = GroupsDB()
            groups = await db.get_groups(interaction.guild.id)
            if not groups:
                await interaction.followup.send("グループが存在しません。", ephemeral=True)
                return
            embed = discord.Embed(title="グループ削除", description="削除するグループを選択してください。", color=discord.Colour.orange())
            await interaction.followup.send(embed=embed, view=GroupDeleteView(groups), ephemeral=True)

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
        
        group_id = self.group_id.value
        grp = Group(api_client)
        db = GroupsDB()
        try:
            groups = await db.get_groups(interaction.guild.id)
            Log.info(f"Existing groups: {groups}")
            if any(group.get("id") == group_id for group in groups.values()):
                embed = discord.Embed(description="このグループは既に追加されています。", color=discord.Colour.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                        
            resp_raw = await grp.fetch(group_id)
            resp: dict = filter(dict(resp_raw))
            Log.info(f"Fetched group data: {resp}")
            
            check = await grp.validate_user(group_id)
            if check:
                await db.add_group(interaction.guild.id, resp)
                embed = discord.Embed(title="グループ追加成功", description=f"グループ '{resp['name']}' を追加しました。", color=discord.Colour.green())
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description="あなたはこのグループのメンバーではありません。グループの追加に失敗しました。", color=discord.Colour.red())
                await interaction.followup.send(embed=embed, ephemeral=True)

        except ApiException:
            embed = discord.Embed(description=f"グループの取得に失敗しました。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

class GroupDeleteView(discord.ui.View):
    def __init__(self, groups):
        super().__init__(timeout=None)
        self.add_item(GroupDeleteSelect(groups))

class GroupDeleteSelect(discord.ui.Select):
    def __init__(self, groups):
        options = [
            discord.SelectOption(label=group['name'], description=f"ID: {group['id']}", value=group['id'])
            for group in groups.values()
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_group_id = self.values[0]
        await interaction.response.defer(ephemeral=True)
        db = GroupsDB()
        success = await db.remove_group(interaction.guild.id, selected_group_id)
        if success:
            embed = discord.Embed(title="グループ削除成功", description=f"グループID '{selected_group_id}' を削除しました。", color=discord.Colour.green())
        else:
            embed = discord.Embed(description=f"グループID '{selected_group_id}' の削除に失敗しました。", color=discord.Colour.red())
        await interaction.followup.send(embed=embed, ephemeral=True)