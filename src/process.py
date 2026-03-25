
import os
import time
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from typing import List

from config.dirs import DirConfig
from config.json_tree import TreeConfig
from config.output import OutputConfig
from log import Logger
from utils.tools import TimeUtils, FileUtils, JsonUtils, HashTool

class ProcessThread(QThread):
    """后台处理线程"""
    finished_signal = Signal()
    
    def __init__(self, directory: str, target: str, break_on_error: bool, enable_md5: bool, enable_blake3: bool, enable_xxh3: bool):
        """初始化处理线程"""
        super().__init__()
        self.directory = directory
        self.target = target
        self.break_on_error = break_on_error
        self.dir_config = DirConfig()
        self.tree_config = TreeConfig()
        self.output_config = OutputConfig()
        self.found_dirs = {key: False for key in self.dir_config.config.keys()}
        self.enable_md5 = enable_md5
        self.enable_blake3 = enable_blake3
        self.enable_xxh3 = enable_xxh3
        self.start_time = None
        self.end_time = None
        
    def run(self):
        try:
            self.start_time = datetime.now()

            # 任务开始日志
            Logger.reset_log_file()
            enabled = [name for name, enabled in [
                ("MD5", self.enable_md5),
                ("Blake3", self.enable_blake3),
                ("XXH3", self.enable_xxh3)
            ] if enabled]
            start_log = (
                f"任务开始：已启用的校验 - [{'、'.join(enabled)}]。"
                if enabled else
                "任务开始：未启用校验。"
            )
            Logger.endpoint(start_log)

            # 加载目录配置, 检查所选目录中的目标目录是否存在
            stopped = False
            self.dir_config.load(self.target)
            for dir_name in self.dir_config.config.keys():
                self.found_dirs[dir_name] = FileUtils.check_exist(self.directory, dir_name)
                if not self.found_dirs[dir_name]:
                    # 任务中止，日志输出
                    if self.break_on_error:
                        stopped = True
                    Logger.error(f"所选目录中未找到目标：{dir_name}，请检查配置或目录后重试")
            
            # 目标目录全部存在才继续处理
            if not stopped:
                # 加载树视图配置
                self.tree_config.load(self.target)

                # 加载输出配置
                self.output_config.load(self.target)

                # 处理各个目录
                for dir_name in self.dir_config.config.keys():
                    if self.found_dirs[dir_name]:
                        if not self._process_directory(dir_name):
                            if self.break_on_error:
                                stopped = True
                            break

                # 任务结束后日志输出
                if not stopped:
                    self.end_time = datetime.now()
                    duration = (self.end_time - self.start_time).total_seconds()
                    Logger.endpoint(f"任务完成：总共消耗{TimeUtils.human_readable_seconds(duration)}")
        except Exception as e:
            Logger.error(f"发生错误：{str(e)}")
        finally:
            self.finished_signal.emit()
    
    def _process_directory(self, dir_name: str) -> bool:
        """处理目录（支持有子目录和无子目录的情况）
        
        Args:
            dir_name: 目录名称
        """
        config = self.dir_config.config[dir_name]
        dir_path = os.path.join(self.directory, dir_name).replace("\\", "/")
        
        # 区别处理有子目录和无子目录的情况
        if config['hasSubdirs']:
            return self._process_directory_with_subdirs(dir_path, dir_name, config)
        else:
            return self._process_directory_single(dir_path, dir_name, config)

    def _process_directory_with_subdirs(self, dir_path: str, dir_name: str, config: dict) -> bool:
        """处理有子目录的目录类型"""
        # 列取子目录
        try:
            subdirs = [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))]
        except OSError as e:
            Logger.error(f"在{dir_name}目录下列取子目录失败：{str(e)}")
            return
        
        # 确认是否有配置文件
        config_file_name = config.get('configFile')
        if config_file_name:
            # 加载目录应读配置
            dir_tree_config = self.tree_config.load_config_from_name(dir_name)
            if not dir_tree_config:
                Logger.error(f"未找到目录{dir_name}的树视图配置！")
                return False
        
        # 处理每个子目录
        for subdir in subdirs:
            subdir_path = os.path.join(dir_path, subdir).replace("\\", "/")
            if not self._process_dir_imp(dir_tree_config, self.output_config.config[dir_name], subdir_path, config_file_name):
                if self.break_on_error:
                    return False
        return True

    def _process_directory_single(self, dir_path: str, dir_name: str, config: dict):
        """处理单目录类型"""
        # 确认是否有配置文件
        dir_tree_config = None
        config_file_name = config.get('configFile')
        if config_file_name:
            # 加载目录应读配置
            dir_tree_config = self.tree_config.load_config_from_name(dir_name)
            if not dir_tree_config:
                Logger.error(f"未找到目录{dir_name}的树视图配置！")
                return False

        # 处理目录
        if not self._process_dir_imp(dir_tree_config, self.output_config.config[dir_name], dir_path, config_file_name):
            return False
        return True

    def _process_dir_imp(self, dir_tree_config, dir_output_config, dir_path: str, json_file_name: str) -> bool:
        """处理目录"""
        Logger.info(f"准备处理目录：{dir_path}")

        # 先删除目录中的FileChecksums.json文件
        json_checksum_path = os.path.join(dir_path, dir_output_config['file']).replace("\\", "/")
        if os.path.exists(json_checksum_path):
            os.remove(json_checksum_path)

        # 分别处理有配置文件和没有配置文件的情况
        if json_file_name:
            # 加载JSON文件
            json_file_path = os.path.join(dir_path, json_file_name)
            json_data = JsonUtils.load_json(json_file_path)
            if json_data is None:
                Logger.error(f"读取配置文件失败：{json_file_path}")
                return False

            # 遍历应读配置读取json配置中的fileList节点
            file_list: List[str] = [ json_file_name ]
            if not self.tree_config.load_file_list_by_tree_node_array(dir_path, json_data, dir_tree_config, file_list):
                # 中断处理，函数内已打印过错误日志
                return False

            # 检查所有文件存在性
            all_exists = True
            for filename in file_list:
                filepath = os.path.join(dir_path, filename)
                if not os.path.isfile(filepath):
                    # 中断处理并记录错误
                    Logger.error(f"在{dir_path}目录下未找到文件：{filename}")
                    all_exists = False
            
            if not all_exists:
                # 中断处理
                Logger.error(f"在{dir_path}目录下的检查结束，请补全未找到的文件。")
                return False
        else:
            # 遍历文件夹下的全部文件
            try:
                file_list = [d for d in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, d))]
            except OSError as e:
                Logger.error(f"在{dir_path}目录下获取文件列表失败：{str(e)}")
                return False

        # 开始计算所有文件的校验码
        checksum_list = []
        self._calculate_checksums(dir_path, file_list, checksum_list)

        # 构造FileChecksums.json内容
        checksum_json_data = {}
        checksum_json_data["path"] = json_checksum_path.replace(f'{self.directory}/', '')

        # 根据OutputConfig.json配置拷贝原配置数据
        copies = dir_output_config.get('copy')
        if copies:
            if json_file_name:
                self._copy_config(checksum_json_data, json_data, copies)
            else:
                # 中断处理
                Logger.error(f"请检查{dir_path}目录下的Output.json配置，没有在Dirs.json中配置可以Copy的configFile。")
                return False
        
        # 赋值checksum列表节点
        checksum_json_data[dir_output_config['node']] = checksum_list

        # 输出FileChecksums.json文件
        if not JsonUtils.save_json(json_checksum_path, checksum_json_data):
            Logger.error(f"在{dir_path}目录下保存配置文件失败!")
            return False
        return True
    
    def _copy_config(self, checksum_json_data, json_data, output_config_array):
        for item in output_config_array:
            key = item['key']
            dst = item.get('dst')
            children = item.get('child')
            if children:
                self._copy_config(checksum_json_data, json_data[key], children)
            elif dst:
                checksum_json_data[dst] = json_data[key]
            else:
                checksum_json_data[key] = json_data[key]

    def _calculate_checksums(self, dir_path: str, file_list: List[str], checksum_list: List[dict]) -> bool:
        """计算目录下所有文件的校验码"""
        for filename in file_list:
            filepath = os.path.join(dir_path, filename)
            
            try:
                file_size = os.path.getsize(filepath)
            except OSError as e:
                Logger.error(f"在{dir_path}目录下获取文件大小失败：{filename}: {str(e)}")
                return False

            file_entry = {
                "name": filename, 
                "size": file_size
            }
            
            # 记录每个计算方式的耗时
            timing_info = []
            
            # 根据勾选框计算相应的哈希值，并记录耗时
            if self.enable_md5:
                start_time = time.time()
                md5_hash = HashTool.calculate_md5(filepath)
                if md5_hash is None:
                    Logger.error(f"在{dir_path}目录下计算文件MD5值失败：{filename}")
                    return False
                else:
                    elapsed = time.time() - start_time
                    file_entry["md5"] = md5_hash
                    timing_info.append(f"MD5-{TimeUtils.human_readable_seconds(elapsed)}")
            
            if self.enable_blake3:
                start_time = time.time()
                blake3_hash = HashTool.calculate_blake3(filepath)
                if blake3_hash is None:
                    Logger.error(f"在{dir_path}目录下计算文件Blake3值失败：{filename}")
                    return False
                else:
                    elapsed = time.time() - start_time
                    file_entry["blake3"] = blake3_hash
                    timing_info.append(f"Blake3-{TimeUtils.human_readable_seconds(elapsed)}")
            
            if self.enable_xxh3:
                start_time = time.time()
                xxh3_hash = HashTool.calculate_xxh3(filepath)
                if xxh3_hash is None:
                    Logger.error(f"在{dir_path}目录下计算文件XXH3值失败：{filename}")
                    return False
                else:
                    elapsed = time.time() - start_time
                    file_entry["xxh3"] = xxh3_hash
                    timing_info.append(f"XXH3-{TimeUtils.human_readable_seconds(elapsed)}")
            
            # 打印文件处理信息和耗时信息
            if len(file_entry) > 2:  # name和size都有
                # 添加到结果列表
                checksum_list.append(file_entry)
                if timing_info:
                    timing_message = f"文件 {filename} - " + "，".join(timing_info)
                    Logger.info(timing_message)
        return True