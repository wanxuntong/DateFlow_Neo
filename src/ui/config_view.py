#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置视图
用于设置应用程序的各项配置
"""

from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QGridLayout, QTimeEdit,
    QCheckBox, QComboBox, QSpinBox, QFileDialog,
    QGroupBox, QPushButton
)
from PyQt5.QtGui import QColor

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, ColorPickerButton,
    ToggleButton, BodyLabel, CardWidget, MessageBox,
    SubtitleLabel, LineEdit, SearchLineEdit, SwitchButton,
    TitleLabel, InfoBar, InfoBarPosition, ComboBox,
    SpinBox, PrimaryPushButton, TransparentToolButton,
    Theme, setTheme, isDarkTheme, MessageBoxBase, 
    setThemeColor, ToolTipFilter, ToolTipPosition
)

import json
import os
from datetime import datetime

# 基本设置卡片
class SettingCard(CardWidget):
    """基本设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("SettingCard")
        
        # 主布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(16, 16, 16, 16)
        self.hBoxLayout.setSpacing(16)
        
        # 图标
        self.iconWidget = TransparentToolButton(icon, self)
        self.iconWidget.setFixedSize(20, 20)
        self.iconWidget.setEnabled(False)
        self.hBoxLayout.addWidget(self.iconWidget)
        
        # 信息区域
        self.infoLayout = QVBoxLayout()
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(4)
        
        # 标题
        self.titleLabel = SubtitleLabel(title, self)
        self.infoLayout.addWidget(self.titleLabel)
        
        # 内容
        if content:
            self.contentLabel = BodyLabel(content, self)
            self.infoLayout.addWidget(self.contentLabel)
            
        self.hBoxLayout.addLayout(self.infoLayout)
        self.hBoxLayout.addStretch(1)
    
    def setTitle(self, title):
        """设置标题"""
        self.titleLabel.setText(title)
    
    def title(self):
        """获取标题"""
        return self.titleLabel.text()
    
    def setContent(self, content):
        """设置内容"""
        if hasattr(self, 'contentLabel'):
            self.contentLabel.setText(content)
        else:
            self.contentLabel = BodyLabel(content, self)
            self.infoLayout.addWidget(self.contentLabel)
    
    def content(self):
        """获取内容"""
        if hasattr(self, 'contentLabel'):
            return self.contentLabel.text()
        return ""
        
# 开关设置卡片
class SwitchSettingCard(SettingCard):
    """带有开关的设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化开关设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加开关
        self.switchButton = SwitchButton(self)
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
    
    def setChecked(self, isChecked):
        """设置开关状态"""
        self.switchButton.setChecked(isChecked)
    
    def isChecked(self):
        """获取开关状态"""
        return self.switchButton.isChecked()

# 下拉框设置卡片
class ComboBoxSettingCard(SettingCard):
    """带有下拉框的设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化下拉框设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加下拉框
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        self.comboBox.setMinimumWidth(150)
    
# 按钮设置卡片
class PushSettingCard(SettingCard):
    """带有按钮的设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化按钮设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加按钮
        self.button = PushButton(self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

# 颜色选择设置卡片
class ColorSettingCard(SettingCard):
    """带有颜色选择的设置卡片"""
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化颜色选择设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加颜色选择按钮
        self.colorButton = ColorPickerButton(QColor(0, 120, 212), str(title), self)
        self.colorButton.colorChanged.connect(self.colorChanged)
        self.hBoxLayout.addWidget(self.colorButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
    
    def setColor(self, color):
        """设置颜色"""
        self.colorButton.setColor(color)
    
    def color(self):
        """获取颜色"""
        return self.colorButton.color()
        
    def title(self):
        """获取标题文本"""
        return self.titleLabel.text()
        
    def setTitle(self, title):
        """设置标题文本"""
        self.titleLabel.setText(title)
        # 更新ColorPickerButton的title
        if hasattr(self, 'colorButton'):
            self.colorButton.title = str(title)

# 输入框设置卡片
class LineEditSettingCard(SettingCard):
    """带有输入框的设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化输入框设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加输入框
        self.lineEdit = LineEdit(self)
        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        self.lineEdit.setMinimumWidth(200)

