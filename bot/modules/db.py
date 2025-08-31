import aiosqlite
import os
import json
from typing import Dict, List, Optional, Any
from modules.logger import Logger

Log = Logger()
cwd = os.getcwd()
DB_PATH = f"{cwd}/bot/db"
GROUPS_DB = f"{DB_PATH}/groups.db"
USER_GROUPS_DB = f"{DB_PATH}/user_groups.db"

def filter(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    Log.debug(f"Raw group data: {raw_data}")
    return {
        "id": raw_data.get("id"),
        "name": raw_data.get("name"),
        "shortCode": raw_data.get("shortCode"),
        "discriminator": raw_data.get("discriminator"),
        "description": raw_data.get("description"),
        "iconUrl": raw_data.get("iconUrl"),
        "bannerUrl": raw_data.get("bannerUrl"),
        "ownerId": raw_data.get("ownerId"),
    }

class GroupsDB:
    def __init__(self):
        os.makedirs(DB_PATH, exist_ok=True)
    
    async def init_db(self) -> None:
        async with aiosqlite.connect(GROUPS_DB) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    guild_id TEXT PRIMARY KEY,
                    groups_data TEXT NOT NULL
                )
            ''')
            await db.commit()
    
    async def add_group(self, guild_id: str, group_data: Dict[str, Any]) -> bool:
        try:
            groups = await self.get_groups(guild_id)
            group_id = group_data.get('id')
            if not group_id:
                return False
            
            groups[group_id] = group_data
            await self._save_groups(guild_id, groups)
            return True
        except Exception as e:
            Log.error(f"Failed to add group: {e}")
            return False
    
    async def remove_group(self, guild_id: str, group_id: str) -> bool:
        try:
            groups = await self.get_groups(guild_id)
            if group_id in groups:
                del groups[group_id]
                await self._save_groups(guild_id, groups)
                return True
            return False
        except Exception as e:
            Log.error(f"Failed to remove group: {e}")
            return False
    
    async def update_group(self, guild_id: str, group_id: str, group_data: Dict[str, Any]) -> bool:
        try:
            groups = await self.get_groups(guild_id)
            if group_id in groups:
                groups[group_id].update(group_data)
                await self._save_groups(guild_id, groups)
                return True
            return False
        except Exception as e:
            Log.error(f"Failed to update group: {e}")
            return False
    
    async def get_groups(self, guild_id: str) -> Dict[str, Dict[str, Any]]:
        try:
            async with aiosqlite.connect(GROUPS_DB) as db:
                cursor = await db.execute('SELECT groups_data FROM groups WHERE guild_id = ?', (guild_id,))
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return {}
        except Exception as e:
            Log.error(f"Failed to get groups: {e}")
            return {}
    
    async def get_group(self, guild_id: str, group_id: str) -> Optional[Dict[str, Any]]:
        groups = await self.get_groups(guild_id)
        return groups.get(group_id)
    
    async def _save_groups(self, guild_id: str, groups: Dict[str, Dict[str, Any]]) -> None:
        async with aiosqlite.connect(GROUPS_DB) as db:
            await db.execute(
                'INSERT OR REPLACE INTO groups (guild_id, groups_data) VALUES (?, ?)',
                (guild_id, json.dumps(groups))
            )
            await db.commit()


class UserGroupsDB:
    def __init__(self):
        os.makedirs(DB_PATH, exist_ok=True)
    
    async def init_db(self) -> None:
        async with aiosqlite.connect(USER_GROUPS_DB) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_groups (
                    user_id TEXT PRIMARY KEY,
                    groups_data TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_joined_groups (
                    user_id TEXT PRIMARY KEY,
                    joined_groups TEXT NOT NULL
                )
            ''')
            await db.commit()
    
    async def add_group(self, user_id: str, group_data: Dict[str, Any]) -> bool:
        try:
            groups = await self.get_groups(user_id)
            group_id = group_data.get('id')
            if not group_id:
                return False
            
            groups[group_id] = group_data
            await self._save_groups(user_id, groups)
            return True
        except Exception as e:
            Log.error(f"Failed to add user group: {e}")
            return False
    
    async def remove_group(self, user_id: str, group_id: str) -> bool:
        try:
            groups = await self.get_groups(user_id)
            if group_id in groups:
                del groups[group_id]
                await self._save_groups(user_id, groups)
                return True
            return False
        except Exception as e:
            Log.error(f"Failed to remove user group: {e}")
            return False
    
    async def update_group(self, user_id: str, group_id: str, group_data: Dict[str, Any]) -> bool:
        try:
            groups = await self.get_groups(user_id)
            if group_id in groups:
                groups[group_id].update(group_data)
                await self._save_groups(user_id, groups)
                return True
            return False
        except Exception as e:
            Log.error(f"Failed to update user group: {e}")
            return False
    
    async def get_groups(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        try:
            async with aiosqlite.connect(USER_GROUPS_DB) as db:
                cursor = await db.execute('SELECT groups_data FROM user_groups WHERE user_id = ?', (user_id,))
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return {}
        except Exception as e:
            Log.error(f"Failed to get user groups: {e}")
            return {}
    
    async def get_group(self, user_id: str, group_id: str) -> Optional[Dict[str, Any]]:
        groups = await self.get_groups(user_id)
        return groups.get(group_id)
    
    async def cache_joined(self, user_id: str, joined_groups: List[Dict[str, Any]]) -> bool:
        try:
            filtered_groups = [self.filter(group) for group in joined_groups]
            async with aiosqlite.connect(USER_GROUPS_DB) as db:
                await db.execute(
                    'INSERT OR REPLACE INTO user_joined_groups (user_id, joined_groups) VALUES (?, ?)',
                    (user_id, json.dumps(filtered_groups))
                )
                await db.commit()
            return True
        except Exception as e:
            Log.error(f"Failed to cache joined groups: {e}")
            return False
    
    async def get_joined(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            async with aiosqlite.connect(USER_GROUPS_DB) as db:
                cursor = await db.execute('SELECT joined_groups FROM user_joined_groups WHERE user_id = ?', (user_id,))
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return []
        except Exception as e:
            Log.error(f"Failed to get joined groups: {e}")
            return []
    
    async def clear_joined(self, user_id: str) -> bool:
        try:
            async with aiosqlite.connect(USER_GROUPS_DB) as db:
                await db.execute('DELETE FROM user_joined_groups WHERE user_id = ?', (user_id,))
                await db.commit()
            return True
        except Exception as e:
            Log.error(f"Failed to clear joined groups: {e}")
            return False
    
    async def _save_groups(self, user_id: str, groups: Dict[str, Dict[str, Any]]) -> None:
        async with aiosqlite.connect(USER_GROUPS_DB) as db:
            await db.execute(
                'INSERT OR REPLACE INTO user_groups (user_id, groups_data) VALUES (?, ?)',
                (user_id, json.dumps(groups))
            )
            await db.commit()