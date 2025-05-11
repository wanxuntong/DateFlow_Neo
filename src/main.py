#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
个人排期软件主程序
负责启动应用程序并加载主界面
"""

import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from qfluentwidgets import FluentTranslator

# 导入配置管理器和插件管理器
from core.config_manager import ConfigManager
from core.plugin_manager import PluginManager
from core.app_context import AppContext

# 导入主窗口
from ui.main_window import SchedulerMainWindow

# 导入日志工具
from utils.logger import configure_logging, get_logger

# 配置日志系统
configure_logging(console_level="info", file_level="debug")
logger = get_logger("Main", app="InfoFlow")

def main():
    """程序入口函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="InfoFlow个人排期管理工具")
    parser.add_argument("--no-splash", action="store_true", help="不显示启动画面")
    args = parser.parse_args()
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置样式和翻译
    translator = FluentTranslator()
    app.installTranslator(translator)
    
    # 创建启动画面（除非指定了--no-splash参数）
    splash = None
    if not args.no_splash:
        splash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "images", "splash.png")
        if os.path.exists(splash_path):
            splash_pix = QPixmap(splash_path)
            splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
            splash.setWindowFlag(Qt.FramelessWindowHint)
            splash.show()
            app.processEvents()
            logger.info("启动画面已显示")
        else:
            logger.warning(f"未找到启动画面图片: {splash_path}")
    
    # 初始化配置管理器
    logger.debug("初始化配置管理器")
    config_manager = ConfigManager()
    
    # 初始化插件管理器
    logger.debug("初始化插件管理器")
    plugin_manager = PluginManager(config_manager)
    
    # 创建主窗口
    logger.debug("创建主窗口")
    window = SchedulerMainWindow(config_manager, plugin_manager)
    
    # 延迟显示主窗口，加载插件
    def show_main_window():
        # 创建应用程序上下文
        logger.debug("创建应用程序上下文")
        app_context = AppContext(
            main_window=window,
            config_manager=config_manager,
            plugin_manager=plugin_manager,
            scheduler_manager=window.scheduler_manager
        )
        
        # 加载启用的插件
        logger.info("开始加载插件")
        plugin_results = plugin_manager.load_enabled_plugins(app_context)
        if plugin_results:
            logger.info("插件加载完成", count=len(plugin_results))
            
        # 显示主窗口
        logger.info("显示主窗口")
        window.show()
        
        # 关闭启动画面
        if splash:
            splash.finish(window)
            logger.debug("关闭启动画面")
    
    # 设置延时显示
    logger.debug("设置延时显示主窗口")
    QTimer.singleShot(1000 if splash else 0, show_main_window)
    
    # 运行应用程序
    logger.info("应用程序开始运行")
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"程序运行出错: {str(e)}")
        raise 