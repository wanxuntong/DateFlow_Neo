#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日程视图模块
以日历形式展示任务安排
"""

import calendar
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QDate, QRect, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QCalendarWidget, QFrame, 
    QSizePolicy, QGridLayout, QMenu, QApplication,
    QMessageBox
)

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, IconWidget, 
    CalendarPicker, ComboBox, TeachingTip, 
    InfoBar, InfoBarPosition, RoundMenu, Action, MessageBox
)

from ui.task_dialog import TaskDialog

class CalendarTaskWidget(QWidget):
    """日历中的任务小部件"""
    
    clicked = pyqtSignal(dict)  # 点击任务时发出信号，包含任务数据
    
    def __init__(self, task_data, parent=None):
        print(f"Creating CalendarTaskWidget for task {task_data.get('title')}")
        super().__init__(parent)
        self.task_data = task_data
        
        # 直接在构造函数中初始化
        # 设置更小的最小高度
        self.setMinimumHeight(18)
        # 使其填充可用宽度
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 检查任务状态是否暂停
        status = self.task_data.get("status", "未开始")
        if status == "已暂停":
            # 暂停状态使用灰色
            self.bg_color = QColor(224, 224, 224)  # 灰色
            self.text_color = QColor(120, 120, 120)  # 深灰色文本
        else:
            # 根据优先级设置背景颜色
            priority = self.task_data.get("priority", "中")
            if priority == "紧急":
                self.bg_color = QColor(255, 205, 210)  # 淡红色
            elif priority == "高":
                self.bg_color = QColor(255, 224, 178)  # 淡橙色
            elif priority == "中":
                self.bg_color = QColor(187, 222, 251)  # 淡蓝色
            else:  # 低
                self.bg_color = QColor(200, 230, 201)  # 淡绿色
            
            # 设置文本颜色
            self.text_color = QColor(0, 0, 0)
        
        # 设置工具提示
        self.setToolTip(
            f"标题: {self.task_data.get('title')}\n"
            f"描述: {self.task_data.get('description')}\n"
            f"开始: {self.task_data.get('start_time').strftime('%Y-%m-%d %H:%M')}\n"
            f"结束: {self.task_data.get('end_time').strftime('%Y-%m-%d %H:%M')}\n"
            f"优先级: {self.task_data.get('priority', '中')}\n"
            f"状态: {status}"
        )
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        print(f"Finished creating CalendarTaskWidget for task {task_data.get('title')}")
    
    def paintEvent(self, event):
        """绘制任务小部件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.bg_color))
        
        # 判断是否为暂停状态，如果是，使用虚线边框
        status = self.task_data.get("status", "未开始")
        if status == "已暂停":
            # 绘制背景
            painter.drawRoundedRect(self.rect(), 3, 3)
            
            # 使用虚线边框表示暂停状态
            pen = QPen(QColor(150, 150, 150), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 3, 3)
        else:
            painter.drawRoundedRect(self.rect(), 3, 3)
        
        # 绘制文本
        painter.setPen(QPen(self.text_color))
        
        # 获取任务标题和时间
        title = self.task_data.get("title", "")
        start_time = self.task_data.get("start_time")
        end_time = self.task_data.get("end_time")
        
        # 计算文本区域和字体度量
        text_rect = QRect(4, 0, self.width() - 8, self.height())
        
        # 设置较小字体以适应紧凑布局
        painter.setFont(QFont("Microsoft YaHei", 7))
        fm = painter.fontMetrics()
        available_width = text_rect.width()
        
        # 智能显示策略
        # 1. 如果空间充足，显示时间范围和标题
        # 2. 如果空间有限，优先显示时间，然后尽可能多显示标题
        # 3. 如果空间非常有限，只显示开始时间
        
        # 时间格式
        short_time = f"{start_time.strftime('%H:%M')}"
        full_time = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        
        # 计算各部分文本宽度
        short_time_width = fm.width(short_time)
        full_time_width = fm.width(full_time)
        
        # 选择合适的时间格式
        if full_time_width + 10 <= available_width:  # 留出至少10px给标题
            time_str = full_time
            time_width = full_time_width
        else:
            time_str = short_time
            time_width = short_time_width
        
        # 计算标题可用宽度
        title_available_width = available_width - time_width - 4  # 留出4px间距
        
        # 如果有空间显示标题
        if title_available_width > 10:  # 至少能显示几个字符
            # 如果标题太长，进行截断
            if fm.width(title) > title_available_width:
                title = fm.elidedText(title, Qt.ElideRight, title_available_width)
            
            # 绘制完整文本
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, f"{time_str} {title}")
        else:
            # 空间不足，只显示时间
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, time_str)
            
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task_data)
        super().mousePressEvent(event)

