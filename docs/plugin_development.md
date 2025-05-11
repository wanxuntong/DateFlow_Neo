# DateFlow 插件开发文档

DateFlow提供了一套灵活的插件系统，允许开发者扩展应用的功能。本文档将详细介绍如何开发DateFlow插件。

## 插件系统简介

DateFlow采用基于PluginBase的组件化插件架构，允许开发者创建独立的插件模块，插件可以：

- 添加新的视图到主界面
- 扩展现有功能
- 处理应用事件
- 定义自己的设置选项
- 与主程序数据进行交互

## 快速开始

为了帮助您快速开始插件开发，我们提供了一个插件模板：

- [下载插件模板](plugin_template.zip)

下载并解压模板后，将其重命名为您的插件ID，放入`src/plugins/`目录即可开始开发。

## 插件目录结构

一个标准的DateFlow插件目录结构如下：

```
your_plugin_name/
├── __init__.py          # 插件入口点
├── plugin_info.json     # 插件元数据
├── icon.png             # 插件图标
├── main_view.py         # 主视图实现
├── assets/              # 资源文件目录
└── other_modules.py     # 其他功能模块
```

## 创建插件步骤

### 1. 创建插件目录

在`src/plugins/`目录下创建你的插件目录：

```
mkdir -p src/plugins/your_plugin_name
```

### 2. 创建plugin_info.json

这个文件包含插件的元数据信息：

```json
{
    "name": "插件显示名称",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "作者名称",
    "requires": [],
    "settings": [
        {
            "key": "setting_key",
            "name": "设置名称",
            "description": "设置描述",
            "type": "string|number|boolean|time|date|color",
            "default": "默认值"
        }
    ]
}
```

### 3. 创建插件主类

在`__init__.py`中创建继承自`PluginBase`的插件主类：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件描述
"""

from core.plugin_manager import PluginBase
from PyQt5.QtGui import QIcon
import os
from utils.logger import get_logger

# 创建日志记录器
logger = get_logger("YourPlugin", app="DateFlow")

class YourPlugin(PluginBase):
    """插件类"""
    
    def __init__(self):
        """初始化插件"""
        super().__init__(
            plugin_id="your_plugin_id",
            name="插件名称",
            version="1.0.0",
            description="插件描述"
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
            logger.info("初始化插件")
            self.app_context = app_context
            
            # 创建主界面
            from .main_view import YourPluginView
            self.main_widget = YourPluginView(app_context)
            
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
            
            logger.info("插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup(self):
        """清理插件资源
        
        返回:
            bool: 清理成功返回True
        """
        try:
            logger.info("清理插件资源")
            self.app_context.unregister_plugin_view(self.plugin_id)
            return True
        except Exception as e:
            logger.error(f"插件清理失败: {e}")
            return False
    
    def on_application_start(self, event):
        """应用程序启动事件处理
        
        参数:
            event: 事件对象
        """
        logger.info("插件已加载")
```

### 4. 创建插件视图

在`main_view.py`文件中创建插件的主视图：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件主视图
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import PrimaryPushButton

class YourPluginView(QWidget):
    """插件主视图"""
    
    def __init__(self, app_context):
        """初始化视图
        
        参数:
            app_context: 应用程序上下文
        """
        super().__init__()
        self.app_context = app_context
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("你的插件标题", self)
        title.setAlignment(Qt.AlignCenter)
        
        # 按钮
        button = PrimaryPushButton("点击按钮", self)
        button.clicked.connect(self.on_button_clicked)
        
        # 添加到布局
        layout.addWidget(title)
        layout.addWidget(button)
        layout.addStretch(1)
        
        self.setLayout(layout)
    
    def on_button_clicked(self):
        """按钮点击处理"""
        print("按钮被点击")
```

### 5. 添加图标

为插件添加一个图标文件（icon.png）。

## 应用上下文 API

插件可以通过`app_context`访问以下API：

### 任务操作

```python
# 获取所有任务
tasks = self.app_context.get_all_tasks()

# 创建新任务
task_id = self.app_context.create_task(title, start_time, end_time, **kwargs)

# 更新任务
success = self.app_context.update_task(task_id, **kwargs)

# 删除任务
success = self.app_context.delete_task(task_id)
```

### 事件系统

```python
# 注册事件处理器
self.register_event_handler(event_type, handler_function)

# 发送事件
self.app_context.event_manager.emit_event(event_type, data)
```

常用事件类型：

- `EVENT_APPLICATION_START` - 应用启动
- `EVENT_TASK_CREATED` - 任务创建
- `EVENT_TASK_UPDATED` - 任务更新
- `EVENT_TASK_DELETED` - 任务删除
- `EVENT_VIEW_CHANGED` - 视图切换

### 插件设置

```python
# 获取设置值
value = self.app_context.get_plugin_setting(self.plugin_id, "setting_key")

# 保存设置值
self.app_context.set_plugin_setting(self.plugin_id, "setting_key", value)
```

## 发布插件

完成插件开发后，您可以通过以下方式发布：

1. 将插件打包为zip文件
2. 在GitHub上发布插件仓库
3. 提交到DateFlow插件目录

## 插件开发最佳实践

1. **遵循命名规范** - 使用清晰的命名风格和适当的注释
2. **错误处理** - 确保插件在各种情况下都能优雅地处理错误
3. **资源管理** - 在cleanup方法中释放所有资源
4. **性能优化** - 避免在主线程中执行耗时操作
5. **国际化** - 使用字符串资源以支持多语言

## 插件示例

参考`src/plugins/schedule_assistant`目录中的示例插件，了解完整的插件实现。

## 常见问题

### 插件无法加载

- 检查插件目录结构是否正确
- 确保plugin_info.json格式正确
- 查看日志文件获取详细错误信息

### 插件界面不显示

- 确保正确注册了插件视图
- 检查视图创建过程是否有错误

### 与主程序交互问题

- 确保使用正确的app_context API
- 检查事件监听器注册是否正确

## API参考

有关所有可用API的详细信息，请参考[API参考文档](plugin_api_reference.md)。

## 帮助和支持

如果您在开发过程中遇到问题，可以通过以下方式获取帮助：

- 查阅[GitHub Issues](https://github.com/HeDaas-Code/DateFlow/issues)
- 加入开发者社区
- 发送邮件到维护者邮箱 