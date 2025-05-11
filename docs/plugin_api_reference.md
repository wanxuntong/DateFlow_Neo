# DateFlow 插件API参考

本文档详细介绍了DateFlow插件可以使用的所有API。

## 核心接口

### PluginBase 类

所有插件都必须继承自`PluginBase`类。

```python
from core.plugin_manager import PluginBase

class YourPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            plugin_id="your_plugin_id",
            name="插件名称", 
            version="版本号",
            description="插件描述"
        )
```

#### 必须实现的方法

| 方法 | 说明 |
|------|------|
| `initialize(app_context)` | 插件初始化方法，返回布尔值表示成功或失败 |
| `cleanup()` | 插件清理方法，返回布尔值表示成功或失败 |

#### 可选实现的方法

| 方法 | 说明 |
|------|------|
| `on_enable()` | 插件启用时调用 |
| `on_disable()` | 插件禁用时调用 |
| `get_settings()` | 返回插件设置选项列表 |
| `on_settings_changed()` | 插件设置变更时调用 |

## 应用上下文 (AppContext)

`app_context`对象提供了与主应用程序交互的API。

### 任务管理

#### 获取任务

```python
# 获取所有任务
all_tasks = app_context.get_all_tasks()

# 获取特定任务
task = app_context.get_task(task_id)

# 获取时间范围内的任务
tasks = app_context.get_tasks_in_range(start_time, end_time)

# 获取特定标签的任务
tasks = app_context.get_tasks_by_tag(tag)

# 搜索任务
tasks = app_context.search_tasks(query)
```

#### 任务操作

```python
# 创建任务
task_id = app_context.create_task(
    title="任务标题",
    description="任务描述",
    start_time=datetime.datetime(2023, 10, 1, 10, 0),
    end_time=datetime.datetime(2023, 10, 1, 11, 0),
    priority=1,  # 1-5，数字越大优先级越高
    tags=["工作", "会议"],
    reminder=15  # 提前15分钟提醒
)

# 更新任务
app_context.update_task(
    task_id,
    title="新标题",
    description="新描述",
    # ... 其他属性
)

# 删除任务
app_context.delete_task(task_id)

# 完成任务
app_context.complete_task(task_id)

# 取消完成任务
app_context.uncomplete_task(task_id)
```

### 视图管理

```python
# 注册插件视图
app_context.register_plugin_view(
    plugin_id,  # 插件ID
    widget,     # QWidget实例
    icon,       # QIcon实例
    title       # 视图标题
)

# 注销插件视图
app_context.unregister_plugin_view(plugin_id)

# 获取当前活动视图
current_view = app_context.get_active_view()

# 切换到指定视图
app_context.switch_to_view(view_id)
```

### 事件系统

```python
# 注册事件处理器
self.register_event_handler(event_type, handler_function)

# 注销事件处理器
self.unregister_event_handler(event_type, handler_function)

# 发送事件
app_context.event_manager.emit_event(event_type, data)
```

#### 标准事件类型

| 事件类型 | 说明 | 数据格式 |
|----------|------|----------|
| `EVENT_APPLICATION_START` | 应用启动 | `None` |
| `EVENT_APPLICATION_QUIT` | 应用退出 | `None` |
| `EVENT_TASK_CREATED` | 任务创建 | `{"task_id": "...", "task": {...}}` |
| `EVENT_TASK_UPDATED` | 任务更新 | `{"task_id": "...", "old_task": {...}, "new_task": {...}}` |
| `EVENT_TASK_DELETED` | 任务删除 | `{"task_id": "...", "task": {...}}` |
| `EVENT_TASK_COMPLETED` | 任务完成 | `{"task_id": "...", "task": {...}}` |
| `EVENT_VIEW_CHANGED` | 视图切换 | `{"from": "view_id", "to": "view_id"}` |
| `EVENT_PLUGIN_ENABLED` | 插件启用 | `{"plugin_id": "..."}` |
| `EVENT_PLUGIN_DISABLED` | 插件禁用 | `{"plugin_id": "..."}` |

### 设置管理

```python
# 获取插件设置
value = app_context.get_plugin_setting(plugin_id, key, default=None)

# 保存插件设置
app_context.set_plugin_setting(plugin_id, key, value)

# 获取应用设置
value = app_context.get_app_setting(key, default=None)

# 保存全局用户设置
app_context.set_user_setting(key, value)
```

### 通知系统