class DayWidget(QWidget):
    """日历中的单日小部件"""
    
    def __init__(self, date, tasks, scheduler_manager, parent=None):
        print(f"Creating DayWidget for date {date.day()}")
        super().__init__(parent)
        self.date = date
        self.tasks = tasks
        self.scheduler_manager = scheduler_manager
        self.selected = False
        
        # 设置尺寸策略为扩展，使其可以完全填充分配的空间
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 最小大小仍然保留，避免过小
        self.setMinimumSize(QSize(100, 80))
        self.setMouseTracking(True)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 添加日期标签
        self.date_label = QLabel(str(self.date.day()), self)
        self.date_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(self.date_label)
        
        # 如果是当前日期，设置不同的样式
        now = QDate.currentDate()
        if self.date == now:
            self.date_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        # 添加任务小部件
        for task in self.tasks:
            task_widget = CalendarTaskWidget(task, self)
            task_widget.clicked.connect(self.edit_task)
            layout.addWidget(task_widget)
            
        # 添加弹性空间，但使用整数参数，避免类型错误
        layout.addStretch(1)
        
        # 启用上下文菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        print(f"Finished creating DayWidget for date {date.day()}")
    
    def paintEvent(self, event):
        """绘制日期小部件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制边框
        if self.selected:
            painter.setPen(QPen(QColor(25, 118, 210), 2))
        else:
            painter.setPen(QPen(QColor(200, 200, 200)))
            
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)
    
    def show_context_menu(self, position):
        """显示上下文菜单"""
        # 创建菜单
        menu = RoundMenu(self)
        
        # 添加新任务选项（在当前日期）
        add_action = Action(FluentIcon.ADD, "添加新任务")
        add_action.triggered.connect(self.add_new_task)
        menu.addAction(add_action)
        
        # 添加查看选项
        view_action = Action(FluentIcon.VIEW, "查看当日详情")
        view_action.triggered.connect(self.view_day_detail)
        menu.addAction(view_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(position))
    
    def add_new_task(self):
        """在当前日期添加新任务"""
        # 设置合理的开始结束时间
        start_datetime = datetime.combine(self.date.toPyDate(), datetime.min.time().replace(hour=9))
        end_datetime = datetime.combine(self.date.toPyDate(), datetime.min.time().replace(hour=10))
        
        # 创建任务数据
        task_data = {
            "id": None,  # 新任务，ID为空
            "title": "",
            "description": "",
            "start_time": start_datetime,
            "end_time": end_datetime,
            "priority": "中",
            "status": "未开始",
            "completed": False
        }
        
        # 打开任务编辑对话框
        dialog = TaskDialog(
            self.window(), 
            self.scheduler_manager, 
            self.window().config_manager,
            self.window().subtask_manager,
            task_data
        )
        if dialog.exec_():
            # 通知日历视图刷新
            self.window().findChild(CalendarView).refresh()
    
    def view_day_detail(self):
        """查看日视图详情"""
        # 获取日历视图并切换到日视图
        calendar_view = self.window().findChild(CalendarView)
        if calendar_view:
            # 设置当前日期
            calendar_view.current_date = self.date
            # 切换到日视图
            calendar_view.view_combo.setCurrentText("日视图")
    
    def edit_task(self, task_data):
        """编辑任务"""
        try:
            dialog = TaskDialog(
                self.window(), 
                self.scheduler_manager,
                self.window().config_manager,
                self.window().subtask_manager,
                task_data
            )
            if dialog.exec_():
                # 通知日历视图刷新
                self.window().findChild(CalendarView).refresh()
        except Exception as e:
            print(f"编辑任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title="错误",
                content=f"编辑任务时出错: {e}",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )

class CalendarView(ScrollArea):
    """日历视图"""
    
    def __init__(self, scheduler_manager, parent=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.current_date = QDate.currentDate()
        self.selected_date = self.current_date
        self.is_updating = False  # 添加标志以防止递归
        
        # 初始化界面
        self.init_ui()
        
        # 加载当前月份的任务
        self.load_month_tasks()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setObjectName("calendarView")
        self.setWidgetResizable(True)
        
        # 创建主窗口
        self.main_widget = QWidget(self)
        self.setWidget(self.main_widget)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.main_layout.setSpacing(0)  # 减少组件间距
        
        # 添加顶部工具栏
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(5, 5, 5, 5)  # 保留工具栏的一些边距
        
        # 添加月份选择器
        self.month_label = QLabel("当前月份: ", self)
        self.toolbar_layout.addWidget(self.month_label)
        
        self.date_picker = CalendarPicker(self)
        self.date_picker.setDate(self.current_date)
        self.date_picker.dateChanged.connect(self.on_month_changed)
        self.toolbar_layout.addWidget(self.date_picker)
        
        # 添加导航按钮
        self.prev_btn = PushButton("上个月", self)
        self.prev_btn.setIcon(FluentIcon.CHEVRON_RIGHT)
        self.prev_btn.clicked.connect(self.prev_navigation)
        self.toolbar_layout.addWidget(self.prev_btn)
        
        self.today_btn = PushButton("今天", self)
        self.today_btn.setIcon(FluentIcon.DATE_TIME)
        self.today_btn.clicked.connect(self.today_navigation)
        self.toolbar_layout.addWidget(self.today_btn)
        
        self.next_btn = PushButton("下个月", self)
        self.next_btn.setIcon(FluentIcon.CHEVRON_RIGHT)
        self.next_btn.clicked.connect(self.next_navigation)
        self.toolbar_layout.addWidget(self.next_btn)
        
        self.toolbar_layout.addStretch(1)
        
        # 添加视图切换按钮
        self.view_combo = ComboBox(self)
        self.view_combo.addItems(["月视图", "周视图", "日视图"])
        self.view_combo.setCurrentIndex(0)
        self.view_combo.currentIndexChanged.connect(self.on_view_changed)
        self.toolbar_layout.addWidget(QLabel("视图: "))
        self.toolbar_layout.addWidget(self.view_combo)
        
        self.main_layout.addLayout(self.toolbar_layout)
        
        # 添加星期标签
        self.week_layout = QHBoxLayout()
        self.week_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for day in weekdays:
            label = QLabel(day, self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; padding: 3px;")  # 减少内边距
            self.week_layout.addWidget(label)
        
        self.main_layout.addLayout(self.week_layout)
        
        # 创建日历网格
        self.calendar_widget = QWidget(self)
        self.calendar_layout = QGridLayout(self.calendar_widget)
        self.calendar_layout.setSpacing(1)
        self.calendar_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        # 设置拉伸因子，使网格均匀分布
        for i in range(6):  # 6行
            self.calendar_layout.setRowStretch(i, 1)
        for j in range(7):  # 7列
            self.calendar_layout.setColumnStretch(j, 1)
            
        self.main_layout.addWidget(self.calendar_widget, 1)  # 日历部分占据所有剩余空间
        
        # 初始化导航按钮文本
        self.update_navigation_buttons()
        
        # 启用上下文菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_month_calendar(self, year, month):
        """创建月视图日历"""
        # 获取月份的第一天和天数
        first_day = QDate(year, month, 1)
        days_in_month = first_day.daysInMonth()
        
        # 计算月份第一天是星期几（0是周一，6是周日）
        first_weekday = first_day.dayOfWeek() - 1  
        if first_weekday == -1:  # 周日调整为6
            first_weekday = 6
            
        # 创建日期网格
        row = 0
        col = first_weekday
        
        # 计算需要的总行数
        rows_needed = (first_weekday + days_in_month + 6) // 7
        
        # 填充日期网格
        for day in range(1, days_in_month + 1):
            date = QDate(year, month, day)
            
            # 获取当天的任务
            tasks = self.scheduler_manager.get_tasks_by_date(date.toPyDate())
            
            # 创建日期小部件
            day_widget = DayWidget(date, tasks, self.scheduler_manager)
            
            # 如果是选中日期，设为选中状态
            if date == self.selected_date:
                day_widget.selected = True
            
            self.calendar_layout.addWidget(day_widget, row, col)
            
            # 移到下一列
            col += 1
            if col > 6:
                col = 0
                row += 1
                
        # 填充前后的空白单元格，使用透明的占位小部件
        # 填充月初空白
        for i in range(first_weekday):
            placeholder = QWidget()
            placeholder.setStyleSheet("background: transparent;")
            self.calendar_layout.addWidget(placeholder, 0, i)
            
        # 填充月末空白，确保总行数为所需行数
        if row < rows_needed - 1 or col > 0:
            # 填充当前行剩余空白
            while col <= 6:
                placeholder = QWidget()
                placeholder.setStyleSheet("background: transparent;")
                self.calendar_layout.addWidget(placeholder, row, col)
                col += 1
                
            # 填充整行
            row += 1
            while row < rows_needed:
                for i in range(7):
                    placeholder = QWidget()
                    placeholder.setStyleSheet("background: transparent;")
                    self.calendar_layout.addWidget(placeholder, row, i)
                row += 1
    
    def clean_views(self):
        """清理所有视图组件，避免重复删除错误"""
        # 清理月视图
        if hasattr(self, 'calendar_widget') and self.calendar_widget and self.calendar_widget.isWidgetType():
            try:
                self.main_layout.removeWidget(self.calendar_widget)
                self.calendar_widget.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.calendar_widget = None

        # 清理周视图
        if hasattr(self, 'week_widget') and self.week_widget and self.week_widget.isWidgetType():
            try:
                self.main_layout.removeWidget(self.week_widget)
                self.week_widget.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.week_widget = None

        # 清理日视图
        if hasattr(self, 'day_widget') and self.day_widget and self.day_widget.isWidgetType():
            try:
                self.main_layout.removeWidget(self.day_widget)
                self.day_widget.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.day_widget = None

    def load_month_tasks(self):
        """加载当前月份的任务"""
        if self.is_updating:  # 如果已经在更新中，则直接返回
            return
            
        self.is_updating = True  # 设置更新标志
        
        try:
            # 清理所有视图
            self.clean_views()
            
            # 确保星期标题行在月视图中可见
            for i in range(self.week_layout.count()):
                item = self.week_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(True)
            
            # 创建新的日历小部件和布局
            self.calendar_widget = QWidget(self)
            self.calendar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.calendar_layout = QGridLayout(self.calendar_widget)
            self.calendar_layout.setSpacing(1)
            self.calendar_layout.setContentsMargins(0, 0, 0, 0)
            
            # 设置网格布局的行列拉伸因子，确保均匀分布
            for i in range(6):  # 6行
                self.calendar_layout.setRowStretch(i, 1)
            for j in range(7):  # 7列
                self.calendar_layout.setColumnStretch(j, 1)
                
            self.main_layout.addWidget(self.calendar_widget, 1)  # 日历占据所有剩余空间
            
            # 获取当前年月
            year = self.current_date.year()
            month = self.current_date.month()
            
            # 创建月视图
            self.create_month_calendar(year, month)
            
            # 更新月份标签
            self.date_picker.blockSignals(True)  # 阻止信号以避免递归
            self.date_picker.setDate(QDate(year, month, 1))
            self.date_picker.blockSignals(False)
        finally:
            self.is_updating = False  # 清除更新标志
    
    def on_month_changed(self, date):
        """月份变化处理"""
        if self.is_updating:  # 如果已经在更新中，则直接返回
            return
            
        self.current_date = date
        self.selected_date = date
        self.load_month_tasks()
    
    def update_navigation_buttons(self):
        """根据当前视图类型更新导航按钮文本"""
        view_type = self.view_combo.currentText()
        
        if view_type == "月视图":
            self.prev_btn.setText("上个月")
            self.today_btn.setText("本月")
            self.next_btn.setText("下个月")
        elif view_type == "周视图":
            self.prev_btn.setText("上一周")
            self.today_btn.setText("本周")
            self.next_btn.setText("下一周")
        elif view_type == "日视图":
            self.prev_btn.setText("前一天")
            self.today_btn.setText("今天")
            self.next_btn.setText("后一天")
    
    def prev_navigation(self):
        """导航到前一个时间单位（月/周/日）"""
        if self.is_updating:
            return
            
        view_type = self.view_combo.currentText()
        
        if view_type == "月视图":
            # 上个月
            year = self.current_date.year()
            month = self.current_date.month() - 1
            
            # 处理年份变化
            if month < 1:
                month = 12
                year -= 1
                
            self.current_date = QDate(year, month, 1)
            self.selected_date = self.current_date
            self.load_month_tasks()
            
        elif view_type == "周视图":
            # 上一周
            # 确保总是以周一为起点
            current_monday = self.get_monday_of_week(self.current_date)
            # 前一周的周一是当前周一减7天
            prev_monday = current_monday.addDays(-7)
            self.current_date = prev_monday
            self.create_week_view(prev_monday)
            
        elif view_type == "日视图":
            # 前一天
            self.current_date = self.current_date.addDays(-1)
            self.create_day_view(self.current_date)
    
    def next_navigation(self):
        """导航到后一个时间单位（月/周/日）"""
        if self.is_updating:
            return
            
        view_type = self.view_combo.currentText()
        
        if view_type == "月视图":
            # 下个月
            year = self.current_date.year()
            month = self.current_date.month() + 1
            
            # 处理年份变化
            if month > 12:
                month = 1
                year += 1
                
            self.current_date = QDate(year, month, 1)
            self.selected_date = self.current_date
            self.load_month_tasks()
            
        elif view_type == "周视图":
            # 下一周
            # 确保总是以周一为起点
            current_monday = self.get_monday_of_week(self.current_date)
            # 下一周的周一是当前周一加7天
            next_monday = current_monday.addDays(7)
            self.current_date = next_monday
            self.create_week_view(next_monday)
            
        elif view_type == "日视图":
            # 后一天
            self.current_date = self.current_date.addDays(1)
            self.create_day_view(self.current_date)
    
    def today_navigation(self):
        """导航到当前时间单位（本月/本周/今天）"""
        if self.is_updating:
            return
            
        view_type = self.view_combo.currentText()
        today = QDate.currentDate()
        
        if view_type == "月视图":
            # 本月
            year = today.year()
            month = today.month()
            self.current_date = QDate(year, month, 1)
            self.selected_date = today
            self.load_month_tasks()
            
        elif view_type == "周视图":
            # 本周，从本周的周一开始
            current_monday = self.get_monday_of_week(today)
            self.current_date = current_monday
            self.create_week_view(current_monday)
            
        elif view_type == "日视图":
            # 今天
            self.current_date = today
            self.create_day_view(self.current_date)
            
    def get_monday_of_week(self, date):
        """获取指定日期所在周的周一日期"""
        days_to_monday = date.dayOfWeek() - 1
        # 处理周日的特殊情况
        if days_to_monday < 0:
            days_to_monday = 6
        return date.addDays(-days_to_monday)
    
    def create_week_view(self, start_date):
        """创建周视图"""
        if self.is_updating:
            return
            
        self.is_updating = True
        
        try:
            # 清理所有视图
            self.clean_views()
                
            # 创建新的周视图小部件
            self.week_widget = QWidget(self)
            self.main_layout.addWidget(self.week_widget)
            
            # 创建周视图布局，减少顶部间距
            week_layout = QVBoxLayout(self.week_widget)
            week_layout.setContentsMargins(0, 0, 0, 0)
            week_layout.setSpacing(0)
            
            # 创建日期标题栏
            header_container = QWidget()
            header_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            header_container.setFixedHeight(30)  # 控制高度
            header_container.setStyleSheet("background-color: #F8F8F8; border-bottom: 1px solid #E0E0E0;")
            
            header_layout = QHBoxLayout(header_container)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(0)
            
            # 添加左侧空白，对齐时间轴
            time_axis_header = QWidget()
            time_axis_header.setFixedWidth(50)  # 增加宽度以适应时间标签
            time_axis_header.setStyleSheet("background-color: #F2F2F2; border-right: 1px solid #E0E0E0;")
            header_layout.addWidget(time_axis_header)
            
            # 确保始终从周一开始显示
            first_day_of_week = start_date.dayOfWeek()
            if first_day_of_week != 1:  # 如果不是周一
                # 计算到最近的周一的天数差
                days_to_monday = -(first_day_of_week - 1)
                if days_to_monday == 0:
                    days_to_monday = -6  # 如果是周日，回退6天到上周一
                # 调整开始日期
                start_date = start_date.addDays(days_to_monday)
            
            # 添加每天的标题
            self.header_dates = []  # 存储为实例属性以便后续访问
            for i in range(7):
                day_date = start_date.addDays(i)
                self.header_dates.append(day_date)
                day_header = WeekDayHeader(day_date)
                # 设置拉伸因子为1，使所有标题均匀分布
                header_layout.addWidget(day_header, 1)
                
                # 给每个日期标题添加上下文菜单
                day_header.setContextMenuPolicy(Qt.CustomContextMenu)
                day_header.customContextMenuRequested.connect(
                    lambda pos, date=day_date: self.show_day_context_menu(pos, date)
                )
            
            week_layout.addWidget(header_container)
            
            # 创建主内容滚动区域
            content_scroll = ScrollArea()
            content_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
            content_scroll.setWidgetResizable(True)
            week_layout.addWidget(content_scroll, 1)  # 使其占据所有可用空间
            
            # 创建主内容容器
            content_widget = QWidget()
            content_widget.setObjectName("weekViewContent")
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            content_scroll.setWidget(content_widget)
            
            # 创建时间轴
            time_axis = QWidget()
            time_axis.setFixedWidth(50)  # 增加宽度以适应时间标签
            time_axis.setStyleSheet("background-color: #F2F2F2; border-right: 1px solid #E0E0E0;")
            time_axis_layout = QVBoxLayout(time_axis)
            time_axis_layout.setContentsMargins(0, 0, 0, 0)
            time_axis_layout.setSpacing(0)
            
            # 工作时间索引，用于滚动
            work_hour_index = None
            
            # 每小时高度
            hour_height = 50
            
            # 添加小时标签
            for hour_idx, hour in enumerate(range(0, 24)):
                # 记录工作开始时间
                if hour == 9:
                    work_hour_index = hour_idx
                    
                hour_label = HourlyLabel(hour)
                hour_label.setFixedHeight(hour_height)
                time_axis_layout.addWidget(hour_label)
            
            content_layout.addWidget(time_axis)
            
            # 创建任务区域容器
            days_container = QWidget()
            days_container.setObjectName("daysContainer")
            days_layout = QHBoxLayout(days_container)
            days_layout.setContentsMargins(0, 0, 0, 0)
            days_layout.setSpacing(1)  # 日列之间的间距
            
            # 创建每一天的列
            self.day_columns = []  # 存储为实例属性以便后续访问
            for i in range(7):
                day_date = self.header_dates[i]
                
                # 创建列容器
                day_column = QWidget()
                day_column.setObjectName(f"dayColumn_{i}")
                day_column.setStyleSheet("background-color: white;")
                day_column.setFixedHeight(24 * hour_height)  # 总高度
                
                # 为日期列创建布局
                day_layout = QVBoxLayout(day_column)
                day_layout.setContentsMargins(0, 0, 0, 0)
                day_layout.setSpacing(0)
                
                # 创建小时行背景
                for hour in range(24):
                    hour_row = QFrame(day_column)
                    hour_row.setFrameShape(QFrame.NoFrame)
                    hour_row.setFixedHeight(hour_height)
                    
                    # 差异化工作时间和非工作时间的背景
                    if 9 <= hour < 18:  # 工作时间
                        hour_row.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #e0e0e0;")
                    else:  # 非工作时间
                        hour_row.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e0e0;")
                    
                    # 给每个小时行添加上下文菜单
                    current_datetime = datetime.combine(day_date.toPyDate(), datetime.min.time().replace(hour=hour))
                    hour_row.setContextMenuPolicy(Qt.CustomContextMenu)
                    hour_row.customContextMenuRequested.connect(
                        lambda pos, dt=current_datetime: self.show_time_slot_context_menu(pos, dt)
                    )
                    
                    day_layout.addWidget(hour_row)
                
                # 添加日列到布局
                days_layout.addWidget(day_column, 1)  # 均分宽度
                self.day_columns.append(day_column)
                
                # 给日期列添加上下文菜单
                day_column.setContextMenuPolicy(Qt.CustomContextMenu)
                day_column.customContextMenuRequested.connect(
                    lambda pos, date=day_date: self.show_day_context_menu(pos, date)
                )
            
            content_layout.addWidget(days_container, 1)  # 日容器占据主要空间
            
            # 收集一周的所有任务
            week_tasks = []
            
            # 获取每一天的任务并存储
            for i, day_date in enumerate(self.header_dates):
                py_date = day_date.toPyDate()
                
                # 获取当天的任务
                day_tasks = self.scheduler_manager.get_tasks_by_date(py_date)
                
                # 为每个任务添加当天索引
                for task in day_tasks:
                    # 深拷贝任务数据以防止引用问题
                    task_copy = task.copy()
                    task_copy['day_index'] = i
                    week_tasks.append(task_copy)
            
            # 按开始时间排序任务
            week_tasks.sort(key=lambda x: x.get("start_time"))
            
            # 强制更新布局，确保能获取正确的列宽度
            self.week_widget.adjustSize()
            self.main_layout.update()
            QApplication.processEvents()
            
            # 为每天计算任务布局，优化任务显示
            self.day_task_layouts = {}  # 存储为实例属性以便后续访问
            
            # 根据day_index将任务分配到对应的日期
            for task in week_tasks:
                day_index = task.get('day_index', 0)
                
                # 初始化该日的任务列表（如果不存在）
                if day_index not in self.day_task_layouts:
                    self.day_task_layouts[day_index] = []
                
                # 将任务添加到当天
                self.day_task_layouts[day_index].append(task)
            
            # 为每一天创建任务小部件
            for day_index in range(7):
                if day_index not in self.day_task_layouts:
                    continue
                    
                day_tasks = self.day_task_layouts[day_index]
                day_column = self.day_columns[day_index]
                day_date = self.header_dates[day_index]
                
                # 确保列有固定宽度和高度
                column_width = max(100, day_column.width())  # 确保最小宽度
                
                # 按小时段收集任务并统一处理，避免重叠
                hour_task_groups = {}  # 每小时的任务组
                
                for task in day_tasks:
                    task_start = task.get("start_time")
                    task_end = task.get("end_time")
                    
                    # 处理跨天任务
                    start_hour = 0 if task_start.date() < day_date.toPyDate() else task_start.hour
                    end_hour = 24 if task_end.date() > day_date.toPyDate() else task_end.hour + (1 if task_end.minute > 0 else 0)
                    
                    # 将任务添加到所有覆盖的小时组
                    for hour in range(start_hour, end_hour):
                        if hour not in hour_task_groups:
                            hour_task_groups[hour] = []
                        hour_task_groups[hour].append(task)
                
                # 创建任务小部件，横向均分显示
                created_widgets = set()  # 使用集合避免重复创建
                
                for hour, hour_tasks in sorted(hour_task_groups.items()):
                    # 如果有任务，计算每个任务的大小和位置
                    if hour_tasks:
                        # 计算每个任务的宽度，确保不为0
                        task_width = (column_width - 10) / len(hour_tasks)
                        task_width = max(50, task_width)  # 确保最小宽度
                        
                        for task_index, task in enumerate(hour_tasks):
                            task_id = task.get("id")
                            
                            # 检查任务是否已经创建过小部件
                            if task_id in created_widgets:
                                continue
                                
                            task_start = task.get("start_time")
                            task_end = task.get("end_time")
                            
                            # 计算任务在视图中的正确位置
                            # 垂直位置（y坐标）取决于任务的小时和分钟
                            # 水平位置（x坐标）取决于任务所属日期列
                            
                            # 计算垂直位置和高度
                            task_start_date = task_start.date()
                            task_end_date = task_end.date()
                            day_py_date = day_date.toPyDate()
                            
                            # 确定开始时间（分钟）
                            if task_start_date < day_py_date:
                                # 跨天任务，在当天开始位置为0分钟
                                start_minutes = 0
                            else:
                                # 当天任务，根据实际时间计算
                                start_minutes = task_start.hour * 60 + task_start.minute
                            
                            # 确定结束时间（分钟）
                            if task_end_date > day_py_date:
                                # 跨天任务，在当天结束位置为24小时（1440分钟）
                                end_minutes = 24 * 60
                            else:
                                # 当天任务，根据实际时间计算
                                end_minutes = task_end.hour * 60 + task_end.minute
                            
                            # 确保开始时间不大于结束时间（可能由于日期计算误差导致）
                            if start_minutes >= end_minutes:
                                # 如果是同一天的任务但计算出错误的时间，至少显示1小时
                                if task_start_date == task_end_date and task_start_date == day_py_date:
                                    end_minutes = start_minutes + 60  # 至少持续1小时
                                # 如果是跨天任务，则应该填充整天
                                else:
                                    start_minutes = 0
                                    end_minutes = 24 * 60
                            
                            # 转换为视图中的位置
                            # 小时高度是每小时的像素高度
                            start_y = (start_minutes / 60.0) * hour_height
                            height = ((end_minutes - start_minutes) / 60.0) * hour_height
                            height = max(25, height)  # 确保最小高度
                            
                            # 计算水平位置（均分）
                            x_pos = 5 + task_index * task_width
                            
                            # 创建任务小部件
                            task_widget = WeekTaskWidget(task)
                            task_widget.setParent(day_column)
                            task_widget.setGeometry(int(x_pos), int(start_y), int(task_width - 5), int(height))
                            
                            # 连接点击和上下文菜单事件
                            task_widget.clicked.connect(lambda task_data=task: self.edit_task(task_data))
                            task_widget.setContextMenuPolicy(Qt.CustomContextMenu)
                            task_widget.customContextMenuRequested.connect(
                                lambda pos, t=task: self.show_task_context_menu(pos, t)
                            )
                            
                            task_widget.show()
                            
                            # 记录已创建的小部件
                            created_widgets.add(task_id)
            
            # 添加任务列表显示完成后的回调，确保每列的任务在窗口调整大小时能正确显示
            QTimer.singleShot(100, self.on_layout_done)
            
            # 更新日期选择器
            self.date_picker.blockSignals(True)
            self.date_picker.setDate(start_date)
            self.date_picker.blockSignals(False)
            
            # 更新当前日期
            self.current_date = start_date
            
            # 滚动到工作时间
            if work_hour_index is not None:
                QTimer.singleShot(100, lambda: 
                    content_scroll.verticalScrollBar().setValue(work_hour_index * hour_height - hour_height))
        finally:
            self.is_updating = False
            
    def on_layout_done(self):
        """布局完成后的回调，用于初始化窗口大小变化处理"""
        # 为每列初始化大小变化事件处理
        try:
            # 检查是否处于周视图
            if hasattr(self, 'day_columns') and self.day_columns:
                for i, day_column in enumerate(self.day_columns):
                    if not hasattr(self, 'day_task_layouts') or i not in self.day_task_layouts:
                        continue
                        
                    day_date = self.header_dates[i]
                    
                    # 设置大小调整事件处理
                    day_column.resizeEvent = lambda event, column=day_column, date=day_date: self.column_resize_event(event, column, date)
        except (AttributeError, IndexError) as e:
            print(f"错误：{e}")
            # 可能不在周视图中或属性尚未初始化
            pass
    
    def column_resize_event(self, event, column, day_date):
        """周视图列大小调整事件处理"""
        # 获取当前列宽
        column_width = column.width()
        
        # 获取当前列中的所有任务小部件，并按小时分组
        hour_widgets = {}
        
        for child in column.children():
            if isinstance(child, WeekTaskWidget):
                task_data = child.task_data
                task_start = task_data.get("start_time")
                task_start_date = task_start.date()
                day_py_date = day_date.toPyDate()
                
                # 获取任务的小时，处理跨天任务
                if task_start_date < day_py_date:
                    start_hour = 0
                else:
                    start_hour = task_start.hour
                
                # 按小时为键分组任务小部件
                if start_hour not in hour_widgets:
                    hour_widgets[start_hour] = []
                hour_widgets[start_hour].append(child)
        
        # 遍历所有小时组，调整每组中任务的宽度和位置
        for hour, widgets in hour_widgets.items():
            if not widgets:
                continue
                
            # 计算同一时间段内每个任务的宽度
            task_width = (column_width - 10) / len(widgets)
            task_width = max(50, task_width)  # 确保最小宽度
            
            # 重新计算每个任务的水平位置，保持垂直位置不变
            for idx, widget in enumerate(widgets):
                x_pos = 5 + idx * task_width
                widget.setGeometry(int(x_pos), widget.y(), 
                                  int(task_width - 5), widget.height())
        
        # 调用原始的事件处理函数
        QWidget.resizeEvent(column, event)

    def create_day_view(self, date):
        """创建日视图"""
        if self.is_updating:
            return
            
        self.is_updating = True
        print(f"创建日视图: {date.toString('yyyy-MM-dd')}")
        
        try:
            # 清理所有视图
            self.clean_views()
                
            # 创建新的日视图小部件
            self.day_widget = QWidget(self)
            self.main_layout.addWidget(self.day_widget)
            
            # 创建日视图布局，减少顶部空白
            day_layout = QVBoxLayout(self.day_widget)
            day_layout.setContentsMargins(0, 0, 0, 0)
            day_layout.setSpacing(0)
            
            # 创建日期标题
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            weekday = weekday_names[date.dayOfWeek() - 1]
            date_str = date.toString("yyyy年MM月dd日")
            
            # 创建日期标题容器并设置自适应宽度
            date_header_container = QWidget()
            date_header_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            date_header_container.setFixedHeight(30)  # 增加高度
            date_header_container.setStyleSheet("background-color: #F8F8F8; border-bottom: 1px solid #E0E0E0;")
            
            date_header_layout = QHBoxLayout(date_header_container)
            date_header_layout.setContentsMargins(10, 0, 10, 0)  # 添加水平边距
            
            # 创建日期标题标签
            date_header = QLabel(f"{date_str} ({weekday})")
            date_header.setAlignment(Qt.AlignCenter)
            
            # 根据星期几设置样式
            if date.dayOfWeek() > 5:  # 周末
                date_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #E53935;")  # 红色
            elif date.toPyDate() == datetime.now().date():  # 今天
                date_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")  # 蓝色
            else:
                date_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
                
            date_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            date_header_layout.addWidget(date_header)
            
            day_layout.addWidget(date_header_container)
            
            # 创建主内容滚动区域
            content_scroll = ScrollArea()
            content_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
            content_scroll.setWidgetResizable(True)
            day_layout.addWidget(content_scroll, 1)  # 占据所有可用空间
            
            # 创建主内容容器
            content_widget = QWidget()
            content_widget.setObjectName("dayViewContent")
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            content_scroll.setWidget(content_widget)
            
            # 创建时间轴
            time_axis = QWidget()
            time_axis.setFixedWidth(50)  # 增加宽度以适应时间标签
            time_axis.setStyleSheet("background-color: #F2F2F2; border-right: 1px solid #E0E0E0;")
            time_axis_layout = QVBoxLayout(time_axis)
            time_axis_layout.setContentsMargins(0, 0, 0, 0)
            time_axis_layout.setSpacing(0)
            
            # 设置时间槽高度
            time_slot_height = 25  # 每30分钟的高度
            
            # 添加30分钟间隔的时间标签
            time_slots = []
            for hour in range(0, 24):
                for minute in [0, 30]:
                    time_slot = QWidget()
                    time_slot.setFixedHeight(time_slot_height)
                    time_slot_layout = QHBoxLayout(time_slot)
                    time_slot_layout.setContentsMargins(0, 0, 5, 0)
                    
                    time_label = QLabel(f"{hour:02d}:{minute:02d}")
                    time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # 设置时间标签样式
                    if 9 <= hour < 18:  # 工作时间
                        time_label.setStyleSheet("font-size: 10px; color: #333333;")
                    else:  # 非工作时间
                        time_label.setStyleSheet("font-size: 10px; color: #757575;")
                        
                    time_slot_layout.addWidget(time_label)
                    time_axis_layout.addWidget(time_slot)
                    time_slots.append(time_slot)
            
            content_layout.addWidget(time_axis)
            
            # 创建任务区域
            tasks_container = QWidget()
            tasks_container.setObjectName("tasksContainer")
            tasks_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tasks_container.setFixedHeight(48 * time_slot_height)  # 48个半小时时间槽
            tasks_container.setStyleSheet("background-color: white;")
            
            # 获取当天的任务
            day_tasks = self.scheduler_manager.get_tasks_by_date(date.toPyDate())
            day_tasks.sort(key=lambda x: x.get("start_time"))  # 按开始时间排序
            
            print(f"找到 {len(day_tasks)} 个任务")
            for i, task in enumerate(day_tasks):
                print(f"任务 {i+1}: {task.get('title')} - {task.get('start_time')} 至 {task.get('end_time')}")
            
            # 记录工作时间的位置，用于后续滚动
            work_hour_index = None
            
            # 创建时间槽背景
            for slot_idx, (hour, minute) in enumerate([(h, m) for h in range(24) for m in [0, 30]]):
                # 记录早上9点的位置，用于初始滚动
                if hour == 9 and minute == 0:
                    work_hour_index = slot_idx
                
                # 创建时间槽背景
                slot_bg = QFrame(tasks_container)
                slot_bg.setFixedHeight(time_slot_height)
                slot_bg.move(0, slot_idx * time_slot_height)
                slot_bg.resize(tasks_container.width(), time_slot_height)
                
                # 设置时间槽样式
                if 9 <= hour < 18:  # 工作时间
                    slot_bg.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #e0e0e0;")
                else:  # 非工作时间
                    slot_bg.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e0e0;")
                
                # 设置时间槽的上下文菜单
                current_datetime = datetime.combine(date.toPyDate(), datetime.min.time().replace(hour=hour, minute=minute))
                slot_bg.setContextMenuPolicy(Qt.CustomContextMenu)
                slot_bg.customContextMenuRequested.connect(
                    lambda pos, dt=current_datetime: self.show_time_slot_context_menu(pos, dt)
                )
            
            # 创建任务小部件
            # 先分配任务到各个时间槽，用于检测重叠的任务
            time_slot_tasks = {}  # 存储每个小时的任务组
            created_task_widgets = set()  # 避免创建重复的任务小部件
            
            # 按时间分组任务，用于后续的位置计算
            for task in day_tasks:
                task_id = task.get("id")
                if not task_id:
                    print(f"警告: 任务 {task.get('title')} 没有ID")
                    continue
                    
                task_start = task.get("start_time")
                task_end = task.get("end_time")
                
                if not task_start or not task_end:
                    print(f"警告: 任务 {task.get('title')} 没有开始或结束时间")
                    continue
                
                # 计算任务在视图中的位置和时间跨度（以分钟为单位）
                start_minutes = task_start.hour * 60 + task_start.minute
                end_minutes = task_end.hour * 60 + task_end.minute
                
                # 处理跨天任务
                task_start_date = task_start.date()
                task_end_date = task_end.date()
                selected_date = date.toPyDate()
                
                # 调整任务在当天的时间范围
                if task_start_date < selected_date:
                    print(f"任务 {task.get('title')} 开始于前一天，调整开始时间为 00:00")
                    start_minutes = 0
                    
                if task_end_date > selected_date:
                    print(f"任务 {task.get('title')} 结束于后一天，调整结束时间为 23:59")
                    end_minutes = 24 * 60 - 1  # 23:59
                
                # 确保任务至少持续30分钟，便于显示
                if end_minutes - start_minutes < 30:
                    end_minutes = start_minutes + 30
                
                # 分配任务到时间槽
                for hour in range(start_minutes // 60, (end_minutes + 59) // 60):
                    if hour < 0:
                        hour = 0
                    if hour >= 24:
                        hour = 23
                        
                    if hour not in time_slot_tasks:
                        time_slot_tasks[hour] = []
                    
                    # 检查是否已经添加过这个任务
                    if not any(t.get("id") == task_id for t in time_slot_tasks[hour]):
                        time_slot_tasks[hour].append(task)
            
            # 对每个时间槽内的任务进行位置计算
            for hour, hour_tasks in sorted(time_slot_tasks.items()):
                if not hour_tasks:
                    continue
                    
                # 计算当前小时内每个任务的宽度
                task_count = len(hour_tasks)
                available_width = tasks_container.width() - 10  # 减去边距
                task_width = max(available_width / task_count, 50)  # 确保最小宽度
                
                # 为每个任务创建小部件
                for idx, task in enumerate(hour_tasks):
                    task_id = task.get("id")
                    
                    # 避免重复创建
                    if task_id in created_task_widgets:
                        continue
                        
                    created_task_widgets.add(task_id)
                    
                    task_start = task.get("start_time")
                    task_end = task.get("end_time")
                    
                    # 计算开始和结束时间（分钟数）
                    start_minutes = task_start.hour * 60 + task_start.minute
                    end_minutes = task_end.hour * 60 + task_end.minute
                    
                    # 处理跨天任务
                    task_start_date = task_start.date()
                    task_end_date = task_end.date()
                    selected_date = date.toPyDate()
                    
                    if task_start_date < selected_date:
                        start_minutes = 0
                    if task_end_date > selected_date:
                        end_minutes = 24 * 60 - 1
                    
                    # 确保任务至少持续30分钟，便于显示
                    if end_minutes - start_minutes < 30:
                        end_minutes = start_minutes + 30
                    
                    # 分配任务到时间槽
                    for hour in range(start_minutes // 60, (end_minutes + 59) // 60):
                        if hour < 0:
                            hour = 0
                        if hour >= 24:
                            hour = 23
                            
                        if hour not in time_slot_tasks:
                            time_slot_tasks[hour] = []
                        
                        # 检查是否已经添加过这个任务
                        if not any(t.get("id") == task_id for t in time_slot_tasks[hour]):
                            time_slot_tasks[hour].append(task)
            
            # 对每个时间槽内的任务进行位置计算
            for hour, hour_tasks in sorted(time_slot_tasks.items()):
                if not hour_tasks:
                    continue
                    
                # 计算当前小时内每个任务的宽度
                task_count = len(hour_tasks)
                available_width = tasks_container.width() - 10  # 减去边距
                task_width = max(available_width / task_count, 50)  # 确保最小宽度
                
                # 为每个任务创建小部件
                for idx, task in enumerate(hour_tasks):
                    task_id = task.get("id")
                    
                    # 避免重复创建
                    if task_id in created_task_widgets:
                        continue
                        
                    created_task_widgets.add(task_id)
                    
                    task_start = task.get("start_time")
                    task_end = task.get("end_time")
                    
                    # 计算开始和结束时间（分钟数）
                    start_minutes = task_start.hour * 60 + task_start.minute
                    end_minutes = task_end.hour * 60 + task_end.minute
                    
                    # 处理跨天任务
                    task_start_date = task_start.date()
                    task_end_date = task_end.date()
                    selected_date = date.toPyDate()
                    
                    if task_start_date < selected_date:
                        start_minutes = 0
                    if task_end_date > selected_date:
                        end_minutes = 24 * 60 - 1
                    
                    # 确保任务在图表范围内
                    start_minutes = max(0, min(start_minutes, 24 * 60 - 1))
                    end_minutes = max(start_minutes + 30, min(end_minutes, 24 * 60 - 1))
                    
                    # 计算对应的时间槽索引
                    start_slot_idx = start_minutes // 30
                    end_slot_idx = (end_minutes + 29) // 30  # 向上取整
                    end_slot_idx = min(end_slot_idx, 48 - 1)  # 确保不超过最大时间槽
                    
                    # 计算垂直位置和高度（每30分钟为一个槽）
                    # 修正：算出每分钟在像素上的高度，然后计算精确的位置
                    minutes_per_pixel = 30.0 / time_slot_height
                    
                    # 计算起始位置的像素偏移量
                    start_y = start_slot_idx * time_slot_height
                    # 加上分钟偏移（如果不是整点或半点）
                    minutes_offset = start_minutes % 30
                    if minutes_offset > 0:
                        start_y += minutes_offset / minutes_per_pixel
                    
                    # 计算高度（单位：像素）
                    total_minutes = end_minutes - start_minutes
                    height = total_minutes / minutes_per_pixel
                    
                    # 确保最小高度
                    height = max(25, height)
                    
                    # 计算水平位置
                    x_pos = 5 + idx * task_width
                    
                    # 创建任务小部件
                    task_widget = WeekTaskWidget(task)
                    task_widget.setParent(tasks_container)
                    
                    # 设置位置和大小
                    task_widget.setGeometry(int(x_pos), int(start_y), int(task_width - 5), int(height))
                    
                    # 添加上下文菜单
                    task_widget.setContextMenuPolicy(Qt.CustomContextMenu)
                    task_widget.customContextMenuRequested.connect(
                        lambda pos, t=task: self.show_task_context_menu(pos, t)
                    )
                    
                    # 连接点击事件
                    task_widget.clicked.connect(lambda t=task: self.edit_task(t))
                    
                    task_widget.show()
                    print(f"创建任务组件: {task.get('title')} 位置:({int(x_pos)}, {int(start_y)}) 大小:({int(task_width - 5)}, {int(height)})")
            
            # 使用专门的大小调整事件处理器
            tasks_container.resizeEvent = lambda event: self.tasks_container_resize_event(
                event, tasks_container, time_slot_tasks, date
            )
            
            content_layout.addWidget(tasks_container, 1)  # 任务区域占据主要空间
            
            # 设置容器上下文菜单
            tasks_container.setContextMenuPolicy(Qt.CustomContextMenu)
            tasks_container.customContextMenuRequested.connect(
                lambda pos: self.show_context_menu(pos)
            )
            
            # 更新日期选择器
            self.date_picker.blockSignals(True)
            self.date_picker.setDate(date)
            self.date_picker.blockSignals(False)
            
            # 更新当前日期
            self.current_date = date
            
            # 滚动到工作时间
            if work_hour_index is not None:
                QTimer.singleShot(100, lambda: 
                    content_scroll.verticalScrollBar().setValue(
                        work_hour_index * time_slot_height - time_slot_height * 3)
                )
        finally:
            self.is_updating = False
            
    def tasks_container_resize_event(self, event, container, time_slot_tasks, date):
        """处理任务容器大小变化事件"""
        try:
            # 清除现有任务小部件
            for child in container.children():
                if isinstance(child, WeekTaskWidget):
                    child.hide()
                    child.deleteLater()
            
            # 重新计算并创建任务小部件
            created_task_widgets = set()
            time_slot_height = 25  # 每30分钟的高度
            
            # 对每个时间槽内的任务进行位置计算
            for hour, hour_tasks in sorted(time_slot_tasks.items()):
                if not hour_tasks:
                    continue
                    
                # 计算当前小时内每个任务的宽度
                task_count = len(hour_tasks)
                available_width = container.width() - 10  # 减去边距
                task_width = max(available_width / task_count, 50)  # 确保最小宽度
                
                # 为每个任务创建小部件
                for idx, task in enumerate(hour_tasks):
                    task_id = task.get("id")
                    
                    # 避免重复创建
                    if task_id in created_task_widgets:
                        continue
                        
                    created_task_widgets.add(task_id)
                    
                    task_start = task.get("start_time")
                    task_end = task.get("end_time")
                    
                    # 计算开始和结束时间（分钟数）
                    start_minutes = task_start.hour * 60 + task_start.minute
                    end_minutes = task_end.hour * 60 + task_end.minute
                    
                    # 处理跨天任务
                    task_start_date = task_start.date()
                    task_end_date = task_end.date()
                    selected_date = date.toPyDate()
                    
                    if task_start_date < selected_date:
                        start_minutes = 0
                    if task_end_date > selected_date:
                        end_minutes = 24 * 60 - 1
                    
                    # 确保任务在图表范围内
                    start_minutes = max(0, min(start_minutes, 24 * 60 - 1))
                    end_minutes = max(start_minutes + 30, min(end_minutes, 24 * 60 - 1))
                    
                    # 计算对应的时间槽索引
                    start_slot_idx = start_minutes // 30
                    end_slot_idx = (end_minutes + 29) // 30  # 向上取整
                    end_slot_idx = min(end_slot_idx, 48 - 1)  # 确保不超过最大时间槽
                    
                    # 计算垂直位置和高度（每30分钟为一个槽）
                    # 修正：算出每分钟在像素上的高度，然后计算精确的位置
                    minutes_per_pixel = 30.0 / time_slot_height
                    
                    # 计算起始位置的像素偏移量
                    start_y = start_slot_idx * time_slot_height
                    # 加上分钟偏移（如果不是整点或半点）
                    minutes_offset = start_minutes % 30
                    if minutes_offset > 0:
                        start_y += minutes_offset / minutes_per_pixel
                    
                    # 计算高度（单位：像素）
                    total_minutes = end_minutes - start_minutes
                    height = total_minutes / minutes_per_pixel
                    
                    # 确保最小高度
                    height = max(25, height)
                    
                    # 计算水平位置
                    x_pos = 5 + idx * task_width
                    
                    # 创建任务小部件
                    task_widget = WeekTaskWidget(task)
                    task_widget.setParent(container)
                    
                    # 设置位置和大小
                    task_widget.setGeometry(int(x_pos), int(start_y), int(task_width - 5), int(height))
                    
                    # 添加上下文菜单
                    task_widget.setContextMenuPolicy(Qt.CustomContextMenu)
                    task_widget.customContextMenuRequested.connect(
                        lambda pos, t=task: self.show_task_context_menu(pos, t)
                    )
                    
                    # 连接点击事件
                    task_widget.clicked.connect(lambda t=task: self.edit_task(t))
                    
                    task_widget.show()
            
            # 调用原始的事件处理函数
            QWidget.resizeEvent(container, event)
        except Exception as e:
            print(f"调整任务容器大小时出错: {e}")
    
    def show_day_context_menu(self, position, date):
        """显示日期上下文菜单（在周视图中）"""
        # 创建菜单
        menu = RoundMenu(self)
        
        # 确定发送者对象
        sender = self.sender()
        
        # 添加新任务选项
        add_action = Action(FluentIcon.ADD, "添加新任务")
        date_str = date.toString("yyyy-MM-dd")
        add_action.triggered.connect(lambda: self.add_task_on_date(date))
        menu.addAction(add_action)
        
        # 添加查看选项
        view_action = Action(FluentIcon.VIEW, "查看日视图")
        view_action.triggered.connect(lambda: self.view_specific_day(date))
        menu.addAction(view_action)
        
        # 显示菜单
        # 使用sender的全局位置，确保菜单正确显示在右键点击位置
        if sender:
            menu.exec_(sender.mapToGlobal(position))
        else:
            menu.exec_(self.mapToGlobal(position))
    
    def add_task_on_date(self, date):
        """在指定日期添加新任务"""
        # 设置合理的开始结束时间
        start_datetime = datetime.combine(date.toPyDate(), datetime.min.time().replace(hour=9))
        end_datetime = datetime.combine(date.toPyDate(), datetime.min.time().replace(hour=10))
        
        # 创建任务数据
        task_data = {
            "id": None,  # 新任务，ID为空
            "title": "",
            "description": "",
            "start_time": start_datetime,
            "end_time": end_datetime,
            "priority": "中",
            "status": "未开始",
            "completed": False
        }
        
        # 打开任务编辑对话框
        try:
            dialog = TaskDialog(
                self.window(), 
                self.scheduler_manager,
                self.window().config_manager,
                self.window().subtask_manager,
                task_data
            )
            if dialog.exec_():
                # 刷新视图
                self.refresh()
        except Exception as e:
            print(f"添加任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title="错误",
                content=f"添加任务时出错: {e}",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def view_specific_day(self, date):
        """查看特定日期的日视图"""
        # 设置当前日期并切换到日视图
        self.current_date = date
        self.view_combo.setCurrentText("日视图")
    
    def show_time_slot_context_menu(self, position, datetime_val):
        """显示时间槽上下文菜单（在日视图中）"""
        # 创建菜单
        menu = RoundMenu(self)
        
        # 获取发送者对象确保正确的位置
        sender = self.sender()
        
        # 添加新任务选项，使用特定时间
        time_str = datetime_val.strftime("%H:%M")
        add_action = Action(FluentIcon.ADD, f"在 {time_str} 添加新任务")
        add_action.triggered.connect(lambda: self.add_task_at_time(datetime_val))
        menu.addAction(add_action)
        
        # 显示菜单在正确位置
        if sender:
            menu.exec_(sender.mapToGlobal(position))
        else:
            menu.exec_(self.mapToGlobal(position))
    
    def add_task_at_time(self, start_datetime):
        """在指定时间添加新任务"""
        # 创建任务数据，设置结束时间为开始时间后一小时
        end_datetime = start_datetime + timedelta(hours=1)
        
        # 创建任务数据
        task_data = {
            "id": None,  # 新任务，ID为空
            "title": "",
            "description": "",
            "start_time": start_datetime,
            "end_time": end_datetime,
            "priority": "中",
            "status": "未开始",
            "completed": False
        }
        
        # 打开任务编辑对话框
        try:
            dialog = TaskDialog(
                self.window(), 
                self.scheduler_manager,
                self.window().config_manager,
                self.window().subtask_manager,
                task_data
            )
            if dialog.exec_():
                # 刷新视图
                self.refresh()
                
                # 显示成功消息
                InfoBar.success(
                    title="成功",
                    content="任务已更新",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000
                )
        except Exception as e:
            print(f"编辑任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title="错误",
                content=f"编辑任务时出错: {e}",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def on_view_changed(self, index):
        """视图切换事件处理"""
        if self.is_updating:
            return
            
        # 获取当前选择的视图类型
        view_type = self.view_combo.currentText()
        
        # 更新导航按钮
        self.update_navigation_buttons()
        
        # 管理星期标签行的可见性
        for i in range(self.week_layout.count()):
            item = self.week_layout.itemAt(i)
            if item and item.widget():
                # 只在月视图中显示星期标签
                item.widget().setVisible(view_type == "月视图")
        
        if view_type == "月视图":
            self.load_month_tasks()
        elif view_type == "周视图":
            # 计算本周的起始日期（周一）
            current_monday = self.get_monday_of_week(self.current_date)
            
            # 创建周视图
            self.create_week_view(current_monday)
        elif view_type == "日视图":
            # 创建日视图
            self.create_day_view(self.current_date)
    
    def refresh(self):
        """刷新当前视图"""
        try:
            # 自动更新任务状态
            self.scheduler_manager.auto_update_task_status()
            
            # 根据当前视图刷新
            view_type = self.view_combo.currentText()
            
            if view_type == "月视图":
                self.load_month_tasks()
            elif view_type == "周视图":
                # 计算当前周的起始日期（周一）
                days_to_monday = self.current_date.dayOfWeek() - 1
                if days_to_monday < 0:  # 如果是周日
                    days_to_monday = 6
                monday = self.current_date.addDays(-days_to_monday)
                self.create_week_view(monday)
            elif view_type == "日视图":
                self.create_day_view(self.current_date)
                
            print(f"日历视图已刷新: {view_type}")
        except Exception as e:
            print(f"刷新视图时出错: {e}")
            import traceback
            traceback.print_exc()

    def show_context_menu(self, position):
        """显示上下文菜单"""
        # 创建菜单
        menu = RoundMenu(self)
        
        # 获取发送者对象确保正确的位置
        sender = self.sender()
        
        # 添加新任务选项
        add_action = Action(FluentIcon.ADD, "添加新任务")
        add_action.triggered.connect(self.add_new_task)
        menu.addAction(add_action)
        
        # 分隔线
        menu.addSeparator()
        
        # 刷新选项
        refresh_action = Action(text="刷新视图")
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)
        
        # 根据当前视图类型添加特定选项
        view_type = self.view_combo.currentText()
        if view_type == "月视图":
            # 查看本周选项
            view_week_action = Action(FluentIcon.CALENDAR, "查看本周")
            view_week_action.triggered.connect(lambda: self.view_combo.setCurrentText("周视图"))
            menu.addAction(view_week_action)
        elif view_type == "周视图" or view_type == "日视图":
            # 返回月视图选项
            view_month_action = Action(FluentIcon.CALENDAR, "返回月视图")
            view_month_action.triggered.connect(lambda: self.view_combo.setCurrentText("月视图"))
            menu.addAction(view_month_action)
        
        # 显示菜单在正确位置
        if sender:
            menu.exec_(sender.mapToGlobal(position))
        else:
            menu.exec_(self.mapToGlobal(position))
            
    def add_new_task(self):
        """添加新任务"""
        # 根据当前视图和日期创建新任务
        view_type = self.view_combo.currentText()
        selected_date = self.current_date
        
        # 设置合理的开始结束时间
        start_datetime = datetime.combine(selected_date.toPyDate(), datetime.min.time().replace(hour=9))
        end_datetime = datetime.combine(selected_date.toPyDate(), datetime.min.time().replace(hour=10))
        
        # 创建任务数据
        task_data = {
            "id": None,  # 新任务，ID为空
            "title": "",
            "description": "",
            "start_time": start_datetime,
            "end_time": end_datetime,
            "priority": "中",
            "status": "未开始",
            "completed": False
        }
        
        # 打开任务编辑对话框
        try:
            dialog = TaskDialog(
                self.window(), 
                self.scheduler_manager,
                self.window().config_manager,
                self.window().subtask_manager,
                task_data
            )
            if dialog.exec_():
                # 刷新视图
                self.refresh()
        except Exception as e:
            print(f"添加任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title="错误",
                content=f"添加任务时出错: {e}",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def show_task_context_menu(self, position, task):
        """显示任务上下文菜单"""
        # 创建菜单
        menu = RoundMenu(self)
        sender = self.sender()
        
        # 编辑任务
        edit_action = Action(FluentIcon.EDIT, "编辑任务")
        edit_action.triggered.connect(lambda: self.edit_task(task))
        menu.addAction(edit_action)
        
        # 任务状态快速切换
        status = task.get("status", "未开始")
        completed = task.get("completed", False)
        
        if completed:
            # 取消完成 - 使用普通的CHECKBOX图标代替CHECKBOX_UNCHECKED
            complete_action = Action(FluentIcon.CHECKBOX, "标记为未完成")
            complete_action.triggered.connect(lambda: self.quick_change_task_completion(task, False))
        else:
            # 标记完成
            complete_action = Action(FluentIcon.CHECKBOX, "标记为已完成")
            complete_action.triggered.connect(lambda: self.quick_change_task_completion(task, True))
            
        menu.addAction(complete_action)
        
        # 添加暂停/恢复选项
        if status == "进行中":
            pause_action = Action(FluentIcon.PAUSE, "暂停任务")
            pause_action.triggered.connect(lambda: self.quick_change_status(task, "已暂停"))
            menu.addAction(pause_action)
        elif status == "已暂停":
            # 检查任务时间，确定恢复后的状态
            suggested_status = self.scheduler_manager.check_task_time_status(task)
            if suggested_status == "未开始":
                resume_text = "恢复为待办"
            else:
                resume_text = "恢复为进行中"
                
            resume_action = Action(FluentIcon.PLAY, resume_text)
            resume_action.triggered.connect(lambda: self.quick_change_status(task, "auto"))
            menu.addAction(resume_action)
        elif status == "未开始":
            start_action = Action(FluentIcon.PLAY, "开始任务")
            start_action.triggered.connect(lambda: self.quick_change_status(task, "进行中"))
            menu.addAction(start_action)
        
        # 添加删除选项
        delete_action = Action(FluentIcon.DELETE, "删除任务")
        delete_action.triggered.connect(lambda: self.delete_task(task))
        menu.addAction(delete_action)
        
        # 分隔线
        menu.addSeparator()
        
        # 快速修改优先级
        priority_menu = RoundMenu("修改优先级", self)
        
        # 优先级选项
        for priority in ["低", "中", "高", "紧急"]:
            priority_action = Action(text=priority)
            # 如果是当前优先级，添加选中标记
            if priority == task.get("priority"):
                priority_action.setCheckable(True)
                priority_action.setChecked(True)
                
            priority_action.triggered.connect(
                lambda checked, p=priority, t=task: self.quick_change_priority(t, p)
            )
            priority_menu.addAction(priority_action)
            
        menu.addMenu(priority_menu)
        
        # 快速修改状态
        status_menu = RoundMenu("修改状态", self)
        
        # 状态选项
        for status_option in ["未开始", "进行中", "已暂停", "已完成"]:
            status_action = Action(text=status_option)
            # 如果是当前状态，添加选中标记
            if status_option == status:
                status_action.setCheckable(True)
                status_action.setChecked(True)
                
            status_action.triggered.connect(
                lambda checked, s=status_option, t=task: self.quick_change_status(t, s)
            )
            status_menu.addAction(status_action)
            
        menu.addMenu(status_menu)
        
        # 显示菜单在正确位置
        if sender:
            menu.exec_(sender.mapToGlobal(position))
        else:
            menu.exec_(self.mapToGlobal(position))
            
    def quick_change_task_completion(self, task, completed):
        """快速更改任务完成状态"""
        # 复制任务数据并修改完成状态
        updated_task = task.copy()
        updated_task["completed"] = completed
        
        # 如果标记为完成，自动设置状态为已完成
        if completed:
            updated_task["status"] = "已完成"
        
        # 更新任务
        if self.scheduler_manager.update_task(updated_task):
            # 显示成功消息
            completion_status = "已完成" if completed else "未完成"
            try:
                InfoBar.success(
                    title="已更新",
                    content=f"任务已标记为{completion_status}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            # 刷新视图
            self.refresh()
        else:
            # 显示错误消息
            try:
                InfoBar.error(
                    title="更新失败",
                    content="无法更新任务状态，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            
    def quick_change_status(self, task, status):
        """快速修改任务状态"""
        # 复制任务数据并修改状态
        updated_task = task.copy()
        old_status = task.get("status", "未开始")
        
        # 处理自动状态和从暂停状态恢复
        if status == "auto" or (old_status == "已暂停" and status != "已暂停"):
            # 根据当前时间自动判断应该设置为"未开始"还是"进行中"
            suggested_status = self.scheduler_manager.check_task_time_status(updated_task)
            # 如果建议的状态不是"已暂停"，则使用建议的状态
            if suggested_status != "已暂停" and suggested_status != "已完成":
                status = suggested_status
        
        updated_task["status"] = status
        
        # 如果状态改为已完成，自动标记完成
        if status == "已完成":
            updated_task["completed"] = True
        
        # 更新任务
        if self.scheduler_manager.update_task(updated_task):
            # 显示成功消息
            try:
                InfoBar.success(
                    title="已更新",
                    content=f"任务状态已设置为 {status}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            # 刷新视图
            self.refresh()
        else:
            # 显示错误消息
            try:
                InfoBar.error(
                    title="更新失败",
                    content="无法更新任务状态，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
                
    def quick_change_priority(self, task, priority):
        """快速修改任务优先级"""
        # 复制任务数据并修改优先级
        updated_task = task.copy()
        updated_task["priority"] = priority
        
        # 更新任务
        if self.scheduler_manager.update_task(updated_task):
            # 显示成功消息
            try:
                InfoBar.success(
                    title="已更新",
                    content=f"任务优先级已设置为 {priority}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            # 刷新视图
            self.refresh()
        else:
            # 显示错误消息
            try:
                InfoBar.error(
                    title="更新失败",
                    content="无法更新任务优先级，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
    
    def delete_task(self, task):
        """删除任务"""
        # 显示确认对话框
        confirm = MessageBox(
            "确认删除",
            f"确定要删除任务 '{task.get('title', '未命名任务')}' 吗？",
            self
        )
        if not confirm.exec_():
            return
        
        # 删除任务
        if self.scheduler_manager.delete_task(task["id"]):
            # 显示成功消息
            try:
                InfoBar.success(
                    title="已删除",
                    content="任务已成功删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            # 刷新视图
            self.refresh()
        else:
            # 显示错误消息
            try:
                InfoBar.error(
                    title="删除失败",
                    content="无法删除任务，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")

    def edit_task(self, task_data):
        """编辑任务"""
        try:
            # 导入任务对话框
            from ui.task_dialog import TaskDialog
            
            dialog = TaskDialog(
                self, 
                self.scheduler_manager,
                self.window().config_manager if hasattr(self.window(), 'config_manager') else None,
                self.window().subtask_manager if hasattr(self.window(), 'subtask_manager') else None,
                task_data
            )
            if dialog.exec_():
                # 刷新视图
                self.refresh()
        except Exception as e:
            print(f"编辑任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 显示错误消息
            try:
                InfoBar.error(
                    title="编辑失败",
                    content=f"编辑任务时出错: {e}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
            
class WeekTaskWidget(QWidget):
    """周视图中的任务小部件"""
    
    clicked = pyqtSignal(dict)  # 点击任务时发出信号，包含任务数据
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setMinimumHeight(20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 设置边框、圆角和阴影效果
        self.setStyleSheet("""
            QWidget {
                border-radius: 3px;
                border: none;
            }
        """)
        
        # 检查任务状态
        status = self.task_data.get("status", "未开始")
        if status == "已暂停":
            # 暂停状态使用灰色
            self.bg_color = QColor(224, 224, 224)  # 灰色
            self.border_color = QColor(180, 180, 180)  # 深灰色边框
            self.text_color = QColor(120, 120, 120)  # 深灰色文本
        else:
            # 设置任务背景色
            priority = self.task_data.get("priority", "中")
            if priority == "紧急":
                self.bg_color = QColor(255, 205, 210)  # 淡红色
                self.border_color = QColor(229, 115, 115)  # 深红色边框
            elif priority == "高":
                self.bg_color = QColor(255, 224, 178)  # 淡橙色
                self.border_color = QColor(255, 183, 77)  # 深橙色边框
            elif priority == "中":
                self.bg_color = QColor(187, 222, 251)  # 淡蓝色
                self.border_color = QColor(100, 181, 246)  # 深蓝色边框
            else:  # 低
                self.bg_color = QColor(200, 230, 201)  # 淡绿色
                self.border_color = QColor(129, 199, 132)  # 深绿色边框
            
            # 设置文本颜色
            self.text_color = QColor(33, 33, 33)  # 深灰色文本
        
        # 激活鼠标跟踪以实现悬停效果
        self.setMouseTracking(True)
        self.is_hovered = False
        
        # 显示tooltip
        self.update_tooltip()
    
    def update_tooltip(self):
        """更新工具提示"""
        title = self.task_data.get("title", "")
        start_time = self.task_data.get("start_time")
        end_time = self.task_data.get("end_time")
        description = self.task_data.get("description", "")
        priority = self.task_data.get("priority", "中")
        status = self.task_data.get("status", "未开始")
        date_format = "%Y-%m-%d %H:%M"
        
        tooltip_text = (
            f"<b>{title}</b><br>"
            f"<b>时间:</b> {start_time.strftime(date_format)} 至 {end_time.strftime(date_format)}<br>"
            f"<b>优先级:</b> {priority}<br>"
            f"<b>状态:</b> {status}<br>"
        )
        
        if description:
            # 限制描述长度，避免过长
            max_desc_len = 100
            if len(description) > max_desc_len:
                description = description[:max_desc_len] + "..."
            tooltip_text += f"<b>描述:</b> {description}"
        
        self.setToolTip(tooltip_text)
    
    def paintEvent(self, event):
        """绘制任务小部件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取任务数据
        title = self.task_data.get("title", "")
        start_time = self.task_data.get("start_time")
        end_time = self.task_data.get("end_time")
        status = self.task_data.get("status", "未开始")
        
        # 定义绘制区域
        rect = self.rect().adjusted(1, 1, -1, -1)  # 缩小1像素，留出边距
        
        # 绘制背景和边框
        if self.is_hovered:
            # 悬停时背景更明亮
            bg_color = self.bg_color.lighter(105)
            border_color = self.border_color.darker(110)
            shadow_color = QColor(0, 0, 0, 40)
            
            # 绘制轻微阴影效果
            shadow_rect = rect.adjusted(2, 2, 2, 2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawRoundedRect(shadow_rect, 3, 3)
        else:
            bg_color = self.bg_color
            border_color = self.border_color
        
        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 3, 3)
        
        # 绘制左侧边框
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(border_color))
        painter.drawRect(0, 0, 3, self.height())
        
        # 如果是暂停状态，绘制虚线边框
        if status == "已暂停":
            pen = QPen(border_color, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 3, 3)
        
        # 文本区域（留出左侧边框和右侧边距）
        text_rect = QRect(6, 0, self.width() - 8, self.height())
        
        # 适应不同尺寸的显示策略
        painter.setPen(QPen(self.text_color))
        
        # 基于宽度选择字体大小
        available_width = self.width()
        if available_width < 60:  # 极窄空间
            font_size = 6
        elif available_width < 80:  # 窄空间
            font_size = 7
        else:  # 正常空间
            font_size = 8
            
        # 基于高度选择显示内容
        if self.height() >= 50:  # 高度足够显示完整信息
            # 画标题
            title_font = QFont("Microsoft YaHei", font_size + 1)
            title_font.setBold(True)
            painter.setFont(title_font)
            
            title_rect = QRect(6, 3, self.width() - 10, 20)
            elided_title = painter.fontMetrics().elidedText(title, Qt.ElideRight, title_rect.width())
            painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, elided_title)
            
            # 画时间
            time_font = QFont("Microsoft YaHei", font_size)
            painter.setFont(time_font)
            
            time_text = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            time_rect = QRect(6, title_rect.bottom(), self.width() - 10, 20)
            painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignTop, time_text)
            
            # 如果有描述且高度足够，显示部分描述
            description = self.task_data.get("description", "")
            if description and self.height() >= 70:
                desc_font = QFont("Microsoft YaHei", font_size)
                painter.setFont(desc_font)
                
                desc_rect = QRect(6, time_rect.bottom(), self.width() - 10, self.height() - title_rect.height() - time_rect.height() - 5)
                # 截断过长的描述
                elided_desc = painter.fontMetrics().elidedText(description, Qt.ElideRight, desc_rect.width() * 2)  # 允许多行
                # 最多显示两行
                lines = elided_desc.split("\n")
                if len(lines) > 2:
                    elided_desc = "\n".join(lines[:2]) + "..."
                painter.drawText(desc_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, elided_desc)
                
        elif self.height() >= 30:  # 中等高度，只显示标题和时间
            # 使用适应宽度的字体
            painter.setFont(QFont("Microsoft YaHei", font_size))
            
            # 显示开始时间和标题
            time_text = start_time.strftime('%H:%M')
            
            # 检查宽度是否足够显示时间和标题
            time_width = painter.fontMetrics().width(time_text)
            
            # 添加暂停状态指示
            prefix = ""
            if status == "已暂停":
                prefix = "⏸ "
            
            if available_width > time_width + 15 and title:
                # 计算可用于标题的宽度
                title_width = available_width - time_width - 12
                elided_title = painter.fontMetrics().elidedText(title, Qt.ElideRight, title_width)
                display_text = f"{prefix}{time_text} {elided_title}"
            else:
                display_text = f"{prefix}{time_text}"
                
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, display_text)
            
        else:  # 最小高度，优先显示时间
            # 使用最小字体
            painter.setFont(QFont("Microsoft YaHei", font_size))
            
            # 仅显示开始时间，如果空间允许则显示部分标题
            time_text = start_time.strftime('%H:%M')
            time_width = painter.fontMetrics().width(time_text)
            
            # 添加暂停状态指示
            prefix = ""
            if status == "已暂停":
                prefix = "⏸ "
            
            # 如果宽度足够，加上标题
            if available_width > time_width + 15 and title:
                remaining_width = available_width - time_width - 12
                elided_title = painter.fontMetrics().elidedText(title, Qt.ElideRight, remaining_width)
                display_text = f"{prefix}{time_text} {elided_title}"
            else:
                display_text = f"{prefix}{time_text}"
                
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, display_text)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.setCursor(Qt.PointingHandCursor)
        self.update()  # 触发重绘
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.setCursor(Qt.ArrowCursor)
        self.update()  # 触发重绘
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task_data)
        # 注意：右键事件由上下文菜单策略处理
        super().mousePressEvent(event)

