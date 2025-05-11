#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
排期助手主视图
提供插件的主要功能界面
"""

from PyQt5.QtCore import Qt, QDate, QDateTime, QTime, QSize, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QDateTimeEdit, QSpinBox, QComboBox, 
    QScrollArea, QGroupBox, QTabWidget, QGridLayout,
    QListWidget, QListWidgetItem, QMessageBox, QCheckBox,
    QTimeEdit, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFrame, QProgressBar
)
from PyQt5.QtGui import QIcon, QColor, QFont, QBrush
from datetime import datetime, timedelta
import uuid

class BatchTaskCreationTab(QWidget):
    """批量任务创建标签页"""
    
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        self.tasks_list = []
        # 设置对象名称
        self.setObjectName("batchTaskCreationTab")
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 创建顶部表单
        form_group = QGroupBox("创建批量任务")
        form_layout = QFormLayout()
        
        # 任务标题模板
        self.title_template = QLineEdit()
        self.title_template.setPlaceholderText("任务标题模板 (例如: 'Task #{index}')")
        form_layout.addRow("标题模板:", self.title_template)
        
        # 任务数量
        self.task_count = QSpinBox()
        self.task_count.setMinimum(1)
        self.task_count.setMaximum(100)
        self.task_count.setValue(5)
        form_layout.addRow("任务数量:", self.task_count)
        
        # 开始日期时间
        self.start_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_datetime.setCalendarPopup(True)
        form_layout.addRow("开始时间:", self.start_datetime)
        
        # 选择时间间隔类型
        self.interval_type = QComboBox()
        self.interval_type.addItems(["分钟", "小时", "天", "周"])
        self.interval_type.setCurrentIndex(2)  # 默认为天
        form_layout.addRow("间隔类型:", self.interval_type)
        
        # 时间间隔
        self.interval_value = QSpinBox()
        self.interval_value.setMinimum(1)
        self.interval_value.setMaximum(9999)
        self.interval_value.setValue(1)
        form_layout.addRow("间隔值:", self.interval_value)
        
        # 任务持续时间（小时）
        self.duration_hours = QSpinBox()
        self.duration_hours.setMinimum(0)
        self.duration_hours.setMaximum(24)
        self.duration_hours.setValue(1)
        
        # 任务持续时间（分钟）
        self.duration_minutes = QSpinBox()
        self.duration_minutes.setMinimum(0)
        self.duration_minutes.setMaximum(59)
        self.duration_minutes.setValue(0)
        self.duration_minutes.setSingleStep(15)
        
        # 水平布局用于小时和分钟选择器
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(self.duration_hours)
        duration_layout.addWidget(QLabel("小时"))
        duration_layout.addWidget(self.duration_minutes)
        duration_layout.addWidget(QLabel("分钟"))
        
        form_layout.addRow("任务时长:", duration_layout)
        
        # 任务优先级
        self.priority = QComboBox()
        self.priority.addItems(["低", "中", "高"])
        self.priority.setCurrentIndex(1)  # 默认为中
        form_layout.addRow("优先级:", self.priority)
        
        # 描述模板
        self.description_template = QLineEdit()
        self.description_template.setPlaceholderText("描述模板 (例如: '批量创建的任务 #{index}')")
        form_layout.addRow("描述模板:", self.description_template)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 预览按钮
        preview_btn = QPushButton("预览任务")
        preview_btn.clicked.connect(self.preview_tasks)
        layout.addWidget(preview_btn)
        
        # 任务预览列表
        preview_group = QGroupBox("任务预览")
        preview_layout = QVBoxLayout()
        self.preview_list = QListWidget()
        preview_layout.addWidget(self.preview_list)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 创建任务按钮
        create_btn = QPushButton("创建任务")
        create_btn.clicked.connect(self.create_tasks)
        layout.addWidget(create_btn)
        
    def preview_tasks(self):
        """预览将要创建的任务"""
        # 清空预览列表和任务列表
        self.preview_list.clear()
        self.tasks_list.clear()
        
        # 获取表单数据
        title_template = self.title_template.text() or "任务 #{index}"
        task_count = self.task_count.value()
        start_datetime = self.start_datetime.dateTime().toPyDateTime()
        interval_type = self.interval_type.currentText()
        interval_value = self.interval_value.value()
        duration_hours = self.duration_hours.value()
        duration_minutes = self.duration_minutes.value()
        priority = self.priority.currentText()
        description_template = self.description_template.text() or "批量创建的任务 #{index}"
        
        # 计算间隔时间
        delta = None
        if interval_type == "分钟":
            delta = timedelta(minutes=interval_value)
        elif interval_type == "小时":
            delta = timedelta(hours=interval_value)
        elif interval_type == "天":
            delta = timedelta(days=interval_value)
        elif interval_type == "周":
            delta = timedelta(weeks=interval_value)
        
        # 计算任务持续时间
        duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        
        # 生成任务列表
        current_datetime = start_datetime
        for i in range(task_count):
            task_index = i + 1
            title = title_template.replace("{index}", str(task_index))
            description = description_template.replace("{index}", str(task_index))
            
            # 任务结束时间
            end_datetime = current_datetime + duration
            
            # 创建任务项
            task = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "start_time": current_datetime,
                "end_time": end_datetime,
                "priority": priority,
                "created_at": datetime.now(),
                "completed": False,
                "remind": False,
            }
            
            # 添加到任务列表
            self.tasks_list.append(task)
            
            # 添加到预览列表
            item_text = f"{title} - {current_datetime.strftime('%Y-%m-%d %H:%M')} 到 {end_datetime.strftime('%Y-%m-%d %H:%M')}"
            self.preview_list.addItem(item_text)
            
            # 更新下一个任务的开始时间
            current_datetime += delta
    
    def create_tasks(self):
        """创建预览中的任务"""
        # 检查是否有预览任务
        if not self.tasks_list:
            QMessageBox.warning(self, "警告", "请先预览任务")
            return
            
        # 获取调度管理器
        scheduler_manager = self.app_context.scheduler_manager
        if not scheduler_manager:
            QMessageBox.critical(self, "错误", "无法获取调度管理器")
            return
        
        # 创建任务
        success_count = 0
        for task in self.tasks_list:
            try:
                # 调用调度管理器添加任务
                if scheduler_manager.add_task(task):
                    success_count += 1
            except Exception as e:
                print(f"创建任务失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 显示结果
        QMessageBox.information(
            self, 
            "任务创建结果", 
            f"成功创建 {success_count} 个任务，失败 {len(self.tasks_list) - success_count} 个"
        )
        
        # 清空预览
        self.preview_list.clear()
        self.tasks_list.clear()


class TimeRecommendationTab(QWidget):
    """时间推荐标签页"""
    
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        # 设置对象名称
        self.setObjectName("timeRecommendationTab")
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 创建任务参数表单
        form_group = QGroupBox("任务参数")
        form_layout = QFormLayout()
        
        # 任务标题
        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("输入任务标题")
        form_layout.addRow("任务标题:", self.task_title)
        
        # 任务持续时间
        self.duration_hours = QSpinBox()
        self.duration_hours.setMinimum(0)
        self.duration_hours.setMaximum(24)
        self.duration_hours.setValue(1)
        
        self.duration_minutes = QSpinBox()
        self.duration_minutes.setMinimum(0)
        self.duration_minutes.setMaximum(59)
        self.duration_minutes.setValue(0)
        self.duration_minutes.setSingleStep(15)
        
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(self.duration_hours)
        duration_layout.addWidget(QLabel("小时"))
        duration_layout.addWidget(self.duration_minutes)
        duration_layout.addWidget(QLabel("分钟"))
        form_layout.addRow("任务时长:", duration_layout)
        
        # 选择日期范围
        self.start_date = QDateTimeEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("开始日期:", self.start_date)
        
        self.end_date = QDateTimeEdit(QDate.currentDate().addDays(7))
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("结束日期:", self.end_date)
        
        # 工作时间选项
        self.work_hours_checkbox = QCheckBox("仅考虑工作时间 (9:00-18:00)")
        self.work_hours_checkbox.setChecked(True)
        form_layout.addRow("", self.work_hours_checkbox)
        
        # 避开已有任务选项
        self.avoid_existing_checkbox = QCheckBox("避开已有任务")
        self.avoid_existing_checkbox.setChecked(True)
        form_layout.addRow("", self.avoid_existing_checkbox)
        
        # 推荐时间数量
        self.recommendation_count = QSpinBox()
        self.recommendation_count.setMinimum(1)
        self.recommendation_count.setMaximum(10)
        self.recommendation_count.setValue(3)
        form_layout.addRow("推荐数量:", self.recommendation_count)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 查找按钮
        find_btn = QPushButton("查找可用时间")
        find_btn.clicked.connect(self.find_available_times)
        layout.addWidget(find_btn)
        
        # 推荐时间列表
        recommend_group = QGroupBox("推荐时间")
        recommend_layout = QVBoxLayout()
        self.recommend_list = QListWidget()
        self.recommend_list.setSelectionMode(QListWidget.SingleSelection)
        recommend_layout.addWidget(self.recommend_list)
        recommend_group.setLayout(recommend_layout)
        layout.addWidget(recommend_group)
        
        # 创建任务按钮
        create_btn = QPushButton("创建任务")
        create_btn.clicked.connect(self.create_task_at_selected_time)
        layout.addWidget(create_btn)
    
    def find_available_times(self):
        """查找可用时间"""
        # 清空推荐列表
        self.recommend_list.clear()
        
        # 获取表单数据
        title = self.task_title.text() or "新任务"
        duration_hours = self.duration_hours.value()
        duration_minutes = self.duration_minutes.value()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # 计算任务持续时间（分钟）
        duration_minutes_total = duration_hours * 60 + duration_minutes
        
        # 获取任务列表
        scheduler_manager = self.app_context.scheduler_manager
        if not scheduler_manager:
            QMessageBox.critical(self, "错误", "无法获取调度管理器")
            return
            
        # 存储所有可用时间段
        available_slots = []
        
        # 遍历日期范围内的每一天
        current_date = start_date
        while current_date <= end_date:
            # 获取当天的任务
            daily_tasks = scheduler_manager.get_tasks_by_date(current_date)
            
            # 如果只考虑工作时间，设置一天的起止时间为工作时间
            if self.work_hours_checkbox.isChecked():
                day_start = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=0))
                day_end = datetime.combine(current_date, datetime.min.time().replace(hour=18, minute=0))
            else:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
            
            # 创建忙碌时间段列表
            busy_times = []
            if self.avoid_existing_checkbox.isChecked():
                for task in daily_tasks:
                    start_time = task.get("start_time")
                    end_time = task.get("end_time")
                    if start_time and end_time:
                        busy_times.append((start_time, end_time))
                        
                # 按开始时间排序
                busy_times.sort(key=lambda x: x[0])
            
            # 寻找可用时间段
            available_time = day_start
            for busy_start, busy_end in busy_times:
                # 如果在忙碌时间前有足够的时间，添加到可用时间段
                if (busy_start - available_time).total_seconds() / 60 >= duration_minutes_total:
                    available_slots.append((available_time, busy_start))
                
                # 更新可用时间为忙碌时间结束
                if busy_end > available_time:
                    available_time = busy_end
            
            # 检查一天中最后可能的时段
            if (day_end - available_time).total_seconds() / 60 >= duration_minutes_total:
                available_slots.append((available_time, day_end))
            
            # 前进到下一天
            current_date += timedelta(days=1)
        
        # 按开始时间排序所有可用时间段
        available_slots.sort(key=lambda x: x[0])
        
        # 限制推荐数量
        recommended_count = min(self.recommendation_count.value(), len(available_slots))
        
        # 添加到推荐列表
        for i in range(recommended_count):
            start_time, end_time = available_slots[i]
            # 计算推荐的结束时间（任务开始时间 + 持续时间）
            recommended_end_time = start_time + timedelta(minutes=duration_minutes_total)
            
            # 确保结束时间不超过可用时段的结束时间
            if recommended_end_time > end_time:
                recommended_end_time = end_time
                
            # 添加到列表
            item_text = f"{start_time.strftime('%Y-%m-%d %H:%M')} - {recommended_end_time.strftime('%Y-%m-%d %H:%M')}"
            item = QListWidgetItem(item_text)
            # 保存时间信息为项目数据
            item.setData(Qt.UserRole, (start_time, recommended_end_time))
            self.recommend_list.addItem(item)
    
    def create_task_at_selected_time(self):
        """在选定的时间创建任务"""
        # 检查是否选择了时间段
        selected_items = self.recommend_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择一个推荐时间")
            return
        
        # 获取选定的时间段
        selected_item = selected_items[0]
        start_time, end_time = selected_item.data(Qt.UserRole)
        
        # 获取任务标题
        title = self.task_title.text() or "新任务"
        
        # 创建任务数据
        task_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": f"通过排期助手创建的任务",
            "start_time": start_time,
            "end_time": end_time,
            "priority": "中",
            "created_at": datetime.now(),
            "completed": False,
            "remind": False,
        }
        
        # 获取调度管理器
        scheduler_manager = self.app_context.scheduler_manager
        if not scheduler_manager:
            QMessageBox.critical(self, "错误", "无法获取调度管理器")
            return
        
        # 创建任务
        try:
            if scheduler_manager.add_task(task_data):
                QMessageBox.information(self, "成功", f"成功创建任务: {title}")
                self.recommend_list.clear()
            else:
                QMessageBox.warning(self, "警告", "创建任务失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()


class RecurringTaskTab(QWidget):
    """重复任务管理标签页"""
    
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        # 设置对象名称
        self.setObjectName("recurringTaskTab")
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 创建上部分表单
        form_group = QGroupBox("创建重复任务")
        form_layout = QFormLayout()
        
        # 任务标题
        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("输入任务标题")
        form_layout.addRow("任务标题:", self.task_title)
        
        # 任务描述
        self.task_description = QLineEdit()
        self.task_description.setPlaceholderText("输入任务描述")
        form_layout.addRow("任务描述:", self.task_description)
        
        # 开始日期时间
        self.start_date = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("开始日期:", self.start_date)
        
        # 任务持续时间
        self.duration_hours = QSpinBox()
        self.duration_hours.setMinimum(0)
        self.duration_hours.setMaximum(24)
        self.duration_hours.setValue(1)
        
        self.duration_minutes = QSpinBox()
        self.duration_minutes.setMinimum(0)
        self.duration_minutes.setMaximum(59)
        self.duration_minutes.setValue(0)
        self.duration_minutes.setSingleStep(15)
        
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(self.duration_hours)
        duration_layout.addWidget(QLabel("小时"))
        duration_layout.addWidget(self.duration_minutes)
        duration_layout.addWidget(QLabel("分钟"))
        form_layout.addRow("任务时长:", duration_layout)
        
        # 重复类型
        self.recurrence_type = QComboBox()
        self.recurrence_type.addItems(["每天", "每周", "每两周", "每月", "每年"])
        form_layout.addRow("重复类型:", self.recurrence_type)
        
        # 重复次数
        self.recurrence_count = QSpinBox()
        self.recurrence_count.setMinimum(1)
        self.recurrence_count.setMaximum(100)
        self.recurrence_count.setValue(10)
        form_layout.addRow("重复次数:", self.recurrence_count)
        
        # 重复截止日期
        self.end_date = QDateTimeEdit(QDateTime.currentDateTime().addMonths(1))
        self.end_date.setCalendarPopup(True)
        self.use_end_date = QCheckBox("使用截止日期")
        
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(self.use_end_date)
        end_date_layout.addWidget(self.end_date)
        form_layout.addRow("截止日期:", end_date_layout)
        
        # 提醒选项
        self.remind_checkbox = QCheckBox("启用提醒")
        form_layout.addRow("", self.remind_checkbox)
        
        # 任务优先级
        self.priority = QComboBox()
        self.priority.addItems(["低", "中", "高"])
        self.priority.setCurrentIndex(1)  # 默认为中
        form_layout.addRow("优先级:", self.priority)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 预览按钮
        preview_btn = QPushButton("预览任务")
        preview_btn.clicked.connect(self.preview_recurring_tasks)
        layout.addWidget(preview_btn)
        
        # 任务预览列表
        preview_group = QGroupBox("任务预览")
        preview_layout = QVBoxLayout()
        self.preview_list = QListWidget()
        preview_layout.addWidget(self.preview_list)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 创建任务按钮
        create_btn = QPushButton("创建重复任务")
        create_btn.clicked.connect(self.create_recurring_tasks)
        layout.addWidget(create_btn)
    
    def preview_recurring_tasks(self):
        """预览重复任务"""
        # 清空预览列表
        self.preview_list.clear()
        
        # 获取表单数据
        title = self.task_title.text() or "重复任务"
        description = self.task_description.text() or "重复任务描述"
        start_datetime = self.start_date.dateTime().toPyDateTime()
        duration_hours = self.duration_hours.value()
        duration_minutes = self.duration_minutes.value()
        
        recurrence_type = self.recurrence_type.currentText()
        recurrence_count = self.recurrence_count.value()
        use_end_date = self.use_end_date.isChecked()
        end_date = self.end_date.dateTime().toPyDateTime() if use_end_date else None
        
        # 计算任务持续时间
        duration = timedelta(hours=duration_hours, minutes=duration_minutes)
        
        # 计算重复间隔
        if recurrence_type == "每天":
            delta = timedelta(days=1)
        elif recurrence_type == "每周":
            delta = timedelta(weeks=1)
        elif recurrence_type == "每两周":
            delta = timedelta(weeks=2)
        elif recurrence_type == "每月":
            # 创建一个简单的月间隔
            delta = timedelta(days=30)
        elif recurrence_type == "每年":
            # 创建一个简单的年间隔
            delta = timedelta(days=365)
        
        # 生成重复任务
        current_datetime = start_datetime
        task_instances = []
        
        for i in range(recurrence_count):
            # 检查是否超过截止日期
            if use_end_date and current_datetime > end_date:
                break
                
            # 任务结束时间
            end_datetime = current_datetime + duration
            
            # 创建任务项
            task = {
                "title": f"{title} ({i+1})",
                "description": description,
                "start_time": current_datetime,
                "end_time": end_datetime
            }
            
            # 添加到任务实例列表
            task_instances.append(task)
            
            # 添加到预览列表
            item_text = f"{title} ({i+1}) - {current_datetime.strftime('%Y-%m-%d %H:%M')} 到 {end_datetime.strftime('%Y-%m-%d %H:%M')}"
            self.preview_list.addItem(item_text)
            
            # 更新下一个任务的开始时间
            current_datetime += delta
        
        # 保存任务实例用于创建
        self.task_instances = task_instances
    
    def create_recurring_tasks(self):
        """创建重复任务"""
        # 检查是否有预览任务
        if not hasattr(self, 'task_instances') or not self.task_instances:
            QMessageBox.warning(self, "警告", "请先预览任务")
            return
            
        # 获取调度管理器
        scheduler_manager = self.app_context.scheduler_manager
        if not scheduler_manager:
            QMessageBox.critical(self, "错误", "无法获取调度管理器")
            return
        
        # 获取共通属性
        priority = self.priority.currentText()
        remind = self.remind_checkbox.isChecked()
        
        # 创建任务
        success_count = 0
        for task_instance in self.task_instances:
            try:
                # 完善任务数据
                task_data = {
                    "id": str(uuid.uuid4()),
                    "title": task_instance["title"],
                    "description": task_instance["description"],
                    "start_time": task_instance["start_time"],
                    "end_time": task_instance["end_time"],
                    "priority": priority,
                    "created_at": datetime.now(),
                    "completed": False,
                    "remind": remind,
                }
                
                # 调用调度管理器添加任务
                if scheduler_manager.add_task(task_data):
                    success_count += 1
            except Exception as e:
                print(f"创建任务失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 显示结果
        QMessageBox.information(
            self, 
            "任务创建结果", 
            f"成功创建 {success_count} 个重复任务，失败 {len(self.task_instances) - success_count} 个"
        )
        
        # 清空预览
        self.preview_list.clear()
        self.task_instances = []


class DashboardTab(QWidget):
    """任务信息概览标签页"""
    
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        # 设置对象名称
        self.setObjectName("dashboardTab")
        
        # 初始化刷新计时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.setInterval(15000)  # 15秒刷新一次
        
        self.init_ui()
        
        # 首次加载数据
        self.refresh_data()
        
        # 启动自动刷新
        self.refresh_timer.start()
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建顶部统计概览
        stats_group = QGroupBox("任务统计")
        stats_layout = QHBoxLayout()
        
        # 待办任务统计
        self.pending_tasks_frame = QFrame()
        self.pending_tasks_frame.setFrameShape(QFrame.StyledPanel)
        pending_layout = QVBoxLayout(self.pending_tasks_frame)
        self.pending_tasks_count = QLabel("0")
        self.pending_tasks_count.setAlignment(Qt.AlignCenter)
        self.pending_tasks_count.setStyleSheet("font-size: 24pt; font-weight: bold; color: #2980b9;")
        pending_layout.addWidget(self.pending_tasks_count)
        pending_layout.addWidget(QLabel("待办任务", alignment=Qt.AlignCenter))
        stats_layout.addWidget(self.pending_tasks_frame)
        
        # 已完成任务统计
        self.completed_tasks_frame = QFrame()
        self.completed_tasks_frame.setFrameShape(QFrame.StyledPanel)
        completed_layout = QVBoxLayout(self.completed_tasks_frame)
        self.completed_tasks_count = QLabel("0")
        self.completed_tasks_count.setAlignment(Qt.AlignCenter)
        self.completed_tasks_count.setStyleSheet("font-size: 24pt; font-weight: bold; color: #27ae60;")
        completed_layout.addWidget(self.completed_tasks_count)
        completed_layout.addWidget(QLabel("已完成任务", alignment=Qt.AlignCenter))
        stats_layout.addWidget(self.completed_tasks_frame)
        
        # 今日任务统计
        self.today_tasks_frame = QFrame()
        self.today_tasks_frame.setFrameShape(QFrame.StyledPanel)
        today_layout = QVBoxLayout(self.today_tasks_frame)
        self.today_tasks_count = QLabel("0")
        self.today_tasks_count.setAlignment(Qt.AlignCenter)
        self.today_tasks_count.setStyleSheet("font-size: 24pt; font-weight: bold; color: #e74c3c;")
        today_layout.addWidget(self.today_tasks_count)
        today_layout.addWidget(QLabel("今日任务", alignment=Qt.AlignCenter))
        stats_layout.addWidget(self.today_tasks_frame)
        
        # 明日任务统计
        self.tomorrow_tasks_frame = QFrame()
        self.tomorrow_tasks_frame.setFrameShape(QFrame.StyledPanel)
        tomorrow_layout = QVBoxLayout(self.tomorrow_tasks_frame)
        self.tomorrow_tasks_count = QLabel("0")
        self.tomorrow_tasks_count.setAlignment(Qt.AlignCenter)
        self.tomorrow_tasks_count.setStyleSheet("font-size: 24pt; font-weight: bold; color: #f39c12;")
        tomorrow_layout.addWidget(self.tomorrow_tasks_count)
        tomorrow_layout.addWidget(QLabel("明日任务", alignment=Qt.AlignCenter))
        stats_layout.addWidget(self.tomorrow_tasks_frame)
        
        # 完成进度
        self.progress_frame = QFrame()
        self.progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_layout = QVBoxLayout(self.progress_frame)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_percent = QLabel("0%")
        self.progress_percent.setAlignment(Qt.AlignCenter)
        self.progress_percent.setStyleSheet("font-size: 24pt; font-weight: bold; color: #8e44ad;")
        progress_layout.addWidget(self.progress_percent)
        progress_layout.addWidget(QLabel("任务完成率", alignment=Qt.AlignCenter))
        progress_layout.addWidget(self.progress_bar)
        stats_layout.addWidget(self.progress_frame)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # 创建搜索和筛选工具栏
        filter_group = QGroupBox("查询和筛选")
        filter_layout = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索任务...")
        self.search_input.textChanged.connect(self.filter_tasks)
        filter_layout.addWidget(QLabel("搜索:"))
        filter_layout.addWidget(self.search_input)
        
        # 优先级筛选
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["全部优先级", "紧急", "高", "中", "低"])
        self.priority_filter.currentIndexChanged.connect(self.filter_tasks)
        filter_layout.addWidget(QLabel("优先级:"))
        filter_layout.addWidget(self.priority_filter)
        
        # 时间筛选
        self.time_filter = QComboBox()
        self.time_filter.addItems(["全部时间", "今天", "明天", "本周", "本月"])
        self.time_filter.currentIndexChanged.connect(self.filter_tasks)
        filter_layout.addWidget(QLabel("时间范围:"))
        filter_layout.addWidget(self.time_filter)
        
        # 状态筛选
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部状态", "待办", "已完成", "已暂停"])
        self.status_filter.currentIndexChanged.connect(self.filter_tasks)
        filter_layout.addWidget(QLabel("状态:"))
        filter_layout.addWidget(self.status_filter)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # 创建任务表格
        task_group = QGroupBox("任务列表")
        task_layout = QVBoxLayout()
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(["标题", "开始时间", "结束时间", "优先级", "状态", "剩余时间"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        task_layout.addWidget(self.task_table)
        task_group.setLayout(task_layout)
        main_layout.addWidget(task_group)
        
        # 添加自动刷新状态指示器
        refresh_status_layout = QHBoxLayout()
        self.auto_refresh_label = QLabel("自动刷新: 已启用 (15秒)")
        self.toggle_refresh_btn = QPushButton("停止自动刷新")
        self.toggle_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        
        refresh_status_layout.addWidget(self.auto_refresh_label)
        refresh_status_layout.addStretch()
        refresh_status_layout.addWidget(self.toggle_refresh_btn)
        
        main_layout.addLayout(refresh_status_layout)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            # 获取调度管理器
            scheduler_manager = self.app_context.scheduler_manager
            if not scheduler_manager:
                return
            
            # 获取所有任务
            all_tasks = scheduler_manager.get_all_tasks()
            if not all_tasks:
                all_tasks = []
            
            # 更新统计数据
            pending_count = 0
            completed_count = 0
            today_count = 0
            tomorrow_count = 0
            
            # 获取今天和明天的日期
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            for task in all_tasks:
                # 计算任务状态统计
                if task.get('completed', False):
                    completed_count += 1
                else:
                    pending_count += 1
                
                # 检查任务是否处于暂停状态
                status = task.get('status', '未开始')
                if status == '已暂停':
                    # 暂停的任务不计入今日和明日任务统计
                    continue
                
                # 计算今天和明天的任务
                start_time = task.get('start_time')
                end_time = task.get('end_time')
                
                if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                    continue
                
                task_start_date = start_time.date()
                task_end_date = end_time.date()
                
                # 检查任务是否在今天或明天
                if task_start_date <= today <= task_end_date:
                    today_count += 1
                if task_start_date <= tomorrow <= task_end_date:
                    tomorrow_count += 1
            
            # 更新统计显示
            self.pending_tasks_count.setText(str(pending_count))
            self.completed_tasks_count.setText(str(completed_count))
            self.today_tasks_count.setText(str(today_count))
            self.tomorrow_tasks_count.setText(str(tomorrow_count))
            
            # 更新完成进度
            total_tasks = pending_count + completed_count
            completion_percent = 0 if total_tasks == 0 else (completed_count / total_tasks) * 100
            self.progress_bar.setValue(int(completion_percent))
            self.progress_percent.setText(f"{int(completion_percent)}%")
            
            # 更新任务列表（应用筛选条件）
            self.filter_tasks()
            
        except Exception as e:
            print(f"刷新数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def filter_tasks(self):
        """根据筛选条件过滤任务"""
        try:
            # 获取调度管理器
            scheduler_manager = self.app_context.scheduler_manager
            if not scheduler_manager:
                return
            
            # 获取所有任务
            all_tasks = scheduler_manager.get_all_tasks()
            if not all_tasks:
                all_tasks = []
            
            # 获取筛选条件
            search_text = self.search_input.text().lower()
            priority_filter = self.priority_filter.currentText()
            time_filter = self.time_filter.currentText()
            status_filter = self.status_filter.currentText()
            
            # 获取今天的日期以及本周、本月的日期范围
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            month_start = today.replace(day=1)
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year + 1 if today.month == 12 else today.year
            month_end = datetime(next_year, next_month, 1).date() - timedelta(days=1)
            
            # 过滤任务
            filtered_tasks = []
            for task in all_tasks:
                # 搜索文本过滤
                title = task.get('title', '').lower()
                description = task.get('description', '').lower()
                
                if search_text and search_text not in title and search_text not in description:
                    continue
                
                # 优先级过滤
                task_priority = task.get('priority', '中')
                if priority_filter != "全部优先级" and task_priority != priority_filter:
                    continue
                
                # 状态过滤
                is_completed = task.get('completed', False)
                status = task.get('status', '未开始')
                
                if status_filter == "待办" and (is_completed or status == "已暂停"):
                    continue
                if status_filter == "已完成" and not is_completed:
                    continue
                if status_filter == "已暂停" and status != "已暂停":
                    continue
                
                # 时间范围过滤
                start_time = task.get('start_time')
                end_time = task.get('end_time')
                
                if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                    continue
                
                task_start_date = start_time.date()
                task_end_date = end_time.date()
                
                if time_filter == "今天" and not (task_start_date <= today <= task_end_date):
                    continue
                elif time_filter == "明天" and not (task_start_date <= tomorrow <= task_end_date):
                    continue
                elif time_filter == "本周" and not (
                    (task_start_date <= week_end and task_end_date >= week_start)
                ):
                    continue
                elif time_filter == "本月" and not (
                    (task_start_date <= month_end and task_end_date >= month_start)
                ):
                    continue
                
                # 如果通过所有过滤条件，添加到过滤后的任务列表中
                filtered_tasks.append(task)
            
            # 清空表格并重新填充
            self.task_table.setRowCount(0)
            
            # 按开始时间排序
            filtered_tasks.sort(key=lambda x: x.get('start_time', datetime.max))
            
            # 填充表格
            for i, task in enumerate(filtered_tasks):
                self.task_table.insertRow(i)
                
                # 标题
                title_item = QTableWidgetItem(task.get('title', ''))
                self.task_table.setItem(i, 0, title_item)
                
                # 开始时间
                start_time = task.get('start_time')
                start_item = QTableWidgetItem(
                    start_time.strftime('%Y-%m-%d %H:%M') if isinstance(start_time, datetime) else '未知'
                )
                self.task_table.setItem(i, 1, start_item)
                
                # 结束时间
                end_time = task.get('end_time')
                end_item = QTableWidgetItem(
                    end_time.strftime('%Y-%m-%d %H:%M') if isinstance(end_time, datetime) else '未知'
                )
                self.task_table.setItem(i, 2, end_item)
                
                # 优先级
                priority = task.get('priority', '中')
                priority_item = QTableWidgetItem(priority)
                
                # 根据优先级设置颜色
                if priority == '紧急':
                    priority_item.setForeground(QBrush(QColor(231, 76, 60)))  # 红色
                elif priority == '高':
                    priority_item.setForeground(QBrush(QColor(243, 156, 18)))  # 橙色
                elif priority == '中':
                    priority_item.setForeground(QBrush(QColor(52, 152, 219)))  # 蓝色
                else:  # 低
                    priority_item.setForeground(QBrush(QColor(46, 204, 113)))  # 绿色
                    
                self.task_table.setItem(i, 3, priority_item)
                
                # 状态
                is_completed = task.get('completed', False)
                status = task.get('status', '未开始')
                
                if is_completed:
                    status_text = '已完成'
                    status_color = QColor(46, 204, 113)  # 绿色
                elif status == '已暂停':
                    status_text = '已暂停'
                    status_color = QColor(150, 150, 150)  # 灰色
                else:
                    status_text = '待办'
                    status_color = QColor(52, 152, 219)  # 蓝色
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QBrush(status_color))
                self.task_table.setItem(i, 4, status_item)
                
                # 剩余时间
                if isinstance(end_time, datetime) and not is_completed:
                    now = datetime.now()
                    if end_time > now:
                        remaining = end_time - now
                        days = remaining.days
                        hours, remainder = divmod(remaining.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        
                        if days > 0:
                            remaining_text = f"{days}天 {hours}小时"
                        else:
                            remaining_text = f"{hours}小时 {minutes}分钟"
                    else:
                        remaining_text = "已过期"
                else:
                    remaining_text = "N/A"
                    
                remaining_item = QTableWidgetItem(remaining_text)
                self.task_table.setItem(i, 5, remaining_item)
                
                # 如果任务已完成或已暂停，使用对应背景色
                if is_completed:
                    bg_color = QColor(240, 240, 240)  # 浅灰色
                elif status == '已暂停':
                    bg_color = QColor(224, 224, 224)  # 灰色
                else:
                    bg_color = None
                
                if bg_color:
                    for col in range(self.task_table.columnCount()):
                        item = self.task_table.item(i, col)
                        if item:
                            item.setBackground(QBrush(bg_color))
            
        except Exception as e:
            print(f"过滤任务出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def toggle_auto_refresh(self):
        """切换自动刷新状态"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.auto_refresh_label.setText("自动刷新: 已禁用")
            self.toggle_refresh_btn.setText("启用自动刷新")
        else:
            self.refresh_timer.start()
            self.auto_refresh_label.setText("自动刷新: 已启用 (15秒)")
            self.toggle_refresh_btn.setText("停止自动刷新")


