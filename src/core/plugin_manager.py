#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于事件驱动的插件管理器
负责插件的发现、加载、初始化和事件管理
"""

import os
import sys
import logging
import importlib.util
import traceback
import json
import shutil
from typing import Dict, Any, List, Optional, Callable, Set, Union
from utils.logger import get_logger
import inspect

# 创建模块级别的日志记录器
logger = get_logger("PluginManager", module="core.plugin_manager")


class PluginEvent:
    """插件事件类，用于在事件分发时携带数据"""
    
    def __init__(self, event_type: str, data: Any = None):
        """
        初始化事件
        
        参数:
            event_type: 事件类型
            data: 事件携带的数据
        """
        self.event_type = event_type
        self.data = data
        self.prevented = False
        self.modified_data = None
        
    def prevent_default(self):
        """阻止事件的默认行为"""
        self.prevented = True
        
    def is_default_prevented(self) -> bool:
        """判断事件的默认行为是否被阻止"""
        return self.prevented
        
    def set_data(self, data: Any):
        """设置事件数据"""
        self.modified_data = data
        
    def get_data(self) -> Any:
        """获取事件数据（优先返回修改后的数据）"""
        if self.modified_data is not None:
            return self.modified_data
        return self.data


class PluginBase:
    """插件基类，所有插件都应该继承这个类"""
    
    def __init__(self, plugin_id: str, name: str, version: str, description: str):
        """
        初始化插件
        
        参数:
            plugin_id: 插件唯一标识
            name: 插件名称
            version: 插件版本
            description: 插件描述
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.config = {}
        self.enabled = True
        self._event_handlers = {}  # 事件处理函数映射
        
    def initialize(self, app_context: Any) -> bool:
        """
        初始化插件
        
        参数:
            app_context: 应用程序上下文，包含应用程序所需的各种管理器和对象
        
        返回:
            bool: 初始化成功返回True，失败返回False
        """
        return True
        
    def cleanup(self) -> bool:
        """
        清理插件资源
        
        返回:
            bool: 清理成功返回True，失败返回False
        """
        return True
    
    def register_event_handler(self, event_type: str, handler: Callable[[PluginEvent], None]):
        """
        注册事件处理函数
        
        参数:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def get_event_handlers(self, event_type: str) -> List[Callable[[PluginEvent], None]]:
        """
        获取特定事件类型的所有处理函数
        
        参数:
            event_type: 事件类型
            
        返回:
            List[Callable]: 处理函数列表
        """
        return self._event_handlers.get(event_type, [])
        
    def get_config_ui(self):
        """
        获取插件配置界面
        
        返回:
            QWidget: 配置界面组件，如无配置界面则返回None
        """
        return None
        
    def get_main_ui(self):
        """
        获取插件主界面
        
        返回:
            QWidget: 主界面组件，如无主界面则返回None
        """
        return None


class PluginManager:
    """事件驱动的插件管理器，负责加载和管理插件"""
    
    # 定义系统事件类型常量
    EVENT_APPLICATION_START = "application.start"         # 应用程序启动
    EVENT_APPLICATION_QUIT = "application.quit"           # 应用程序退出
    EVENT_TASK_CREATED = "task.created"                  # 任务创建
    EVENT_TASK_UPDATED = "task.updated"                  # 任务更新
    EVENT_TASK_DELETED = "task.deleted"                  # 任务删除
    EVENT_TASK_PAUSED = "task.paused"                    # 任务暂停
    EVENT_TASK_RESUMED = "task.resumed"                  # 任务恢复
    EVENT_VIEW_CHANGED = "view.changed"                  # 视图切换
    EVENT_SETTINGS_CHANGED = "settings.changed"          # 设置变更
    EVENT_PLUGIN_LOADED = "plugin.loaded"                # 插件加载
    EVENT_PLUGIN_UNLOADED = "plugin.unloaded"            # 插件卸载
    
    def __init__(self, config_manager=None):
        """
        初始化插件管理器
        
        参数:
            config_manager: 配置管理器实例，用于获取插件配置
        """
        self.config_manager = config_manager
        self.plugins = {}  # 已加载的插件实例，key为插件ID
        self.plugin_modules = {}  # 已加载的插件模块，key为插件ID
        
        # 计算相对于当前文件的基础目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
        
        # 设置插件目录
        if self.config_manager:
            # 首先尝试从配置获取
            plugin_directory = self.config_manager.get_config_value("system", "plugin_directory", "")
            plugins_dir = self.config_manager.get_config_value("system", "plugins_dir", "")
            
            # 使用配置中的路径，优先使用plugins_dir
            if plugins_dir:
                self.plugin_dir = plugins_dir
            elif plugin_directory:
                self.plugin_dir = plugin_directory
            else:
                # 使用默认相对路径
                self.plugin_dir = os.path.join(os.path.dirname(current_dir), 'plugins')
                
                # 更新配置
                self.config_manager.set_config_value("system", "plugins_dir", self.plugin_dir)
        else:
            # 默认插件目录
            self.plugin_dir = os.path.join(os.path.dirname(current_dir), 'plugins')
        
        # 确保插件目录存在
        os.makedirs(self.plugin_dir, exist_ok=True)
        logger.info(f"插件目录：{self.plugin_dir}")
        
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        发现所有可用的插件
        
        返回:
            List[Dict]: 插件信息列表
        """
        # 检查插件目录是否存在
        if not os.path.exists(self.plugin_dir):
            logger.error("插件目录不存在", plugin_dir=self.plugin_dir)
            os.makedirs(self.plugin_dir, exist_ok=True)
            return []
        
        plugins_info = []
        
        # 遍历插件目录中的所有文件夹
        for item in os.listdir(self.plugin_dir):
            try:
                plugin_dir = os.path.join(self.plugin_dir, item)
                
                # 忽略非目录项和特殊目录
                if not os.path.isdir(plugin_dir) or item.startswith("__") or item.startswith("."):
                    continue
                    
                # 读取插件信息
                plugin_info_path = os.path.join(plugin_dir, "plugin_info.json")
                
                if os.path.exists(plugin_info_path):
                    with open(plugin_info_path, "r", encoding="utf-8") as f:
                        plugin_info = json.load(f)
                        plugin_info["id"] = item  # 设置插件ID
                        plugins_info.append(plugin_info)
                else:
                    # 尝试从插件模块中读取信息
                    plugin_module = os.path.join(plugin_dir, "__init__.py")
                    if os.path.exists(plugin_module):
                        # 插件存在但信息不完整，创建基本信息
                        plugins_info.append({
                            "id": item,
                            "name": item,
                            "version": "未知",
                            "description": "无描述信息",
                            "author": "未知",
                            "requires": []
                        })
            except Exception as e:
                logger.error("读取插件信息出错", plugin=item, error=str(e))
        
        return plugins_info
        
    def load_plugin(self, plugin_id: str, app_context: Any = None) -> bool:
        """
        加载插件
        
        参数:
            plugin_id: 插件ID
            app_context: 应用程序上下文
            
        返回:
            bool: 加载成功返回True，失败返回False
        """
        # 检查插件是否已加载
        if plugin_id in self.plugins:
            logger.info("插件已加载", plugin_id=plugin_id)
            return True
        
        try:
            # 插件目录路径
            plugin_dir = os.path.join(self.plugin_dir, plugin_id)
            
            # 检查插件目录是否存在
            if not os.path.exists(plugin_dir):
                logger.error("插件目录不存在", plugin_dir=plugin_dir)
                return False
            
            # 检查插件入口文件是否存在
            plugin_init = os.path.join(plugin_dir, "__init__.py")
            if not os.path.exists(plugin_init):
                logger.error("插件入口文件不存在", plugin_id=plugin_id)
                return False
            
            # 导入插件模块
            module_name = f"plugins.{plugin_id}"
            module_spec = importlib.util.find_spec(module_name)
            
            if not module_spec:
                logger.error("无法加载插件规范", plugin_id=plugin_id)
                return False
            
            # 导入模块
            module = importlib.import_module(module_name)
            self.plugin_modules[plugin_id] = module
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    obj.__module__ == module.__name__ and 
                    issubclass(obj, PluginBase) and 
                    obj is not PluginBase):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error("未找到插件类", plugin_id=plugin_id)
                return False
            
            # 实例化插件
            plugin = plugin_class()
            
            # 初始化插件
            if app_context and not plugin.initialize(app_context):
                logger.error("插件初始化失败", plugin_id=plugin_id)
                return False
            
            # 将插件添加到管理器
            self.plugins[plugin_id] = plugin
            
            # 触发插件加载事件
            self.dispatch_event(self.EVENT_PLUGIN_LOADED, plugin)
            
            logger.info("成功加载插件", plugin_id=plugin_id)
            return True
            
        except Exception as e:
            logger.error("加载插件出错", plugin_id=plugin_id, error=str(e))
            logger.error(traceback.format_exc())
            return False
            
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 卸载成功返回True，失败返回False
        """
        # 检查插件是否已加载
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            logger.warning("插件未加载，无需卸载", plugin_id=plugin_id)
            return True
        
        try:
            # 调用插件清理方法
            plugin.cleanup()
            
            # 触发插件卸载事件
            self.dispatch_event(self.EVENT_PLUGIN_UNLOADED, plugin)
            
            # 从模块缓存中移除
            if f"plugins.{plugin_id}" in sys.modules:
                del sys.modules[f"plugins.{plugin_id}"]
            
            # 移除插件对象
            del self.plugins[plugin_id]
            if plugin_id in self.plugin_modules:
                del self.plugin_modules[plugin_id]
            
            logger.info("成功卸载插件", plugin_id=plugin_id)
            return True
            
        except Exception as e:
            logger.error("卸载插件出错", plugin_id=plugin_id, error=str(e))
            logger.error(traceback.format_exc())
            return False
            
    def reload_plugin(self, plugin_id: str, app_context: Any = None) -> bool:
        """
        重新加载插件
        
        参数:
            plugin_id: 插件ID
            app_context: 应用程序上下文
            
        返回:
            bool: 重载成功返回True，失败返回False
        """
        if self.unload_plugin(plugin_id):
            return self.load_plugin(plugin_id, app_context)
        return False
            
    def load_enabled_plugins(self, app_context: Any = None) -> Dict[str, bool]:
        """
        加载所有启用的插件
        
        参数:
            app_context: 应用程序上下文
            
        返回:
            Dict[str, bool]: 插件加载结果，key为插件ID，value为是否成功加载
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return {}
            
        # 获取已启用的插件列表
        enabled_plugins = self.config_manager.get_config_value("system", "enabled_plugins", [])
        if not enabled_plugins:
            logger.info("没有已启用的插件")
            return {}
            
        # 加载每个插件
        results = {}
        for plugin_id in enabled_plugins:
            results[plugin_id] = self.load_plugin(plugin_id, app_context)
            
        return results
    
    def dispatch_event(self, event_type: str, data: Any = None) -> PluginEvent:
        """
        分发事件到所有插件
        
        参数:
            event_type: 事件类型
            data: 事件数据
            
        返回:
            PluginEvent: 事件对象
        """
        event = PluginEvent(event_type, data)
        
        # 遍历所有启用的插件
        for plugin_id, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
                
            # 获取该事件类型的所有处理函数
            handlers = plugin.get_event_handlers(event_type)
            
            # 调用每个处理函数
            for handler in handlers:
                try:
                    handler(event)
                    
                    # 如果事件被阻止处理，就停止调用其他处理函数
                    if event.is_default_prevented():
                        break
                        
                except Exception as e:
                    logger.error("插件处理事件出错", 
                               plugin_id=plugin_id, 
                               event_type=event_type, 
                               error=str(e))
                    logger.error(traceback.format_exc())
        
        return event
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """
        获取插件实例
        
        参数:
            plugin_id: 插件ID
            
        返回:
            Optional[PluginBase]: 插件实例，如果插件不存在则返回None
        """
        return self.plugins.get(plugin_id)
        
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """
        获取所有已加载的插件
        
        返回:
            Dict[str, PluginBase]: 插件字典，key为插件ID，value为插件实例
        """
        return self.plugins.copy()
        
    def cleanup(self) -> bool:
        """
        清理所有插件资源
        
        返回:
            bool: 所有插件清理成功返回True，任一插件清理失败返回False
        """
        success = True
        for plugin_id in list(self.plugins.keys()):
            if not self.unload_plugin(plugin_id):
                success = False
                
        return success
        
    def get_all_plugins_info(self) -> List[Dict[str, Any]]:
        """
        获取所有插件信息
        
        返回:
            List[Dict]: 插件信息列表
        """
        all_plugins = self.discover_plugins()
        enabled_plugins = self.config_manager.get_config_value("system", "enabled_plugins", []) if self.config_manager else []
        
        # 添加启用状态信息
        for plugin in all_plugins:
            plugin["enabled"] = plugin["id"] in enabled_plugins
            plugin["loaded"] = plugin["id"] in self.plugins
            
        return all_plugins
        
    def enable_plugin(self, plugin_id: str, app_context: Any = None) -> bool:
        """
        启用插件
        
        参数:
            plugin_id: 插件ID
            app_context: 应用程序上下文
            
        返回:
            bool: 启用成功返回True，失败返回False
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return False
            
        # 获取已启用的插件列表
        enabled_plugins = self.config_manager.get_config_value("system", "enabled_plugins", [])
        
        # 如果插件已经启用，直接返回成功
        if plugin_id in enabled_plugins:
            logger.info("插件已经启用", plugin_id=plugin_id)
            return True
            
        # 添加到启用列表
        enabled_plugins.append(plugin_id)
        self.config_manager.set_config_value("system", "enabled_plugins", enabled_plugins)
        
        # 加载插件
        if app_context:
            return self.load_plugin(plugin_id, app_context)
        return True
        
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        禁用插件
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 禁用成功返回True，失败返回False
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return False
            
        # 获取已启用的插件列表
        enabled_plugins = self.config_manager.get_config_value("system", "enabled_plugins", [])
        
        # 如果插件尚未启用，直接返回成功
        if plugin_id not in enabled_plugins:
            logger.info("插件尚未启用", plugin_id=plugin_id)
            return True
            
        # 从启用列表中移除
        enabled_plugins.remove(plugin_id)
        self.config_manager.set_config_value("system", "enabled_plugins", enabled_plugins)
        
        # 卸载插件
        return self.unload_plugin(plugin_id)
        
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        卸载并删除插件
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 卸载成功返回True，失败返回False
        """
        # 先卸载插件
        if plugin_id in self.plugins:
            if not self.unload_plugin(plugin_id):
                return False
            
        # 禁用插件
        if self.config_manager:
            enabled_plugins = self.config_manager.get_config_value("system", "enabled_plugins", [])
            if plugin_id in enabled_plugins:
                enabled_plugins.remove(plugin_id)
                self.config_manager.set_config_value("system", "enabled_plugins", enabled_plugins)
        
        # 删除插件目录
        plugin_dir = os.path.join(self.plugin_dir, plugin_id)
        if os.path.exists(plugin_dir):
            try:
                shutil.rmtree(plugin_dir)
                logger.info("成功删除插件目录", plugin_dir=plugin_dir)
            except Exception as e:
                logger.error("删除插件目录出错", plugin_dir=plugin_dir, error=str(e))
                return False
        
        return True
            
    def get_enabled_plugins_ids(self) -> List[str]:
        """
        获取已启用的插件ID列表
        
        返回:
            List[str]: 插件ID列表
        """
        if not self.config_manager:
            return []
            
        return self.config_manager.get_config_value("system", "enabled_plugins", []) 