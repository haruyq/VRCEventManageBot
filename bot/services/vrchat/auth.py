# vrchatapi
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException

# import
import asyncio

# local import
from bot.services.vrchat.store import Store

# utils
from bot.utils.logger import Logger
from bot.utils.enums import AuthResult

Log = Logger()

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