#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
排期软件主窗口
实现主界面布局和功能
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QDateTime, QSettings, QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QSplitter, QSystemTrayIcon, QMenu, QAction,
    QMessageBox, QDateEdit, QTimeEdit, QDialog, QLineEdit, QPushButton,
    QTextEdit, QComboBox, QFormLayout, QApplication
)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, MessageBox,
    isDarkTheme, setTheme, Theme, SubtitleLabel, BodyLabel, 
    PushButton, FluentIcon, SplashScreen, InfoBar, InfoBarPosition, 
    FluentWindow, CalendarPicker, RoundMenu, Action, NavigationWidget,
    ComboBox, LineEdit, Dialog, PrimaryPushButton, TransparentToolButton,
    MSFluentWindow
)

from core.scheduler import SchedulerManager
from core.config_manager import ConfigManager
from core.plugin_manager import PluginManager
from core.subtask_manager import SubtaskManager
from ui.calendar_view import CalendarView
from ui.gantt_view import GanttView
from ui.task_dialog import TaskDialog
from ui.settings_dialog import SettingsDialog
from ui.config_view import ConfigView
from ui.plugin_view import PluginView

# 配置日志
logger = logging.getLogger("MainWindow")

class SchedulerMainWindow(FluentWindow):
    """排期软件主窗口"""
    
    def __init__(self, config_manager=None, plugin_manager=None):
        super().__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle("个人排期助手")
        self.resize(1000, 700)
        
        # 初始化配置管理器
        self.config_manager = config_manager if config_manager else ConfigManager()
        
        # 初始化插件管理器
        self.plugin_manager = plugin_manager if plugin_manager else PluginManager(self.config_manager)
        
        # 初始化调度管理器
        data_file = self.config_manager.get_config_value("system", "data_dir", None)
        self.scheduler_manager = SchedulerManager(data_file, self.plugin_manager)
        
        # 初始化子任务管理器
        self.subtask_manager = SubtaskManager(self.scheduler_manager)
        
        # 插件视图容器
        self.plugin_views = {}
        
        # 初始化界面
        self.initUi()
        
        # 初始化系统托盘和提醒功能
        self.initTray()
        
        # 设置定时器检查提醒（每分钟检查一次）
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.checkReminders)
        self.reminder_timer.start(60000)  # 60秒 = 1分钟
        
        # 设置定时器检查任务到期状态（每10分钟检查一次）
        self.overdue_timer = QTimer(self)
        self.overdue_timer.timeout.connect(self.checkOverdueTasks)
        self.overdue_timer.start(600000)  # 600秒 = 10分钟
        
        # 加载用户配置
        self.loadUserConfig()
        
        # 触发应用程序启动事件
        self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_APPLICATION_START, self)
    
    def initUi(self):
        """初始化用户界面"""
        # 创建视图
        self.calendar_view = CalendarView(self.scheduler_manager)
        self.gantt_view = GanttView(self.scheduler_manager)
        
        # 添加导航项
        self.addSubInterface(self.calendar_view, FluentIcon.DATE_TIME, "日程视图")
        self.addSubInterface(self.gantt_view, FluentIcon.VIEW, "甘特图")
        
        # 添加到底部导航栏
        self.navigationInterface.addItem(
            routeKey='add_task',
            icon=FluentIcon.ADD,
            text="添加任务",
            onClick=self.addTask,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 添加设置菜单
        self.navigationInterface.addItem(
            routeKey='settings',
            icon=FluentIcon.SETTING,
            text="设置",
            onClick=self.openSettings,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 添加插件管理按钮
        self.navigationInterface.addItem(
            routeKey='plugins',
            icon=FluentIcon.APPLICATION,
            text="插件管理",
            onClick=self.openPluginManager,
            position=NavigationItemPosition.BOTTOM
        )
    
    def loadUserConfig(self):
        """加载用户配置"""
        # 设置主题
        theme = self.config_manager.get_config_value("user", "theme", "auto")
        if theme == "dark":
            setTheme(Theme.DARK)
        elif theme == "light":
            setTheme(Theme.LIGHT)
        # auto模式下不需要设置，qfluentwidgets会自动适应系统主题
        
        # 设置视图
        start_view = self.config_manager.get_config_value("user", "start_view", "calendar")
        if start_view == "calendar":
            self.switchTo(self.calendar_view)
        elif start_view == "gantt":
            self.switchTo(self.gantt_view)
    
    def addTask(self):
        """添加新任务"""
        dialog = TaskDialog(
            self, 
            self.scheduler_manager,
            self.config_manager,
            self.subtask_manager
        )
        if dialog.exec_():
            # 获取新创建的任务
            latest_task = self.scheduler_manager.get_latest_task()
            if latest_task:
                # 触发任务创建事件
                self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_TASK_CREATED, latest_task)
            
            # 刷新各个视图
            self.calendar_view.refresh()
            self.gantt_view.refresh()
            
            # 刷新插件视图
            for view in self.plugin_views.values():
                if hasattr(view, 'refresh') and callable(view.refresh):
                    view.refresh()
            
            # 显示添加成功提示
            InfoBar.success(
                title="成功",
                content="任务已添加到排期中",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
    
    def initTray(self):
        """初始化系统托盘图标和菜单"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用默认应用图标
        app_icon = QIcon(QPixmap(":/gallery/images/logo.png"))
        if app_icon.isNull():
            # 如果找不到图标，使用FluentIcon
            from qfluentwidgets import getIconColor, Theme, isDarkTheme
            self.tray_icon.setIcon(FluentIcon.CALENDAR.icon(getIconColor() if isDarkTheme() else Theme.DARK))
        else:
            self.tray_icon.setIcon(app_icon)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加操作
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        # 最小化到托盘选项
        minimize_action = tray_menu.addAction("关闭时最小化到托盘")
        minimize_action.setCheckable(True)
        minimize_action.setChecked(self.config_manager.get_config_value("system", "minimize_to_tray", True))
        minimize_action.triggered.connect(self.toggleMinimizeToTray)
        
        tray_menu.addSeparator()
        
        # 正常退出 - 应用关闭策略
        exit_action = tray_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 强制退出 - 直接退出
        force_quit_action = tray_menu.addAction("强制退出")
        force_quit_action.triggered.connect(self.forceQuit)
        
        # 设置菜单
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.onTrayActivated)
        self.tray_icon.show()
    
    def toggleMinimizeToTray(self, checked):
        """切换关闭时最小化到托盘的选项"""
        self.config_manager.set_config_value("system", "minimize_to_tray", checked)
        self.config_manager.save_config()
    
    def onTrayActivated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def checkReminders(self):
        """检查是否有需要提醒的任务"""
        try:
            now = datetime.now()
            reminders = self.scheduler_manager.get_reminders(now)
            
            for task in reminders:
                # 显示系统通知
                self.tray_icon.showMessage(
                    "任务提醒",
                    f"{task['title']} - {task.get('description', '')}",
                    QSystemTrayIcon.Information,
                    5000
                )
        except Exception as e:
            print(f"检查提醒时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def checkOverdueTasks(self):
        """检查并更新已到期任务的状态"""
        logger.info("检查任务到期状态")
        try:
            # 调用调度管理器的到期检查方法
            if self.scheduler_manager.check_overdue_tasks():
                # 如果有任务状态被更新，刷新视图
                logger.info("有任务状态被更新，刷新视图")
                # 刷新各个视图
                self.calendar_view.refresh()
                self.gantt_view.refresh()
                
                # 刷新插件视图
                for view in self.plugin_views.values():
                    if hasattr(view, 'refresh') and callable(view.refresh):
                        try:
                            view.refresh()
                        except Exception as e:
                            logger.error(f"刷新插件视图时出错: {e}")
        except Exception as e:
            logger.error(f"检查任务到期状态时出错: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件，处理最小化到托盘或退出"""
        # 检查是否要退出或最小化到托盘
        if self.config_manager.get_config_value("user", "minimize_to_tray", False):
            # 用户设置了最小化到托盘
            if not QSystemTrayIcon.isSystemTrayAvailable():
                # 系统不支持托盘图标，直接退出
                InfoBar.error(
                    title="错误",
                    content="系统不支持托盘功能，程序将直接退出",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                self.saveWindowState()
                # 停止调度管理器的定时器
                self.scheduler_manager.stop_timer()
                event.accept()
                return
            
            # 最小化到托盘
            event.ignore()
            self.hide()
            InfoBar.success(
                title="提示",
                content="程序已最小化到系统托盘",
                parent=None,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000
            )
        else:
            # 触发应用程序退出事件
            self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_APPLICATION_QUIT, self)
            # 保存窗口状态
            self.saveWindowState()
            # 停止调度管理器的定时器
            self.scheduler_manager.stop_timer()
            # 清理插件资源
            self.plugin_manager.cleanup()
            # 接受关闭事件
            event.accept()
    
    def saveWindowState(self):
        """保存窗口状态"""
        try:
            settings = QSettings("InfoFlow", "PersonalScheduler")
            settings.setValue("geometry", self.saveGeometry())
        except Exception as e:
            logger.error(f"保存窗口状态时出错: {e}")
            
    def forceQuit(self):
        """强制退出程序"""
        # 停止调度管理器的定时器
        self.scheduler_manager.stop_timer()
        # 确保真正退出
        self.tray_icon.hide()
        QApplication.quit()

    def find_calendar_view(self):
        """查找日历视图
        
        Returns:
            CalendarView: 日历视图实例，如果找不到则返回None
        """
        try:
            for interface in self.findChildren(QWidget):
                if isinstance(interface, CalendarView):
                    return interface
            return None
        except Exception as e:
            logger.error(f"查找日历视图时出错: {e}")
            return None
    
    def find_gantt_view(self):
        """查找甘特图视图
        
        Returns:
            GanttView: 甘特图视图实例，如果找不到则返回None
        """
        try:
            for interface in self.findChildren(QWidget):
                if isinstance(interface, GanttView):
                    return interface
            return None
        except Exception as e:
            logger.error(f"查找甘特图视图时出错: {e}")
            return None
    
    def openSettings(self):
        """打开设置对话框"""
        # 创建设置对话框
        dialog = SettingsDialog(self, self.config_manager)
        if dialog.exec_():
            # 用户点击了保存按钮
            
            # 重新加载用户配置
            self.loadUserConfig()
            
            # 触发设置变更事件
            self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_SETTINGS_CHANGED, {
                "config_manager": self.config_manager
            })
            
            # 刷新日程视图
            self.calendar_view.refresh()
            self.gantt_view.refresh()
            
            # 刷新插件视图
            for view in self.plugin_views.values():
                if hasattr(view, 'refresh') and callable(view.refresh):
                    view.refresh()
    
    def openPluginManager(self):
        """打开插件管理器窗口"""
        # 创建插件视图
        plugin_view = PluginView(self.plugin_manager, self.config_manager, self)
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("插件管理")
        dialog.resize(900, 600)
        
        # 设置布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(plugin_view)
        
        # 显示对话框
        dialog.exec_()
    
    def register_plugin_view(self, plugin_id, view, icon, title):
        """
        注册插件视图
        
        参数:
            plugin_id: 插件ID
            view: 插件视图组件
            icon: 图标
            title: 标题
            
        返回:
            bool: 注册成功返回True，失败返回False
        """
        # 检查插件ID是否已注册
        if plugin_id in self.plugin_views:
            return False
            
        try:
            # 添加到导航界面
            from qfluentwidgets import FluentIcon
            
            # 处理图标，如果是字符串，尝试从FluentIcon获取
            if isinstance(icon, str) and hasattr(FluentIcon, icon.replace("FluentIcon.", "")):
                icon_name = icon.replace("FluentIcon.", "")
                icon = getattr(FluentIcon, icon_name)
                
            # 添加到导航界面
            self.addSubInterface(view, icon, title)
            
            # 保存到插件视图字典
            self.plugin_views[plugin_id] = view
            
            # 触发视图变更事件
            self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_VIEW_CHANGED, {
                "plugin_id": plugin_id,
                "action": "added",
                "view": view,
                "title": title
            })
            
            return True
        except Exception as e:
            logger.error(f"注册插件视图失败: {str(e)}")
            return False
    
    def unregister_plugin_view(self, plugin_id):
        """
        取消注册插件视图
        
        参数:
            plugin_id: 插件ID
            
        返回:
            bool: 取消注册成功返回True，失败返回False
        """
        # 检查插件ID是否已注册
        if plugin_id not in self.plugin_views:
            return False
            
        try:
            # 获取视图组件
            view = self.plugin_views[plugin_id]
            
            # 从导航界面移除
            self.removeSubInterface(view)
            
            # 从插件视图字典中移除
            del self.plugin_views[plugin_id]
            
            # 触发视图变更事件
            self.plugin_manager.dispatch_event(self.plugin_manager.EVENT_VIEW_CHANGED, {
                "plugin_id": plugin_id,
                "action": "removed",
                "view": view
            })
            
            return True
        except Exception as e:
            logger.error(f"取消注册插件视图失败: {str(e)}")
            return False
    
    def reload_plugin(self, plugin_id):
        """重新加载指定插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 重载成功返回True，失败返回False
        """
        try:
            # 如果存在相应视图，先移除
            if plugin_id in self.plugin_views:
                # 使用unregister_plugin_view方法移除视图，避免直接调用不存在的方法
                self.unregister_plugin_view(plugin_id)
            
            # 卸载插件
            if plugin_id in self.plugin_manager.plugins:
                self.plugin_manager.unload_plugin(plugin_id)
                
            # 创建应用程序上下文
            from core.app_context import AppContext
            app_context = AppContext(
                main_window=self,
                config_manager=self.config_manager,
                plugin_manager=self.plugin_manager,
                scheduler_manager=self.scheduler_manager
            )
                
            # 重新加载插件
            success = self.plugin_manager.load_plugin(plugin_id, app_context)
            if success:
                # 获取插件实例
                plugin = self.plugin_manager.get_plugin(plugin_id)
                
                # 获取主界面，如果有
                if hasattr(plugin, 'get_main_ui') and callable(plugin.get_main_ui):
                    main_ui = plugin.get_main_ui()
                    if main_ui:
                        # 注册视图
                        self.register_plugin_view(
                            plugin_id, 
                            main_ui, 
                            FluentIcon.APPLICATION, 
                            plugin.name
                        )
                
                InfoBar.success(
                    title="成功",
                    content=f"插件 {plugin_id} 已重新加载",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return True
            
            InfoBar.error(
                title="失败",
                content=f"插件 {plugin_id} 重新加载失败",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            return False
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"重新加载插件时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            import traceback
            traceback.print_exc()
            return False

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        
    def resizeEvent(self, event):
        """重写窗口大小变化事件"""
        super().resizeEvent(event)

    def removeSubInterface(self, interface):
        """
        从界面中移除子界面
        
        参数:
            interface: 要移除的界面
        """
        try:
            # 首先判断当前是否在该界面，如果是则切换到安全界面
            if hasattr(self, 'stackedWidget') and self.stackedWidget.currentWidget() == interface:
                # 切换到日程视图
                if hasattr(self, 'calendar_view') and self.calendar_view:
                    self.switchTo(self.calendar_view)
                # 如果没有日程视图，尝试切换到第一个可用的视图
                elif hasattr(self, 'stackedWidget') and self.stackedWidget.count() > 1:
                    for i in range(self.stackedWidget.count()):
                        widget = self.stackedWidget.widget(i)
                        if widget != interface:
                            self.switchTo(widget)
                            break
            
            # 如果界面在栈部件中，移除它
            if hasattr(self, 'stackedWidget'):
                index = self.stackedWidget.indexOf(interface)
                if index >= 0:
                    self.stackedWidget.removeWidget(interface)
            
            # 隐藏界面并设置无父级
            interface.hide()
            interface.setParent(None)
            
            return True
        except Exception as e:
            logger.error(f"移除子界面失败: {str(e)}")
            return False 