class ScheduleAssistantView(QWidget):
    """排期助手主视图"""
    
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        # 设置对象名称
        self.setObjectName("scheduleAssistantView")
        
        # 设置 interface 属性，这是 FluentWindow 需要的
        self.interface = self
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setObjectName("mainLayout")
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标题
        title_label = QLabel("排期助手")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setObjectName("scheduleTabs")
        
        # 信息概览标签页
        self.dashboard_tab = DashboardTab(self.app_context)
        self.dashboard_tab.setObjectName("dashboardTab")
        self.tabs.addTab(self.dashboard_tab, "信息概览")
        
        # 批量任务创建标签页
        self.batch_tab = BatchTaskCreationTab(self.app_context)
        self.batch_tab.setObjectName("batchTaskTab")
        self.tabs.addTab(self.batch_tab, "批量任务创建")
        
        # 时间推荐标签页
        self.recommend_tab = TimeRecommendationTab(self.app_context)
        self.recommend_tab.setObjectName("timeRecommendTab")
        self.tabs.addTab(self.recommend_tab, "时间推荐")
        
        # 重复任务管理标签页
        self.recurring_tab = RecurringTaskTab(self.app_context)
        self.recurring_tab.setObjectName("recurringTaskTab")
        self.tabs.addTab(self.recurring_tab, "重复任务管理")
        
        layout.addWidget(self.tabs)
        
    def refresh(self):
        """刷新视图数据"""
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.refresh_data() 