# 数字选择设置卡片
class SpinBoxSettingCard(SettingCard):
    """带有数字选择的设置卡片"""
    
    def __init__(self, icon, title, content=None, parent=None):
        """
        初始化数字选择设置卡片
        
        Args:
            icon: 图标
            title: 标题
            content: 内容描述
            parent: 父组件
        """
        super().__init__(icon, title, content, parent)
        
        # 添加数字选择框
        self.spinBox = SpinBox(self)
        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        self.spinBox.setMinimumWidth(100)

# 设置组
class SettingCardGroup(QWidget):
    """设置组"""
    
    def __init__(self, title, parent=None):
        """
        初始化设置组
        
        Args:
            title: 标题
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("SettingCardGroup")
        
        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 16, 16, 16)
        self.vBoxLayout.setSpacing(0)
        
        # 标题
        self.titleLabel = SubtitleLabel(title, self)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(10)
        
        # 内容布局
        self.contentLayout = QVBoxLayout()
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(2)
        
        self.vBoxLayout.addLayout(self.contentLayout)
    
    def addSettingCard(self, card):
        """添加设置卡片"""
        self.contentLayout.addWidget(card)
    
    def title(self):
        """获取标题"""
        return self.titleLabel.text()
    
    def setTitle(self, title):
        """设置标题"""
        self.titleLabel.setText(title)
    
    def layout(self):
        """获取内容布局"""
        return self.contentLayout

class ConfigView(ScrollArea):
    """配置视图"""
    
    def __init__(self, config_manager, parent=None):
        """
        初始化配置视图
        
        Args:
            config_manager: 配置管理器
            parent: 父组件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        
        # 设置属性
        self.setObjectName("configView")
        self.setWidgetResizable(True)
        
        # 初始化界面
        self.init_ui()
        
        # 加载配置
        self.load_config()
    
    def init_ui(self):
        """初始化界面"""
        # 创建主窗口
        self.main_widget = QWidget(self)
        self.setWidget(self.main_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # 添加标题和操作按钮区域
        header_layout = QHBoxLayout()
        
        # 标题
        self.title_label = TitleLabel("系统配置")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索设置...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self.search_config)
        header_layout.addWidget(self.search_edit)
        
        # 操作按钮
        self.import_button = TransparentToolButton(FluentIcon.DOWNLOAD, self)
        self.import_button.setToolTip("从文件导入配置")
        self.import_button.clicked.connect(self.import_config)
        header_layout.addWidget(self.import_button)
        
        self.export_button = TransparentToolButton(FluentIcon.SAVE, self)
        self.export_button.setToolTip("将当前配置导出到文件")
        self.export_button.clicked.connect(self.export_config)
        header_layout.addWidget(self.export_button)
        
        self.reset_button = TransparentToolButton(FluentIcon.RETURN, self)
        self.reset_button.setToolTip("恢复默认设置")
        self.reset_button.clicked.connect(self.reset_config)
        header_layout.addWidget(self.reset_button)
        
        self.main_layout.addLayout(header_layout)
        
        # ================ 外观设置 ================
        self.appearance_group = SettingCardGroup("外观设置", self.main_widget)
        
        # 主题设置
        self.theme_card = ComboBoxSettingCard(
            icon=FluentIcon.BRUSH,
            title="主题模式",
            content="选择应用程序的显示主题",
            parent=self.appearance_group
        )
        self.theme_card.comboBox.addItems(["浅色", "深色", "跟随系统"])
        self.theme_card.comboBox.setCurrentIndex(2)  # 默认跟随系统
        self.theme_card.comboBox.currentIndexChanged.connect(self.on_theme_changed)
        self.appearance_group.addSettingCard(self.theme_card)
        
        # 主题色设置
        self.theme_color_card = ColorSettingCard(
            icon=FluentIcon.PALETTE,
            title="主题色",
            content="选择应用程序的主题颜色",
            parent=self.appearance_group
        )
        self.theme_color_card.colorChanged.connect(self.on_theme_color_changed)
        self.appearance_group.addSettingCard(self.theme_color_card)
        
        # 使用系统主题色
        self.use_system_color_card = SwitchSettingCard(
            icon=FluentIcon.SYNC,
            title="使用系统主题色",
            content="跟随系统主题颜色设置",
            parent=self.appearance_group
        )
        self.appearance_group.addSettingCard(self.use_system_color_card)
        
        # 文字大小
        self.font_size_card = SpinBoxSettingCard(
            icon=FluentIcon.FONT_SIZE,
            title="文字大小",
            content="调整界面文字的大小",
            parent=self.appearance_group
        )
        self.font_size_card.spinBox.setRange(8, 18)
        self.font_size_card.spinBox.setValue(9)
        self.appearance_group.addSettingCard(self.font_size_card)
        
        # 语言设置
        self.language_card = ComboBoxSettingCard(
            icon=FluentIcon.LANGUAGE,
            title="语言",
            content="选择应用程序的显示语言",
            parent=self.appearance_group
        )
        self.language_card.comboBox.addItems(["简体中文", "English"])
        self.language_card.comboBox.setCurrentIndex(0)
        self.appearance_group.addSettingCard(self.language_card)
        
        self.main_layout.addWidget(self.appearance_group)
        
        # ================ 视图设置 ================
        self.view_group = SettingCardGroup("视图设置", self.main_widget)
        
        # 默认视图
        self.default_view_card = ComboBoxSettingCard(
            icon=FluentIcon.VIEW,
            title="默认视图",
            content="选择应用程序启动时显示的默认视图",
            parent=self.view_group
        )
        self.default_view_card.comboBox.addItems(["日程视图", "甘特图", "流程图"])
        self.view_group.addSettingCard(self.default_view_card)
        
        # 显示已完成任务
        self.show_completed_card = SwitchSettingCard(
            icon=FluentIcon.CHECKBOX,
            title="显示已完成任务",
            content="在视图中显示已完成的任务",
            parent=self.view_group
        )
        self.view_group.addSettingCard(self.show_completed_card)
        
        # 紧凑模式
        self.compact_mode_card = SwitchSettingCard(
            icon=FluentIcon.MINIMIZE,
            title="紧凑模式",
            content="使用更紧凑的界面布局以显示更多内容",
            parent=self.view_group
        )
        self.view_group.addSettingCard(self.compact_mode_card)
        
        # 动画速度
        self.animation_speed_card = ComboBoxSettingCard(
            icon=FluentIcon.SPEED_HIGH,
            title="动画速度",
            content="设置界面动画的速度",
            parent=self.view_group
        )
        self.animation_speed_card.comboBox.addItems(["关闭", "慢速", "正常", "快速"])
        self.animation_speed_card.comboBox.setCurrentIndex(2)  # 默认正常
        self.view_group.addSettingCard(self.animation_speed_card)
        
        self.main_layout.addWidget(self.view_group)
        
        # ================ 工作设置 ================
        self.work_group = SettingCardGroup("工作设置", self.main_widget)
        
        # 工作日选择
        self.work_days_card = PushSettingCard(
            icon=FluentIcon.CALENDAR,
            title="工作日",
            content="设置每周的工作日",
            parent=self.work_group
        )
        self.work_days_card.button.setText("设置")
        self.work_days_card.button.clicked.connect(self.show_work_days_dialog)
        self.work_group.addSettingCard(self.work_days_card)
        
        # 工作时间
        self.work_hours_card = PushSettingCard(
            icon=FluentIcon.DATE_TIME,
            title="工作时间",
            content="设置每天的工作时间",
            parent=self.work_group
        )
        self.work_hours_card.button.setText("设置")
        self.work_hours_card.button.clicked.connect(self.show_work_hours_dialog)
        self.work_group.addSettingCard(self.work_hours_card)
        
        # 任务默认时长
        self.default_duration_card = SpinBoxSettingCard(
            icon=FluentIcon.STOP_WATCH,
            title="任务默认时长(小时)",
            content="创建新任务时的默认持续时间",
            parent=self.work_group
        )
        self.default_duration_card.spinBox.setRange(1, 24)
        self.default_duration_card.spinBox.setSingleStep(1)
        self.default_duration_card.spinBox.setValue(1)
        self.work_group.addSettingCard(self.default_duration_card)
        
        self.main_layout.addWidget(self.work_group)
        
        # ================ 提醒设置 ================
        self.reminder_group = SettingCardGroup("提醒设置", self.main_widget)
        
        # 任务提醒
        self.enable_reminder_card = SwitchSettingCard(
            icon=FluentIcon.INFO,
            title="启用任务提醒",
            content="在任务开始前发送提醒通知",
            parent=self.reminder_group
        )
        self.reminder_group.addSettingCard(self.enable_reminder_card)
        
        # 提醒提前时间
        self.reminder_advance_card = SpinBoxSettingCard(
            icon=FluentIcon.DATE_TIME,
            title="提醒提前时间(分钟)",
            content="任务开始前多少分钟发送提醒",
            parent=self.reminder_group
        )
        self.reminder_advance_card.spinBox.setRange(1, 120)
        self.reminder_advance_card.spinBox.setValue(15)
        self.reminder_group.addSettingCard(self.reminder_advance_card)
        
        # 提醒方式
        self.reminder_method_card = ComboBoxSettingCard(
            icon=FluentIcon.CHAT,
            title="提醒方式",
            content="选择任务提醒的通知方式",
            parent=self.reminder_group
        )
        self.reminder_method_card.comboBox.addItems(["系统通知", "弹窗提醒", "声音提醒", "全部"])
        self.reminder_method_card.comboBox.setCurrentIndex(0)
        self.reminder_group.addSettingCard(self.reminder_method_card)
        
        self.main_layout.addWidget(self.reminder_group)
        
        # ================ 系统设置 ================
        self.system_group = SettingCardGroup("系统设置", self.main_widget)
        
        # 自动保存间隔
        self.auto_save_card = SpinBoxSettingCard(
            icon=FluentIcon.SAVE,
            title="自动保存间隔(分钟)",
            content="自动保存数据的时间间隔",
            parent=self.system_group
        )
        self.auto_save_card.spinBox.setRange(1, 60)
        self.auto_save_card.spinBox.setValue(5)
        self.system_group.addSettingCard(self.auto_save_card)
        
        # 数据目录
        self.data_dir_card = PushSettingCard(
            icon=FluentIcon.FOLDER,
            title="数据目录",
            content="设置数据文件的存储位置",
            parent=self.system_group
        )
        self.data_dir_card.button.setText("浏览")
        self.data_dir_card.button.clicked.connect(self.select_data_dir)
        self.system_group.addSettingCard(self.data_dir_card)
        
        # 备份设置
        self.backup_card = PushSettingCard(
            icon=FluentIcon.HISTORY,
            title="创建备份",
            content="创建当前配置和数据的备份",
            parent=self.system_group
        )
        self.backup_card.button.setText("备份")
        self.backup_card.button.clicked.connect(self.create_backup)
        self.system_group.addSettingCard(self.backup_card)
        
        # 恢复备份
        self.restore_backup_card = PushSettingCard(
            icon=FluentIcon.SYNC,
            title="恢复备份",
            content="从备份文件恢复配置和数据",
            parent=self.system_group
        )
        self.restore_backup_card.button.setText("恢复")
        self.restore_backup_card.button.clicked.connect(self.restore_backup)
        self.system_group.addSettingCard(self.restore_backup_card)
        
        # 自动检查更新
        self.update_check_card = SwitchSettingCard(
            icon=FluentIcon.UPDATE,
            title="自动检查更新",
            content="启动时检查程序更新",
            parent=self.system_group
        )
        self.system_group.addSettingCard(self.update_check_card)
        
        self.main_layout.addWidget(self.system_group)
        
        # ================ 高级设置 ================
        self.advanced_group = SettingCardGroup("高级设置", self.main_widget)
        
        # 撤销步数
        self.undo_steps_card = SpinBoxSettingCard(
            icon=FluentIcon.RETURN,
            title="最大撤销步数",
            content="可以撤销的最大操作数量",
            parent=self.advanced_group
        )
        self.undo_steps_card.spinBox.setRange(5, 100)
        self.undo_steps_card.spinBox.setValue(20)
        self.advanced_group.addSettingCard(self.undo_steps_card)
        
        # 启用崩溃报告
        self.crash_report_card = SwitchSettingCard(
            icon=FluentIcon.INFO,
            title="启用崩溃报告",
            content="在程序崩溃时发送匿名诊断信息",
            parent=self.advanced_group
        )
        self.advanced_group.addSettingCard(self.crash_report_card)
        
        # 日志级别
        self.log_level_card = ComboBoxSettingCard(
            icon=FluentIcon.LIBRARY,
            title="日志级别",
            content="设置程序日志的详细程度",
            parent=self.advanced_group
        )
        self.log_level_card.comboBox.addItems(["调试", "信息", "警告", "错误", "严重"])
        self.log_level_card.comboBox.setCurrentIndex(1)  # 默认信息级别
        self.advanced_group.addSettingCard(self.log_level_card)
        
        # 开发者模式
        self.developer_mode_card = SwitchSettingCard(
            icon=FluentIcon.CODE,
            title="开发者模式",
            content="启用高级调试功能和开发工具",
            parent=self.advanced_group
        )
        self.advanced_group.addSettingCard(self.developer_mode_card)
        
        self.main_layout.addWidget(self.advanced_group)
        
        # 底部空间
        self.main_layout.addStretch(1)
        
        # 应用和取消按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        self.apply_button = PrimaryPushButton("应用", self)
        self.apply_button.setIcon(FluentIcon.ACCEPT)
        self.apply_button.clicked.connect(self.save_config)
        buttons_layout.addWidget(self.apply_button)
        
        self.main_layout.addLayout(buttons_layout)
    
    def search_config(self, text):
        """搜索配置项"""
        if not text:
            # 如果搜索框为空，显示所有设置组
            for group in [self.appearance_group, self.view_group, self.work_group, 
                          self.reminder_group, self.system_group, self.advanced_group]:
                group.setVisible(True)
            return
            
        # 转换为小写进行不区分大小写搜索
        search_text = text.lower()
        
        # 检查每个设置组中的设置卡是否匹配搜索文本
        for group in [self.appearance_group, self.view_group, self.work_group, 
                      self.reminder_group, self.system_group, self.advanced_group]:
            # 检查组标题是否匹配
            group_match = search_text in group.title().lower()
            
            # 检查组内每个设置卡是否匹配
            cards_match = False
            for i in range(group.layout().count()):
                widget = group.layout().itemAt(i).widget()
                if widget and hasattr(widget, 'title') and hasattr(widget, 'content'):
                    if (search_text in widget.title().lower() or 
                        search_text in widget.content().lower()):
                        cards_match = True
                        break
            
            # 如果组标题或任何设置卡匹配，显示该组，否则隐藏
            group.setVisible(group_match or cards_match)
    
    def import_config(self):
        """从文件导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 显示确认对话框
            confirm_dialog = MessageBox(
                "导入配置",
                "导入配置将覆盖当前的所有设置，确定要继续吗？",
                self
            )
            
            if confirm_dialog.exec_():
                # 导入各个配置组
                for group_name, group_data in config_data.items():
                    if group_name in self.config_manager.config_groups:
                        self.config_manager.config_groups[group_name].items = group_data
                
                # 保存到配置文件
                for group_name in config_data.keys():
                    self.config_manager.save_config_group(group_name)
                
                # 重新加载配置
                self.load_config()
                
                InfoBar.success(
                    title="成功",
                    content="配置导入成功",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"配置导入失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def export_config(self):
        """导出配置到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            # 收集所有配置组数据
            config_data = {}
            for name, group in self.config_manager.config_groups.items():
                config_data[name] = group.items
                
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
                
            InfoBar.success(
                title="成功",
                content="配置导出成功",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
                
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"配置导出失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def reset_config(self):
        """重置配置到默认设置"""
        # 显示确认对话框
        confirm_dialog = MessageBox(
            "重置设置",
            "确定要将所有设置恢复为默认值吗？此操作无法撤销。",
            self
        )
        
        if confirm_dialog.exec_():
            # 调用配置管理器的重置功能
            result = self.config_manager.reset_config()
            
            if result:
                # 重新加载配置
                self.load_config()
                
                InfoBar.success(
                    title="成功",
                    content="设置已重置为默认值",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="重置设置失败",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
    
    def load_config(self):
        """从配置管理器加载配置"""
        try:
            # 加载用户配置
            user_config = self.config_manager.user_config
            
            # 主题设置
            theme = user_config.get("theme", "auto")
            if theme == "light":
                self.theme_card.comboBox.setCurrentIndex(0)
            elif theme == "dark":
                self.theme_card.comboBox.setCurrentIndex(1)
            else:  # auto
                self.theme_card.comboBox.setCurrentIndex(2)
            
            # 语言设置
            language = user_config.get("language", "zh_CN")
            if language == "zh_CN":
                self.language_card.comboBox.setCurrentIndex(0)
            else:  # en_US
                self.language_card.comboBox.setCurrentIndex(1)
            
            # 主题色
            theme_color = user_config.get("theme_color", "#2196F3")
            self.theme_color_card.setColor(QColor(theme_color))
            
            # 默认视图
            start_view = user_config.get("start_view", "calendar")
            if start_view == "calendar":
                self.default_view_card.comboBox.setCurrentIndex(0)
            elif start_view == "gantt":
                self.default_view_card.comboBox.setCurrentIndex(1)
            else:  # flow
                self.default_view_card.comboBox.setCurrentIndex(2)
            
            # 显示已完成任务
            show_completed = user_config.get("show_completed_tasks", True)
            self.show_completed_card.setChecked(show_completed)
            
            # 默认任务时长
            default_duration = user_config.get("default_task_duration_hours", 1)
            self.default_duration_card.spinBox.setValue(default_duration)
            
            # 提醒设置
            enable_reminder = user_config.get("enable_reminder", True)
            self.enable_reminder_card.setChecked(enable_reminder)
            
            reminder_advance = user_config.get("reminder_advance_minutes", 15)
            self.reminder_advance_card.spinBox.setValue(reminder_advance)
            
            # 系统设置
            system_config = self.config_manager.system_config
            
            auto_save_interval = user_config.get("auto_save_interval_minutes", 5)
            self.auto_save_card.spinBox.setValue(auto_save_interval)
            
            update_check = system_config.get("update_check", True)
            self.update_check_card.setChecked(update_check)
            
            crash_report = system_config.get("enable_crash_report", True)
            self.crash_report_card.setChecked(crash_report)
            
            # 数据目录
            data_dir = system_config.get("data_dir", "")
            if data_dir:
                self.data_dir_card.setContent(data_dir)
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"加载配置时出错: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def save_config(self):
        """保存配置到配置管理器"""
        try:
            # 用户配置
            user_config = self.config_manager.user_config
            
            # 主题设置
            theme_index = self.theme_card.comboBox.currentIndex()
            if theme_index == 0:
                user_config["theme"] = "light"
            elif theme_index == 1:
                user_config["theme"] = "dark"
            else:
                user_config["theme"] = "auto"
            
            # 语言设置
            language_index = self.language_card.comboBox.currentIndex()
            user_config["language"] = "zh_CN" if language_index == 0 else "en_US"
            
            # 主题色
            theme_color = self.theme_color_card.color().name()
            user_config["theme_color"] = theme_color
            
            # 默认视图
            view_index = self.default_view_card.comboBox.currentIndex()
            if view_index == 0:
                user_config["start_view"] = "calendar"
            elif view_index == 1:
                user_config["start_view"] = "gantt"
            else:
                user_config["start_view"] = "flow"
            
            # 显示已完成任务
            user_config["show_completed_tasks"] = self.show_completed_card.isChecked()
            
            # 默认任务时长
            user_config["default_task_duration_hours"] = self.default_duration_card.spinBox.value()
            
            # 提醒设置
            user_config["enable_reminder"] = self.enable_reminder_card.isChecked()
            user_config["reminder_advance_minutes"] = self.reminder_advance_card.spinBox.value()
            
            # 自动保存间隔
            user_config["auto_save_interval_minutes"] = self.auto_save_card.spinBox.value()
            
            # 保存用户配置
            self.config_manager.save_user_config()
            
            # 系统配置
            system_config = self.config_manager.system_config
            
            # 更新检查
            system_config["update_check"] = self.update_check_card.isChecked()
            
            # 崩溃报告
            system_config["enable_crash_report"] = self.crash_report_card.isChecked()
            
            # 保存系统配置
            self.config_manager.save_system_config()
            
            # 显示成功信息
            InfoBar.success(
                title="成功",
                content="配置已保存",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            
            # 应用主题设置
            self.apply_theme_settings()
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"保存配置时出错: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def apply_theme_settings(self):
        """应用主题设置"""
        # 设置主题
        theme_index = self.theme_card.comboBox.currentIndex()
        if theme_index == 0:
            setTheme(Theme.LIGHT)
        elif theme_index == 1:
            setTheme(Theme.DARK)
        else:
            # 根据系统主题设置
            pass
        
        # 设置主题色
        theme_color = self.theme_color_card.color()
        setThemeColor(theme_color)
    
    def show_work_days_dialog(self):
        """显示工作日设置对话框"""
        # 创建一个对话框
        from qfluentwidgets import Dialog
        
        dialog = Dialog("工作日设置", self.window())
        
        # 创建内容
        layout = QVBoxLayout()
        
        # 添加工作日选择
        days_label = SubtitleLabel("选择工作日：")
        layout.addWidget(days_label)
        
        # 工作日复选框
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.day_checkboxes = []
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            # 加载当前设置
            work_days = self.config_manager.user_config.get("work_days", [0, 1, 2, 3, 4])
            checkbox.setChecked(i in work_days)
            self.day_checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        
        layout.addSpacing(10)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        ok_button = PrimaryPushButton("确认")
        cancel_button = PushButton("取消")
        
        ok_button.clicked.connect(lambda: self.save_work_days(dialog))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置对话框内容
        dialog.setLayout(layout)
        
        # 显示对话框
        dialog.exec_()
    
    def save_work_days(self, dialog):
        """保存工作日设置"""
        work_days = []
        for i, checkbox in enumerate(self.day_checkboxes):
            if checkbox.isChecked():
                work_days.append(i)
        
        # 确保至少选择一个工作日
        if not work_days:
            InfoBar.warning(
                title="警告",
                content="请至少选择一个工作日",
                parent=dialog,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            return
        
        # 更新配置
        self.config_manager.user_config["work_days"] = work_days
        
        # 更新工作日卡片内容
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        selected_days = [days[i] for i in work_days]
        self.work_days_card.setContent(f"已选择: {', '.join(selected_days)}")
        
        # 关闭对话框
        dialog.accept()
    
    def show_work_hours_dialog(self):
        """显示工作时间设置对话框"""
        # 创建一个对话框
        from qfluentwidgets import Dialog
        
        dialog = Dialog("工作时间设置", self.window())
        
        # 创建内容
        layout = QVBoxLayout()
        
        # 添加工作时间选择
        hours_label = SubtitleLabel("设置工作时间：")
        layout.addWidget(hours_label)
        
        form_layout = QGridLayout()
        
        # 开始时间
        start_label = QLabel("开始时间：")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        
        # 结束时间
        end_label = QLabel("结束时间：")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        
        # 加载当前设置
        work_hours = self.config_manager.user_config.get("work_hours", {"start": "09:00", "end": "18:00"})
        self.start_time_edit.setTime(QTime.fromString(work_hours.get("start", "09:00"), "HH:mm"))
        self.end_time_edit.setTime(QTime.fromString(work_hours.get("end", "18:00"), "HH:mm"))
        
        form_layout.addWidget(start_label, 0, 0)
        form_layout.addWidget(self.start_time_edit, 0, 1)
        form_layout.addWidget(end_label, 1, 0)
        form_layout.addWidget(self.end_time_edit, 1, 1)
        
        layout.addLayout(form_layout)
        layout.addSpacing(10)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        ok_button = PrimaryPushButton("确认")
        cancel_button = PushButton("取消")
        
        ok_button.clicked.connect(lambda: self.save_work_hours(dialog))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置对话框内容
        dialog.setLayout(layout)
        
        # 显示对话框
        dialog.exec_()
    
    def save_work_hours(self, dialog):
        """保存工作时间设置"""
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        
        # 验证开始时间早于结束时间
        if self.start_time_edit.time() >= self.end_time_edit.time():
            InfoBar.warning(
                title="警告",
                content="开始时间必须早于结束时间",
                parent=dialog,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            return
        
        # 更新配置
        self.config_manager.user_config["work_hours"] = {
            "start": start_time,
            "end": end_time
        }
        
        # 更新工作时间卡片内容
        self.work_hours_card.setContent(f"{start_time} - {end_time}")
        
        # 关闭对话框
        dialog.accept()
    
    def select_data_dir(self):
        """选择数据目录"""
        # 获取当前数据目录
        current_dir = self.config_manager.system_config.get("data_dir", "")
        
        # 打开目录选择对话框
        data_dir = QFileDialog.getExistingDirectory(
            self,
            "选择数据目录",
            current_dir
        )
        
        if data_dir:
            # 显示确认对话框
            message_box = MessageBoxBase(
                title="确认更改",
                content="更改数据目录将重新启动应用程序，是否继续？",
                parent=self.window()
            )
            
            # 添加按钮
            message_box.yesButton.setText("确认")
            message_box.cancelButton.setText("取消")
            
            if message_box.exec_():
                # 更新配置
                self.config_manager.system_config["data_dir"] = data_dir
                self.config_manager.save_system_config()
                
                # 更新数据目录卡片内容
                self.data_dir_card.setContent(data_dir)
                
                # 提示需要重启应用程序
                InfoBar.success(
                    title="成功",
                    content="数据目录已更改，请重启应用程序以应用更改",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
    
    def create_backup(self):
        """创建数据备份"""
        try:
            backup_file = self.config_manager.create_backup()
            
            if backup_file:
                InfoBar.success(
                    title="成功",
                    content=f"已创建备份: {backup_file}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="创建备份失败",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"创建备份出错: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def restore_backup(self):
        """恢复数据备份"""
        try:
            # 获取备份目录
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            backup_dir = os.path.join(base_dir, 'data', 'backups')
            
            # 打开文件选择对话框
            backup_file, _ = QFileDialog.getOpenFileName(
                self,
                "选择备份文件",
                backup_dir,
                "备份文件 (*.zip)"
            )
            
            if not backup_file:
                return
            
            # 显示确认对话框
            message_box = MessageBoxBase(
                title="确认恢复",
                content="恢复备份将覆盖当前数据，是否继续？",
                parent=self.window()
            )
            
            # 添加按钮
            message_box.yesButton.setText("确认")
            message_box.cancelButton.setText("取消")
            
            if message_box.exec_():
                # 恢复备份
                success = self.config_manager.restore_backup(backup_file)
                
                if success:
                    InfoBar.success(
                        title="成功",
                        content="已恢复备份，请重启应用程序以应用更改",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
                else:
                    InfoBar.error(
                        title="错误",
                        content="恢复备份失败",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"恢复备份出错: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def on_theme_changed(self, index):
        """主题变更事件处理"""
        if index == 0:  # 浅色
            setTheme(Theme.LIGHT)
        elif index == 1:  # 深色
            setTheme(Theme.DARK)
        else:  # 跟随系统
            # 可以根据系统主题设置
            pass
    
    def on_theme_color_changed(self, color):
        """主题色变更事件处理"""
        setThemeColor(color) 