# vrchatapi
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import ApiException
from vrchatapi.models.group import Group as VRChatGroup

# modules
from modules.db import UserGroupsDB

# utils
from utils.logger import Logger

Log = Logger()

class Group:
    def __init__(self, api_client: vrchatapi.ApiClient):
        self.api_client = api_client
        self.configuration = vrchatapi.Configuration(
            host = "https://api.vrchat.cloud/api/1"
        )

    async def fetch(self, id):
        api_instance = vrchatapi.GroupsApi(self.api_client)
        try:
            resp: VRChatGroup = api_instance.get_group(id, include_roles=True)
            resp_dict = resp.to_dict()
            return resp_dict
        except ApiException as e:
            Log.error(f"グループの取得中にエラー: {e}")
    
    async def validate_user(self, grp_id):
        auth_api = authentication_api.AuthenticationApi(self.api_client)
        users_api = vrchatapi.UsersApi(self.api_client)
        try:
            user = auth_api.get_current_user()
            user_groups = users_api.get_user_groups(user.id)
            for g in user_groups:
                if g.group_id == grp_id:
                    return True
            return False
        except ApiException as e:
            Log.error(f"ユーザーの検証中にエラー: {e}")
            return False
        
    async def cache_groups(self, user_id):
        auth_api = authentication_api.AuthenticationApi(self.api_client)
        users_api = vrchatapi.UsersApi(self.api_client)
        try:
            user = auth_api.get_current_user()
            user_groups = users_api.get_user_groups(user.id)
            db = UserGroupsDB()
            await db.cache_joined(str(user_id), [g.to_dict() for g in user_groups])
            
        except ApiException as e:
            Log.error(f"ユーザーグループのキャッシュ中にエラー: {e}")