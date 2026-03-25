import json
import os

from pathlib import Path

class UserConfig:
    """用户配置类"""

    # 配置文件路径
    CONFIG_FILE = "./config/UserConfig.json"

    # 配置项目
    CONFIG_SELECTED_DIR = "selectedDir"

    CONFIG_TARGET = "target"

    CONFIG_LOG_LEVEL = "logLevel"
    LOG_LEVELS = ["endpoint", "error", "warning", "info", "debug"]

    CONFIG_HASH_LIST = "hash"
    CONFIG_MD5    = "md5"
    CONFIG_BLAKE3 = "blake3"
    CONFIG_XXH3   = "xxh3"

    # 配置值
    selected_dir = None
    targets = [ "Tread XP" ]
    target = "Tread XP"
    log_level = "info"

    md5_state = False
    blake3_state = False
    xxh3_state = True

    def load_config(self):
        """加载配置文件，恢复勾选框状态"""
        folder_path = Path(r'./config')
        self.targets = [p.name for p in folder_path.iterdir() if p.is_dir()]
        try:
            if os.path.exists(UserConfig.CONFIG_FILE):
                with open(UserConfig.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                    self.selected_dir = config.get(UserConfig.CONFIG_SELECTED_DIR)
                    self.target = config.get(UserConfig.CONFIG_TARGET, "Tread XP")
                    self.log_level = config.get(UserConfig.CONFIG_LOG_LEVEL, "info").lower()

                    hash_config = config.get(UserConfig.CONFIG_HASH_LIST, {})

                    self.md5_state = hash_config.get(UserConfig.CONFIG_MD5, False)
                    self.blake3_state = hash_config.get(UserConfig.CONFIG_BLAKE3, False)
                    self.xxh3_state = hash_config.get(UserConfig.CONFIG_XXH3, True)
        except Exception as e:
            # 配置文件读取失败，使用默认值（已在UI中设置）
            print(f"读取配置文件失败：{str(e)}")

    def select_dir(self, selected_dir: str):
        """更改目标目录"""
        self.selected_dir = selected_dir

    def set_target(self, new_target: str):
        """更改目标平台"""
        self.target = new_target

    def set_log_level(self, level: str):
        """设置日志级别"""
        if level in UserConfig.LOG_LEVELS:
            self.log_level = level
    
    def set_md5_state(self, state: bool):
        """设置MD5勾选框状态"""
        self.md5_state = state

    def set_blake3_state(self, state: bool):
        """设置Blake3勾选框状态"""
        self.blake3_state = state

    def set_xxh3_state(self, state: bool):
        """设置XXH3勾选框状态"""
        self.xxh3_state = state

    def save_config(self):
        """保存勾选框状态到配置文件"""
        try:
            config = {
                UserConfig.CONFIG_SELECTED_DIR: self.selected_dir,
                UserConfig.CONFIG_TARGET: self.target,
                UserConfig.CONFIG_LOG_LEVEL: self.log_level,
                UserConfig.CONFIG_HASH_LIST: {
                    UserConfig.CONFIG_MD5: self.md5_state,
                    UserConfig.CONFIG_BLAKE3: self.blake3_state,
                    UserConfig.CONFIG_XXH3: self.xxh3_state
                }
            }
            with open(UserConfig.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败：{str(e)}")