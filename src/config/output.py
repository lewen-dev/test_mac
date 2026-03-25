import json
import os

from log import Logger

class OutputConfig:
    """输出配置类"""
    
    # 配置文件路径
    config_file_path = "./config/Tread XP/Output.json"
    config = {}

    def load(self, target = "Tread XP"):
        """加载输出配置"""
        try:
            self.config_file_path = f"./config/{target}/Output.json"
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            Logger.error(f"读取输出配置文件{self.config_file_path}失败：{str(e)}")
