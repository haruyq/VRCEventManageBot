import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode

import json
import os
import asyncio
from cryptography.fernet import Fernet
from http.cookiejar import Cookie
from enum import Enum

from modules.logger import Logger

Log = Logger()

cwd = os.getcwd()
CONFIG_DIR = f"{cwd}/bot/configs"
LOGINDATA_DIR = f"{cwd}/bot/logins"

class AuthResult(Enum):
    SUCCESS = "Success"
    EMAIL_REQUIRED = "EmailRequired"
    TOTP_REQUIRED = "OTPRequired"
    FAILED = "Failed"

class Store:
    @staticmethod
    def save(filename: str, username: str, password: str, auth: str, twofa_auth: str) -> None:
        with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        key = str(data["secret"]).encode()
        cipher = Fernet(key)
        
        encrypted_username = cipher.encrypt(username.encode())
        encrypted_password = cipher.encrypt(password.encode())
        encrypted_auth = cipher.encrypt(auth.encode())
        encrypted_twofa_auth = cipher.encrypt(twofa_auth.encode())
        
        with open(f"{LOGINDATA_DIR}/{filename}.enc", "wb") as f:
            f.write(encrypted_username + b"\n")
            f.write(encrypted_password + b"\n")
            f.write(encrypted_auth + b"\n")
            f.write(encrypted_twofa_auth + b"\n")

    @staticmethod
    def load(filename: str) -> vrchatapi.ApiClient:
        with open(f"{CONFIG_DIR}/config.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        key = str(data["key"]).encode()
        cipher = Fernet(key)

        with open(f"{LOGINDATA_DIR}/{filename}.enc", "rb") as f:
            lines = f.readlines()

        username = cipher.decrypt(lines[0].strip()).decode()
        password = cipher.decrypt(lines[1].strip()).decode()
        auth = cipher.decrypt(lines[2].strip()).decode()
        twofa_auth = cipher.decrypt(lines[3].strip()).decode()

        configuration = vrchatapi.Configuration(
            username=username,
            password=password,
        )
        try:
            with vrchatapi.ApiClient(configuration) as api_client:
                api_client.user_agent = "VRCEVENTMANAGER/0.0.1 haruwaiku@gmail.com"
                api_client.rest_client.cookie_jar.set_cookie(
                    Store._make_cookie("auth", f"{auth}"))
                api_client.rest_client.cookie_jar.set_cookie(
                    Store._make_cookie("twoFactorAuth", f"{twofa_auth}"))

                auth_api = authentication_api.AuthenticationApi(api_client)
                auth_api.get_current_user()
                return (AuthResult.SUCCESS, api_client)
        except vrchatapi.ApiException as e:
            Log.error(e)
            return (AuthResult.FAILED, None)

    def _make_cookie(name, value):
        return Cookie(0, name, value,
                    None, False,
                    "api.vrchat.cloud", True, False,
                    "/", False,
                    False,
                    173106866300,
                    False,
                    None,
                    None, {})

class TwoFA:
    def __init__(self, username: str, password: str, user_id, api_client: vrchatapi.ApiClient):
        self.username = username
        self.password = password
        self.user_id = user_id
        self.api_client = api_client
    
    async def email(self, code):
        try:
            auth_api = authentication_api.AuthenticationApi(self.api_client)
            auth_api.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(code))
            user = auth_api.get_current_user()
            
            cookie_jar = self.api_client.rest_client.cookie_jar._cookies["api.vrchat.cloud"]["/"]
            auth = cookie_jar["auth"].value
            twofa_auth = cookie_jar["twoFactorAuth"].value
            Store.save(self.user_id, self.username, self.password, auth, twofa_auth)
            
            return (True, user.display_name)
        except vrchatapi.ApiException as e:
            Log.error(f"APIコール中にエラー:\n {e}")
            return (False, None)
    
    async def totp(self, code):
        try:
            auth_api = authentication_api.AuthenticationApi(self.api_client)
            auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(code))
            user = auth_api.get_current_user()

            cookie_jar = self.api_client.rest_client.cookie_jar._cookies["api.vrchat.cloud"]["/"]
            auth = cookie_jar["auth"].value
            twofa_auth = cookie_jar["twoFactorAuth"].value
            Store.save(self.user_id, self.username, self.password, auth, twofa_auth)

            return (True, user.display_name)
        except vrchatapi.ApiException as e:
            Log.error(f"APIコール中にエラー:\n {e}")
            return (False, None)

class Auth:
    def __init__(self, username: str, password: str):
        self.configuration = vrchatapi.Configuration(username=username, password=password)
        self.username = username
        self.password = password
    
    async def login(self, user_id, use_cookie: bool = False):
        return await asyncio.to_thread(self._login, user_id, use_cookie)

    def _login(self, user_id, use_cookie: bool = False):
        with vrchatapi.ApiClient(self.configuration) as api_client:
            api_client.user_agent = "VRCEVENTMANAGER/0.0.1 haruwaiku@gmail.com"
            auth_api = authentication_api.AuthenticationApi(api_client)

            if use_cookie:
                result, api_client = Store.load(str(user_id))
                if result == AuthResult.SUCCESS:
                    return (AuthResult.SUCCESS, api_client)
                    
            else:
                try:
                    auth_api.get_current_user()
                except UnauthorizedException as e:
                    if e.status == 200:
                        if "Email 2 Factor Authentication" in e.reason:
                            return (AuthResult.EMAIL_REQUIRED, api_client)

                        elif "2 Factor Authentication" in e.reason:
                            return (AuthResult.TOTP_REQUIRED, api_client)

                        auth_api.get_current_user()
                    else:
                        Log.error(f"APIコール中にエラー:\n {e}")
                        return (AuthResult.FAILED, None)
                except vrchatapi.ApiException as e:
                    Log.error(f"APIコール中にエラー(ApiException):\n {e}")
                    return (AuthResult.FAILED, None)

                cookie_jar = api_client.rest_client.cookie_jar._cookies["api.vrchat.cloud"]["/"]
                auth = cookie_jar["auth"].value
                twofa_auth = cookie_jar["twoFactorAuth"].value
                Store.save(user_id, self.username, self.password, auth, twofa_auth)

                return (AuthResult.SUCCESS, api_client)