import json
import os

from log import Logger

class DirConfig:
    """目录配置类"""

    config = {}

    def load(self, target = "Tread XP"):
        """加载目录配置"""
        try:
            # 配置文件路径
            path = f"./config/{target}/Dirs.json"
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            Logger.error(f"读取目录配置文件{path}失败：{str(e)}")