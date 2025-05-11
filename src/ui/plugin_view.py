#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件管理视图
用于管理和配置插件
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QSplitter, QStackedWidget
)

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, 
    ToggleButton, BodyLabel, CardWidget, 
    SubtitleLabel, LineEdit, SearchLineEdit,
    TitleLabel, InfoBar, InfoBarPosition,
    TransparentToolButton, ToolTipFilter, ToolTipPosition,
    IconWidget
)

class PluginCard(CardWidget):
    """插件卡片组件"""
    
    # 插件状态变更信号
    statusChanged = pyqtSignal(str, bool)
    # 插件设置信号
    configClicked = pyqtSignal(str)
    # 插件重新加载信号
    reloadClicked = pyqtSignal(str)
    # 插件卸载信号
    uninstallClicked = pyqtSignal(str)
    
    def __init__(self, plugin_id, plugin_info, parent=None):
        """
        初始化插件卡片
        
        Args:
            plugin_id: 插件ID
            plugin_info: 插件信息
            parent: 父组件
        """
        super().__init__(parent)
        self.plugin_id = plugin_id
        self.plugin_info = plugin_info
        self.is_enabled = False
        
        # 初始化界面
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)
        
        # 顶部布局 - 标题和开关
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 插件图标
        self.icon_widget = IconWidget(FluentIcon.APPLICATION)
        self.icon_widget.setFixedSize(32, 32)
        top_layout.addWidget(self.icon_widget)
        
        # 插件标题
        title_label = SubtitleLabel(self.plugin_info.get('name', '未命名插件'))
        title_label.setObjectName("PluginTitle")
        top_layout.addWidget(title_label)
        
        top_layout.addStretch(1)
        
        # 右侧状态切换按钮
        self.toggle_button = ToggleButton(self)
        self.toggle_button.setChecked(self.is_enabled)
        self.toggle_button.clicked.connect(self.on_toggle_status)
        self.toggle_button.setToolTip("启用/禁用插件")
        top_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(top_layout)
        
        # 描述
        if self.plugin_info.get('description'):
            description_layout = QHBoxLayout()
            description_layout.setContentsMargins(8, 4, 8, 4)
            description_label = BodyLabel(self.plugin_info['description'])
            description_label.setWordWrap(True)
            description_layout.addWidget(description_label)
            main_layout.addLayout(description_layout)
        
        # 标签和更多信息
        tags_info_layout = QHBoxLayout()
        tags_info_layout.setContentsMargins(8, 4, 8, 4)
        
        # 标签
        if 'tags' in self.plugin_info and self.plugin_info['tags']:
            for tag in self.plugin_info['tags'][:3]:  # 最多显示3个标签
                tag_label = QLabel(tag)
                tag_label.setObjectName("TagLabel")
                tags_info_layout.addWidget(tag_label)
                
        tags_info_layout.addStretch(1)
        
        # 版本信息
        version = self.plugin_info.get('version', '0.0.0')
        version_label = QLabel(f"v{version}")
        version_label.setObjectName("VersionLabel")
        tags_info_layout.addWidget(version_label)
        
        # 作者信息
        author = self.plugin_info.get('author', 'Unknown')
        author_label = QLabel(f"作者: {author}")
        author_label.setObjectName("AuthorLabel")
        tags_info_layout.addWidget(author_label)
        
        main_layout.addLayout(tags_info_layout)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)
        
        # 设置按钮
        self.config_button = TransparentToolButton(FluentIcon.SETTING, self)
        self.config_button.setObjectName("PluginButton")
        self.config_button.setToolTip("配置插件")
        self.config_button.clicked.connect(lambda: self.configClicked.emit(self.plugin_id))
        buttons_layout.addWidget(self.config_button)
        
        # 重新加载按钮
        self.reload_button = TransparentToolButton(FluentIcon.SYNC, self)
        self.reload_button.setObjectName("PluginButton")
        self.reload_button.setToolTip("重新加载插件")
        self.reload_button.clicked.connect(lambda: self.reloadClicked.emit(self.plugin_id))
        buttons_layout.addWidget(self.reload_button)
        
        # 文档按钮
        if 'documentation' in self.plugin_info and self.plugin_info['documentation']:
            self.doc_button = TransparentToolButton(FluentIcon.DOCUMENT, self)
            self.doc_button.setObjectName("PluginButton")
            self.doc_button.setToolTip("查看插件文档")
            buttons_layout.addWidget(self.doc_button)
        
        buttons_layout.addStretch(1)
        
        # 卸载按钮
        self.uninstall_button = TransparentToolButton(FluentIcon.DELETE, self)
        self.uninstall_button.setObjectName("PluginButton")
        self.uninstall_button.setToolTip("卸载插件")
        self.uninstall_button.clicked.connect(lambda: self.uninstallClicked.emit(self.plugin_id))
        buttons_layout.addWidget(self.uninstall_button)
        
        main_layout.addLayout(buttons_layout)
        
        # 设置最小高度
        self.setMinimumHeight(150)
    
    def on_toggle_status(self):
        """切换插件状态"""
        self.is_enabled = self.toggle_button.isChecked()
        self.statusChanged.emit(self.plugin_id, self.is_enabled)
    
    def set_status(self, enabled):
        """设置插件状态"""
        self.is_enabled = enabled
        self.toggle_button.setChecked(enabled)


