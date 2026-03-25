import json
import os

from log import Logger

class TreeConfig:
    """树视图配置类"""

    # 配置文件路径
    config_file_path = "./config/Tread XP/JsonTree.json"
    config = {}

    def load(self, target = "Tread XP"):
        """加载树视图配置"""
        try:
            self.config_file_path = f"./config/{target}/JsonTree.json"
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            Logger.error(f"读取树视图配置文件{self.config_file_path}失败：{str(e)}")

    def load_config_from_name(self, name: str):
        """根据文件类型加载对应的文件列表配置"""
        return self.config.get(name, None)
    
    def load_file_list_by_tree_node_array(self, dir: str, json_data, tree_node_array, file_list: list) -> bool:
        for tree_node in tree_node_array:
            if not self._load_file_list_by_tree_node(dir, json_data, tree_node, file_list):
                return False
        return True
    
    def _load_file_list_by_tree_node(self, dir: str, json_data, tree_node, file_list: list) -> bool:
        if tree_node["type"] == "array":
            # 此时sub_json_data是一个array
            sub_json_data = json_data[tree_node['key']]
            if not isinstance(sub_json_data, list):
                Logger.error(f"树视图配置文件{self.config_file_path}配置错误：{tree_node['key']}不是{tree_node['type']}类型")
                return False

            # 遍历处理sub_json_data每个子节点的每个属性
            for sub_json_data_item in sub_json_data:
                for sub_tree_node in tree_node["child"]:
                    # 递归处理子节点
                    if not self._load_file_list_by_tree_node(dir, sub_json_data_item, sub_tree_node, file_list):
                        return False
        elif tree_node["type"] == "obj":
            # 此时sub_json_data是一个object
            sub_json_data = json_data[tree_node['key']]
            if not sub_json_data:
                Logger.error(f"在配置中解析对象的{tree_node['key']}失败：{str(json_data)}")
                return False
            if not isinstance(sub_json_data, dict):
                Logger.error(f"树视图配置文件{self.config_file_path}配置错误：{tree_node['key']}不是{tree_node['type']}类型")
                return False

            # 遍历处理sub_json_data每个属性
            for sub_tree_node in tree_node["child"]:
                # 递归处理子节点
                if not self._load_file_list_by_tree_node(dir, sub_json_data, sub_tree_node, file_list):
                    return False
        else:
            # 处理文件类型节点
            if not self._load_filename_by_file_tree_node(dir, json_data[tree_node['key']], tree_node, file_list):
                return False
        return True

    def _load_filename_by_file_tree_node(self, dir, json_value, tree_node, file_list: list) -> bool:
        if tree_node["type"] == "origin":
            # 直接使用value作为文件名
            filename = json_value
        elif tree_node["type"] == "path":
            # 解析文件路径获取文件名
            filename = os.path.basename(json_value)
        elif tree_node["type"] == "url":
            # 解析URL获取文件名
            tmp1 = json_value.split('/')[-1]
            filename = tmp1.split('?')[0]
        elif tree_node["type"] == "url-param":
            param_name = tree_node['param']
            # 解析URL中的get参数获取文件名
            tmp1 = json_value.split('?')[1]
            tmp2 = tmp1.split(f'{param_name}=')[1]
            filename = tmp2.split('&')[0]
        else:
            # 未支持的文件名解析类型，报错
            Logger.error(f"树视图配置文件{self.config_file_path}中发现未支持的文件名解析类型：{tree_node['type']}")
            return False
        
        # 检查文件名是否为空
        if not filename:
            Logger.error(f"在配置中解析文件名失败：{str(json_value)}")
            return False
        
        # 是否需要添加文件后缀
        if tree_node.get("suffix"):
            filename += f".{tree_node['suffix']}"

        # 检查file_list是否已有该文件，去重
        if filename in file_list:
            Logger.debug(f"配置的文件重复，忽略：{filename}")
            return True
        
        # 记录文件
        file_list.append(filename)
        Logger.debug(f"加入列表 - 文件名：{filename}")
        return True