```python
# 发送通知
app_context.notify(
    title="通知标题",
    message="通知内容",
    level="info",  # 'info', 'warning', 'error', 'success'
    duration=5000  # 显示时间（毫秒）
)

# 发送系统托盘通知
app_context.notify_system_tray(
    title="通知标题", 
    message="通知内容",
    icon=None  # 可选的QIcon对象
)
```

### 数据存储

```python
# 保存插件数据
app_context.save_plugin_data(plugin_id, key, data)

# 加载插件数据
data = app_context.load_plugin_data(plugin_id, key)
```

### 用户界面辅助工具

```python
# 获取主窗口
main_window = app_context.get_main_window()

# 获取主题
theme = app_context.get_theme()

# 设置主题
app_context.set_theme("light")  # 或 "dark"

# 显示确认对话框
result = app_context.show_confirm_dialog(
    title="确认操作",
    message="确定要执行此操作吗？",
    default_button="yes"  # "yes" 或 "no"
)

# 显示输入对话框
text = app_context.show_input_dialog(
    title="输入信息",
    message="请输入名称：",
    default_value=""
)

# 显示选择对话框
choice = app_context.show_select_dialog(
    title="选择选项",
    message="请选择一个选项：",
    options=["选项1", "选项2", "选项3"],
    default_option="选项1"
)
```

## 数据类型

### 任务 (Task)

任务对象的结构:

```python
{
    "id": "唯一标识符",
    "title": "任务标题",
    "description": "任务描述",
    "start_time": datetime.datetime(...),  # 开始时间
    "end_time": datetime.datetime(...),    # 结束时间
    "created_at": datetime.datetime(...),  # 创建时间
    "updated_at": datetime.datetime(...),  # 更新时间
    "priority": 3,        # 优先级 (1-5)
    "status": "pending",  # 状态 ('pending', 'in_progress', 'completed', 'cancelled')
    "tags": ["标签1", "标签2"],  # 标签列表
    "color": "#FF5733",   # 颜色代码
    "reminder": 15,       # 提前提醒时间（分钟）
    "repeat": {           # 重复设置 (可选)
        "type": "daily",  # 'daily', 'weekly', 'monthly', 'yearly'
        "interval": 1,    # 间隔
        "end_date": datetime.datetime(...),  # 结束日期 (可选)
        "end_count": 10,  # 结束次数 (可选)
        "weekdays": [0, 1, 2, 3, 4],  # 周几重复，0-6表示周日到周六 (仅weekly)
        "monthday": 15,   # 每月几号 (仅monthly)
    },
    "completed_at": datetime.datetime(...),  # 完成时间 (可选)
    "location": "地点",   # 地点 (可选)
    "metadata": {},       # 自定义元数据 (可用于插件存储额外数据)
}
```

## 最佳实践

### 异常处理

插件应当处理所有可能的异常，不应该让异常传播到主程序：

```python
try:
    # 可能抛出异常的代码
    result = risky_operation()
except Exception as e:
    logger.error(f"操作失败: {e}")
    # 优雅地处理错误
    app_context.notify("操作失败", str(e), "error")
    return False
```

### 性能考虑

插件不应该在主线程中执行耗时操作：

```python
from PyQt5.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# 使用示例
def long_running_task():
    # 耗时操作
    pass

def on_result(result):
    # 处理结果
    pass

def on_error(error_msg):
    # 处理错误
    pass

worker = WorkerThread(long_running_task)
worker.finished.connect(on_result)
worker.error.connect(on_error)
worker.start()
```

### 资源管理

确保在插件禁用或卸载时释放所有资源：

```python
def cleanup(self):
    # 停止所有线程
    for thread in self.threads:
        thread.quit()
        thread.wait()
    
    # 关闭所有打开的文件
    for file in self.open_files:
        file.close()
    
    # 断开所有信号连接
    for connection in self.connections:
        connection.disconnect()
    
    # 注销所有事件处理器
    for event_type, handler in self.event_handlers:
        self.unregister_event_handler(event_type, handler)
    
    return True
```

### 国际化

支持多语言：

```python
# 在插件中定义语言资源
self.strings = {
    "zh_CN": {
        "title": "插件标题",
        "button_add": "添加",
        "error_not_found": "未找到项目"
    },
    "en_US": {
        "title": "Plugin Title",
        "button_add": "Add",
        "error_not_found": "Item not found"
    }
}

# 获取当前语言
current_lang = app_context.get_app_setting("language", "zh_CN")

# 获取字符串
def get_string(key):
    lang_strings = self.strings.get(current_lang, self.strings["zh_CN"])
    return lang_strings.get(key, key)
``` 