#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设置对话框
负责显示和编辑应用程序设置
"""

import os
import sys
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QSpinBox, QGroupBox, QGridLayout, QLineEdit,
    QFrame, QDialog, QPushButton, QTabWidget
)

from qfluentwidgets import (
    PrimaryPushButton, FluentIcon, InfoBar, InfoBarPosition
)

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.parent = parent
        
        # 设置对话框属性
        self.setWindowTitle("应用设置")
        self.resize(700, 500)
        
        # 初始化UI
        self.initUI()
        
        # 加载当前设置
        self.loadSettings()
        
    def initUI(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡控件
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # ========== 外观设置 ==========
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        appearance_group = QGroupBox("外观和主题")
        appearance_group_layout = QGridLayout(appearance_group)
        
        # 主题设置
        theme_label = QLabel("应用主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["自动", "浅色", "深色"])
        appearance_group_layout.addWidget(theme_label, 0, 0)
        appearance_group_layout.addWidget(self.theme_combo, 0, 1)
        
        appearance_layout.addWidget(appearance_group)
        appearance_layout.addStretch(1)
        
        # ========== 视图设置 ==========
        view_tab = QWidget()
        view_layout = QVBoxLayout(view_tab)
        
        view_group = QGroupBox("视图设置")
        view_group_layout = QGridLayout(view_group)
        
        # 默认视图设置
        start_view_label = QLabel("默认视图:")
        self.start_view_combo = QComboBox()
        self.start_view_combo.addItems(["日程视图", "甘特图"])
        view_group_layout.addWidget(start_view_label, 0, 0)
        view_group_layout.addWidget(self.start_view_combo, 0, 1)
        
        # 显示已完成任务
        show_completed_label = QLabel("显示已完成任务:")
        self.show_completed_check = QCheckBox()
        view_group_layout.addWidget(show_completed_label, 1, 0)
        view_group_layout.addWidget(self.show_completed_check, 1, 1)
        
        view_layout.addWidget(view_group)
        view_layout.addStretch(1)
        
        # ========== 任务设置 ==========
        task_tab = QWidget()
        task_layout = QVBoxLayout(task_tab)
        
        task_group = QGroupBox("任务设置")
        task_group_layout = QGridLayout(task_group)
        
        # 默认任务时长
        task_duration_label = QLabel("默认任务时长(小时):")
        self.task_duration_spin = QSpinBox()
        self.task_duration_spin.setRange(1, 72)
        task_group_layout.addWidget(task_duration_label, 0, 0)
        task_group_layout.addWidget(self.task_duration_spin, 0, 1)
        
        # 提醒时间
        reminder_label = QLabel("提醒时间(分钟):")
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(0, 1440)
        self.reminder_spin.setSingleStep(5)
        task_group_layout.addWidget(reminder_label, 1, 0)
        task_group_layout.addWidget(self.reminder_spin, 1, 1)
        
        # 默认优先级
        priority_label = QLabel("默认优先级:")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["低", "中", "高", "紧急"])
        task_group_layout.addWidget(priority_label, 2, 0)
        task_group_layout.addWidget(self.priority_combo, 2, 1)
        
        task_layout.addWidget(task_group)
        task_layout.addStretch(1)
        
        # ========== 数据设置 ==========
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        data_group = QGroupBox("数据设置")
        data_group_layout = QGridLayout(data_group)
        
        # 自动保存
        auto_save_label = QLabel("自动保存间隔(分钟):")
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 60)
        data_group_layout.addWidget(auto_save_label, 0, 0)
        data_group_layout.addWidget(self.auto_save_spin, 0, 1)
        
        # 备份间隔
        backup_label = QLabel("自动备份间隔(天):")
        self.backup_spin = QSpinBox()
        self.backup_spin.setRange(1, 30)
        data_group_layout.addWidget(backup_label, 1, 0)
        data_group_layout.addWidget(self.backup_spin, 1, 1)
        
        # 备份数量
        backup_count_label = QLabel("保留备份数量:")
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        data_group_layout.addWidget(backup_count_label, 2, 0)
        data_group_layout.addWidget(self.backup_count_spin, 2, 1)
        
        data_layout.addWidget(data_group)
        data_layout.addStretch(1)
        
        # 添加所有选项卡
        self.tabs.addTab(appearance_tab, "外观")
        self.tabs.addTab(view_tab, "视图")
        self.tabs.addTab(task_tab, "任务")
        self.tabs.addTab(data_tab, "数据")
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # 重置按钮
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self.resetSettings)
        button_layout.addWidget(self.reset_button)
        
        # 添加弹性空间
        button_layout.addStretch(1)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 保存按钮
        self.save_button = PrimaryPushButton("保存")
        self.save_button.clicked.connect(self.saveSettings)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
    def loadSettings(self):
        """加载当前设置"""
        # 主题设置
        theme = self.config_manager.get_config_value("user", "theme", "auto")
        theme_index = {"auto": 0, "light": 1, "dark": 2}.get(theme, 0)
        self.theme_combo.setCurrentIndex(theme_index)
        
        # 默认视图
        start_view = self.config_manager.get_config_value("user", "start_view", "calendar")
        view_index = {"calendar": 0, "gantt": 1}.get(start_view, 0)
        self.start_view_combo.setCurrentIndex(view_index)
        
        # 显示已完成任务
        show_completed = self.config_manager.get_config_value("user", "show_completed_tasks", True)
        self.show_completed_check.setChecked(show_completed)
        
        # 默认任务时长
        task_duration = self.config_manager.get_config_value("user", "default_task_duration_hours", 1)
        self.task_duration_spin.setValue(task_duration)
        
        # 提醒时间
        reminder_time = self.config_manager.get_config_value("user", "reminder_advance_minutes", 15)
        self.reminder_spin.setValue(reminder_time)
        
        # 默认优先级
        default_priority = self.config_manager.get_config_value("user", "default_priority", "中")
        priority_index = {"低": 0, "中": 1, "高": 2, "紧急": 3}.get(default_priority, 1)
        self.priority_combo.setCurrentIndex(priority_index)
        
        # 自动保存间隔
        auto_save = self.config_manager.get_config_value("user", "auto_save_interval_minutes", 5)
        self.auto_save_spin.setValue(auto_save)
        
        # 备份间隔
        backup_interval = self.config_manager.get_config_value("system", "backup_interval_days", 7)
        self.backup_spin.setValue(backup_interval)
        
        # 备份数量
        backup_count = self.config_manager.get_config_value("system", "backup_count", 5)
        self.backup_count_spin.setValue(backup_count)
        
    def saveSettings(self):
        """保存设置"""
        try:
            # 主题设置
            theme_map = {0: "auto", 1: "light", 2: "dark"}
            theme = theme_map.get(self.theme_combo.currentIndex(), "auto")
            self.config_manager.set_config_value("user", "theme", theme)
            
            # 默认视图
            view_map = {0: "calendar", 1: "gantt"}
            start_view = view_map.get(self.start_view_combo.currentIndex(), "calendar")
            self.config_manager.set_config_value("user", "start_view", start_view)
            
            # 显示已完成任务
            self.config_manager.set_config_value("user", "show_completed_tasks", self.show_completed_check.isChecked())
            
            # 默认任务时长
            self.config_manager.set_config_value("user", "default_task_duration_hours", self.task_duration_spin.value())
            
            # 提醒时间
            self.config_manager.set_config_value("user", "reminder_advance_minutes", self.reminder_spin.value())
            
            # 默认优先级
            priority_map = {0: "低", 1: "中", 2: "高", 3: "紧急"}
            priority = priority_map.get(self.priority_combo.currentIndex(), "中")
            self.config_manager.set_config_value("user", "default_priority", priority)
            
            # 自动保存间隔
            self.config_manager.set_config_value("user", "auto_save_interval_minutes", self.auto_save_spin.value())
            
            # 备份间隔
            self.config_manager.set_config_value("system", "backup_interval_days", self.backup_spin.value())
            
            # 备份数量
            self.config_manager.set_config_value("system", "backup_count", self.backup_count_spin.value())
            
            # 保存配置组
            self.config_manager.save_config_group("user")
            self.config_manager.save_config_group("system")
            
            # 显示成功消息
            InfoBar.success(
                title="成功",
                content="设置已保存",
                parent=self.parent or self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            
            # 关闭对话框
            self.accept()
            
            # 应用主题变更
            if self.parent and hasattr(self.parent, "loadUserConfig"):
                self.parent.loadUserConfig()
                
        except Exception as e:
            # 显示错误消息
            InfoBar.error(
                title="错误",
                content=f"保存设置失败: {str(e)}",
                parent=self.parent or self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
    def resetSettings(self):
        """重置设置为默认值"""
        # 重置用户配置
        self.config_manager.reset_config("user")
        self.config_manager.reset_config("system")
        
        # 重新加载设置
        self.loadSettings()
        
        # 显示提示
        InfoBar.success(
            title="成功",
            content="设置已重置为默认值",
            parent=self.parent or self,
            position=InfoBarPosition.TOP,
            duration=2000
        ) 