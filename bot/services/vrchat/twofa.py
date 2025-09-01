# vrchatapi
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode

# local import
from bot.services.vrchat.store import Store

# utils
from bot.utils.logger import Logger

Log = Logger()

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