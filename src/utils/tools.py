import os
import json
from datetime import timedelta
from typing import Dict, Optional

class TimeUtils:
    """时间处理工具类"""

    @staticmethod
    def human_readable_seconds(seconds: float) -> str:
        if seconds < 0:
            return "-" + TimeUtils.human_readable_seconds(-seconds)
        
        # 处理整数部分
        td = timedelta(seconds=int(seconds))
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs_int = divmod(remainder, 60)

        # 小数部分
        frac = seconds - int(seconds)
        secs = secs_int + frac

        parts = []

        # 天、小时、分的显示规则：有值就显示
        if days:
            parts.append(f"{days}天")
        if hours:
            parts.append(f"{hours}小时")
        if minutes:
            parts.append(f"{minutes}分")

        # 秒的显示规则：
        # 1. 如果前面没有任何单位（纯秒），必须显示秒
        # 2. 如果前面有单位，只有当秒不为0时才显示
        if not parts or secs != 0:
            if secs == int(secs):
                sec_str = str(int(secs))
            else:
                # 保留最3位小数
                sec_str = f"{secs:.3f}"
            parts.append(f"{sec_str}秒")

        if not parts:
            return "0秒"

        return "".join(parts)

class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def check_exist(directory: str, name: str) -> bool:
        """检查目标是否存在"""
        path = os.path.join(directory, name)
        return os.path.isdir(path)

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小为人类可读形式"""
        if size_bytes < 0:
            return "-" + FileUtils.format_size(-size_bytes)
        elif size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        index = 0
        size = float(size_bytes)

        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1

        if size == int(size):
            size_str = str(int(size))
        else:
            size_str = f"{size:.2f}"

        return f"{size_str} {units[index]}"
    
class JsonUtils:
    """JSON处理工具类"""

    @staticmethod
    def load_json(json_file_path: str) -> Optional[Dict]:
        """加载JSON文件"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return data
    
    @staticmethod
    def save_json(json_file_path: str, data: Dict) -> bool:
        """保存JSON文件，失败时返回 False"""
        try:
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return False
        return True

class HashTool:
    """哈希计算工具类"""

    @staticmethod
    def calculate_md5(file_path: str) -> Optional[str]:
        """计算文件的MD5值"""
        try:
            import hashlib
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return None
        
    @staticmethod
    def calculate_blake3(file_path: str) -> Optional[str]:
        """计算文件的Blake3值"""
        try:
            import blake3
            hasher = blake3.blake3()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return None
    
    @staticmethod
    def calculate_xxh3(file_path: str) -> Optional[str]:
        """计算文件的XXH3值"""
        try:
            import xxhash
            hasher = xxhash.xxh3_64()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return None