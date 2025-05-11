#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用程序上下文
提供插件与主程序交互的上下文环境
"""

class AppContext:
    """应用程序上下文，包含主应用程序的各种管理器和对象"""
    
    def __init__(self, main_window=None, config_manager=None, plugin_manager=None, scheduler_manager=None):
        """
        初始化应用程序上下文
        
        参数:
            main_window: 主窗口实例
            config_manager: 配置管理器
            plugin_manager: 插件管理器
            scheduler_manager: 日程管理器
        """
        self.main_window = main_window
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        self.scheduler_manager = scheduler_manager
    
    def register_plugin_view(self, plugin_id, view, icon, title):
        """
        注册插件视图到主窗口
        
        参数:
            plugin_id: 插件ID
            view: 视图组件
            icon: 图标
            title: 标题
            
        返回:
            bool: 注册成功返回True，失败返回False
        """
        if self.main_window and hasattr(self.main_window, 'register_plugin_view'):
            return self.main_window.register_plugin_view(plugin_id, view, icon, title)
        return False
    
    def unregister_plugin_view(self, plugin_id):
        """
        从主窗口取消注册插件视图
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 取消注册成功返回True，失败返回False
        """
        if self.main_window and hasattr(self.main_window, 'unregister_plugin_view'):
            return self.main_window.unregister_plugin_view(plugin_id)
        return False
    
    def get_task(self, task_id):
        """
        获取任务
        
        参数:
            task_id: 任务ID
            
        返回:
            dict: 任务信息
        """
        if self.scheduler_manager:
            return self.scheduler_manager.get_task(task_id)
        return None
    
    def get_all_tasks(self):
        """
        获取所有任务
        
        返回:
            list: 任务列表
        """
        if self.scheduler_manager:
            return self.scheduler_manager.get_all_tasks()
        return []
    
    def get_config(self, group, key, default=None):
        """
        获取配置值
        
        参数:
            group: 配置组
            key: 配置键
            default: 默认值
            
        返回:
            any: 配置值
        """
        if self.config_manager:
            return self.config_manager.get_config_value(group, key, default)
        return default
    
    def set_config(self, group, key, value):
        """
        设置配置值
        
        参数:
            group: 配置组
            key: 配置键
            value: 值
            
        返回:
            bool: 设置成功返回True
        """
        if self.config_manager:
            return self.config_manager.set_config_value(group, key, value)
        return False 