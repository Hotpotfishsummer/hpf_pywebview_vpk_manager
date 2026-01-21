"""用户偏好设置和数据持久化的存储服务"""

import json
from pathlib import Path
from typing import Any, Optional


class StorageService:
    """持久化用户偏好设置到本地存储的单例服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 在用户文稿目录中创建存储目录
        self._storage_dir = Path.home() / 'Documents' / 'L4D2-VPK-Manager'
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        # 存储文件路径
        self._storage_file = self._storage_dir / 'preferences.json'

        # 加载现有偏好设置
        self._preferences = self._load_preferences()

        self._initialized = True

    def _load_preferences(self) -> dict:
        """从存储文件加载偏好设置"""
        if not self._storage_file.exists():
            return {}

        try:
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载偏好设置出错: {e}")
            return {}

    def _save_preferences(self):
        """将偏好设置保存到存储文件"""
        try:
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存偏好设置出错: {e}")

    def set(self, key: str, value: Any):
        """设置偏好值"""
        self._preferences[key] = value
        self._save_preferences()
        print(f"StorageService.set: key='{key}', value='{value}'")

    def get(self, key: str, default: Any = None) -> Any:
        """获取偏好值"""
        return self._preferences.get(key, default)

    def remove(self, key: str):
        """移除偏好"""
        if key in self._preferences:
            del self._preferences[key]
            self._save_preferences()
            print(f"StorageService.remove: key='{key}'")

    def clear(self):
        """清除所有偏好"""
        self._preferences.clear()
        self._save_preferences()
        print("StorageService.clear: 所有偏好已清除")

    def get_l4d2_directory(self) -> Optional[str]:
        """获取保存的 L4D2 目录路径"""
        return self.get('l4d2_directory')

    def save_l4d2_directory(self, directory: str):
        """保存 L4D2 目录路径"""
        self.set('l4d2_directory', directory)
