import discord

import os
import json

from typing import Dict, Any

from bot.utils.core import DATA_DIR
from bot.utils.logger import Logger

from bot.modules.db import GroupsDB

Log = Logger()

class Store:
    @staticmethod
    def save_selected(guild_id: str, group_id: str):
        try:
            dir_path = f"{DATA_DIR}/select/{guild_id}"
            os.makedirs(dir_path, exist_ok=True)
            file_path = f"{dir_path}/selected_group.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"group_id": group_id}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            Log.error(f"選択されたグループの保存失敗: {e}")
            return False

    @staticmethod
    def load_selected(guild_id: str):
        try:
            dir_path = f"{DATA_DIR}/select/{guild_id}"
            if os.path.exists(dir_path):
                file_path = f"{dir_path}/selected_group.json"
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data["group_id"]
            else:
                Log.debug("存在しないデータ読み込みをスキップ -> return False")
                return False
        except Exception as e:
            Log.error(f"選択されたグループの読み込み失敗: {e}")
            return False

class SelectGroupView(discord.ui.View):
    def __init__(self, groups: Dict[str, Any]):
        super().__init__(timeout=None)
        self.groups = groups
        self.add_item(SelectGroupSelect(groups))
        self.add_item(ScopeSelect())

class ScopeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="サーバー全体", description="サーバー全体でグループを管理します", value="server"),
            discord.SelectOption(label="ロール別", description="ロール別でグループを管理します", value="role"),
        ]
        super().__init__(placeholder="管理スコープを選択...", options=options, row=1)
    
    async def callback(self, interaction: discord.Interaction):
        scope: str = self.values[0]
        if scope == "role":
            await interaction.response.defer(ephemeral=True)
            roles = [role for role in interaction.guild.roles if role.name != "@everyone"]
            if not roles:
                embed = discord.Embed(description="管理可能なロールが存在しません。", color=discord.Colour.red())
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                return
            
            embed = discord.Embed(title="ロール選択", description="管理対象のロールを選択してください。", color=discord.Colour.blue())
            view = self.view
            view.clear_items()
            view.add_item(RoleSelectSelect(roles, view.groups))
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
        else:
            self.view.scope = "server"
            await interaction.response.defer()

class RoleSelectSelect(discord.ui.Select):
    def __init__(self, roles: list, groups: Dict[str, Any]):
        options = [
            discord.SelectOption(label=role.name, description=f"ID: {role.id}", value=str(role.id))
            for role in roles[:25]
        ]
        super().__init__(placeholder="ロールを選択...", options=options)
        self.groups = groups
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        role_id: str = self.values[0]
        role = interaction.guild.get_role(int(role_id))
        
        if not role:
            embed = discord.Embed(description="ロールが見つかりません。", color=discord.Colour.red())
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            return
        
        embed = discord.Embed(title="グループ選択", description=f"ロール **{role.name}** で管理するグループを選択してください。", color=discord.Colour.purple())
        view = self.view
        view.clear_items()
        view.add_item(SelectGroupSelect(self.groups, role_id))
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)

class SelectGroupSelect(discord.ui.Select):
    def __init__(self, groups: Dict[str, Any], role_id: str = None):
        options = [
            discord.SelectOption(
                label=f"{group['name']} ({group['short_code']}.{group['discriminator']})", 
                description=f"{group['id']}", 
                value=group['id']
            )
            for group in groups.values()
        ]
        super().__init__(placeholder="選択...", options=options)
        self.role_id = role_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        group_id: str = self.values[0]
        db = GroupsDB()
        groups = await db.get_groups(interaction.guild.id)
        group = groups.get(group_id)
        
        if group:
            if self.role_id:
                db = GroupsDB()
                result = await db.set_role_group(interaction.guild.id, self.role_id, group_id)
                scope_text = f"ロール <@&{self.role_id}> で"
            else:
                result = Store.save_selected(str(interaction.guild.id), group_id)
                scope_text = "サーバー全体で"
            
            if result:
                embed = discord.Embed(
                    title="グループ選択成功", 
                    description=f"{scope_text}管理するグループを **{group['name']}** `({group['short_code']}.{group['discriminator']})` に設定しました。", 
                    color=discord.Colour.green()
                )
            else:
                embed = discord.Embed(description=f"グループID `{group_id}` の選択に失敗しました。", color=discord.Colour.red())
        else:
            embed = discord.Embed(description=f"グループID `{group_id}` の選択に失敗しました。", color=discord.Colour.red())
        
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)