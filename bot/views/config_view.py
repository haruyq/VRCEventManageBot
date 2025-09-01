import discord

import json

from bot.utils.core import CONFIG_DIR

class ConfigSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="動作モード変更", description="Botの動作モードを変更します。(GuildMode/UserMode)", value="mode"),
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        if selected_value == "mode":
            embed = discord.Embed(
                title="⚙️｜動作モード変更",
                color=discord.Colour.blue()
            )
            await interaction.response.edit_message(embed=embed, view=ModeSelect())

class ConfigBack(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="戻る", style=discord.ButtonStyle.gray, custom_id="config_back")
    async def back(self, interaction: discord.Interaction, button: discord.Button):
        embed = discord.Embed(
            title="⚙️｜設定パネル",
            description="ここではBotの設定を変更できます。\n以下のメニューから変更する設定を選択してください。",
            color=discord.Colour.blue()
        )
        await interaction.response.edit_message(embed=embed, view=ConfigSelect())

class ModeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="GuildMode", description="組織単位でグループを管理。(スタッフが複数名居る場合に推奨)", value="guild"),
            discord.SelectOption(label="UserMode", description="個人単位でグループを管理。(スタッフが居ない場合に推奨)", value="user"),
        ]
        super().__init__(placeholder="選択...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        embed = discord.Embed(description=f"設定が{selected_value}に変更されました。", color=discord.Colour.green())
        
        if selected_value == "guild":
            with open(f"{CONFIG_DIR}/config.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["mode"] = "guild"
                json.dump(data, f, ensure_ascii=False, indent=4)
            await interaction.edit_original_response(embed=embed, view=ConfigBack(), ephemeral=True)
            
        elif selected_value == "user":
            with open(f"{CONFIG_DIR}/config.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["mode"] = "user"
                json.dump(data, f, ensure_ascii=False, indent=4)
            await interaction.response.send_message(embed=embed, view=ConfigBack(), ephemeral=True)