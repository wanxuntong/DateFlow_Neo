#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理器模块
负责管理系统配置、用户偏好以及人员信息
"""

import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ConfigManager")

class ConfigGroup:
    """配置分组类，用于组织相关配置"""
    
    def __init__(self, name: str, title: str, icon: str = None, description: str = None):
        """
        初始化配置分组
        
        参数:
            name: 分组名称（唯一标识）
            title: 分组显示标题
            icon: 分组图标
            description: 分组描述
        """
        self.name = name
        self.title = title
        self.icon = icon
        self.description = description
        self.items = {}
        
    def to_dict(self) -> dict:
        """将配置分组转换为字典"""
        return {
            "name": self.name,
            "title": self.title,
            "icon": self.icon,
            "description": self.description,
            "items": self.items
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'ConfigGroup':
        """从字典创建配置分组"""
        group = cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            icon=data.get("icon"),
            description=data.get("description")
        )
        group.items = data.get("items", {})
        return group

class ConfigManager:
    """配置管理器类，负责管理系统设置和配置"""
    
    CONFIG_VERSION = "1.1.0"  # 配置版本号
    
    def __init__(self, config_dir=None):
        """
        初始化配置管理器
        
        参数:
            config_dir: 配置文件目录，默认为None，将使用默认路径
        """
        # 设置配置文件目录
        if config_dir is None:
            # 默认配置目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_dir = os.path.join(base_dir, 'data', 'config')
        else:
            self.config_dir = config_dir
            
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 配置文件路径
        self.system_config_file = os.path.join(self.config_dir, 'system.json')
        self.user_config_file = os.path.join(self.config_dir, 'user.json')
        self.people_file = os.path.join(self.config_dir, 'people.json')
        self.locations_file = os.path.join(self.config_dir, 'locations.json')
        self.ui_config_file = os.path.join(self.config_dir, 'ui_config.json')
        self.plugin_config_file = os.path.join(self.config_dir, 'plugin_config.json')
        
        # 加载配置
        self.system_config = self.load_config(self.system_config_file, self.get_default_system_config())
        self.user_config = self.load_config(self.user_config_file, self.get_default_user_config())
        self.people = self.load_config(self.people_file, [])
        self.locations = self.load_config(self.locations_file, [])
        self.ui_config = self.load_config(self.ui_config_file, self.get_default_ui_config())
        self.plugin_config = self.load_config(self.plugin_config_file, {})
        
        # 配置分组
        self.config_groups = self.init_config_groups()
        
        # 注册的配置回调函数
        self.config_callbacks = {}
        
    def init_config_groups(self) -> Dict[str, ConfigGroup]:
        """初始化配置分组"""
        groups = {}
        
        # 系统设置分组
        system_group = ConfigGroup(
            name="system",
            title="系统设置",
            icon="SystemSettingsOutline",
            description="系统级配置项，包括备份和日志设置"
        )
        system_group.items = self.system_config
        groups["system"] = system_group
        
        # 用户偏好分组
        user_group = ConfigGroup(
            name="user",
            title="用户偏好",
            icon="PersonEditOutline",
            description="用户个性化设置，包括主题和语言"
        )
        user_group.items = self.user_config
        groups["user"] = user_group
        
        # 日期管理分组
        date_group = ConfigGroup(
            name="date",
            title="日期管理",
            icon="CalendarOutline",
            description="日期相关设置，包括工作日和日历显示"
        )
        date_group.items = {
            "week_start_day": 0,  # 0=周一, 6=周日
            "work_days": self.user_config["work_days"],
            "work_hours": self.user_config["work_hours"],
            "date_format": "YYYY-MM-DD",
            "time_format": "HH:mm",
            "reminder_advance_minutes": self.user_config["reminder_advance_minutes"],
            "timezone": "Asia/Shanghai",
            "enable_reminders": True,
            "show_week_numbers": True,
            "highlight_holidays": True,
            "holidays": []  # 假日列表
        }
        groups["date"] = date_group
        
        # 界面设置分组
        ui_group = ConfigGroup(
            name="ui",
            title="界面设置",
            icon="DesktopMacOutline",
            description="用户界面外观和行为设置"
        )
        ui_group.items = self.ui_config
        groups["ui"] = ui_group
        
        # 流程图设置分组
        flow_group = ConfigGroup(
            name="flow",
            title="流程图设置",
            icon="FlowOutline",
            description="流程图视图相关的设置"
        )
        flow_group.items = {
            "default_layout": "层次布局",  # 默认布局方式
            "node_spacing": 50,  # 节点间距
            "level_spacing": 100,  # 层级间距
            "auto_layout": True,  # 自动布局
            "show_task_details": True,  # 显示任务详情
            "animation_speed": 300,  # 动画速度(毫秒)
            "connection_style": "贝塞尔曲线",  # 连接线样式
            "enable_drag_drop": True,  # 允许拖放
            "snap_to_grid": True,  # 对齐网格
            "grid_size": 10,  # 网格大小
            "show_grid": False,  # 显示网格
            "node_width": 200,  # 节点宽度
            "node_height": 80  # 节点高度
        }
        groups["flow"] = flow_group
        
        return groups
    
    def get_default_system_config(self) -> Dict[str, Any]:
        """获取默认系统配置"""
        return {
            "config_version": self.CONFIG_VERSION,
            "data_dir": os.path.join(os.path.dirname(self.config_dir), 'data'),
            "backup_dir": os.path.join(os.path.dirname(self.config_dir), 'backup'),
            "backup_interval_days": 7,
            "keep_backups_count": 10,
            "log_level": "INFO",
            "auto_save_interval_minutes": 5,
            "auto_update_check": True,
            "show_welcome": True,
            "plugins_dir": os.path.join(os.path.dirname(os.path.dirname(self.config_dir)), 'plugins'),
            "enabled_plugins": ["demo_plugin"],  # 默认启用的插件
            "minimize_to_tray": True  # 关闭窗口时最小化到托盘
        }
    
    def get_default_user_config(self) -> Dict[str, Any]:
        """获取默认用户配置"""
        return {
            "theme": "auto",  # auto, light, dark
            "language": "zh_CN",
            "start_view": "calendar",  # calendar, gantt, flow
            "work_days": [0, 1, 2, 3, 4],  # 0=周一，6=周日
            "work_hours": {"start": "09:00", "end": "18:00"},
            "reminder_advance_minutes": 15,
            "show_completed_tasks": True,
            "default_task_duration_hours": 1,
            "auto_save_interval_minutes": 5,
            "task_priority_colors": {
                "低": "#4CAF50",  # 绿色
                "中": "#2196F3",  # 蓝色
                "高": "#FF9800",  # 橙色
                "紧急": "#F44336"  # 红色
            },
            "default_priority": "中"
        }
    
    def get_default_ui_config(self) -> Dict[str, Any]:
        """获取默认UI配置"""
        return {
            "sidebar_width": 220,
            "compact_mode": False,
            "animation_speed": "normal",  # slow, normal, fast, none
            "use_system_accent_color": True,
            "accent_color": "#0078D7", 
            "icon_size": "medium",  # small, medium, large
            "font_family": "Microsoft YaHei",
            "font_size": 9,
            "enable_tooltips": True,
            "show_statusbar": True,
            "toolbar_style": "标准",  # 标准, 紧凑, 文本
            "show_toolbar_text": True,
            "window_state": {
                "maximized": False,
                "width": 1024,
                "height": 768,
                "x": 100,
                "y": 100
            }
        }
        
    def load_config(self, config_file, default_config):
        """从文件加载配置
        
        Args:
            config_file: 配置文件路径
            default_config: 默认配置
            
        Returns:
            dict: 加载的配置
        """
        try:
            if not os.path.exists(config_file):
                # 如果文件不存在，创建默认配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                return default_config
            
            # 读取配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # 处理配置升级（如果默认配置有新增项）
            if isinstance(default_config, dict) and isinstance(loaded_config, dict):
                # 合并配置，确保新字段被添加
                merged_config = default_config.copy()
                merged_config.update(loaded_config)
                
                # 检查是否有新增字段
                if len(merged_config) > len(loaded_config):
                    # 保存更新后的配置
                    self.save_config(config_file, merged_config)
                    return merged_config
                
                return loaded_config
            else:
                # 对于列表类型的配置，直接返回
                return loaded_config
                
        except Exception as e:
            logger.error(f"加载配置出错: {e}")
            # 返回默认配置
            return default_config
    
    def save_config(self, config_file, config_data):
        """保存配置到文件
        
        Args:
            config_file: 配置文件路径
            config_data: 配置数据
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"保存配置出错: {e}")
            return False
    
    def save_system_config(self):
        """保存系统配置"""
        return self.save_config(self.system_config_file, self.system_config)
    
    def save_user_config(self):
        """保存用户配置"""
        return self.save_config(self.user_config_file, self.user_config)
    
    def save_people(self):
        """保存人员列表"""
        return self.save_config(self.people_file, self.people)
    
    def save_locations(self):
        """保存地点列表"""
        return self.save_config(self.locations_file, self.locations)
        
    def save_ui_config(self):
        """保存UI配置"""
        return self.save_config(self.ui_config_file, self.ui_config)
        
    def save_plugin_config(self):
        """保存插件配置"""
        return self.save_config(self.plugin_config_file, self.plugin_config)
        
    def save_config_group(self, group_name: str) -> bool:
        """保存指定的配置分组
        
        Args:
            group_name: 配置分组名称
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        if group_name not in self.config_groups:
            logger.error(f"未找到配置分组: {group_name}")
            return False
            
        group = self.config_groups[group_name]
        
        # 根据分组类型保存到对应的配置文件
        if group_name == "system":
            self.system_config = group.items
            return self.save_system_config()
        elif group_name == "user":
            self.user_config = group.items
            return self.save_user_config()
        elif group_name == "ui":
            self.ui_config = group.items
            return self.save_ui_config()
        elif group_name == "date":
            # 更新用户配置中的相关项
            self.user_config["work_days"] = group.items["work_days"]
            self.user_config["work_hours"] = group.items["work_hours"]
            self.user_config["reminder_advance_minutes"] = group.items["reminder_advance_minutes"]
            # 保存日期配置
            date_config_file = os.path.join(self.config_dir, 'date_config.json')
            return self.save_config(date_config_file, group.items) and self.save_user_config()
        elif group_name == "flow":
            # 保存流程图配置
            flow_config_file = os.path.join(self.config_dir, 'flow_config.json')
            return self.save_config(flow_config_file, group.items)
        else:
            # 自定义分组，保存到单独的文件
            custom_config_file = os.path.join(self.config_dir, f'{group_name}_config.json')
            return self.save_config(custom_config_file, group.items)
    
    def get_config_value(self, group_name: str, key: str, default=None) -> Any:
        """获取配置项的值
        
        Args:
            group_name: 配置分组名称
            key: 配置项键名
            default: 默认值，当配置项不存在时返回
            
        Returns:
            Any: 配置项的值
        """
        if group_name not in self.config_groups:
            logger.warning(f"未找到配置分组: {group_name}")
            return default
            
        group = self.config_groups[group_name]
        return group.items.get(key, default)
        
    def has_config_group(self, group_name: str) -> bool:
        """检查配置分组是否存在
        
        Args:
            group_name: 配置分组名称
            
        Returns:
            bool: 存在返回True，不存在返回False
        """
        return group_name in self.config_groups
        
    def set_config_value(self, group_name: str, key: str, value: Any) -> bool:
        """设置配置项的值
        
        Args:
            group_name: 配置分组名称
            key: 配置项键名
            value: 配置项的值
            
        Returns:
            bool: 设置成功返回True，失败返回False
        """
        if group_name not in self.config_groups:
            # 如果分组不存在则创建一个新分组
            logger.info(f"创建新的配置分组: {group_name}")
            self.config_groups[group_name] = ConfigGroup(
                name=group_name,
                title=group_name.capitalize(),
                description=f"自动创建的{group_name}配置分组"
            )
        
        group = self.config_groups[group_name]
        old_value = group.items.get(key)
        
        # 更新配置项
        group.items[key] = value
        
        # 调用回调函数(如果存在)
        callback_key = f"{group_name}.{key}"
        if callback_key in self.config_callbacks:
            for callback in self.config_callbacks[callback_key]:
                try:
                    callback(value, old_value)
                except Exception as e:
                    logger.error(f"配置回调函数执行出错: {e}")
        
        # 保存配置
        return self.save_config_group(group_name)
        
    def register_config_callback(self, group_name: str, key: str, callback: Callable[[Any, Any], None]) -> bool:
        """注册配置项变更回调函数
        
        Args:
            group_name: 配置分组名称
            key: 配置项键名
            callback: 回调函数，接收两个参数(新值, 旧值)
            
        Returns:
            bool: 注册成功返回True，失败返回False
        """
        if group_name not in self.config_groups:
            logger.warning(f"未找到配置分组: {group_name}")
            return False
            
        callback_key = f"{group_name}.{key}"
        if callback_key not in self.config_callbacks:
            self.config_callbacks[callback_key] = []
            
        self.config_callbacks[callback_key].append(callback)
        return True
        
    def unregister_config_callback(self, group_name: str, key: str, callback: Callable[[Any, Any], None]) -> bool:
        """取消注册配置项变更回调函数
        
        Args:
            group_name: 配置分组名称
            key: 配置项键名
            callback: 回调函数
            
        Returns:
            bool: 取消注册成功返回True，失败返回False
        """
        callback_key = f"{group_name}.{key}"
        if callback_key not in self.config_callbacks:
            return False
            
        if callback in self.config_callbacks[callback_key]:
            self.config_callbacks[callback_key].remove(callback)
            return True
            
        return False
    
    def add_person(self, person_data):
        """添加人员
        
        Args:
            person_data: 人员数据字典，必须包含id和name字段
            
        Returns:
            bool: 添加成功返回True，失败返回False
        """
        try:
            if not isinstance(person_data, dict):
                logger.error("人员数据必须是字典类型")
                return False
                
            if 'id' not in person_data or 'name' not in person_data:
                logger.error("人员数据必须包含id和name字段")
                return False
            
            # 检查是否已存在相同ID
            for person in self.people:
                if person.get('id') == person_data['id']:
                    logger.warning(f"已存在ID为{person_data['id']}的人员")
                    return False
            
            # 添加人员
            self.people.append(person_data)
            
            # 保存到文件
            return self.save_people()
        except Exception as e:
            logger.error(f"添加人员出错: {e}")
            return False
    
    def update_person(self, person_data):
        """更新人员信息
        
        Args:
            person_data: 人员数据字典，必须包含id字段
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            if not isinstance(person_data, dict) or 'id' not in person_data:
                logger.error("无效的人员数据")
                return False
            
            # 查找人员
            for i, person in enumerate(self.people):
                if person.get('id') == person_data['id']:
                    # 更新人员数据
                    self.people[i] = person_data
                    
                    # 保存到文件
                    return self.save_people()
            
            logger.warning(f"未找到ID为{person_data['id']}的人员")
            return False
        except Exception as e:
            logger.error(f"更新人员出错: {e}")
            return False
    
    def delete_person(self, person_id):
        """删除人员
        
        Args:
            person_id: 人员ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            # 查找人员
            for i, person in enumerate(self.people):
                if person.get('id') == person_id:
                    # 删除人员
                    del self.people[i]
                    
                    # 保存到文件
                    return self.save_people()
            
            logger.warning(f"未找到ID为{person_id}的人员")
            return False
        except Exception as e:
            logger.error(f"删除人员出错: {e}")
            return False
    
    def get_person(self, person_id):
        """获取人员信息
        
        Args:
            person_id: 人员ID
            
        Returns:
            dict: 人员信息，如未找到则返回None
        """
        for person in self.people:
            if person.get('id') == person_id:
                return person
        return None
    
    def get_all_people(self):
        """获取所有人员
        
        Returns:
            list: 人员列表
        """
        return self.people
    
    def add_location(self, location_data):
        """添加地点
        
        Args:
            location_data: 地点数据字典，必须包含id和name字段
            
        Returns:
            bool: 添加成功返回True，失败返回False
        """
        try:
            if not isinstance(location_data, dict):
                logger.error("地点数据必须是字典类型")
                return False
                
            if 'id' not in location_data or 'name' not in location_data:
                logger.error("地点数据必须包含id和name字段")
                return False
            
            # 检查是否已存在相同ID
            for location in self.locations:
                if location.get('id') == location_data['id']:
                    logger.warning(f"已存在ID为{location_data['id']}的地点")
                    return False
            
            # 添加地点
            self.locations.append(location_data)
            
            # 保存到文件
            return self.save_locations()
        except Exception as e:
            logger.error(f"添加地点出错: {e}")
            return False
    
    def update_location(self, location_data):
        """更新地点信息
        
        Args:
            location_data: 地点数据字典，必须包含id字段
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            if not isinstance(location_data, dict) or 'id' not in location_data:
                logger.error("无效的地点数据")
                return False
            
            # 查找地点
            for i, location in enumerate(self.locations):
                if location.get('id') == location_data['id']:
                    # 更新地点数据
                    self.locations[i] = location_data
                    
                    # 保存到文件
                    return self.save_locations()
            
            logger.warning(f"未找到ID为{location_data['id']}的地点")
            return False
        except Exception as e:
            logger.error(f"更新地点出错: {e}")
            return False
    
    def delete_location(self, location_id):
        """删除地点
        
        Args:
            location_id: 地点ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            # 查找地点
            for i, location in enumerate(self.locations):
                if location.get('id') == location_id:
                    # 删除地点
                    del self.locations[i]
                    
                    # 保存到文件
                    return self.save_locations()
            
            logger.warning(f"未找到ID为{location_id}的地点")
            return False
        except Exception as e:
            logger.error(f"删除地点出错: {e}")
            return False
    
    def get_location(self, location_id):
        """获取地点信息
        
        Args:
            location_id: 地点ID
            
        Returns:
            dict: 地点信息，如未找到则返回None
        """
        for location in self.locations:
            if location.get('id') == location_id:
                return location
        return None
    
    def get_all_locations(self):
        """获取所有地点
        
        Returns:
            list: 地点列表
        """
        return self.locations
        
    def get_plugin_config(self, plugin_id, default=None):
        """
        获取插件配置
        
        参数:
            plugin_id: 插件ID
            default: 默认配置
            
        返回:
            插件配置字典
        """
        # 检查插件配置是否存在
        config_key = f"plugin_{plugin_id}"
        if config_key in self.plugin_config:
            return self.plugin_config[config_key]
        
        # 不存在则返回默认配置
        if default is None:
            default = {}
            
        # 设置默认配置
        self.plugin_config[config_key] = default
        return default
        
    def register_plugin(self, plugin_id, plugin_instance):
        """
        注册插件到配置管理器
        
        参数:
            plugin_id: 插件ID
            plugin_instance: 插件实例
            
        返回:
            bool: 注册成功返回True
        """
        # 记录插件到插件列表
        self.plugin_config.setdefault("plugins", {})
        self.plugin_config["plugins"][plugin_id] = {
            "id": plugin_id,
            "name": getattr(plugin_instance, "name", plugin_id),
            "version": getattr(plugin_instance, "version", "0.1.0"),
            "description": getattr(plugin_instance, "description", "")
        }
        
        # 初始化插件配置
        config_key = f"plugin_{plugin_id}"
        if config_key not in self.plugin_config:
            self.plugin_config[config_key] = {}
            
        return True
    
    def create_backup(self):
        """创建配置备份
        
        Returns:
            str: 备份文件路径，失败返回None
        """
        try:
            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(self.config_dir), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            now = datetime.now()
            backup_file = os.path.join(backup_dir, f'config_backup_{now.strftime("%Y%m%d_%H%M%S")}.zip')
            
            # 创建临时备份目录
            temp_dir = os.path.join(backup_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 复制配置文件到临时目录
            for file_name in os.listdir(self.config_dir):
                file_path = os.path.join(self.config_dir, file_name)
                if os.path.isfile(file_path) and file_name.endswith('.json'):
                    shutil.copy2(file_path, os.path.join(temp_dir, file_name))
            
            # 创建ZIP归档
            import zipfile
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_name in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file_name)
                    zipf.write(file_path, file_name)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 更新最后备份时间
            self.system_config['last_backup'] = now.isoformat()
            self.save_system_config()
            
            # 清理旧备份
            self.cleanup_backups(self.system_config['backup_count'])
            
            return backup_file
        except Exception as e:
            logger.error(f"创建备份出错: {e}")
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None
    
    def cleanup_backups(self, keep_count):
        """清理旧备份，只保留指定数量的最新备份
        
        Args:
            keep_count: 保留的备份数量
            
        Returns:
            bool: 清理成功返回True，失败返回False
        """
        try:
            backup_dir = os.path.join(os.path.dirname(self.config_dir), 'backups')
            
            if not os.path.exists(backup_dir):
                return True
            
            # 获取所有备份文件
            backup_files = []
            for file_name in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, file_name)
                if os.path.isfile(file_path) and file_name.startswith('config_backup_') and file_name.endswith('.zip'):
                    backup_files.append(file_path)
            
            # 按修改时间排序
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # 删除旧备份
            if len(backup_files) > keep_count:
                for file_path in backup_files[keep_count:]:
                    os.remove(file_path)
            
            return True
        except Exception as e:
            logger.error(f"清理备份出错: {e}")
            return False
    
    def restore_backup(self, backup_file):
        """还原配置备份
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 还原成功返回True，失败返回False
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 创建临时目录
            temp_dir = os.path.join(os.path.dirname(self.config_dir), 'temp_restore')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # 解压备份文件
            import zipfile
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 备份当前配置
            current_backup = self.create_backup()
            
            # 还原配置文件
            for file_name in os.listdir(temp_dir):
                src_file = os.path.join(temp_dir, file_name)
                dst_file = os.path.join(self.config_dir, file_name)
                
                if os.path.isfile(src_file) and file_name.endswith('.json'):
                    shutil.copy2(src_file, dst_file)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 重新加载配置
            self.system_config = self.load_config(self.system_config_file, self.get_default_system_config())
            self.user_config = self.load_config(self.user_config_file, self.get_default_user_config())
            self.people = self.load_config(self.people_file, [])
            self.locations = self.load_config(self.locations_file, [])
            self.ui_config = self.load_config(self.ui_config_file, self.get_default_ui_config())
            self.plugin_config = self.load_config(self.plugin_config_file, {})
            self.config_groups = self.init_config_groups()
            
            return True
        except Exception as e:
            logger.error(f"还原备份出错: {e}")
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False
            
    def reset_config(self, group_name: str = None) -> bool:
        """重置配置到默认值
        
        Args:
            group_name: 配置分组名称，None表示重置所有配置
            
        Returns:
            bool: 重置成功返回True，失败返回False
        """
        try:
            if group_name is None:
                # 重置所有配置
                self.system_config = self.get_default_system_config()
                self.save_system_config()
                
                self.user_config = self.get_default_user_config()
                self.save_user_config()
                
                self.ui_config = self.get_default_ui_config()
                self.save_ui_config()
                
                # 重新初始化配置分组
                self.config_groups = self.init_config_groups()
                
                return True
            elif group_name in self.config_groups:
                # 重置特定分组
                group = self.config_groups[group_name]
                
                if group_name == "system":
                    group.items = self.get_default_system_config()
                    self.system_config = group.items
                    return self.save_system_config()
                elif group_name == "user":
                    group.items = self.get_default_user_config()
                    self.user_config = group.items
                    return self.save_user_config()
                elif group_name == "ui":
                    group.items = self.get_default_ui_config()
                    self.ui_config = group.items
                    return self.save_ui_config()
                else:
                    # 其他分组使用默认值(由init_config_groups初始化)
                    default_groups = self.init_config_groups()
                    if group_name in default_groups:
                        self.config_groups[group_name].items = default_groups[group_name].items
                        return self.save_config_group(group_name)
                    
                return False
            else:
                logger.warning(f"未找到配置分组: {group_name}")
                return False
        except Exception as e:
            logger.error(f"重置配置出错: {e}")
            return False 
    
    def is_plugin_enabled(self, plugin_id: str) -> bool:
        """
        检查插件是否启用
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 插件启用返回True，否则返回False
        """
        enabled_plugins = self.get_config_value("system", "enabled_plugins", [])
        return plugin_id in enabled_plugins
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        启用插件
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 操作成功返回True，失败返回False
        """
        enabled_plugins = self.get_config_value("system", "enabled_plugins", [])
        if plugin_id not in enabled_plugins:
            enabled_plugins.append(plugin_id)
            self.set_config_value("system", "enabled_plugins", enabled_plugins)
            self.save_system_config()
            
            # 同时更新plugin组中的设置
            plugin_group_enabled = self.get_config_value("plugin", "enabled_plugins", [])
            if plugin_id not in plugin_group_enabled:
                plugin_group_enabled.append(plugin_id)
                self.set_config_value("plugin", "enabled_plugins", plugin_group_enabled)
                self.save_config_group("plugin")
                
            return True
        return False
        
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        禁用插件
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 操作成功返回True，失败返回False
        """
        enabled_plugins = self.get_config_value("system", "enabled_plugins", [])
        if plugin_id in enabled_plugins:
            enabled_plugins.remove(plugin_id)
            self.set_config_value("system", "enabled_plugins", enabled_plugins)
            self.save_system_config()
            
            # 同时更新plugin组中的设置
            plugin_group_enabled = self.get_config_value("plugin", "enabled_plugins", [])
            if plugin_id in plugin_group_enabled:
                plugin_group_enabled.remove(plugin_id)
                self.set_config_value("plugin", "enabled_plugins", plugin_group_enabled)
                self.save_config_group("plugin")
                
            return True
        return False