class WeekDayHeader(QWidget):
    """周视图中的日期标题栏"""
    
    def __init__(self, date, parent=None):
        super().__init__(parent)
        self.date = date
        self.setFixedHeight(30)  # 增加高度以容纳更多内容
        # 移除固定宽度设置，允许自适应
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 设置基础背景色
        self.bg_color = QColor(245, 245, 245)
        self.is_today = False
        self.is_weekend = False
        
        # 检查是否是今天
        today = datetime.now().date()
        if self.date.toPyDate() == today:
            self.bg_color = QColor(220, 237, 255)  # 更明显的今天高亮
            self.is_today = True
            
        # 周末使用略微不同的背景色
        if self.date.dayOfWeek() > 5:  # 周六或周日
            self.bg_color = QColor(252, 245, 245) if not self.is_today else self.bg_color
            self.is_weekend = True
    
    def paintEvent(self, event):
        """绘制日期标题"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRect(self.rect())
        
        # 绘制底部边框，周末或今天使用特殊颜色
        if self.is_today:
            border_color = QColor(100, 181, 246)  # 蓝色边框
            border_width = 2
        elif self.is_weekend:
            border_color = QColor(239, 154, 154)  # 淡红色边框
            border_width = 1
        else:
            border_color = QColor(200, 200, 200)
            border_width = 1
            
        painter.setPen(QPen(border_color, border_width))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        
        # 获取日期信息
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][self.date.dayOfWeek() - 1]
        date_str = self.date.toString("MM-dd")
        
        # 使用不同颜色绘制周末
        if self.is_weekend:
            weekday_color = QColor(239, 83, 80)  # 红色
        else:
            weekday_color = QColor(33, 33, 33)
            
        # 今天使用蓝色
        if self.is_today:
            weekday_color = QColor(33, 150, 243)  # 蓝色
            
        # 绘制星期文本
        painter.setPen(QPen(weekday_color))
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold if self.is_today else QFont.Normal))
        
        # 分别绘制星期和日期
        weekday_rect = QRect(0, 2, self.width(), 15)
        date_rect = QRect(0, 16, self.width(), 14)
        
        painter.drawText(weekday_rect, Qt.AlignCenter, weekday)
        
        # 使用稍小的字体绘制日期
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.drawText(date_rect, Qt.AlignCenter, date_str)

class HourlyLabel(QWidget):
    """时间轴上的小时标签"""
    
    def __init__(self, hour, parent=None):
        super().__init__(parent)
        self.hour = hour
        self.setFixedWidth(50)  # 增加宽度以适应更多文本
    
    def paintEvent(self, event):
        """绘制小时标签"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取小时起止范围
        start_hour_str = f"{self.hour:02d}:00"
        end_hour_str = f"{(self.hour+1) % 24:02d}:00"
        
        # 为工作时间和非工作时间使用不同颜色
        if 9 <= self.hour < 18:  # 工作时间
            text_color = QColor(30, 30, 30)
        else:  # 非工作时间
            text_color = QColor(120, 120, 120)
        
        # 绘制背景
        # 交替使用略微不同的背景色使时间轴更易读
        if self.hour % 2 == 0:
            bg_color = QColor(248, 248, 248)
        else:
            bg_color = QColor(245, 245, 245)
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(self.rect())
        
        # 绘制时间文本
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Microsoft YaHei", 8))
        
        text_rect = QRect(0, 0, self.width() - 5, self.height())
        painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, start_hour_str)
        
        # 绘制右侧和底部分隔线
        painter.setPen(QPen(QColor(220, 220, 220)))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1) 