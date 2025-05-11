#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
甘特图视图模块
以甘特图形式展示任务进度和时间线
"""

from datetime import datetime, timedelta
import math

from PyQt5.QtCore import Qt, QRectF, QDate, QDateTime, QSize, QPoint, pyqtSignal, QTimer, QEvent, QMimeData
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath, QDrag
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QSplitter, QGridLayout, QMenu, QHeaderView, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QFrame, QSizePolicy
)

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, ComboBox, 
    CalendarPicker, LineEdit, InfoBar, InfoBarPosition,
    CheckBox, SpinBox, ToolButton
)

from ui.task_dialog import TaskDialog

class GanttHeaderWidget(QWidget):
    """甘特图头部日期栏"""
    
    def __init__(self, start_date, end_date, day_width=30, parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.end_date = end_date
        self.day_width = day_width
        self.min_day_width = 20  # 最小日期宽度
        self.max_day_width = 100  # 最大日期宽度
        
        # 计算天数
        self.days = (end_date - start_date).days + 1
        
        # 计算总宽度
        self.total_width = self.days * self.day_width
        
        # 设置固定宽度，保证与甘特图任务区域宽度完全一致
        self.setFixedWidth(int(self.total_width))
        self.setFixedHeight(50)
        
    def updateDayWidth(self, new_width):
        """更新日宽度并重新计算总宽度
        
        Args:
            new_width: 新的日宽度
        """
        # 更新日宽度
        self.day_width = min(self.max_day_width, max(self.min_day_width, new_width))
        
        # 重新计算总宽度
        self.total_width = self.days * self.day_width
        
        # 更新固定宽度
        self.setFixedWidth(int(self.total_width))
        
        # 强制重绘
        self.update()
        
    def resizeEvent(self, event):
        """处理大小变化事件，重新计算day_width"""
        # 我们现在不在resize事件中改变day_width，而是通过updateDayWidth方法来控制
        super().resizeEvent(event)
        
    def paintEvent(self, event):
        """绘制日期头部"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        
        # 获取滚动偏移量 - 从父组件中获取
        scroll_offset = 0
        parent = self.parent()
        while parent:
            if isinstance(parent, GanttChart) and parent.horizontalScrollBar():
                scroll_offset = parent.horizontalScrollBar().value()
                break
            parent = parent.parent()
        
        # 获取日期范围
        current_date = self.start_date
        
        # 计算绘制起始位置，考虑滚动偏移量
        start_x = -scroll_offset
        
        # 确定起始日期索引，避免绘制不可见的日期
        if scroll_offset > 0:
            days_to_skip = int(scroll_offset / self.day_width)
            if days_to_skip > 0:
                current_date += timedelta(days=days_to_skip)
                start_x += days_to_skip * self.day_width
        
        # 计算可见区域能显示的天数
        visible_width = self.width()
        days_to_show = int(visible_width / self.day_width) + 2  # 多显示2天确保边界平滑
        
        # 绘制可见区域的日期
        x = start_x
        day_count = 0
        
        while current_date <= self.end_date and day_count < days_to_show:
            # 绘制日期分隔线
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.drawLine(int(x), 0, int(x), self.height())
            
            # 绘制日期文本
            date_str = current_date.strftime("%m-%d")
            day_str = current_date.strftime("%a")
            
            # 周末使用不同颜色
            if current_date.weekday() >= 5:  # 5=周六, 6=周日
                painter.setPen(QPen(QColor(220, 20, 60)))  # 红色
            else:
                painter.setPen(QPen(QColor(0, 0, 0)))
                
            # 绘制日期
            # 当日期宽度小于阈值时显示简化格式
            if self.day_width < 35:
                # 简化日期格式，只显示日
                date_str = current_date.strftime("%d")
                painter.drawText(int(x + (self.day_width - painter.fontMetrics().width(date_str)) / 2), 
                               20, date_str)
                
                # 不显示星期
                if self.day_width >= 25:  # 宽度稍大时尝试显示简化星期
                    day_abbr = current_date.strftime("%a")[0]  # 只取第一个字母
                    painter.drawText(int(x + (self.day_width - painter.fontMetrics().width(day_abbr)) / 2), 
                                  40, day_abbr)
            else:
                # 正常显示
                painter.drawText(int(x + 5), 20, date_str)
                painter.drawText(int(x + 5), 40, day_str)
            
            # 移动到下一天
            current_date += timedelta(days=1)
            x += self.day_width
            day_count += 1
            
        # 绘制今天的指示线
        today = datetime.now().date()
        if self.start_date <= today <= self.end_date:
            days_from_start = (today - self.start_date).days
            today_x = days_from_start * self.day_width - scroll_offset
            
            # 只在可见区域内绘制今日线
            if 0 <= today_x <= visible_width:
                painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.DashLine))
                painter.drawLine(int(today_x), 0, int(today_x), self.height())

