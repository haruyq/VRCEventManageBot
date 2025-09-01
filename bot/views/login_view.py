import discord

from vrchatapi.api import authentication_api

import os
import aiofiles.os

from utils.logger import Logger

from views.twofa_view import EmailTwoFAButton, TOTPTwoFAButton

from services.vrchat.auth import Auth, AuthResult

Log = Logger()
cwd = os.getcwd()
LOGINDATA_DIR = f"{cwd}/logins"

class LoginModal(discord.ui.Modal, title="ログイン"):
    def __init__(self):
        super().__init__(timeout=None)
    
        self.mail = discord.ui.TextInput(label="メールアドレス", placeholder="xxxx@gmail.com", required=True)
        self.pswd = discord.ui.TextInput(label="パスワード", placeholder="hogehoge1234", required=True)
        self.add_item(self.mail)
        self.add_item(self.pswd)
        
    async def on_submit(self, interaction: discord.Interaction) -> None:
        path = f"{LOGINDATA_DIR}/{interaction.user.id}.enc"
        exist = await aiofiles.os.path.exists(path)
        if exist:
            embed = discord.Embed(description="既に認証情報が存在します。\n既存の認証情報を削除しますか？", color=discord.Colour.red())
            await interaction.response.send(embed=embed, view=DeleteView(path))
            
        else:
            await interaction.response.defer(ephemeral=True)
            auth = Auth(self.mail.value, self.pswd.value)
            result, api_client = await auth.login(interaction.user.id, use_cookie=False) # この先を実装するのを忘れていてテストしてしまったのは内緒
            if result == AuthResult.SUCCESS:
                auth_api = authentication_api.AuthenticationApi(api_client)
                current_user = auth_api.get_current_user()
                embed = discord.Embed(description=f"ログインに成功しました。\nユーザー: {current_user.display_name}", color=discord.Colour.green())
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            elif result == AuthResult.EMAIL_REQUIRED:
                embed = discord.Embed(description="メールによる二段階認証が要求されました。\n以下のボタンをクリックし、コードを入力してください。", color=discord.Colour.yellow())
                await interaction.followup.send(embed=embed, view=EmailTwoFAButton(self.mail.value, self.pswd.value, api_client), ephemeral=True)
            
            elif result == AuthResult.TOTP_REQUIRED:
                embed = discord.Embed(description="TOTPによる二段階認証が要求されました。\n以下のボタンをクリックし、コードを入力してください。", color=discord.Colour.yellow())
                await interaction.followup.send(embed=embed, view=TOTPTwoFAButton(self.mail.value, self.pswd.value, api_client), ephemeral=True)
            
            else:
                embed = discord.Embed(description=f"ログインに失敗しました。", color=discord.Colour.red())
                await interaction.followup.send(embed=embed, ephemeral=True)

class DeleteView(discord.ui.View):
    def __init__(self, delete_path: str):
        super().__init__(timeout=None)
        self.delete_path = delete_path
    
    @discord.ui.button(label="はい", style=discord.ButtonStyle.red, custom_id="loginmodal_yes_btn")
    async def yes_btn(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await aiofiles.os.remove(self.delete_path)
            embed = discord.Embed(description="認証情報の削除に成功しました。\n再度/loginを実行してください。", color=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            Log.error(f"認証情報の削除中にエラー:\n{e}")
            embed = discord.Embed(description="予期しないエラーが発生しました。", color=discord.Colour.red())