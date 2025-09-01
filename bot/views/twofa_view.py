import discord

from bot.services.vrchat.twofa import TwoFA

class EmailTwoFAModal(discord.ui.Modal, title="認証コード"):
    def __init__(self, username: str, password: str, api_client):
        super().__init__(timeout=None)
        self.username = username
        self.password = password
        self.api_client = api_client
    
        self.code = discord.ui.TextInput(label="メール認証コード", placeholder="123456")
        self.add_item(self.code)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            twofa = TwoFA(self.username, self.password, interaction.user.id, self.api_client)
            resp, curr_username = await twofa.email(str(self.code.value))
            if resp:
                embed = discord.Embed(description=f"ログインに成功しました。\nユーザー: {curr_username}", color=discord.Colour.green())
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(description=f"エラーが発生しました。\n```py\n{e}\n```")
            await interaction.followup.send(embed=embed, ephemeral=True)

class EmailTwoFAButton(discord.ui.View):
    def __init__(self, username, password, api_client):
        super().__init__(timeout=None)
        self.username = username
        self.password = password
        self.api_client = api_client
    
    @discord.ui.button(label="コードを入力", style=discord.ButtonStyle.green, custom_id="emailcode_enter")
    async def email_entercode(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(EmailTwoFAModal(self.username, self.password, self.api_client))

class TOTPTwoFAModal(discord.ui.Modal, title="認証コード"):
    def __init__(self, username: str, password: str, api_client):
        super().__init__(timeout=None)
        self.username = username
        self.password = password
        self.api_client = api_client
    
        self.code = discord.ui.TextInput(label="TOTP認証コード", placeholder="123456")
        self.add_item(self.code)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        twofa = TwoFA(self.username, self.password, interaction.user.id, self.api_client)
        resp, curr_username = await twofa.totp(str(self.code.value))
        if resp:
            embed = discord.Embed(description=f"ログインに成功しました。\nユーザー: {curr_username}", color=discord.Colour.green())
            await interaction.followup.send(embed=embed, ephemeral=True)

class TOTPTwoFAButton(discord.ui.View):
    def __init__(self, username, password, api_client):
        super().__init__(timeout=None)
        self.username = username
        self.password = password
        self.api_client = api_client
    
    @discord.ui.button(label="コードを入力", style=discord.ButtonStyle.green, custom_id="totpcode_enter")
    async def totp_entercode(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(TOTPTwoFAModal(self.username, self.password, self.api_client))