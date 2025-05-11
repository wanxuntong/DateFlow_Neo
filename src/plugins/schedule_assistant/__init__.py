#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
排期助手插件
提供辅助排期功能，包括任务批量创建、智能推荐时间段、重复任务管理等
"""

from core.plugin_manager import PluginBase
from PyQt5.QtCore import Qt, QSize, QDateTime
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QLineEdit,
                           QComboBox, QDateTimeEdit, QSpinBox,
                           QScrollArea, QMessageBox, QGroupBox,
                           QTabWidget, QListWidget, QListWidgetItem)
import os
from datetime import datetime, timedelta
from utils.logger import get_logger
from qfluentwidgets import FluentIcon

# 创建日志记录器
logger = get_logger("ScheduleAssistant", app="InfoFlow")

class ScheduleAssistantPlugin(PluginBase):
    """排期助手插件类"""
    
    def __init__(self):
        """初始化插件"""
        super().__init__(
            plugin_id="schedule_assistant",
            name="排期助手",
            version="1.0.0",
            description="提供辅助排期功能，包括任务批量创建、智能推荐时间段、重复任务管理等"
        )
        self.app_context = None
        self.main_widget = None
    
    def initialize(self, app_context):
        """初始化插件
        
        参数:
            app_context: 应用程序上下文
        
        返回:
            bool: 初始化成功返回True
        """
        try:
            logger.info("初始化排期助手插件")
            self.app_context = app_context
            
            # 创建主界面
            from .main_view import ScheduleAssistantView
            self.main_widget = ScheduleAssistantView(app_context)
            
            # 使用自定义图标
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
            icon = QIcon(icon_path)
            
            # 注册视图
            result = app_context.register_plugin_view(
                self.plugin_id,
                self.main_widget,
                icon,
                self.name
            )
            
            if not result:
                logger.error("注册插件视图失败")
                return False
            
            # 注册事件处理
            self.register_event_handler(
                self.app_context.plugin_manager.EVENT_APPLICATION_START, 
                self.on_application_start
            )
            self.register_event_handler(
                self.app_context.plugin_manager.EVENT_TASK_CREATED,
                self.on_task_created
            )
            
            logger.info("排期助手插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"排期助手插件初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup(self):
        """清理插件资源
        
        返回:
            bool: 清理成功返回True
        """
        try:
            # 注销事件处理
            logger.info("清理排期助手插件资源")
            self.app_context.unregister_plugin_view(self.plugin_id)
            return True
        except Exception as e:
            logger.error(f"排期助手插件清理失败: {e}")
            return False
    
    def on_application_start(self, event):
        """应用程序启动事件处理
        
        参数:
            event: 事件对象
        """
        logger.info("排期助手插件已加载")
    
    def on_task_created(self, event):
        """任务创建事件处理
        
        参数:
            event: 事件对象
        """
        # 任务创建时，可以进行一些处理，比如记录统计信息
        task = event.get_data()
        if task:
            logger.info(f"捕获到新任务创建: {task.get('title')}") 