class PluginView(ScrollArea):
    """插件管理视图"""
    
    def __init__(self, plugin_manager, config_manager, parent=None):
        """
        初始化插件管理视图
        
        Args:
            plugin_manager: 插件管理器
            config_manager: 配置管理器
            parent: 父组件
        """
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.config_manager = config_manager
        self.plugin_cards = {}  # 存储插件卡片实例
        
        # 设置属性
        self.setObjectName("pluginView")
        self.setWidgetResizable(True)
        
        # 初始化界面
        self.init_ui()
        
        # 加载插件
        self.load_plugins()
    
    def init_ui(self):
        """初始化界面"""
        # 创建主窗口
        self.main_widget = QWidget(self)
        self.setWidget(self.main_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # 添加标题和操作按钮
        header_layout = QHBoxLayout()
        
        # 标题
        self.title_label = TitleLabel("插件管理")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        # 搜索输入框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索插件...")
        self.search_edit.textChanged.connect(self.on_search)
        self.search_edit.setFixedWidth(200)
        header_layout.addWidget(self.search_edit)
        
        # 安装插件按钮
        self.install_button = PushButton("安装插件", self)
        self.install_button.setIcon(FluentIcon.ADD)
        self.install_button.clicked.connect(self.show_install_plugin_dialog)
        header_layout.addWidget(self.install_button)
        
        # 刷新按钮
        self.refresh_button = TransparentToolButton(FluentIcon.SYNC, self)
        self.refresh_button.setObjectName("ActionButton")
        self.refresh_button.setToolTip("刷新插件列表")
        self.refresh_button.clicked.connect(self.load_plugins)
        header_layout.addWidget(self.refresh_button)
        
        self.main_layout.addLayout(header_layout)
        
        # 统计信息栏
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.total_count_label = BodyLabel("总插件数: 0")
        self.stats_layout.addWidget(self.total_count_label)
        
        self.stats_layout.addSpacing(20)
        
        self.enabled_count_label = BodyLabel("已启用: 0")
        self.stats_layout.addWidget(self.enabled_count_label)
        
        self.stats_layout.addStretch(1)
        
        # 查看市场按钮
        self.market_button = PushButton("浏览插件市场", self)
        self.market_button.setIcon(FluentIcon.GLOBE)
        self.market_button.clicked.connect(self.open_plugin_market)
        self.stats_layout.addWidget(self.market_button)
        
        self.main_layout.addLayout(self.stats_layout)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        
        # 左侧插件列表区域
        self.plugin_list_container = QWidget(self)
        self.plugin_list_container_layout = QVBoxLayout(self.plugin_list_container)
        self.plugin_list_container_layout.setContentsMargins(0, 0, 0, 0)
        self.plugin_list_container_layout.setSpacing(0)
        
        # 分类过滤器
        self.category_layout = QHBoxLayout()
        self.category_layout.setContentsMargins(0, 0, 0, 16)
        
        self.all_button = PushButton("全部", self)
        self.all_button.setCheckable(True)
        self.all_button.setChecked(True)
        self.all_button.clicked.connect(lambda: self.filter_by_category("all"))
        self.category_layout.addWidget(self.all_button)
        
        self.tools_button = PushButton("工具", self)
        self.tools_button.setCheckable(True)
        self.tools_button.clicked.connect(lambda: self.filter_by_category("tools"))
        self.category_layout.addWidget(self.tools_button)
        
        self.extensions_button = PushButton("扩展", self)
        self.extensions_button.setCheckable(True)
        self.extensions_button.clicked.connect(lambda: self.filter_by_category("extensions"))
        self.category_layout.addWidget(self.extensions_button)
        
        self.themes_button = PushButton("主题", self)
        self.themes_button.setCheckable(True)
        self.themes_button.clicked.connect(lambda: self.filter_by_category("themes"))
        self.category_layout.addWidget(self.themes_button)
        
        self.category_layout.addStretch(1)
        
        self.plugin_list_container_layout.addLayout(self.category_layout)
        
        # 插件列表
        self.plugin_list_widget = QWidget(self)
        self.plugin_list_layout = QVBoxLayout(self.plugin_list_widget)
        self.plugin_list_layout.setContentsMargins(0, 0, 0, 0)
        self.plugin_list_layout.setSpacing(12)
        self.plugin_list_layout.addStretch(1)
        
        # 创建滚动区域包装插件列表
        self.plugin_list_scroll = ScrollArea(self)
        self.plugin_list_scroll.setWidgetResizable(True)
        self.plugin_list_scroll.setWidget(self.plugin_list_widget)
        
        self.plugin_list_container_layout.addWidget(self.plugin_list_scroll)
        
        # 右侧插件设置
        self.plugin_settings_widget = QStackedWidget(self)
        self.default_settings_widget = QWidget(self)
        default_layout = QVBoxLayout(self.default_settings_widget)
        default_layout.setAlignment(Qt.AlignCenter)
        
        default_icon = IconWidget(FluentIcon.APPLICATION, self)
        default_icon.setFixedSize(48, 48)
        default_layout.addWidget(default_icon, 0, Qt.AlignCenter)
        
        default_label = SubtitleLabel("选择一个插件进行设置")
        default_layout.addWidget(default_label, 0, Qt.AlignCenter)
        
        default_hint = BodyLabel("点击插件卡片上的设置按钮可以打开插件配置界面")
        default_hint.setObjectName("HintText")
        default_layout.addWidget(default_hint, 0, Qt.AlignCenter)
        
        self.plugin_settings_widget.addWidget(self.default_settings_widget)
        
        # 添加到分割器
        self.splitter.addWidget(self.plugin_list_container)
        self.splitter.addWidget(self.plugin_settings_widget)
        
        # 设置初始大小
        self.splitter.setSizes([300, 500])
        
        self.main_layout.addWidget(self.splitter)
        
        # 空白插件提示
        self.empty_plugin_widget = QWidget(self)
        empty_layout = QVBoxLayout(self.empty_plugin_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        # 空状态图标
        empty_icon = IconWidget(FluentIcon.APPLICATION, self)
        empty_icon.setFixedSize(64, 64)
        empty_layout.addWidget(empty_icon, 0, Qt.AlignCenter)
        
        empty_title = SubtitleLabel("暂无可用插件")
        empty_layout.addWidget(empty_title, 0, Qt.AlignCenter)
        
        empty_description = BodyLabel("点击安装插件按钮添加新插件，或浏览插件市场发现更多插件")
        empty_description.setObjectName("EmptyDescription")
        empty_layout.addWidget(empty_description, 0, Qt.AlignCenter)
        
        install_button = PushButton("安装插件", self)
        install_button.setIcon(FluentIcon.ADD)
        install_button.clicked.connect(self.show_install_plugin_dialog)
        empty_layout.addWidget(install_button, 0, Qt.AlignCenter)
        
        self.empty_plugin_widget.setVisible(False)
        self.main_layout.addWidget(self.empty_plugin_widget)
    
    def load_plugins(self):
        """加载插件列表"""
        # 清空当前列表
        while self.plugin_list_layout.count() > 1:
            item = self.plugin_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 清空插件卡片字典
        self.plugin_cards.clear()
        
        # 发现可用插件
        plugins_info = self.plugin_manager.discover_plugins()
        
        # 获取已启用插件
        enabled_plugins = self.plugin_manager.get_enabled_plugins_ids()
        
        if not plugins_info:
            # 无可用插件
            self.empty_plugin_widget.setVisible(True)
            self.splitter.setVisible(False)
            self.total_count_label.setText("总插件数: 0")
            self.enabled_count_label.setText("已启用: 0")
            return
        else:
            self.empty_plugin_widget.setVisible(False)
            self.splitter.setVisible(True)
        
        # 更新统计信息
        self.total_count_label.setText(f"总插件数: {len(plugins_info)}")
        self.enabled_count_label.setText(f"已启用: {len(enabled_plugins)}")
        
        # 添加插件卡片
        for plugin_info in plugins_info:
            plugin_id = plugin_info.get('id')
            
            # 创建插件卡片
            card = PluginCard(plugin_id, plugin_info, self)
            
            # 设置启用状态
            card.set_status(plugin_id in enabled_plugins)
            
            # 连接信号
            card.statusChanged.connect(self.on_plugin_status_changed)
            card.configClicked.connect(self.show_plugin_settings)
            card.reloadClicked.connect(self.reload_plugin)
            card.uninstallClicked.connect(self.uninstall_plugin)
            
            # 添加到布局
            self.plugin_list_layout.insertWidget(0, card)
            
            # 保存引用
            self.plugin_cards[plugin_id] = card
    
    def on_plugin_status_changed(self, plugin_id, enabled):
        """
        处理插件状态变更
        
        Args:
            plugin_id: 插件ID
            enabled: 是否启用
        """
        try:
            if enabled:
                # 启用插件
                success = self.plugin_manager.enable_plugin(plugin_id)
                if not success:
                    # 启用失败，恢复状态
                    self.plugin_cards[plugin_id].set_status(False)
                    InfoBar.error(
                        title="错误",
                        content=f"无法启用插件 {plugin_id}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                else:
                    InfoBar.success(
                        title="成功",
                        content=f"插件 {plugin_id} 已启用",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=2000
                    )
            else:
                # 禁用插件
                success = self.plugin_manager.disable_plugin(plugin_id)
                if not success:
                    # 禁用失败，恢复状态
                    self.plugin_cards[plugin_id].set_status(True)
                    InfoBar.error(
                        title="错误",
                        content=f"无法禁用插件 {plugin_id}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                else:
                    InfoBar.success(
                        title="成功",
                        content=f"插件 {plugin_id} 已禁用",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=2000
                    )
                    
            # 更新统计信息
            enabled_plugins = self.plugin_manager.get_enabled_plugins_ids()
            self.enabled_count_label.setText(f"已启用: {len(enabled_plugins)}")
                
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"更改插件状态时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def show_plugin_settings(self, plugin_id):
        """
        显示插件设置界面
        
        Args:
            plugin_id: 插件ID
        """
        # 获取插件实例
        plugin = self.plugin_manager.get_plugin(plugin_id)
        if not plugin:
            InfoBar.warning(
                title="警告",
                content=f"插件 {plugin_id} 未加载，无法显示设置",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        # 获取插件配置界面
        config_ui = plugin.get_config_ui()
        if not config_ui:
            InfoBar.info(
                title="提示",
                content=f"插件 {plugin_id} 没有提供配置界面",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        # 检查是否已添加到堆栈窗口
        for i in range(self.plugin_settings_widget.count()):
            widget = self.plugin_settings_widget.widget(i)
            if hasattr(widget, 'plugin_id') and widget.plugin_id == plugin_id:
                self.plugin_settings_widget.setCurrentIndex(i)
                return
                
        # 设置插件ID属性
        config_ui.plugin_id = plugin_id
        
        # 添加到堆栈窗口并显示
        self.plugin_settings_widget.addWidget(config_ui)
        self.plugin_settings_widget.setCurrentWidget(config_ui)
    
    def reload_plugin(self, plugin_id):
        """
        重新加载插件
        
        Args:
            plugin_id: 插件ID
        """
        try:
            # 获取主窗口引用
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'reload_plugin'):
                main_window = main_window.parent()
                
            if not main_window:
                InfoBar.error(
                    title="错误",
                    content="无法获取主窗口引用",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return
                
            # 调用主窗口的重载插件方法
            success = main_window.reload_plugin(plugin_id)
            
            if success:
                InfoBar.success(
                    title="成功",
                    content=f"插件 {plugin_id} 已重新加载",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
            else:
                InfoBar.error(
                    title="错误",
                    content=f"重新加载插件 {plugin_id} 失败",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"重新加载插件时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def uninstall_plugin(self, plugin_id):
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
        """
        from qfluentwidgets import MessageBox
        
        # 显示确认对话框
        confirm_dialog = MessageBox(
            "卸载插件",
            f"确定要卸载插件 {plugin_id} 吗？此操作将删除插件的所有文件和配置。",
            self
        )
        
        if confirm_dialog.exec_():
            try:
                # 卸载插件
                success = self.plugin_manager.uninstall_plugin(plugin_id)
                
                if success:
                    # 从列表中移除
                    if plugin_id in self.plugin_cards:
                        self.plugin_cards[plugin_id].deleteLater()
                        del self.plugin_cards[plugin_id]
                    
                    # 更新统计信息
                    plugins_info = self.plugin_manager.discover_plugins()
                    enabled_plugins = self.plugin_manager.get_enabled_plugins_ids()
                    self.total_count_label.setText(f"总插件数: {len(plugins_info)}")
                    self.enabled_count_label.setText(f"已启用: {len(enabled_plugins)}")
                    
                    InfoBar.success(
                        title="成功",
                        content=f"插件 {plugin_id} 已卸载",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=2000
                    )
                    
                    # 检查是否需要显示空插件提示
                    if not plugins_info:
                        self.empty_plugin_widget.setVisible(True)
                        self.splitter.setVisible(False)
                else:
                    InfoBar.error(
                        title="错误",
                        content=f"卸载插件 {plugin_id} 失败",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"卸载插件时出错: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
    
    def show_install_plugin_dialog(self):
        """显示插件安装对话框"""
        from ui.plugin_manager_dialog import PluginManagerDialog
        
        dialog = PluginManagerDialog(self.plugin_manager, self)
        dialog.exec_()
        
        # 对话框关闭后刷新插件列表
        self.load_plugins()
    
    def open_plugin_market(self):
        """打开插件市场"""
        # 这里可以打开一个网页或显示一个对话框，目前只显示一个提示
        InfoBar.info(
            title="插件市场",
            content="插件市场功能正在开发中，敬请期待！",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def filter_by_category(self, category):
        """
        按类别过滤插件
        
        Args:
            category: 类别名称
        """
        # 更新按钮状态
        self.all_button.setChecked(category == "all")
        self.tools_button.setChecked(category == "tools")
        self.extensions_button.setChecked(category == "extensions")
        self.themes_button.setChecked(category == "themes")
        
        # 根据类别过滤插件卡片
        for plugin_id, card in self.plugin_cards.items():
            if category == "all":
                card.setVisible(True)
            else:
                plugin_tags = card.plugin_info.get('tags', [])
                if isinstance(plugin_tags, str):
                    plugin_tags = [plugin_tags]
                
                card.setVisible(category in plugin_tags)
    
    def on_search(self, text):
        """
        搜索插件
        
        Args:
            text: 搜索文本
        """
        if not text:
            # 如果搜索框为空，显示所有插件
            for card in self.plugin_cards.values():
                card.setVisible(True)
            return
            
        # 转换为小写进行不区分大小写搜索
        search_text = text.lower()
        
        # 搜索插件名称、描述和标签
        for plugin_id, card in self.plugin_cards.items():
            plugin_info = card.plugin_info
            name = plugin_info.get('name', '').lower()
            description = plugin_info.get('description', '').lower()
            author = plugin_info.get('author', '').lower()
            
            tags = plugin_info.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            tags_text = ' '.join(tags).lower()
            
            # 如果任何字段匹配，则显示卡片
            if (search_text in name or search_text in description or 
                search_text in author or search_text in tags_text or
                search_text in plugin_id.lower()):
                card.setVisible(True)
            else:
                card.setVisible(False) 