class GanttTaskBar(QWidget):
    """甘特图中的任务条"""
    
    clicked = pyqtSignal(dict)  # 点击任务时发出信号
    dragMoved = pyqtSignal(dict, int)  # 拖动任务时发出信号，包含任务数据和水平偏移量
    resized = pyqtSignal(dict, int, bool)  # 调整大小时发出信号，包含任务数据、天数变化、是否调整开始日期
    
    def __init__(self, task_data, start_date, day_width=30, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.start_date = start_date
        self.day_width = day_width
        self.dragging = False  # 拖拽标记
        self.resize_left = False  # 左侧调整大小标记
        self.resize_right = False  # 右侧调整大小标记
        self.drag_start_x = 0  # 拖拽开始位置
        self.original_x = 0  # 原始X位置
        self.original_width = 0  # 原始宽度
        self.hover = False  # 鼠标悬停标记
        self.last_position = 0  # 最后位置，用于计算变化量
        self.last_width = 0  # 最后宽度，用于计算变化量
        self.resize_margin = 5  # 调整大小的边缘宽度
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 计算任务条位置和大小
        task_start = self.task_data.get("start_time")
        task_end = self.task_data.get("end_time")
        
        # 计算开始位置 - 确保精确对齐到网格
        days_from_start = (task_start.date() - self.start_date).days
        start_offset = days_from_start * self.day_width
        
        # 计算持续时间宽度（至少一天）
        duration_days = max(1, (task_end.date() - task_start.date()).days + 1)
        width = duration_days * self.day_width
        
        # 设置位置和大小 - 使用精确计算结果
        self.setGeometry(int(start_offset), 5, int(width), 25)
        
        # 根据优先级设置颜色
        priority = self.task_data.get("priority", "中")
        if priority == "低":
            self.bg_color = QColor(76, 175, 80)  # 绿色
        elif priority == "中":
            self.bg_color = QColor(33, 150, 243)  # 蓝色
        elif priority == "高":
            self.bg_color = QColor(255, 152, 0)  # 橙色
        else:  # 紧急
            self.bg_color = QColor(244, 67, 54)  # 红色
            
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置工具提示
        self.update_tooltip()
        
    def update_tooltip(self):
        """更新工具提示"""
        task_start = self.task_data.get("start_time")
        task_end = self.task_data.get("end_time")
        completed = self.task_data.get("completed", False)
        status = self.task_data.get("status", "未开始")
        priority = self.task_data.get("priority", "中")
        
        # 计算剩余天数或超期天数
        today = datetime.now().date()
        end_date = task_end.date()
        days_left = (end_date - today).days
        
        days_info = ""
        if not completed:
            if days_left > 0:
                days_info = f"\n剩余天数: {days_left}天"
            elif days_left < 0:
                days_info = f"\n已超期: {-days_left}天"
            else:
                days_info = "\n今日到期"
        
        completion_text = "已完成" if completed else "未完成"
        
        self.setToolTip(
            f"<b>{self.task_data.get('title')}</b>\n"
            f"描述: {self.task_data.get('description')}\n"
            f"开始: {task_start.strftime('%Y-%m-%d %H:%M')}\n"
            f"结束: {task_end.strftime('%Y-%m-%d %H:%M')}\n"
            f"状态: {status}\n"
            f"完成: {completion_text}\n"
            f"优先级: {priority}{days_info}"
        )
        
    def paintEvent(self, event):
        """绘制任务条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 任务完成状态
        completed = self.task_data.get("completed", False)
        
        # 获取任务进度比例
        progress = self.task_data.get("progress", 0)
        if completed:
            progress = 100
        
        # 绘制任务背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 3, 3)
        
        # 悬停效果
        bg_color = self.bg_color
        if self.hover:
            bg_color = bg_color.lighter(110)
            
        painter.fillPath(path, bg_color)
        
        # 绘制进度条背景
        if progress > 0:
            progress_width = (progress / 100.0) * self.width()
            progress_rect = QRectF(0, 0, progress_width, self.height())
            progress_path = QPainterPath()
            progress_path.addRoundedRect(progress_rect, 3, 3)
            
            # 调整进度条颜色
            progress_color = bg_color.darker(120)
            painter.fillPath(progress_path, progress_color)
        
        # 绘制文本
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Microsoft YaHei", 8))
        
        # 获取任务标题
        title = self.task_data.get("title", "")
        
        # 计算文本可见宽度
        visible_width = self.width() - 10
        
        # 在进度上叠加文本
        text_rect = QRectF(5, 0, visible_width, self.height())
        
        # 添加任务完成图标
        display_text = title
        if completed:
            display_text = "✓ " + display_text
        
        # 添加天数提示
        today = datetime.now().date()
        end_date = self.task_data.get("end_time").date()
        days_left = (end_date - today).days
        
        # 如果任务未完成且逾期，添加警告图标
        if not completed and days_left < 0:
            display_text = "⚠ " + display_text
            
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_text)
        
        # 绘制边框，拖拽时边框更明显
        if self.dragging:
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        elif self.hover:
            painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        else:
            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 3, 3)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hover = False
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().leaveEvent(event)
            
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，实现拖拽和调整大小功能"""
        if self.resize_left:
            # 左侧调整大小
            delta_x = event.globalPos().x() - self.drag_start_x
            new_x = self.original_x + delta_x
            new_width = self.original_width - delta_x
            
            # 限制最小宽度为一天
            min_width = self.day_width
            if new_width < min_width:
                new_width = min_width
                new_x = self.original_x + self.original_width - min_width
            
            # 吸附到天网格 - 修复计算错误
            grid_size = self.day_width
            days_offset = round(new_x / grid_size)
            grid_position = days_offset * grid_size
            
            # 如果靠近网格线，吸附到网格
            if abs(new_x - grid_position) < grid_size / 3:
                new_x = grid_position
                new_width = self.original_x + self.original_width - new_x
            
            # 更新位置和大小
            self.setGeometry(int(new_x), self.y(), int(new_width), self.height())
            self.last_position = new_x  # 保存最后位置用于释放时计算
                
        elif self.resize_right:
            # 右侧调整大小
            delta_x = event.globalPos().x() - self.drag_start_x
            new_width = self.original_width + delta_x
            
            # 限制最小宽度为一天
            min_width = self.day_width
            if new_width < min_width:
                new_width = min_width
            
            # 吸附到天网格 - 修复计算错误
            grid_size = self.day_width
            days_width = round(new_width / grid_size)
            grid_width = days_width * grid_size
            
            # 如果靠近网格线，吸附到网格
            if abs(new_width - grid_width) < grid_size / 3:
                new_width = grid_width
            
            # 更新大小
            self.setGeometry(self.x(), self.y(), int(new_width), self.height())
            self.last_width = new_width  # 保存最后宽度用于释放时计算
                
        elif self.dragging:
            # 整体拖动
            delta_x = event.globalPos().x() - self.drag_start_x
            new_x = self.original_x + delta_x
            
            # 限制不能拖拽到开始日期之前
            if new_x < 0:
                new_x = 0
                
            # 吸附到天网格 - 修复计算错误
            grid_size = self.day_width
            days_offset = round(new_x / grid_size)
            grid_position = days_offset * grid_size
            
            # 如果靠近网格线，吸附到网格
            if abs(new_x - grid_position) < grid_size / 3:
                new_x = grid_position
                
            # 更新位置
            self.move(int(new_x), self.y())
            self.last_position = new_x  # 保存最后位置用于释放时计算
                
        elif event.buttons() == Qt.NoButton:
            # 鼠标悬停时更新光标
            x = event.x()
            if x < self.resize_margin:
                self.setCursor(Qt.SizeHorCursor)
            elif x > self.width() - self.resize_margin:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
            
            # 高亮显示
            self.hover = True
            self.update()
            
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_x = event.globalPos().x()
            self.original_x = self.x()
            self.original_width = self.width()
            self.last_position = self.original_x  # 初始化最后位置
            self.last_width = self.original_width  # 初始化最后宽度
            
            # 判断是拖拽还是调整大小
            x = event.x()
            if x < self.resize_margin:
                self.resize_left = True
                self.setCursor(Qt.SizeHorCursor)
            elif x > self.width() - self.resize_margin:
                self.resize_right = True
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.dragging = True
                self.setCursor(Qt.ClosedHandCursor)
                
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            was_dragging = self.dragging
            was_resizing_left = self.resize_left
            was_resizing_right = self.resize_right
            
            # 计算变化量并发送信号 - 只在松开鼠标时发送一次
            if was_dragging:
                # 修复天数计算 - 根据准确的网格位置计算
                grid_size = self.day_width
                original_days = round(self.original_x / grid_size)
                new_days = round(self.last_position / grid_size)
                days_moved = new_days - original_days
                
                # 只有当实际移动了才发出信号
                if days_moved != 0:
                    print(f"拖动完成: 移动了 {days_moved} 天")
                    self.dragMoved.emit(self.task_data, days_moved)
            
            elif was_resizing_left:
                # 修复天数计算 - 根据准确的网格位置计算
                grid_size = self.day_width
                original_days = round(self.original_x / grid_size)
                new_days = round(self.last_position / grid_size)
                days_changed = original_days - new_days
                
                # 只有当实际调整了大小才发出信号
                if days_changed != 0:
                    print(f"左侧调整完成: 变化了 {days_changed} 天")
                    self.resized.emit(self.task_data, days_changed, True)
                    
            elif was_resizing_right:
                # 修复天数计算 - 根据准确的网格位置计算
                grid_size = self.day_width
                original_width_days = round(self.original_width / grid_size)
                new_width_days = round(self.last_width / grid_size)
                days_changed = new_width_days - original_width_days
                
                # 只有当实际调整了大小才发出信号
                if days_changed != 0:
                    print(f"右侧调整完成: 变化了 {days_changed} 天")
                    self.resized.emit(self.task_data, days_changed, False)
            
            # 重置状态
            self.dragging = False
            self.resize_left = False
            self.resize_right = False
            
            # 根据鼠标位置设置光标
            x = event.x()
            if x < self.resize_margin or x > self.width() - self.resize_margin:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
            
            self.update()
            
            # 如果既没有拖拽也没有调整大小，视为点击
            if not was_dragging and not was_resizing_left and not was_resizing_right:
                self.clicked.emit(self.task_data)
                
        super().mouseReleaseEvent(event)

class GanttTaskRow(QWidget):
    """甘特图中的任务行"""
    
    dragStarted = pyqtSignal(object)  # 拖拽开始信号，传递行对象
    dragEntered = pyqtSignal(object)  # 拖拽进入信号，传递行对象
    taskOrderChanged = pyqtSignal(dict, int)  # 任务顺序变化信号，传递任务数据和新顺序
    
    def __init__(self, task_data, start_date, end_date, day_width=30, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.start_date = start_date
        self.end_date = end_date
        self.day_width = day_width
        self.dragging = False  # 水平拖拽标记
        self.vertical_dragging = False  # 垂直拖拽标记
        self.drag_start_y = 0  # 垂直拖拽起始位置
        self.highlight_as_drop_target = False  # 是否高亮显示为放置目标
        
        # 计算总天数
        self.days = (end_date - start_date).days + 1
        
        # 设置固定高度和最小宽度
        self.setFixedHeight(35)
        self.setMinimumWidth(int(self.days * self.day_width))
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        
        # 接受拖放
        self.setAcceptDrops(True)
        
        # 添加任务条
        self.task_bar = GanttTaskBar(task_data, start_date, day_width, self)
        
        # 连接信号
        self.task_bar.clicked.connect(self.on_task_clicked)
        self.task_bar.dragMoved.connect(self.on_task_drag_moved)
        self.task_bar.resized.connect(self.on_task_resized)  # 添加新的连接
        
    def update_layout(self):
        """根据day_width更新布局"""
        # 重新计算行的最小宽度
        self.setMinimumWidth(int(self.days * self.day_width))
        
        # 更新任务条位置和大小
        if self.task_bar:
            # 计算任务条开始位置
            task_start = self.task_data.get("start_time")
            task_end = self.task_data.get("end_time")
            
            # 精确计算开始位置
            days_from_start = (task_start.date() - self.start_date).days
            start_offset = days_from_start * self.day_width
            
            # 精确计算持续时间宽度（至少一天）
            duration_days = max(1, (task_end.date() - task_start.date()).days + 1)
            width = duration_days * self.day_width
            
            # 更新任务条几何属性 - 使用精确的计算结果
            self.task_bar.setGeometry(int(start_offset), 5, int(width), 25)
            self.task_bar.day_width = self.day_width
            
            # 确保任务条正确显示 - 这是一个强制绘制
            self.task_bar.update()
            
        # 更新网格线和背景
        self.update()
        
    def on_task_clicked(self, task_data):
        """当任务被点击时，查找GanttChart并调用其edit_task方法"""
        # 查找GanttChart父级
        parent = self.parent()
        while parent and not isinstance(parent, GanttChart):
            parent = parent.parent()
            
        if parent and isinstance(parent, GanttChart):
            parent.edit_task(task_data)
    
    def on_task_drag_moved(self, task_data, days_moved):
        """处理任务拖拽移动"""
        if days_moved == 0:
            return
        
        print(f"甘特图行: 任务拖动 {days_moved} 天，任务ID = {task_data.get('id')}")
        
        # 创建任务数据副本
        updated_task = task_data.copy()
        
        # 更新开始和结束日期
        start_time = updated_task.get("start_time")
        end_time = updated_task.get("end_time")
        
        new_start = start_time + timedelta(days=days_moved)
        new_end = end_time + timedelta(days=days_moved)
        
        updated_task["start_time"] = new_start
        updated_task["end_time"] = new_end
        
        print(f"  新开始时间: {new_start}")
        print(f"  新结束时间: {new_end}")
        
        # 先更新任务条位置，以便用户有即时反馈
        # 精确计算任务条新位置
        days_from_start = (new_start.date() - self.start_date).days
        start_offset = days_from_start * self.day_width
        
        # 精确计算任务条宽度
        duration_days = max(1, (new_end.date() - new_start.date()).days + 1)
        width = duration_days * self.day_width
        
        # 使用精确计算的结果更新位置
        self.task_bar.setGeometry(int(start_offset), 5, int(width), 25)
        
        # 查找GanttChart并更新任务
        parent = self.parent()
        while parent and not isinstance(parent, GanttChart):
            parent = parent.parent()
            
        if parent and isinstance(parent, GanttChart):
            # 更新任务数据 - 这里将间接触发日历视图更新
            parent.update_task(updated_task)
    
    def on_task_resized(self, task_data, days_changed, is_start_date):
        """处理任务调整大小事件"""
        if days_changed == 0:
            return
            
        print(f"甘特图行: 任务调整大小 {days_changed} 天，调整{'开始' if is_start_date else '结束'}时间，任务ID = {task_data.get('id')}")
            
        # 创建任务数据副本
        updated_task = task_data.copy()
        
        # 更新开始日期或结束日期
        start_time = updated_task.get("start_time")
        end_time = updated_task.get("end_time")
        
        if is_start_date:
            # 调整开始日期
            new_start = start_time - timedelta(days=days_changed)
            updated_task["start_time"] = new_start
            print(f"  新开始时间: {new_start}")
            
            # 先更新任务条的视觉效果，提供即时反馈
            # 精确计算新位置
            days_from_start = (new_start.date() - self.start_date).days
            start_offset = days_from_start * self.day_width
            
            # 精确计算新宽度
            duration_days = max(1, (end_time.date() - new_start.date()).days + 1)
            width = duration_days * self.day_width
            
            # 使用精确计算的结果更新位置和大小
            self.task_bar.setGeometry(int(start_offset), 5, int(width), 25)
        else:
            # 调整结束日期
            new_end = end_time + timedelta(days=days_changed)
            updated_task["end_time"] = new_end
            print(f"  新结束时间: {new_end}")
            
            # 先更新任务条的视觉效果，提供即时反馈
            # 精确计算新位置（开始位置不变）
            days_from_start = (start_time.date() - self.start_date).days
            start_offset = days_from_start * self.day_width
            
            # 精确计算新宽度
            duration_days = max(1, (new_end.date() - start_time.date()).days + 1)
            width = duration_days * self.day_width
            
            # 使用精确计算的结果更新大小
            self.task_bar.setGeometry(int(start_offset), 5, int(width), 25)
        
        # 强制更新任务条显示
        self.task_bar.update()
        
        # 查找GanttChart并更新任务
        parent = self.parent()
        while parent and not isinstance(parent, GanttChart):
            parent = parent.parent()
            
        if parent and isinstance(parent, GanttChart):
            # 更新任务数据 - 这里将间接触发日历视图更新
            parent.update_task(updated_task)

    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于垂直拖拽任务行"""
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier:
            # 按住Shift键进行垂直拖拽
            self.vertical_dragging = True
            self.drag_start_y = event.globalPos().y()
            self.setCursor(Qt.SizeVerCursor)
            # 发射拖拽开始信号
            self.dragStarted.emit(self)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，实现垂直拖拽功能"""
        if self.vertical_dragging:
            # 创建拖拽事件
            drag = QDrag(self)
            mime_data = QMimeData()
            # 保存任务ID作为拖拽数据
            mime_data.setText(str(self.task_data.get("id")))
            drag.setMimeData(mime_data)
            
            # 创建行的半透明图像作为拖拽时的视觉反馈
            pixmap = self.grab()
            pixmap.setDevicePixelRatio(2.0)  # 提高清晰度
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 170))  # 设置半透明
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, 5))
            
            # 执行拖拽操作
            result = drag.exec_(Qt.MoveAction)
            self.vertical_dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasText():
            # 接受拖拽进入
            event.acceptProposedAction()
            # 高亮显示为放置目标
            self.highlight_as_drop_target = True
            self.update()
            # 发射拖拽进入信号
            self.dragEntered.emit(self)
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """处理拖拽离开事件"""
        # 取消高亮显示
        self.highlight_as_drop_target = False
        self.update()
        event.accept()
    
    def dropEvent(self, event):
        """处理放置事件"""
        if event.mimeData().hasText():
            # 获取拖拽的任务ID
            source_task_id = event.mimeData().text()
            
            # 目标位置是当前行的索引
            target_position = self.task_data.get("row_index")
            
            # 查找GanttChart并更新任务顺序
            parent = self.parent()
            while parent and not isinstance(parent, GanttChart):
                parent = parent.parent()
                
            if parent and isinstance(parent, GanttChart):
                parent.reorder_tasks(source_task_id, target_position)
            
            # 取消高亮显示
            self.highlight_as_drop_target = False
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def paintEvent(self, event):
        """绘制任务行背景和网格线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        if self.highlight_as_drop_target:
            # 拖拽目标高亮
            painter.fillRect(0, 0, self.width(), self.height(), QColor(230, 242, 255))
        elif self.task_data.get("is_critical_path", False) and self.parent().parent().show_critical_path:
            # 关键路径高亮
            painter.fillRect(0, 0, self.width(), self.height(), QColor(255, 240, 240))
        elif self.task_data.get("row_index", 0) % 2 == 0:
            # 偶数行背景色
            painter.fillRect(0, 0, self.width(), self.height(), QColor(245, 245, 245))
        else:
            # 奇数行背景色
            painter.fillRect(0, 0, self.width(), self.height(), QColor(255, 255, 255))
        
        # 绘制网格线
        painter.setPen(QPen(QColor(220, 220, 220)))
        current_date = self.start_date
        x = 0
        
        while current_date <= self.end_date:
            # 绘制竖线
            painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.SolidLine))
            painter.drawLine(int(x), 0, int(x), self.height())
            
            # 周末特殊处理
            if current_date.weekday() >= 5:  # 5=周六, 6=周日
                painter.setPen(QPen(QColor(240, 240, 240)))
                painter.fillRect(int(x), 0, int(self.day_width), self.height(), QColor(248, 248, 248))
                painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DotLine))
                painter.drawLine(int(x), 0, int(x), self.height())
            
            # 移动到下一天
            current_date += timedelta(days=1)
            x += self.day_width
            
        # 绘制底部边框线
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

class GanttChart(ScrollArea):
    """甘特图主组件"""
    
    def __init__(self, start_date, end_date, tasks, scheduler_manager, parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.end_date = end_date
        self.tasks = tasks
        self.scheduler_manager = scheduler_manager
        self.day_width = 30
        self.task_rows = {}  # 存储任务行组件的引用
        self.header = None  # 初始化header属性
        
        # 设置滚动区属性
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # 创建主窗口
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建头部容器，固定在顶部不随滚动而移动
        self.header_container = QWidget()
        self.header_container.setFixedHeight(50)
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)
        
        # 添加空白区域与任务列表对齐
        self.header_spacer = QWidget()
        self.header_spacer.setFixedWidth(200)  # 与任务列表宽度一致
        self.header_layout.addWidget(self.header_spacer)
        
        # 添加头部日期栏
        self.header = GanttHeaderWidget(start_date, end_date, self.day_width)
        self.header_layout.addWidget(self.header)
        
        # 将头部容器添加到主布局
        self.main_layout.addWidget(self.header_container)
        
        # 使用分割器管理任务列表和甘特图区域
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 添加任务信息列表
        self.create_task_list()
        
        # 添加甘特图区域
        self.gantt_area = QWidget()
        self.gantt_layout = QVBoxLayout(self.gantt_area)
        self.gantt_layout.setSpacing(0)
        self.gantt_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加任务行
        for i, task in enumerate(tasks):
            task["row_index"] = i
            task_row = GanttTaskRow(task, start_date, end_date, self.day_width)
            self.gantt_layout.addWidget(task_row)
            self.task_rows[task.get("id")] = task_row
        
        # 添加弹性空间
        self.gantt_layout.addStretch(1)
        
        # 添加甘特图区域到分割器
        self.splitter.addWidget(self.gantt_area)
        
        # 设置分割器初始大小
        self.splitter.setSizes([200, 800])
        
        # 添加今日标记线
        self.today_marker = True
        
        # 显示关键路径
        self.show_critical_path = False
        
        # 设置事件处理器连接
        if self.header:
            self.header.installEventFilter(self)
            
        # 连接水平滚动条变化信号，同步标尺位置
        self.horizontalScrollBar().valueChanged.connect(self.sync_header_scroll)
        
        # 连接分割器大小变化信号，更新头部标尺的偏移
        self.splitter.splitterMoved.connect(self.update_header_offset)
        
        # 滚动到今天的位置
        QTimer.singleShot(100, self.scroll_to_today)
    
    def eventFilter(self, obj, event):
        """处理事件过滤器"""
        # 处理头部组件的大小变化事件
        if obj == self.header and event.type() == QEvent.Resize:
            # 更新day_width并通知任务行
            self.day_width = self.header.day_width
            self.update_task_rows_width()
            
        return super().eventFilter(obj, event)
    
    def update_task_rows_width(self, new_day_width=None):
        """更新所有任务行的宽度
        
        Args:
            new_day_width: 可选，指定新的日宽度，如果未提供则使用当前宽度
        """
        # 如果指定了新的日宽度，则更新
        if new_day_width is not None:
            self.day_width = new_day_width
            
        # 更新标尺的日宽度
        if self.header:
            self.header.updateDayWidth(self.day_width)
        
        # 遍历所有任务行，更新它们的day_width
        for task_id, task_row in self.task_rows.items():
            task_row.day_width = self.day_width
            task_row.update_layout()
            
        # 触发重绘
        self.gantt_area.update()
    
    def create_task_list(self):
        """创建任务信息列表"""
        # 创建任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels(["任务", "开始日期", "状态"])
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 设置表格样式
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 填充任务数据
        self.task_table.setRowCount(len(self.tasks))
        
        for i, task in enumerate(self.tasks):
            # 添加任务标题
            title_item = QTableWidgetItem(task.get("title", ""))
            self.task_table.setItem(i, 0, title_item)
            
            # 添加开始日期
            start_date = task.get("start_time").strftime("%Y-%m-%d")
            date_item = QTableWidgetItem(start_date)
            self.task_table.setItem(i, 1, date_item)
            
            # 添加任务状态
            status = task.get("status", "未开始")
            status_item = QTableWidgetItem(status)
            self.task_table.setItem(i, 2, status_item)
            
            # 设置行颜色
            if task.get("completed", False):
                for j in range(3):
                    self.task_table.item(i, j).setBackground(QColor(220, 255, 220))
                    
            # 设置数据用于识别任务
            title_item.setData(Qt.UserRole, task.get("id"))
        
        # 连接点击事件
        self.task_table.itemClicked.connect(self.on_task_item_clicked)
        
        # 添加到分割器
        self.splitter.addWidget(self.task_table)
    
    def on_task_item_clicked(self, item):
        """处理任务表格点击事件"""
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        # 查找对应的任务
        for task in self.tasks:
            if task.get("id") == task_id:
                self.edit_task(task)
                break
    
    def edit_task(self, task_data):
        """打开任务编辑对话框
        
        Args:
            task_data: 任务数据
        """
        try:
            # 打开任务编辑对话框
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
    
    def update_task(self, updated_task):
        """更新任务数据"""
        # 保存当前的滚动位置，以便更新后恢复
        current_h_scroll = self.horizontalScrollBar().value()
        current_v_scroll = self.verticalScrollBar().value()
        
        print(f"甘特图视图: 正在更新任务 ID = {updated_task.get('id')}")
        print(f"  标题: {updated_task.get('title')}")
        print(f"  开始时间: {updated_task.get('start_time')}")
        print(f"  结束时间: {updated_task.get('end_time')}")
        
        # 调用调度管理器的update_task方法，而不是手动更新日历视图
        # 这样可以利用调度管理器的广播通知机制，确保所有视图都得到更新
        if self.scheduler_manager.update_task(updated_task):
            print("甘特图视图: 任务更新成功，调度管理器已通知相关视图更新")
            
            # 仅在甘特图内部更新内存中的任务数据和视觉显示
            # 而不需要触发完整的日历视图刷新，因为调度管理器已经做了这个工作
            task_id = updated_task.get("id")
            for i, task in enumerate(self.tasks):
                if task.get("id") == task_id:
                    # 更新内存中的任务数据
                    self.tasks[i] = updated_task
                    print("甘特图视图: 内存中的任务数据已更新")
                    
                    # 更新对应的任务行
                    if task_id in self.task_rows:
                        task_row = self.task_rows[task_id]
                        # 更新任务行的数据引用
                        task_row.task_data = updated_task
                        # 重新计算任务条位置和大小
                        task_row.update_layout()
                        print("甘特图视图: 任务行视觉显示已更新")
                    break
            
            # 恢复滚动位置
            QTimer.singleShot(10, lambda: self.setScrollPosition(current_h_scroll, current_v_scroll))
            
            # 显示成功消息
            try:
                InfoBar.success(
                    title="已更新",
                    content=f"任务日期已更新",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
        else:
            print("甘特图视图: 任务更新失败")
            # 显示错误消息
            try:
                InfoBar.error(
                    title="更新失败",
                    content="无法更新任务日期，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
    
    def setScrollPosition(self, h_scroll, v_scroll):
        """设置滚动条位置"""
        self.horizontalScrollBar().setValue(h_scroll)
        self.verticalScrollBar().setValue(v_scroll)
    
    def scroll_to_today(self):
        """滚动到今天的位置"""
        if not self.today_marker:
            return
            
        today = datetime.now().date()
        
        # 确保今天在日期范围内
        if today < self.start_date or today > self.end_date:
            return
            
        # 计算今天的X坐标
        days_from_start = (today - self.start_date).days
        x_pos = days_from_start * self.day_width
        
        # 居中显示
        viewport_width = self.viewport().width()
        scroll_pos = max(0, x_pos - viewport_width // 2)
        
        # 设置水平滚动条位置
        self.horizontalScrollBar().setValue(int(scroll_pos))
    
    def sync_header_scroll(self, value=None):
        """同步头部标尺滚动位置
        
        Args:
            value: 滚动条的值，如果未提供则使用当前值
        """
        # 强制更新头部标尺
        if self.header:
            # 更新标尺后要触发重绘
            self.header.update()
    
    def update_header_offset(self, pos=None, index=None):
        """更新头部标尺偏移量
        
        Args:
            pos: 分割器位置
            index: 分割器索引
        """
        # 获取任务列表的宽度
        task_list_width = self.splitter.sizes()[0]
        
        # 更新头部空白区域的宽度，使其与任务列表宽度匹配
        if self.header_spacer:
            self.header_spacer.setFixedWidth(task_list_width)
        
        # 更新头部标尺
        self.sync_header_scroll()
    
    def paintEvent(self, event):
        """绘制甘特图背景和辅助线"""
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 如果启用了今日标记线
        if self.today_marker:
            today = datetime.now().date()
            if self.start_date <= today <= self.end_date:
                days_from_start = (today - self.start_date).days
                x = days_from_start * self.day_width
                
                # 将甘特图坐标转换为视口坐标
                x_viewport = int(x - self.horizontalScrollBar().value())
                
                # 绘制今日线
                if 0 <= x_viewport <= self.viewport().width():
                    painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.DashLine))
                    painter.drawLine(int(x_viewport), 0, int(x_viewport), self.viewport().height())
                    
        # 调用父类绘制方法
        super().paintEvent(event)

    def reorder_tasks(self, source_task_id, target_position):
        """重新排序任务"""
        # 保存当前的滚动位置，以便更新后恢复
        current_h_scroll = self.horizontalScrollBar().value()
        current_v_scroll = self.verticalScrollBar().value()
        
        # 转换为字符串类型确保比较正确
        source_task_id = str(source_task_id)
        
        # 找到源任务
        source_task = None
        source_position = -1
        for i, task in enumerate(self.tasks):
            if str(task.get("id")) == source_task_id:
                source_task = task
                source_position = i
                break
        
        if source_task is None or source_position == target_position:
            return  # 没有找到源任务或位置相同，不需要移动
        
        # 从任务列表中移除源任务
        self.tasks.pop(source_position)
        
        # 插入源任务到目标位置
        # 如果源位置在目标位置之前，则目标位置需要减一，因为源任务已经被移除
        if source_position < target_position:
            target_position -= 1
        
        # 插入到目标位置
        if target_position >= len(self.tasks):
            self.tasks.append(source_task)
        else:
            self.tasks.insert(target_position, source_task)
        
        # 更新所有任务的行索引
        for i, task in enumerate(self.tasks):
            task["row_index"] = i
        
        # 更新任务数据
        updated_tasks = [task for task in self.tasks]
        if self.scheduler_manager.reorder_tasks(updated_tasks):
            # 恢复滚动位置
            QTimer.singleShot(10, lambda: self.setScrollPosition(current_h_scroll, current_v_scroll))
            
            # 显示成功消息
            try:
                InfoBar.success(
                    title="已重排",
                    content=f"任务次序已更新",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")
                
            # 通知甘特图视图刷新 - 这里需要完全刷新因为顺序改变了
            self.window().findChild(GanttView).refresh()
        else:
            # 显示错误消息
            try:
                InfoBar.error(
                    title="重排失败",
                    content="无法更新任务顺序，请稍后重试",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                print(f"显示InfoBar时出错: {e}")

class GanttView(ScrollArea):
    """甘特图视图"""
    
    def __init__(self, scheduler_manager, parent=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.is_updating = False  # 添加标志以防止递归
        
        # 默认显示一个月
        today = datetime.now().date()
        self.start_date = today - timedelta(days=today.day - 1)  # 当月第一天
        self.end_date = today + timedelta(days=30)
        
        # 任务过滤设置
        self.filter_completed = False
        self.filter_priority = None
        self.filter_keyword = ""
        
        # 视图设置 - 固定使用时间线视图
        self.view_mode = "时间线"
        
        # 跟踪是否已自动适应过缩放比例
        self.auto_fitted = False
        
        # 初始化界面
        self.init_ui()
        
        # 加载任务
        self.load_tasks()
        
        # 设置窗口大小变化事件处理
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理窗口大小变化事件"""
        if obj == self and event.type() == QEvent.Resize:
            # 只有当窗口首次显示或大小变化超过阈值时才自动适应
            if not self.auto_fitted and self.isVisible() and self.width() > 100:
                # 延迟执行，避免过于频繁的更新
                QTimer.singleShot(300, self.auto_fit_if_needed)
                self.auto_fitted = True
        
        return super().eventFilter(obj, event)
    
    def auto_fit_if_needed(self):
        """根据需要自动适应甘特图比例"""
        if self.is_updating:
            return
            
        # 找到甘特图实例
        gantt_chart = None
        for i in range(self.gantt_container.count()):
            item = self.gantt_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GanttChart):
                gantt_chart = item.widget()
                break
                
        if gantt_chart:
            # 检查当前比例是否合适
            available_width = gantt_chart.splitter.sizes()[1] - 20
            days_total = (self.end_date - self.start_date).days + 1
            
            if available_width > 0 and days_total > 0:
                current_day_width = gantt_chart.day_width
                optimal_day_width = max(20, min(100, available_width / days_total))
                
                # 如果当前宽度与最优宽度相差太大，则调整
                if abs(current_day_width - optimal_day_width) > 5:
                    gantt_chart.update_task_rows_width(optimal_day_width)
                    gantt_chart.sync_header_scroll()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setObjectName("ganttView")
        self.setWidgetResizable(True)
        
        # 创建主窗口
        self.main_widget = QWidget(self)
        self.setWidget(self.main_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        # 添加顶部工具栏
        self.create_toolbar()
        
        # 添加筛选栏
        self.create_filter_bar()
        
        # 添加甘特图容器
        self.gantt_container = QVBoxLayout()
        self.gantt_container.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.gantt_container, 1)
    
    def create_toolbar(self):
        """创建顶部工具栏"""
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("ganttToolbar")
        toolbar_widget.setStyleSheet("""
            #ganttToolbar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        self.toolbar_layout = QHBoxLayout(toolbar_widget)
        self.toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 添加日期选择器
        self.start_date_label = QLabel("开始日期:", self)
        self.toolbar_layout.addWidget(self.start_date_label)
        
        self.start_date_picker = CalendarPicker(self)
        self.start_date_picker.setDate(QDate(self.start_date.year, self.start_date.month, self.start_date.day))
        self.start_date_picker.dateChanged.connect(self.on_date_changed)
        self.toolbar_layout.addWidget(self.start_date_picker)
        
        self.end_date_label = QLabel("结束日期:", self)
        self.toolbar_layout.addWidget(self.end_date_label)
        
        self.end_date_picker = CalendarPicker(self)
        self.end_date_picker.setDate(QDate(self.end_date.year, self.end_date.month, self.end_date.day))
        self.end_date_picker.dateChanged.connect(self.on_date_changed)
        self.toolbar_layout.addWidget(self.end_date_picker)
        
        # 添加日期范围快捷按钮
        self.toolbar_layout.addWidget(QLabel("快速选择:"))
        
        self.month_btn = PushButton("月", self)
        self.month_btn.clicked.connect(self.show_month)
        self.toolbar_layout.addWidget(self.month_btn)
        
        self.quarter_btn = PushButton("季度", self)
        self.quarter_btn.clicked.connect(self.show_quarter)
        self.toolbar_layout.addWidget(self.quarter_btn)
        
        self.half_year_btn = PushButton("半年", self)
        self.half_year_btn.clicked.connect(self.show_half_year)
        self.toolbar_layout.addWidget(self.half_year_btn)
        
        # 空间
        self.toolbar_layout.addStretch(1)
        
        # 移除视图选择下拉框，只保留时间线视图
        # self.toolbar_layout.addWidget(QLabel("视图:"))
        
        # self.view_combo = ComboBox(self)
        # self.view_combo.addItems(["时间线", "资源视图", "里程碑视图"])
        # self.view_combo.setCurrentText(self.view_mode)
        # self.view_combo.currentTextChanged.connect(self.on_view_mode_changed)
        # self.toolbar_layout.addWidget(self.view_combo)
        
        # 固定使用时间线视图
        self.view_mode = "时间线"
        
        # 添加缩放按钮
        self.zoom_in_btn = ToolButton()
        self.zoom_in_btn.setIcon(FluentIcon.ADD)
        self.zoom_in_btn.setToolTip("放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.toolbar_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = ToolButton()
        self.zoom_out_btn.setIcon(FluentIcon.REMOVE)
        self.zoom_out_btn.setToolTip("缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.toolbar_layout.addWidget(self.zoom_out_btn)
        
        # 添加适应宽度按钮
        self.fit_width_btn = ToolButton()
        self.fit_width_btn.setIcon(FluentIcon.ZOOM_IN)  # 使用已知存在的图标
        self.fit_width_btn.setToolTip("适应范围宽度")
        self.fit_width_btn.clicked.connect(self.fit_to_width)
        self.toolbar_layout.addWidget(self.fit_width_btn)
        
        # 添加适应任务按钮
        self.fit_tasks_btn = ToolButton()
        self.fit_tasks_btn.setIcon(FluentIcon.SEARCH)  # 使用SEARCH替代不存在的图标
        self.fit_tasks_btn.setToolTip("适应任务")
        self.fit_tasks_btn.clicked.connect(self.fit_to_tasks)
        self.toolbar_layout.addWidget(self.fit_tasks_btn)
        
        # 添加今日按钮
        self.today_btn = ToolButton()
        self.today_btn.setIcon(FluentIcon.CALENDAR)
        self.today_btn.setToolTip("跳转到今天")
        self.today_btn.clicked.connect(lambda: self.scroll_to_date(datetime.now().date()))
        self.toolbar_layout.addWidget(self.today_btn)
        
        self.main_layout.addWidget(toolbar_widget)
    
    def create_filter_bar(self):
        """创建筛选栏"""
        filter_widget = QWidget()
        filter_widget.setObjectName("ganttFilterBar")
        filter_widget.setStyleSheet("""
            #ganttFilterBar {
                background-color: #f9f9f9;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(10, 5, 10, 5)
        
        # 添加关键字搜索
        filter_layout.addWidget(QLabel("搜索:"))
        
        self.search_input = LineEdit(self)
        self.search_input.setPlaceholderText("输入任务关键字")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.search_input)
        
        # 隐藏已完成任务选项
        self.hide_completed_cb = CheckBox("隐藏已完成", self)
        self.hide_completed_cb.stateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.hide_completed_cb)
        
        # 优先级过滤
        filter_layout.addWidget(QLabel("优先级:"))
        
        self.priority_combo = ComboBox(self)
        self.priority_combo.addItems(["全部", "低", "中", "高", "紧急"])
        self.priority_combo.setCurrentText("全部")
        self.priority_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.priority_combo)
        
        # 空间
        filter_layout.addStretch(1)
        
        # 添加刷新按钮
        self.refresh_btn = PushButton("刷新", self)
        self.refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(self.refresh_btn)
        
        self.main_layout.addWidget(filter_widget)
        
    def load_tasks(self):
        """加载任务并创建甘特图"""
        if self.is_updating:  # 如果已经在更新中，则直接返回
            return
            
        self.is_updating = True  # 设置更新标志
        
        try:
            # 清除旧的甘特图
            while self.gantt_container.count() > 0:
                item = self.gantt_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 获取日期范围内的任务
            self.start_date = self.start_date_picker.getDate().toPyDate()
            self.end_date = self.end_date_picker.getDate().toPyDate()
            
            tasks = self.scheduler_manager.get_tasks_by_date_range(self.start_date, self.end_date)
            
            # 应用过滤器
            filtered_tasks = self.apply_filters(tasks)
            
            # 创建甘特图（只使用时间线视图）
            if filtered_tasks:
                # 创建时间线甘特图
                gantt_chart = GanttChart(self.start_date, self.end_date, filtered_tasks, self.scheduler_manager)
                self.gantt_container.addWidget(gantt_chart)
            else:
                # 如果没有任务，显示提示
                empty_label = QLabel("没有任务在所选日期范围内", self)
                empty_label.setAlignment(Qt.AlignCenter)
                self.gantt_container.addWidget(empty_label)
        finally:
            self.is_updating = False  # 清除更新标志
    
    def apply_filters(self, tasks):
        """应用任务过滤条件"""
        filtered_tasks = []
        
        for task in tasks:
            # 过滤已完成任务
            if self.hide_completed_cb.isChecked() and task.get("completed", False):
                continue
                
            # 按优先级过滤
            priority_filter = self.priority_combo.currentText()
            if priority_filter != "全部" and task.get("priority") != priority_filter:
                continue
                
            # 关键字过滤
            keyword = self.search_input.text().strip().lower()
            if keyword:
                title = task.get("title", "").lower()
                description = task.get("description", "").lower()
                if keyword not in title and keyword not in description:
                    continue
                    
            # 通过所有过滤条件，添加到结果
            filtered_tasks.append(task)
            
        return filtered_tasks
    
    def on_date_changed(self, date):
        """日期变化事件处理"""
        if self.is_updating:  # 如果已经在更新中，则直接返回
            return
            
        # 确保结束日期不早于开始日期
        start_date = self.start_date_picker.getDate().toPyDate()
        end_date = self.end_date_picker.getDate().toPyDate()
        
        if end_date < start_date:
            self.end_date_picker.blockSignals(True)
            self.end_date_picker.setDate(self.start_date_picker.getDate())
            self.end_date_picker.blockSignals(False)
            
        # 重新加载任务
        self.load_tasks()
    
    def on_filter_changed(self):
        """过滤条件变化事件处理"""
        if self.is_updating:
            return
            
        # 重新加载任务
        self.load_tasks()
    
    def zoom_in(self):
        """放大甘特图（增加日宽）"""
        if self.is_updating:
            return
            
        # 找到甘特图实例
        gantt_chart = None
        for i in range(self.gantt_container.count()):
            item = self.gantt_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GanttChart):
                gantt_chart = item.widget()
                break
            
        if gantt_chart and gantt_chart.day_width < 100:
            # 增加日宽度并直接更新
            new_width = gantt_chart.day_width + 5
            gantt_chart.update_task_rows_width(new_width)
            
            # 触发滚动同步
            gantt_chart.sync_header_scroll()
    
    def zoom_out(self):
        """缩小甘特图（减少日宽）"""
        if self.is_updating:
            return
            
        # 找到甘特图实例
        gantt_chart = None
        for i in range(self.gantt_container.count()):
            item = self.gantt_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GanttChart):
                gantt_chart = item.widget()
                break
            
        if gantt_chart and gantt_chart.day_width > 15:
            # 减少日宽度并直接更新
            new_width = gantt_chart.day_width - 5
            gantt_chart.update_task_rows_width(new_width)
            
            # 触发滚动同步
            gantt_chart.sync_header_scroll()
    
    def show_month(self):
        """显示一个月的时间范围"""
        if self.is_updating:
            return
            
        today = datetime.now().date()
        first_day = today.replace(day=1)
        next_month = first_day.replace(month=first_day.month+1) if first_day.month < 12 else first_day.replace(year=first_day.year+1, month=1)
        last_day = (next_month - timedelta(days=1))
        
        # 更新日期选择器
        self.start_date_picker.blockSignals(True)
        self.start_date_picker.setDate(QDate(first_day.year, first_day.month, first_day.day))
        self.start_date_picker.blockSignals(False)
        
        self.end_date_picker.blockSignals(True)
        self.end_date_picker.setDate(QDate(last_day.year, last_day.month, last_day.day))
        self.end_date_picker.blockSignals(False)
        
        # 更新日期属性
        self.start_date = first_day
        self.end_date = last_day
        
        # 重新加载任务
        self.load_tasks()
    
    def show_quarter(self):
        """显示一个季度的时间范围"""
        if self.is_updating:
            return
            
        today = datetime.now().date()
        month = today.month
        
        # 确定季度的第一个月
        if month <= 3:
            quarter_start_month = 1
        elif month <= 6:
            quarter_start_month = 4
        elif month <= 9:
            quarter_start_month = 7
        else:
            quarter_start_month = 10
            
        # 计算季度的开始和结束日期
        first_day = today.replace(month=quarter_start_month, day=1)
        if quarter_start_month + 3 > 12:
            last_month = quarter_start_month + 3 - 12
            next_quarter = first_day.replace(year=first_day.year+1, month=last_month)
        else:
            next_quarter = first_day.replace(month=quarter_start_month+3)
            
        last_day = (next_quarter - timedelta(days=1))
        
        # 更新日期选择器
        self.start_date_picker.blockSignals(True)
        self.start_date_picker.setDate(QDate(first_day.year, first_day.month, first_day.day))
        self.start_date_picker.blockSignals(False)
        
        self.end_date_picker.blockSignals(True)
        self.end_date_picker.setDate(QDate(last_day.year, last_day.month, last_day.day))
        self.end_date_picker.blockSignals(False)
        
        # 更新日期属性
        self.start_date = first_day
        self.end_date = last_day
        
        # 重新加载任务
        self.load_tasks()
    
    def show_half_year(self):
        """显示半年的时间范围"""
        if self.is_updating:
            return
            
        today = datetime.now().date()
        month = today.month
        
        # 确定半年的第一个月
        if month <= 6:
            half_year_start_month = 1
        else:
            half_year_start_month = 7
            
        # 计算半年的开始和结束日期
        first_day = today.replace(month=half_year_start_month, day=1)
        if half_year_start_month + 6 > 12:
            last_month = half_year_start_month + 6 - 12
            next_half = first_day.replace(year=first_day.year+1, month=last_month)
        else:
            next_half = first_day.replace(month=half_year_start_month+6)
            
        last_day = (next_half - timedelta(days=1))
        
        # 更新日期选择器
        self.start_date_picker.blockSignals(True)
        self.start_date_picker.setDate(QDate(first_day.year, first_day.month, first_day.day))
        self.start_date_picker.blockSignals(False)
        
        self.end_date_picker.blockSignals(True)
        self.end_date_picker.setDate(QDate(last_day.year, last_day.month, last_day.day))
        self.end_date_picker.blockSignals(False)
        
        # 更新日期属性
        self.start_date = first_day
        self.end_date = last_day
        
        # 重新加载任务
        self.load_tasks()
    
    def scroll_to_date(self, target_date):
        """滚动到特定日期"""
        # 确保目标日期在日期范围内
        if target_date < self.start_date or target_date > self.end_date:
            # 如果目标日期不在当前范围内，调整范围
            days_diff = (target_date - self.start_date).days
            if days_diff < 0:
                # 目标日期在范围前面
                range_days = (self.end_date - self.start_date).days
                new_start = target_date - timedelta(days=7)  # 向前留出一周
                new_end = new_start + timedelta(days=range_days)
            else:
                # 目标日期在范围后面
                range_days = (self.end_date - self.start_date).days
                new_end = target_date + timedelta(days=7)  # 向后留出一周
                new_start = new_end - timedelta(days=range_days)
                
            # 更新日期选择器
            self.start_date_picker.blockSignals(True)
            self.start_date_picker.setDate(QDate(new_start.year, new_start.month, new_start.day))
            self.start_date_picker.blockSignals(False)
            
            self.end_date_picker.blockSignals(True)
            self.end_date_picker.setDate(QDate(new_end.year, new_end.month, new_end.day))
            self.end_date_picker.blockSignals(False)
            
            # 更新日期属性
            self.start_date = new_start
            self.end_date = new_end
            
            # 重新加载任务
            self.load_tasks()
            
            # 延迟滚动，等待甘特图创建完成
            QTimer.singleShot(100, lambda: self.do_scroll_to_date(target_date))
        else:
            # 如果目标日期在当前范围内，直接滚动
            self.do_scroll_to_date(target_date)
    
    def do_scroll_to_date(self, target_date):
        """执行滚动到特定日期"""
        # 找到甘特图实例
        gantt_chart = None
        for i in range(self.gantt_container.count()):
            item = self.gantt_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GanttChart):
                gantt_chart = item.widget()
                break
                
        if gantt_chart:
            # 计算目标日期的X坐标
            days_from_start = (target_date - gantt_chart.start_date).days
            x_pos = days_from_start * gantt_chart.day_width
            
            # 居中显示
            viewport_width = gantt_chart.viewport().width()
            scroll_pos = max(0, x_pos - viewport_width // 2)
            
            # 设置水平滚动条位置
            gantt_chart.horizontalScrollBar().setValue(int(scroll_pos))
    
    def refresh(self):
        """刷新甘特图视图"""
        if not self.is_updating:
            self.load_tasks() 
    
    def fit_to_width(self):
        """让甘特图适应当前视图宽度"""
        if self.is_updating:
            return
            
        # 找到甘特图实例
        gantt_chart = None
        for i in range(self.gantt_container.count()):
            item = self.gantt_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GanttChart):
                gantt_chart = item.widget()
                break
                
        if not gantt_chart:
            return
            
        # 获取甘特图任务区域的可见宽度
        available_width = gantt_chart.splitter.sizes()[1] - 20  # 减去一些边距
        
        # 计算日期范围总天数
        days_total = (self.end_date - self.start_date).days + 1
        
        # 计算合适的日宽度，确保不超过最大和最小限制
        min_day_width = 20  # 最小日期宽度
        max_day_width = 100  # 最大日期宽度
        optimal_day_width = max(min_day_width, min(max_day_width, available_width / days_total))
        
        # 应用新的日宽度
        gantt_chart.update_task_rows_width(optimal_day_width)
        
        # 触发滚动同步
        gantt_chart.sync_header_scroll()
        
        # 显示提示
        try:
            InfoBar.success(
                title="缩放调整",
                content=f"已将甘特图缩放比例调整为 {optimal_day_width:.1f} 像素/天",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            print(f"显示InfoBar时出错: {e}")

    def fit_to_tasks(self):
        """自动调整日期范围和缩放比例以适应所有任务"""
        if self.is_updating:
            return

        # 获取所有任务
        all_tasks = self.scheduler_manager.get_all_tasks()
        if not all_tasks:
            InfoBar.warning(
                title="没有任务",
                content="没有找到任务，无法适应显示",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 找出最早和最晚的任务日期
        min_date = None
        max_date = None
        
        for task in all_tasks:
            task_start = task.get("start_time").date()
            task_end = task.get("end_time").date()
            
            if min_date is None or task_start < min_date:
                min_date = task_start
            
            if max_date is None or task_end > max_date:
                max_date = task_end
        
        # 如果没有有效日期，返回
        if min_date is None or max_date is None:
            return
            
        # 添加一定的边距（前后各增加3天）
        min_date = min_date - timedelta(days=3)
        max_date = max_date + timedelta(days=3)
        
        # 更新日期选择器并保存新的日期范围
        self.start_date_picker.blockSignals(True)
        self.start_date_picker.setDate(QDate(min_date.year, min_date.month, min_date.day))
        self.start_date_picker.blockSignals(False)
        
        self.end_date_picker.blockSignals(True)
        self.end_date_picker.setDate(QDate(max_date.year, max_date.month, max_date.day))
        self.end_date_picker.blockSignals(False)
        
        # 更新日期属性
        self.start_date = min_date
        self.end_date = max_date
        
        # 重新加载任务
        self.load_tasks()
        
        # 适应宽度
        QTimer.singleShot(100, self.fit_to_width)
        
        # 显示提示
        try:
            days_range = (max_date - min_date).days + 1
            InfoBar.success(
                title="适应任务",
                content=f"已调整显示范围至 {min_date.strftime('%Y-%m-%d')} 到 {max_date.strftime('%Y-%m-%d')}，共 {days_range} 天",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            print(f"显示InfoBar时出错: {e}")