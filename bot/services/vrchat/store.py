# vrchatapi
import vrchatapi
from vrchatapi.api import authentication_api

# import
import json

# from import
from cryptography.fernet import Fernet
from http.cookiejar import Cookie

# utils
from bot.utils.core import CONFIG_DIR, LOGINDATA_DIR
from bot.utils.logger import Logger
from bot.utils.enums import AuthResult

Log = Logger()

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

        key = str(data["secret"]).encode()
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