
![DateFlow个人排期助手](src/resources/images/splash.png)
DateFlow个人排期助手 📅
---

注意，程序处于早期构建阶段，其功能并不完善

---
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15.0%2B-green)

DateFlow是一款基于PyQt5和PyQt-Fluent-Widgets开发的现代化个人日程排期软件，提供直观的界面和多种视图模式，帮助您更高效地管理时间和任务。


## ✨ 功能亮点

- **多样化视图**
  - 📆 日程视图：以日历形式直观展示任务安排
  - 📊 甘特图：以时间线方式显示任务进度和持续时间
  - 🔄 流程图：可视化展示任务之间的依赖关系
  
- **灵活任务管理**
  - ✏️ 添加、编辑和删除任务
  - 🔔 自定义提醒时间
  - 🏷️ 任务分类与标签
  - 🌈 优先级视觉区分
  
- **智能提醒**
  - ⏰ 到点系统托盘通知
  - 🔄 可设置重复任务
  - 📱 多种提醒方式
  
- **数据安全**
  - 💾 自动保存数据
  - 📦 支持数据导入导出
  - 🔄 定期备份功能
  
- **插件系统**
  - 🧩 支持扩展功能的插件架构
  - 🛠️ 完整的插件API
  - 📚 内置"排期助手"插件示例

## 🚀 系统要求

- Windows 10/11、macOS 或 Linux
- Python 3.6+
- 1GB+ 可用内存
- 200MB+ 磁盘空间

## 📥 安装方法

```bash
# 1. 克隆仓库
git clone https://github.com/HeDaas-Code/DateFlow.git
cd DateFlow

# 2. 创建虚拟环境(可选但推荐)
python -m venv venv
# Windows激活虚拟环境
venv\Scripts\activate
# Linux/macOS激活虚拟环境
# source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
python src/main.py
```

## 📖 使用指南

### 添加任务
1. 点击界面底部的"添加任务"按钮
2. 填写任务标题、描述、时间范围等信息
3. 设置提醒方式和优先级
4. 点击"保存"完成添加

### 查看任务
- 切换不同视图模式（日程、甘特图、流程图）以不同角度查看任务
- 使用日历导航到特定日期
- 通过筛选器查找特定类型的任务

### 编辑任务
- 双击任务条目打开编辑界面
- 修改任务信息并保存
- 拖拽任务可在某些视图中调整时间

### 任务提醒
当任务时间到达或达到设定的提前提醒时间，系统托盘会弹出通知提醒您。

## 🏗️ 项目结构

```
DateFlow/
├── src/                # 源代码目录
│   ├── core/           # 核心功能模块
│   │   ├── scheduler.py       # 调度管理器
│   │   ├── plugin_manager.py  # 插件管理器
│   │   └── ...
│   ├── ui/             # 用户界面组件
│   │   ├── calendar_view.py   # 日程视图
│   │   ├── flow_view.py       # 流程图视图
│   │   ├── gantt_view.py      # 甘特图视图
│   │   └── ...
│   ├── data/           # 数据存储目录
│   ├── resources/      # 资源文件目录
│   ├── utils/          # 工具函数
│   ├── plugins/        # 插件系统
│   │   ├── __init__.py        # 插件包定义
│   │   └── schedule_assistant/ # 排期助手插件示例
│   └── main.py         # 程序入口
├── docs/               # 文档目录
│   ├── plugin_development.md  # 插件开发文档
│   └── plugin_api_reference.md # 插件API参考
├── logs/               # 日志文件目录
└── requirements.txt    # 项目依赖
```

## 🧩 插件系统

DateFlow采用灵活的插件架构，允许开发者通过插件扩展功能：

- 添加新视图到主界面
- 扩展和自定义现有功能
- 处理应用事件
- 与主程序数据交互

您可以参考以下文档了解插件开发：

- [插件开发指南](docs/plugin_development.md) - 从零开始创建插件
- [插件API参考](docs/plugin_api_reference.md) - 所有可用API详解

## 🔜 开发计划

- [ ] 任务导入/导出功能增强
- [ ] 统计分析功能
- [ ] 优化流程图展示效果
- [ ] 团队协作功能
- [ ] 移动端应用开发
- [ ] 扩展插件生态系统

## 👥 参与贡献

我们欢迎各种形式的贡献，包括但不限于：

1. 提交Bug报告
2. 提出新功能建议
3. 修复Bug或实现新功能
4. 完善文档和翻译

请阅读[贡献指南](CONTRIBUTING.md)了解详情。

## 📋 依赖项

- Python 3.6+
- PyQt5 >= 5.15.0
- PyQt-Fluent-Widgets[full] >= 1.2.0
- structlog >= 22.1.0

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 📞 联系方式

- 项目维护者: HeDaas-Code
- 邮箱: zhangtianzhe0517@stu.sdua.edu.cn
- 项目链接: https://github.com/HeDaas-Code/DateFlow_Neo

---

如果您觉得这个项目有用，请给它一个⭐️！
