#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件管理对话框
负责显示和管理应用插件
"""

import logging
import os
import zipfile
import shutil
import json
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QPushButton, QMessageBox, QTabWidget,
    QFileDialog, QLineEdit, QGridLayout, QListWidget,
    QListWidgetItem, QProgressBar, QTabBar
)
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import (
    PrimaryPushButton, InfoBar, 
    InfoBarPosition, FluentIcon,
    IconWidget, StrongBodyLabel,
    BodyLabel, 
    CardWidget, LineEdit, SearchLineEdit,
    TransparentPushButton, TransparentToolButton,
    ToolTipPosition
)

logger = logging.getLogger(__name__)

class PluginInstallCard(CardWidget):
    """插件安装卡片"""
    
    def __init__(self, plugin_name, description, author, version, parent=None):
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.description = description
        self.author = author
        self.version = version
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        
        # 标题和版本
        title_layout = QHBoxLayout()
        
        icon = IconWidget(FluentIcon.APPLICATION, self)
        icon.setFixedSize(24, 24)
        title_layout.addWidget(icon)
        
        title = StrongBodyLabel(self.plugin_name)
        title_layout.addWidget(title)
        
        title_layout.addStretch(1)
        
        version = QLabel(f"v{self.version}")
        version.setObjectName("PluginVersion")
        title_layout.addWidget(version)
        
        main_layout.addLayout(title_layout)
        
        # 描述
        desc = BodyLabel(self.description)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)
        
        # 作者
        author = QLabel(f"作者: {self.author}")
        author.setObjectName("PluginAuthor")
        main_layout.addWidget(author)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.install_btn = TransparentPushButton("安装")
        self.install_btn.setIcon(FluentIcon.DOWNLOAD)
        button_layout.addWidget(self.install_btn)
        
        main_layout.addLayout(button_layout)

class PluginManagerDialog(QDialog):
    """插件管理对话框"""
    
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.parent = parent
        
        # 设置对话框属性
        self.setWindowTitle("插件管理")
        self.resize(700, 500)
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 头部
        header_layout = QHBoxLayout()
        
        # 标题
        header_label = StrongBodyLabel("插件管理")
        header_label.setObjectName("DialogTitle")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch(1)
        
        # 帮助按钮
        self.help_btn = TransparentToolButton(FluentIcon.INFO, self)
        self.help_btn.setToolTip("查看插件开发文档")
        self.help_btn.clicked.connect(self.open_help_docs)
        header_layout.addWidget(self.help_btn)
        
        main_layout.addLayout(header_layout)
        
        # 选项卡
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("PluginTabWidget")
        
        # 本地安装选项卡
        self.local_tab = QWidget()
        local_layout = QVBoxLayout(self.local_tab)
        local_layout.setContentsMargins(0, 16, 0, 0)
        
        # 本地安装说明
        local_info = BodyLabel("您可以通过以下方式安装插件:")
        local_layout.addWidget(local_info)
        
        # 安装方法选项卡
        install_methods = QTabBar(self)
        install_methods.addTab("从文件安装")
        install_methods.addTab("从目录安装")
        install_methods.addTab("开发新插件")
        
        local_layout.addWidget(install_methods)
        
        # 从文件安装
        self.file_install_widget = QWidget()
        file_layout = QVBoxLayout(self.file_install_widget)
        
        file_hint = BodyLabel("选择一个插件安装包文件 (.zip):")
        file_layout.addWidget(file_hint)
        
        file_select_layout = QHBoxLayout()
        self.file_path_edit = LineEdit(self)
        self.file_path_edit.setPlaceholderText("请选择插件文件...")
        self.file_path_edit.setReadOnly(True)
        file_select_layout.addWidget(self.file_path_edit)
        
        self.browse_btn = QPushButton("浏览", self)
        self.browse_btn.clicked.connect(self.browse_plugin_file)
        file_select_layout.addWidget(self.browse_btn)
        
        file_layout.addLayout(file_select_layout)
        
        install_btn = PrimaryPushButton("安装插件", self)
        install_btn.clicked.connect(self.install_from_file)
        file_layout.addWidget(install_btn, 0, Qt.AlignRight)
        
        file_layout.addStretch(1)
        
        # 从目录安装
        self.dir_install_widget = QWidget()
        dir_layout = QVBoxLayout(self.dir_install_widget)
        
        dir_hint = BodyLabel("选择包含插件的目录:")
        dir_layout.addWidget(dir_hint)
        
        dir_select_layout = QHBoxLayout()
        self.dir_path_edit = LineEdit(self)
        self.dir_path_edit.setPlaceholderText("请选择插件目录...")
        self.dir_path_edit.setReadOnly(True)
        dir_select_layout.addWidget(self.dir_path_edit)
        
        self.browse_dir_btn = QPushButton("浏览", self)
        self.browse_dir_btn.clicked.connect(self.browse_plugin_dir)
        dir_select_layout.addWidget(self.browse_dir_btn)
        
        dir_layout.addLayout(dir_select_layout)
        
        install_dir_btn = PrimaryPushButton("安装插件", self)
        install_dir_btn.clicked.connect(self.install_from_dir)
        dir_layout.addWidget(install_dir_btn, 0, Qt.AlignRight)
        
        dir_layout.addStretch(1)
        
        # 开发新插件
        self.dev_widget = QWidget()
        dev_layout = QVBoxLayout(self.dev_widget)
        
        dev_hint = BodyLabel("创建一个新的插件项目:")
        dev_layout.addWidget(dev_hint)
        
        plugin_id_layout = QHBoxLayout()
        plugin_id_label = QLabel("插件ID:")
        plugin_id_layout.addWidget(plugin_id_label)
        
        self.plugin_id_edit = LineEdit(self)
        self.plugin_id_edit.setPlaceholderText("输入插件ID (如: my_plugin)")
        plugin_id_layout.addWidget(self.plugin_id_edit)
        
        dev_layout.addLayout(plugin_id_layout)
        
        plugin_name_layout = QHBoxLayout()
        plugin_name_label = QLabel("插件名称:")
        plugin_name_layout.addWidget(plugin_name_label)
        
        self.plugin_name_edit = LineEdit(self)
        self.plugin_name_edit.setPlaceholderText("输入插件名称 (如: 我的插件)")
        plugin_name_layout.addWidget(self.plugin_name_edit)
        
        dev_layout.addLayout(plugin_name_layout)
        
        create_btn = PrimaryPushButton("创建插件模板", self)
        create_btn.clicked.connect(self.create_plugin_template)
        dev_layout.addWidget(create_btn, 0, Qt.AlignRight)
        
        dev_layout.addStretch(1)
        
        # 在选项卡之间切换的处理
        def on_tab_changed(index):
            if index == 0:
                local_layout.itemAt(2).widget().setParent(None)
                local_layout.insertWidget(2, self.file_install_widget)
            elif index == 1:
                local_layout.itemAt(2).widget().setParent(None)
                local_layout.insertWidget(2, self.dir_install_widget)
            elif index == 2:
                local_layout.itemAt(2).widget().setParent(None)
                local_layout.insertWidget(2, self.dev_widget)
        
        install_methods.currentChanged.connect(on_tab_changed)
        
        # 默认显示第一个
        local_layout.addWidget(self.file_install_widget)
        
        # 仓库选项卡
        self.repo_tab = QWidget()
        repo_layout = QVBoxLayout(self.repo_tab)
        repo_layout.setContentsMargins(0, 16, 0, 0)
        
        # 仓库说明
        repo_info = BodyLabel("从插件仓库浏览和安装插件:")
        repo_layout.addWidget(repo_info)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.repo_search = SearchLineEdit(self)
        self.repo_search.setPlaceholderText("搜索插件...")
        search_layout.addWidget(self.repo_search)
        
        self.refresh_btn = TransparentToolButton(FluentIcon.SYNC, self)
        self.refresh_btn.setToolTip("刷新仓库")
        self.refresh_btn.clicked.connect(self.refresh_repository)
        search_layout.addWidget(self.refresh_btn)
        
        repo_layout.addLayout(search_layout)
        
        # 插件列表
        self.plugin_list = QListWidget(self)
        self.plugin_list.setObjectName("PluginList")
        repo_layout.addWidget(self.plugin_list)
        
        # 添加示例插件
        self.add_repository_example()
        
        # 添加选项卡
        self.tab_widget.addTab(self.local_tab, "本地安装")
        self.tab_widget.addTab(self.repo_tab, "插件仓库")
        
        main_layout.addWidget(self.tab_widget)
    
    def browse_plugin_file(self):
        """浏览选择插件文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "ZIP压缩文件 (*.zip);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def browse_plugin_dir(self):
        """浏览选择插件目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择插件目录", ""
        )
        
        if dir_path:
            self.dir_path_edit.setText(dir_path)
    
    def install_from_file(self):
        """从文件安装插件"""
        file_path = self.file_path_edit.text()
        if not file_path:
            InfoBar.warning(
                title="警告",
                content="请选择一个插件文件",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        try:
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # 解压文件
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找插件信息文件
            plugin_json = None
            for root, dirs, files in os.walk(temp_dir):
                if 'plugin.json' in files:
                    plugin_json = os.path.join(root, 'plugin.json')
                    break
            
            if not plugin_json:
                InfoBar.error(
                    title="错误",
                    content="无效的插件包，未找到plugin.json文件",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                # 清理临时目录
                shutil.rmtree(temp_dir)
                return
            
            # 读取插件信息
            with open(plugin_json, 'r', encoding='utf-8') as f:
                plugin_info = json.load(f)
            
            # 获取插件ID
            plugin_id = plugin_info.get('id')
            if not plugin_id:
                InfoBar.error(
                    title="错误",
                    content="无效的插件，plugin.json中缺少id字段",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                # 清理临时目录
                shutil.rmtree(temp_dir)
                return
            
            # 获取插件目录
            plugin_dir = getattr(self.plugin_manager, 'plugin_dir', None)
            if not plugin_dir:
                plugin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins')
                
            # 确保插件目录存在
            os.makedirs(plugin_dir, exist_ok=True)
            
            # 检查插件是否已存在
            target_dir = os.path.join(plugin_dir, plugin_id)
            if os.path.exists(target_dir):
                confirm = QMessageBox.question(
                    self,
                    "插件已存在",
                    f"插件 {plugin_id} 已存在，是否覆盖安装？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if confirm == QMessageBox.No:
                    # 清理临时目录
                    shutil.rmtree(temp_dir)
                    return
                
                # 删除现有插件
                shutil.rmtree(target_dir)
            
            # 查找插件根目录（包含plugin.json的目录）
            plugin_root = os.path.dirname(plugin_json)
            
            # 复制插件文件
            shutil.copytree(plugin_root, target_dir)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 刷新插件列表
            if hasattr(self.plugin_manager, "reload_plugins"):
                self.plugin_manager.reload_plugins()
            
            InfoBar.success(
                title="成功",
                content=f"插件 {plugin_id} 安装成功",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            
            # 清空文件路径
            self.file_path_edit.clear()
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"插件安装失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
            # 清理临时目录（如果存在）
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
    
    def install_from_dir(self):
        """从目录安装插件"""
        dir_path = self.dir_path_edit.text()
        if not dir_path:
            InfoBar.warning(
                title="警告",
                content="请选择一个插件目录",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        try:
            # 检查插件结构
            plugin_json = os.path.join(dir_path, 'plugin.json')
            if not os.path.exists(plugin_json):
                InfoBar.error(
                    title="错误",
                    content="无效的插件目录，缺少plugin.json文件",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return
            
            # 读取插件信息
            with open(plugin_json, 'r', encoding='utf-8') as f:
                plugin_info = json.load(f)
            
            # 获取插件ID
            plugin_id = plugin_info.get('id')
            if not plugin_id:
                InfoBar.error(
                    title="错误",
                    content="无效的插件，plugin.json中缺少id字段",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return
            
            # 获取插件目录
            plugin_dir = getattr(self.plugin_manager, 'plugin_dir', None)
            if not plugin_dir:
                plugin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins')
                
            # 确保插件目录存在
            os.makedirs(plugin_dir, exist_ok=True)
            
            # 检查插件是否已存在
            target_dir = os.path.join(plugin_dir, plugin_id)
            if os.path.exists(target_dir):
                confirm = QMessageBox.question(
                    self,
                    "插件已存在",
                    f"插件 {plugin_id} 已存在，是否覆盖安装？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if confirm == QMessageBox.No:
                    return
                
                # 删除现有插件
                shutil.rmtree(target_dir)
            
            # 复制插件目录
            shutil.copytree(dir_path, target_dir)
            
            # 刷新插件列表
            if hasattr(self.plugin_manager, "reload_plugins"):
                self.plugin_manager.reload_plugins()
            
            InfoBar.success(
                title="成功",
                content=f"插件 {plugin_id} 安装成功",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            
            # 清空目录路径
            self.dir_path_edit.clear()
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"插件安装失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def create_plugin_template(self):
        """创建插件模板"""
        plugin_id = self.plugin_id_edit.text()
        plugin_name = self.plugin_name_edit.text()
        
        if not plugin_id:
            InfoBar.warning(
                title="警告",
                content="请输入插件ID",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        if not plugin_name:
            plugin_name = plugin_id
        
        try:
            # 获取插件目录
            plugin_dir = getattr(self.plugin_manager, 'plugin_dir', None)
            if not plugin_dir:
                plugin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins')
                
            # 确保插件目录存在
            os.makedirs(plugin_dir, exist_ok=True)
            
            # 检查插件是否已存在
            target_dir = os.path.join(plugin_dir, plugin_id)
            if os.path.exists(target_dir):
                confirm = QMessageBox.question(
                    self,
                    "插件已存在",
                    f"插件 {plugin_id} 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if confirm == QMessageBox.No:
                    return
                
                # 删除现有插件
                shutil.rmtree(target_dir)
            
            # 创建插件目录
            os.makedirs(target_dir, exist_ok=True)
            
            # 创建插件文件
            self.create_plugin_files(target_dir, plugin_id, plugin_name)
            
            InfoBar.success(
                title="成功",
                content=f"插件模板 {plugin_id} 创建成功",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            
            # 打开插件目录
            QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir))
            
            # 清空输入框
            self.plugin_id_edit.clear()
            self.plugin_name_edit.clear()
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"创建插件模板失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def create_plugin_files(self, plugin_dir, plugin_id, plugin_name):
        """创建插件模板文件"""
        # 创建插件信息文件
        plugin_info = {
            "id": plugin_id,
            "name": plugin_name,
            "version": "0.1.0",
            "description": "一个示例插件",
            "author": "您的名字",
            "email": "your.email@example.com",
            "tags": ["工具"],
            "dependencies": []
        }
        
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w', encoding='utf-8') as f:
            json.dump(plugin_info, f, ensure_ascii=False, indent=4)
        
        # 创建主插件文件
        plugin_py = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
{plugin_name}
一个示例插件
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

# 从插件管理器导入插件基类
from core.plugin_manager import Plugin

# 插件信息
NAME = "{plugin_name}"
VERSION = "0.1.0"
DESCRIPTION = "一个示例插件"

class {plugin_id.capitalize().replace("_", "")}Plugin(Plugin):
    """
    {plugin_name} 插件实现
    """
    
    def __init__(self, plugin_id="{plugin_id}", name=NAME, version=VERSION, description=DESCRIPTION):
        """初始化插件"""
        super().__init__(plugin_id, name, version, description)
    
    def initialize(self, app):
        """
        初始化插件
        
        参数:
            app: 应用程序实例
            
        返回:
            bool: 初始化成功返回True，失败返回False
        """
        # 在这里进行插件的初始化工作
        return True
    
    def cleanup(self):
        """
        清理插件资源
        
        返回:
            bool: 清理成功返回True，失败返回False
        """
        # 在这里进行插件的清理工作
        return True
    
    def get_config_ui(self):
        """
        获取插件配置界面
        
        返回:
            QWidget: 配置界面组件，如无配置界面则返回None
        """
        # 创建一个简单的配置界面
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("这是 {plugin_name} 插件的配置界面"))
        return widget
    
    def get_main_ui(self):
        """
        获取插件主界面
        
        返回:
            QWidget: 主界面组件，如无主界面则返回None
        """
        # 创建一个简单的主界面
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("这是 {plugin_name} 插件的主界面"))
        return widget
'''
        
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w', encoding='utf-8') as f:
            f.write(plugin_py)
        
        # 创建README文件
        readme = f'''# {plugin_name}

一个示例插件

## 功能

请在这里描述您的插件功能

## 安装

1. 下载插件
2. 解压到插件目录
3. 启动应用并在插件管理器中启用插件

## 配置

描述您的插件配置选项

## 使用方法

描述您的插件使用方法

## 版本历史

- 0.1.0: 初始版本

## 作者

您的名字

## 许可证

MIT
'''
        
        with open(os.path.join(plugin_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)
        
        # 创建配置目录
        os.makedirs(os.path.join(plugin_dir, 'config'), exist_ok=True)
        
        # 创建资源目录
        os.makedirs(os.path.join(plugin_dir, 'resources'), exist_ok=True)
    
    def add_repository_example(self):
        """添加示例插件到仓库列表"""
        example_plugins = [
            {
                "name": "任务模板管理器",
                "description": "添加和管理任务模板，快速创建常用任务",
                "author": "插件示例",
                "version": "1.0.0"
            },
            {
                "name": "数据分析工具",
                "description": "提供任务数据的可视化分析功能",
                "author": "插件示例",
                "version": "1.2.1"
            },
            {
                "name": "番茄钟",
                "description": "集成番茄工作法，提高工作效率",
                "author": "插件示例",
                "version": "0.9.5"
            }
        ]
        
        for plugin in example_plugins:
            item = QListWidgetItem()
            self.plugin_list.addItem(item)
            
            card = PluginInstallCard(
                plugin["name"],
                plugin["description"],
                plugin["author"],
                plugin["version"]
            )
            
            item.setSizeHint(card.sizeHint())
            self.plugin_list.setItemWidget(item, card)
    
    def refresh_repository(self):
        """刷新插件仓库"""
        # 显示刷新中状态
        InfoBar.info(
            title="刷新中",
            content="正在从仓库获取最新插件列表...",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
        # 这里只是模拟刷新效果，实际应用应该连接到插件仓库API
        # 清空列表
        self.plugin_list.clear()
        
        # 重新添加示例插件
        self.add_repository_example()
    
    def open_help_docs(self):
        """打开帮助文档"""
        # 这里可以打开本地文档或打开网页
        QDesktopServices.openUrl(QUrl("https://example.com/plugin-docs")) 