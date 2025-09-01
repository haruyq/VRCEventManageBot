import json
import os

from utils.core import DATA_DIR
from utils.logger import Logger

Log = Logger()

class SelectedStore:
    @classmethod
    def save_selected(guild_id, group_id: str):
        try:
            if os.path.exists(f"{DATA_DIR}/selected_groups.json"):
                with open(f"{DATA_DIR}/selected_groups.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}

            data[str(guild_id)] = group_id

            with open(f"{DATA_DIR}/selected_groups.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            Log.error(f"選択されたグループの保存失敗: {e}")
            return False

    @classmethod
    def save_selected_role(cls, guild_id: int, role_id: str, group_id: str) -> bool:
        try:
            key = f"selected_role_{guild_id}_{role_id}"
            with open(f"{DATA_DIR}/{key}.json", "w", encoding="utf-8") as f:
                json.dump({"group_id": group_id}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            Log.error(f"Failed to save selected role group: {e}")
            return False

    @classmethod
    def load_selected_role(cls, guild_id: int, role_id: str) -> str | None:
        try:
            key = f"selected_role_{guild_id}_{role_id}"
            with open(f"{DATA_DIR}/{key}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("group_id")
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        except Exception as e:
            Log.error(f"Failed to load selected role group: {e}")
            return None

    @classmethod
    def remove_selected_role(cls, guild_id: int, role_id: str) -> bool:
        try:
            key = f"selected_role_{guild_id}_{role_id}"
            file_path = f"{DATA_DIR}/{key}.json"
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            Log.error(f"Failed to remove selected role group: {e}")
            return False