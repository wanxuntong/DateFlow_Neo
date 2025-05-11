#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务创建/编辑对话框
用于添加或修改任务的界面
"""

from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QMessageBox, QListWidget, QListWidgetItem, 
    QAbstractItemView, QFrame, QScrollArea, QWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from qfluentwidgets import (
    LineEdit, TextEdit, ComboBox, PrimaryPushButton, 
    PushButton, FluentIcon, CalendarPicker, TimeEdit,
    Dialog, InfoBar, SpinBox, CheckBox, InfoBarPosition,
    ExpandLayout, CompactSpinBox, RadioButton,
    SearchLineEdit, IconWidget, FlowLayout, CardWidget,
    Slider, SegmentedWidget, SwitchButton, PillPushButton,
    TitleLabel, StrongBodyLabel, BodyLabel, CaptionLabel
)

class TaskDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, parent=None, scheduler_manager=None, config_manager=None, subtask_manager=None, task_data=None):
        """
        初始化任务对话框
        
        参数:
            parent: 父窗口
            scheduler_manager: 调度管理器实例
            config_manager: 配置管理器实例
            subtask_manager: 子任务管理器实例
            task_data: 如果是编辑已有任务，则提供任务数据
        """
        super().__init__(parent)
        
        self.scheduler_manager = scheduler_manager
        self.config_manager = config_manager
        self.subtask_manager = subtask_manager
        self.task_data = task_data or {}
        
        # 临时子任务列表 - 用于存储尚未保存主任务时创建的子任务
        self.temp_subtasks = []
        
        # 设置对话框属性
        self.setWindowTitle("添加任务" if not task_data else "编辑任务")
        self.resize(700, 600)
        
        # 初始化界面
        self.init_ui()
        self.fill_data_if_edit()
    
    def init_ui(self):
        """初始化用户界面"""
        # 添加标题栏
        self.title_label = TitleLabel(self.windowTitle(), self)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget(self)
        
        # 基本信息选项卡
        self.basic_info_tab = QWidget()
        self.init_basic_info_tab()
        self.tab_widget.addTab(self.basic_info_tab, "基本信息")
        
        # 人员和地点选项卡
        self.people_location_tab = QWidget()
        self.init_people_location_tab()
        self.tab_widget.addTab(self.people_location_tab, "人员与地点")
        
        # 子任务选项卡
        self.subtasks_tab = QWidget()
        self.init_subtasks_tab()
        self.tab_widget.addTab(self.subtasks_tab, "子任务")
        
        # 高级设置选项卡
        self.advanced_tab = QWidget()
        self.init_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级设置")
        
        # 添加按钮
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self.save_task)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(btn_layout)
    
    def init_basic_info_tab(self):
        """初始化基本信息选项卡"""
        layout = QVBoxLayout(self.basic_info_tab)
        
        # 创建表单控件
        self.title_edit = LineEdit(self)
        self.title_edit.setPlaceholderText("输入任务标题")
        
        self.desc_edit = TextEdit(self)
        self.desc_edit.setPlaceholderText("输入任务详细描述")
        
        # 开始日期和时间
        self.start_date_picker = CalendarPicker(self)
        self.start_date_picker.setDate(QDate.currentDate())
        self.start_date_picker.setToolTip("选择任务开始日期")
        
        self.start_time_edit = TimeEdit(self)
        self.start_time_edit.setTime(QTime.currentTime())
        self.start_time_edit.setToolTip("选择任务开始时间")
        
        # 结束日期和时间
        self.end_date_picker = CalendarPicker(self)
        self.end_date_picker.setDate(QDate.currentDate().addDays(1))
        self.end_date_picker.setToolTip("选择任务结束日期")
        
        self.end_time_edit = TimeEdit(self)
        self.end_time_edit.setTime(QTime.currentTime())
        self.end_time_edit.setToolTip("选择任务结束时间")
        
        # 优先级选择
        self.priority_combo = ComboBox(self)
        self.priority_combo.addItems(["低", "中", "高", "紧急"])
        self.priority_combo.setCurrentIndex(1)  # 默认为中
        self.priority_combo.setToolTip("选择任务优先级，影响任务排序和显示")
        
        # 连接优先级选择框变更信号
        self.priority_combo.currentIndexChanged.connect(self.on_priority_changed)
        
        # 添加连接以更新优先级信息显示
        self.priority_combo.currentIndexChanged.connect(self.update_priority_display)
        
        # 紧急程度滑块
        self.urgency_slider = Slider(Qt.Horizontal, self)
        self.urgency_slider.setRange(0, 10)
        self.urgency_slider.setValue(5)
        self.urgency_slider.setToolTip("设置任务紧急程度(0-10)，表示时间紧迫性")
        
        # 连接紧急程度滑块值变化信号到更新方法
        self.urgency_slider.valueChanged.connect(self.update_urgency_display)
        
        # 任务完成状态
        self.completed_check = CheckBox("已完成", self)
        self.completed_check.setToolTip("勾选表示任务已完成")
        
        # 人员和地点卡片
        self.info_card = CardWidget(self)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(5)
        
        # 标题
        info_header = QHBoxLayout()
        info_header.addWidget(StrongBodyLabel("任务信息一览"))
        info_layout.addLayout(info_header)
        
        # 人员和地点信息
        self.task_info_flow = FlowLayout()
        self.task_info_flow.setSpacing(6)  # 使用setSpacing方法设置间距
        
        # 负责人员信息
        self.people_info_widget = QWidget()
        people_info_layout = QVBoxLayout(self.people_info_widget)
        people_info_layout.setContentsMargins(4, 4, 4, 4)
        people_info_layout.setSpacing(1)
        
        people_header = QHBoxLayout()
        people_header.setSpacing(2)
        
        people_title = StrongBodyLabel("负责人员", self.people_info_widget)
        people_title.setStyleSheet("font-size: 11px; font-weight: bold;")
        people_header.addWidget(people_title)
        people_header.addStretch()
        
        people_info_layout.addLayout(people_header)
        
        self.people_list_label = BodyLabel("未分配人员", self.people_info_widget)
        self.people_list_label.setStyleSheet("font-size: 10px; max-width: 170px;")
        self.people_list_label.setWordWrap(True)
        people_info_layout.addWidget(self.people_list_label)
        
        self.people_info_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f8ff;
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }
        """)
        
        # 任务地点信息
        self.location_info_widget = QWidget()
        location_info_layout = QVBoxLayout(self.location_info_widget)
        location_info_layout.setContentsMargins(4, 4, 4, 4)
        location_info_layout.setSpacing(1)
        
        location_header = QHBoxLayout()
        location_header.setSpacing(2)
        
        location_title = StrongBodyLabel("任务地点", self.location_info_widget)
        location_title.setStyleSheet("font-size: 11px; font-weight: bold;")
        location_header.addWidget(location_title)
        location_header.addStretch()
        
        location_info_layout.addLayout(location_header)
        
        self.location_label = BodyLabel("无指定地点", self.location_info_widget)
        self.location_label.setStyleSheet("font-size: 10px; max-width: 170px;")
        self.location_label.setWordWrap(True)
        location_info_layout.addWidget(self.location_label)
        
        self.location_info_widget.setStyleSheet("""
            QWidget {
                background-color: #f0fff0;
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }
        """)
        
        # 紧急程度信息卡片
        self.urgency_info_widget = QWidget()
        urgency_info_layout = QVBoxLayout(self.urgency_info_widget)
        urgency_info_layout.setContentsMargins(4, 4, 4, 4)
        urgency_info_layout.setSpacing(1)
        
        urgency_header = QHBoxLayout()
        urgency_header.setSpacing(2)
        
        urgency_title = StrongBodyLabel("紧急程度", self.urgency_info_widget)
        urgency_title.setStyleSheet("font-size: 11px; font-weight: bold;")
        urgency_header.addWidget(urgency_title)
        urgency_header.addStretch()
        
        urgency_info_layout.addLayout(urgency_header)
        
        self.urgency_label = BodyLabel("中等(5/10)", self.urgency_info_widget)
        self.urgency_label.setStyleSheet("font-size: 10px; max-width: 170px;")
        self.urgency_label.setWordWrap(True)
        urgency_info_layout.addWidget(self.urgency_label)
        
        self.urgency_info_widget.setStyleSheet("""
            QWidget {
                background-color: #fffaf0;
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }
        """)
        
        # 优先级信息卡片
        self.priority_info_widget = QWidget()
        priority_info_layout = QVBoxLayout(self.priority_info_widget)
        priority_info_layout.setContentsMargins(4, 4, 4, 4)
        priority_info_layout.setSpacing(1)
        
        priority_header = QHBoxLayout()
        priority_header.setSpacing(2)
        
        priority_title = StrongBodyLabel("优先级", self.priority_info_widget)
        priority_title.setStyleSheet("font-size: 11px; font-weight: bold;")
        priority_header.addWidget(priority_title)
        priority_header.addStretch()
        
        priority_info_layout.addLayout(priority_header)
        
        self.priority_label = BodyLabel("中", self.priority_info_widget)
        self.priority_label.setStyleSheet("font-size: 10px; max-width: 170px;")
        self.priority_label.setWordWrap(True)
        priority_info_layout.addWidget(self.priority_label)
        
        self.priority_info_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0ff;
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }
        """)
        
        # 将所有信息添加到流式布局
        self.task_info_flow.addWidget(self.people_info_widget)
        self.task_info_flow.addWidget(self.location_info_widget)
        self.task_info_flow.addWidget(self.urgency_info_widget)
        self.task_info_flow.addWidget(self.priority_info_widget)
        
        # 添加流式布局到信息卡片
        info_layout.addLayout(self.task_info_flow)
        
        # 添加到布局
        form_layout = QVBoxLayout()
        
        # 标题
        title_section = QVBoxLayout()
        title_label = StrongBodyLabel("任务标题:")
        title_label.setToolTip("任务的简短名称，将在列表中显示")
        title_section.addWidget(title_label)
        title_section.addWidget(self.title_edit)
        form_layout.addLayout(title_section)
        
        # 描述
        desc_section = QVBoxLayout()
        desc_label = StrongBodyLabel("任务描述:")
        desc_label.setToolTip("任务的详细说明，可以包含具体要求和注意事项")
        desc_section.addWidget(desc_label)
        desc_section.addWidget(self.desc_edit)
        form_layout.addLayout(desc_section)
        
        # 添加人员和地点信息卡片
        form_layout.addWidget(self.info_card)
        
        # 开始时间
        start_section = QVBoxLayout()
        start_label = StrongBodyLabel("开始时间:")
        start_label.setToolTip("任务计划开始的日期和时间")
        start_section.addWidget(start_label)
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(self.start_date_picker)
        start_time_layout.addWidget(self.start_time_edit)
        start_section.addLayout(start_time_layout)
        form_layout.addLayout(start_section)
        
        # 结束时间
        end_section = QVBoxLayout()
        end_label = StrongBodyLabel("结束时间:")
        end_label.setToolTip("任务计划结束的日期和时间")
        end_section.addWidget(end_label)
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(self.end_date_picker)
        end_time_layout.addWidget(self.end_time_edit)
        end_section.addLayout(end_time_layout)
        form_layout.addLayout(end_section)
        
        # 优先级
        priority_section = QVBoxLayout()
        priority_label = StrongBodyLabel("优先级:")
        priority_label.setToolTip("任务的重要程度，影响任务排序")
        priority_section.addWidget(priority_label)
        priority_section.addWidget(self.priority_combo)
        form_layout.addLayout(priority_section)
        
        # 紧急程度
        urgent_section = QVBoxLayout()
        urgent_label = StrongBodyLabel("紧急程度:")
        urgent_label.setToolTip("表示任务的时间紧迫性，0表示不紧急，10表示非常紧急")
        urgent_section.addWidget(urgent_label)
        urgent_layout = QHBoxLayout()
        not_urgent_label = BodyLabel("不紧急")
        not_urgent_label.setToolTip("时间充裕，可以延后处理")
        very_urgent_label = BodyLabel("非常紧急")
        very_urgent_label.setToolTip("时间紧迫，需要立即处理")
        urgent_layout.addWidget(not_urgent_label)
        urgent_layout.addWidget(self.urgency_slider)
        urgent_layout.addWidget(very_urgent_label)
        urgent_section.addLayout(urgent_layout)
        form_layout.addLayout(urgent_section)
        
        # 完成状态
        complete_section = QVBoxLayout()
        complete_label = StrongBodyLabel("完成状态:")
        complete_label.setToolTip("勾选表示任务已完成")
        complete_section.addWidget(complete_label)
        complete_section.addWidget(self.completed_check)
        form_layout.addLayout(complete_section)
        
        # 添加表单到布局并初始化信息显示
        layout.addLayout(form_layout)
        self.update_priority_display(self.priority_combo.currentIndex())
    
    def update_info_display(self):
        """更新人员和地点信息显示"""
        if not self.config_manager:
            return
            
        # 更新人员信息
        selected_people = self.people_list.selectedItems()
        people_names = [item.text() for item in selected_people]
        
        if people_names:
            self.people_list_label.setText("\n".join(people_names))
            self.people_list_label.setWordWrap(True)
            # 设置详细的悬浮提示
            people_tooltip = f"""
            <div style='font-family: Microsoft YaHei;'>
                <h3 style='margin: 2px;'>负责人员</h3>
                <hr style='margin: 2px;'>
                <ul style='margin-left: 15px; padding-left: 0px;'>
                    {"".join(f"<li>{name}</li>" for name in people_names)}
                </ul>
                <p style='color:#666;font-size:90%;'>共 {len(people_names)} 名人员参与此任务</p>
            </div>
            """
            self.people_info_widget.setToolTip(people_tooltip)
            # 设置背景颜色 - 有人员时为浅蓝色
            self.people_info_widget.setStyleSheet("""
                QWidget {
                    background-color: #e6f2ff;
                    border-radius: 4px;
                    min-height: 50px;
                    min-width: 120px;
                    max-width: 180px;
                }
            """)
        else:
            self.people_list_label.setText("未分配人员")
            self.people_list_label.setWordWrap(True)
            self.people_info_widget.setToolTip("当前任务未分配负责人员")
            # 设置背景颜色 - 无人员时为浅灰色
            self.people_info_widget.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    border-radius: 4px;
                    min-height: 50px;
                    min-width: 120px;
                    max-width: 180px;
                }
            """)
        
        # 更新地点信息
        selected_location = self.location_list.currentItem()
        if selected_location and selected_location.data(Qt.UserRole) is not None:
            location_name = selected_location.text()
            self.location_label.setText(location_name)
            self.location_label.setWordWrap(True)
            location_id = selected_location.data(Qt.UserRole)
            
            # 查找完整的地点信息
            location_obj = None
            locations = self.config_manager.get_all_locations()
            for loc in locations:
                if loc.get('id') == location_id:
                    location_obj = loc
                    break
            
            # 设置详细的悬浮提示
            if location_obj:
                location_tooltip = f"""
                <div style='font-family: Microsoft YaHei;'>
                    <h3 style='margin: 2px;'>{location_obj.get('name', '未命名')}</h3>
                    <hr style='margin: 2px;'>
                    <p><b>ID:</b> {location_obj.get('id', '无')[:8]}...</p>
                    <p><b>创建时间:</b> {location_obj.get('created_at', '未知')[:16]}</p>
                </div>
                """
                self.location_info_widget.setToolTip(location_tooltip)
            else:
                self.location_info_widget.setToolTip(f"任务将在 {location_name} 进行")
            
            # 设置背景颜色 - 有地点时为浅绿色
            self.location_info_widget.setStyleSheet("""
                QWidget {
                    background-color: #e6ffe6;
                    border-radius: 4px;
                    min-height: 50px;
                    min-width: 120px;
                    max-width: 180px;
                }
            """)
        else:
            self.location_label.setText("无指定地点")
            self.location_label.setWordWrap(True)
            self.location_info_widget.setToolTip("当前任务未指定地点")
            # 设置背景颜色 - 无地点时为浅灰色
            self.location_info_widget.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    border-radius: 4px;
                    min-height: 50px;
                    min-width: 120px;
                    max-width: 180px;
                }
            """)
        
        # 更新紧急程度信息
        self.update_urgency_display(self.urgency_slider.value())
        
        # 更新优先级信息
        self.update_priority_display(self.priority_combo.currentIndex())
    
    def update_priority_display(self, index):
        """更新优先级信息显示
        
        参数:
            index: 优先级索引(0=低, 1=中, 2=高, 3=紧急)
        """
        priority_texts = ["低", "中", "高", "紧急"]
        priority_colors = {
            0: "#e6f7ff",  # 淡蓝色 - 低优先级
            1: "#f0f0ff",  # 淡紫色 - 中优先级
            2: "#fff7e6",  # 淡橙色 - 高优先级
            3: "#fff1f0",  # 淡红色 - 紧急优先级
        }
        
        # 获取优先级文本和颜色
        priority_text = priority_texts[index]
        priority_color = priority_colors.get(index, "#f0f0ff")  # 默认为中优先级的颜色
        
        # 更新优先级显示
        self.priority_label.setText(priority_text)
        
        # 设置详细的悬浮提示
        priority_tooltip = f"""
        <div style='font-family: Microsoft YaHei;'>
            <h3 style='margin: 2px;'>优先级: {priority_text}</h3>
            <hr style='margin: 2px;'>
            <p>表示任务的重要程度</p>
            <p style='color:#666;font-size:90%;'>优先级越高，任务越重要，需要更早规划和处理</p>
        </div>
        """
        self.priority_info_widget.setToolTip(priority_tooltip)
        
        # 设置背景颜色
        self.priority_info_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {priority_color};
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }}
        """)
    
    def update_urgency_display(self, value):
        """更新紧急程度信息显示
        
        参数:
            value: 紧急程度值(0-10)
        """
        urgency_text = ""
        urgency_color = "#fffaf0"  # 默认背景色
        
        # 根据紧急程度值设置显示文本和颜色
        if value == 0:
            urgency_text = "不紧急(0/10)"
            urgency_color = "#f0f0f0"  # 淡灰色 - 不紧急
        elif value <= 3:
            urgency_text = f"较低({value}/10)"
            urgency_color = "#e6fffa"  # 淡青色 - 低紧急度
        elif value <= 6:
            urgency_text = f"中等({value}/10)"
            urgency_color = "#fffceb"  # 淡黄色 - 中紧急度
        elif value <= 8:
            urgency_text = f"较高({value}/10)"
            urgency_color = "#fff2e8"  # 淡橙色 - 高紧急度
        else:
            urgency_text = f"非常紧急({value}/10)"
            urgency_color = "#fff1f0"  # 淡红色 - 非常紧急
        
        # 更新紧急程度显示
        self.urgency_label.setText(urgency_text)
        
        # 设置详细的悬浮提示
        urgency_tooltip = f"""
        <div style='font-family: Microsoft YaHei;'>
            <h3 style='margin: 2px;'>紧急程度: {value}/10</h3>
            <hr style='margin: 2px;'>
            <p>表示任务的时间紧迫性</p>
            <p style='color:#666;font-size:90%;'>值越高表示越紧急，需要更高优先级处理</p>
        </div>
        """
        self.urgency_info_widget.setToolTip(urgency_tooltip)
        
        # 设置背景颜色
        self.urgency_info_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {urgency_color};
                border-radius: 4px;
                min-height: 50px;
                min-width: 120px;
                max-width: 180px;
            }}
        """)
    
    def init_people_location_tab(self):
        """初始化人员和地点选项卡"""
        layout = QVBoxLayout(self.people_location_tab)
        
        # 创建人员选择区域
        people_card = CardWidget(self)
        people_layout = QVBoxLayout(people_card)
        people_layout.addWidget(StrongBodyLabel("负责人员"))
        
        # 人员搜索
        self.people_search = SearchLineEdit(self)
        self.people_search.setPlaceholderText("搜索人员...")
        people_layout.addWidget(self.people_search)
        
        # 人员列表
        self.people_list = QListWidget(self)
        self.people_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.people_list.itemSelectionChanged.connect(self.update_info_display)
        people_layout.addWidget(self.people_list)
        
        # 添加人员按钮
        self.add_person_btn = PushButton("添加新人员", self)
        self.add_person_btn.setIcon(FluentIcon.ADD)
        self.add_person_btn.clicked.connect(self.add_new_person)
        people_layout.addWidget(self.add_person_btn)
        
        # 创建地点选择区域
        location_card = CardWidget(self)
        location_layout = QVBoxLayout(location_card)
        location_layout.addWidget(StrongBodyLabel("任务地点"))
        
        # 地点搜索
        self.location_search = SearchLineEdit(self)
        self.location_search.setPlaceholderText("搜索地点...")
        location_layout.addWidget(self.location_search)
        
        # 地点列表
        self.location_list = QListWidget(self)
        self.location_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.location_list.itemSelectionChanged.connect(self.update_info_display)
        location_layout.addWidget(self.location_list)
        
        # 添加地点按钮
        self.add_location_btn = PushButton("添加新地点", self)
        self.add_location_btn.setIcon(FluentIcon.ADD)
        self.add_location_btn.clicked.connect(self.add_new_location)
        location_layout.addWidget(self.add_location_btn)
        
        # 组合布局
        content_layout = QHBoxLayout()
        content_layout.addWidget(people_card, 2)
        content_layout.addWidget(location_card, 1)
        
        layout.addLayout(content_layout)
        
        # 加载人员和地点数据
        self.load_people_and_locations()
        
    def load_people_and_locations(self):
        """加载人员和地点数据"""
        if not self.config_manager:
            return
        
        # 加载人员
        people = self.config_manager.get_all_people()
        self.people_list.clear()
        
        for person in people:
            item = QListWidgetItem(person.get('name', '未命名'))
            item.setData(Qt.UserRole, person.get('id'))
            
            # 添加人员详细信息悬浮提示
            person_info = f"""
            <div style='font-family: Microsoft YaHei;'>
                <h3 style='margin: 2px;'>{person.get('name', '未命名')}</h3>
                <hr style='margin: 2px;'>
                <p><b>ID:</b> {person.get('id', '无')[:8]}...</p>
                <p><b>创建时间:</b> {person.get('created_at', '未知')[:16]}</p>
            </div>
            """
            item.setToolTip(person_info)
            
            self.people_list.addItem(item)
        
        # 加载地点
        locations = self.config_manager.get_all_locations()
        self.location_list.clear()
        
        # 添加"无指定地点"选项
        no_location_item = QListWidgetItem("无指定地点")
        no_location_item.setData(Qt.UserRole, None)
        no_location_item.setToolTip("未指定具体任务地点")
        self.location_list.addItem(no_location_item)
        
        for location in locations:
            item = QListWidgetItem(location.get('name', '未命名'))
            item.setData(Qt.UserRole, location.get('id'))
            
            # 添加地点详细信息悬浮提示
            location_info = f"""
            <div style='font-family: Microsoft YaHei;'>
                <h3 style='margin: 2px;'>{location.get('name', '未命名')}</h3>
                <hr style='margin: 2px;'>
                <p><b>ID:</b> {location.get('id', '无')[:8]}...</p>
                <p><b>创建时间:</b> {location.get('created_at', '未知')[:16]}</p>
            </div>
            """
            item.setToolTip(location_info)
            
            self.location_list.addItem(item)
        
        # 默认选中"无指定地点"
        self.location_list.setCurrentRow(0)
        
        # 更新信息显示
        self.update_info_display()
    
    def init_subtasks_tab(self):
        """初始化子任务选项卡"""
        layout = QVBoxLayout(self.subtasks_tab)
        
        # 创建子任务卡片
        subtasks_card = CardWidget(self)
        subtasks_layout = QVBoxLayout(subtasks_card)
        
        # 顶部标题与说明
        header_layout = QVBoxLayout()
        header_layout.addWidget(StrongBodyLabel("子任务管理"))
        header_layout.addWidget(BodyLabel("添加和管理当前任务的子任务"))
        subtasks_layout.addLayout(header_layout)
        
        # 创建子任务信息表格
        self.subtasks_table = QTableWidget(self)
        self.subtasks_table.setColumnCount(5)
        self.subtasks_table.setHorizontalHeaderLabels(["标题", "开始时间", "结束时间", "优先级", "状态"])
        self.subtasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.subtasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.subtasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.subtasks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.subtasks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.subtasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.subtasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        subtasks_layout.addWidget(self.subtasks_table)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.add_subtask_btn = PushButton("添加子任务", self)
        self.add_subtask_btn.setIcon(FluentIcon.ADD)
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        
        self.edit_subtask_btn = PushButton("编辑子任务", self)
        self.edit_subtask_btn.setIcon(FluentIcon.EDIT)
        self.edit_subtask_btn.clicked.connect(self.edit_subtask)
        
        self.remove_subtask_btn = PushButton("移除子任务", self)
        self.remove_subtask_btn.setIcon(FluentIcon.DELETE)
        self.remove_subtask_btn.clicked.connect(self.remove_subtask)
        
        self.complete_subtask_btn = PushButton("标记完成", self)
        self.complete_subtask_btn.setIcon(FluentIcon.COMPLETED)
        self.complete_subtask_btn.clicked.connect(self.toggle_subtask_completion)
        
        btn_layout.addWidget(self.add_subtask_btn)
        btn_layout.addWidget(self.edit_subtask_btn)
        btn_layout.addWidget(self.remove_subtask_btn)
        btn_layout.addWidget(self.complete_subtask_btn)
        
        subtasks_layout.addLayout(btn_layout)
        
        # 添加卡片到主布局
        layout.addWidget(subtasks_card)
        
        # 如果是编辑模式，加载子任务
        if self.task_data and self.subtask_manager:
            self.load_subtasks()
    
    def init_advanced_tab(self):
        """初始化高级设置选项卡"""
        layout = QVBoxLayout(self.advanced_tab)
        
        # 提醒设置
        reminder_card = CardWidget(self)
        reminder_layout = QVBoxLayout(reminder_card)
        reminder_layout.addWidget(StrongBodyLabel("提醒设置"))
        
        # 是否需要提醒
        self.remind_check = CheckBox("需要提醒", self)
        self.remind_check.setChecked(True)
        reminder_layout.addWidget(self.remind_check)
        
        # 提醒提前时间
        remind_advance_layout = QHBoxLayout()
        remind_advance_layout.addWidget(BodyLabel("提前提醒时间:"))
        
        self.remind_advance_spin = SpinBox(self)
        self.remind_advance_spin.setRange(5, 120)
        self.remind_advance_spin.setValue(15)
        self.remind_advance_spin.setSuffix(" 分钟")
        
        remind_advance_layout.addWidget(self.remind_advance_spin)
        reminder_layout.addLayout(remind_advance_layout)
        
        # 重复设置
        recurrence_card = CardWidget(self)
        recurrence_layout = QVBoxLayout(recurrence_card)
        recurrence_layout.addWidget(StrongBodyLabel("重复设置"))
        
        # 是否重复
        self.recurrence_check = CheckBox("定期重复任务", self)
        recurrence_layout.addWidget(self.recurrence_check)
        
        # 重复类型
        recurrence_type_layout = QHBoxLayout()
        recurrence_type_layout.addWidget(BodyLabel("重复类型:"))
        
        self.recurrence_combo = ComboBox(self)
        self.recurrence_combo.addItems(["每天", "每周", "每月", "自定义"])
        
        recurrence_type_layout.addWidget(self.recurrence_combo)
        recurrence_layout.addLayout(recurrence_type_layout)
        
        # 依赖关系设置
        dependency_card = CardWidget(self)
        dependency_layout = QVBoxLayout(dependency_card)
        dependency_layout.addWidget(StrongBodyLabel("依赖关系"))
        dependency_layout.addWidget(BodyLabel("此任务依赖于以下任务的完成"))
        
        # 依赖任务列表
        self.dependency_list = QListWidget(self)
        dependency_layout.addWidget(self.dependency_list)
        
        # 依赖任务按钮区域
        dep_btn_layout = QHBoxLayout()
        
        # 添加依赖按钮
        self.add_dependency_btn = PushButton("添加依赖", self)
        self.add_dependency_btn.setIcon(FluentIcon.LINK)
        self.add_dependency_btn.clicked.connect(self.add_dependency)
        
        # 移除依赖按钮
        self.remove_dependency_btn = PushButton("移除依赖", self)
        self.remove_dependency_btn.setIcon(FluentIcon.DELETE)
        self.remove_dependency_btn.clicked.connect(self.remove_dependency)
        
        dep_btn_layout.addWidget(self.add_dependency_btn)
        dep_btn_layout.addWidget(self.remove_dependency_btn)
        
        dependency_layout.addLayout(dep_btn_layout)
        
        # 添加所有卡片到布局
        layout.addWidget(reminder_card)
        layout.addWidget(recurrence_card)
        layout.addWidget(dependency_card)
    
    def load_subtasks(self):
        """加载子任务"""
        self.subtasks_table.setRowCount(0)  # 清空表格
        
        # 加载已保存的子任务
        if self.task_data and self.task_data.get('id') and self.subtask_manager:
            task_id = self.task_data.get('id')
            subtasks = self.subtask_manager.get_subtasks(task_id)
            
            for subtask in subtasks:
                self._add_subtask_to_table(subtask)
        
        # 加载临时子任务
        for subtask in self.temp_subtasks:
            self._add_subtask_to_table(subtask)
    
    def _add_subtask_to_table(self, subtask):
        """将子任务添加到表格中"""
        row = self.subtasks_table.rowCount()
        self.subtasks_table.insertRow(row)
        
        # 设置标题
        title_item = QTableWidgetItem(subtask.get('title', '未命名子任务'))
        title_item.setData(Qt.UserRole, subtask.get('id'))
        self.subtasks_table.setItem(row, 0, title_item)
        
        # 设置开始时间
        start_time = subtask.get('start_time')
        if start_time:
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
        else:
            start_time_str = "未设置"
        self.subtasks_table.setItem(row, 1, QTableWidgetItem(start_time_str))
        
        # 设置结束时间
        end_time = subtask.get('end_time')
        if end_time:
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
        else:
            end_time_str = "未设置"
        self.subtasks_table.setItem(row, 2, QTableWidgetItem(end_time_str))
        
        # 设置优先级
        priority = subtask.get('priority', '中')
        self.subtasks_table.setItem(row, 3, QTableWidgetItem(priority))
        
        # 设置完成状态
        status_text = "已完成" if subtask.get('completed', False) else "进行中"
        status_item = QTableWidgetItem(status_text)
        if subtask.get('completed', False):
            from PyQt5.QtGui import QColor, QBrush
            status_item.setForeground(QBrush(QColor(0, 128, 0)))  # 绿色表示已完成
        self.subtasks_table.setItem(row, 4, status_item)
        
        # 为子任务添加详细信息悬浮提示
        subtask_info = f"""
        <div style='font-family: Microsoft YaHei;'>
            <h3 style='margin: 2px;'>{subtask.get('title', '未命名子任务')}</h3>
            <hr style='margin: 2px;'>
            <p><b>描述:</b> {subtask.get('description', '无')[:50]}{'...' if len(subtask.get('description', '')) > 50 else ''}</p>
            <p><b>开始时间:</b> {start_time_str}</p>
            <p><b>结束时间:</b> {end_time_str}</p>
            <p><b>优先级:</b> {priority}</p>
            <p><b>状态:</b> {status_text}</p>
        </div>
        """
        
        # 为每个单元格设置相同的提示信息
        for col in range(5):
            item = self.subtasks_table.item(row, col)
            if item:
                item.setToolTip(subtask_info)
        
        # 如果是临时子任务，设置背景色以区分
        if not subtask.get('id'):
            from PyQt5.QtGui import QBrush, QColor
            for col in range(5):
                item = self.subtasks_table.item(row, col)
                if item:
                    item.setBackground(QBrush(QColor(245, 245, 220)))  # 米色背景
    
    def add_new_person(self):
        """添加新人员"""
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加新人员")
        dialog.setFixedSize(300, 150)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加提示文本
        prompt_label = StrongBodyLabel("请输入人员姓名", dialog)
        layout.addWidget(prompt_label)
        
        # 创建输入框
        name_edit = LineEdit(dialog)
        name_edit.setPlaceholderText("输入人员姓名")
        layout.addWidget(name_edit)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加按钮
        cancel_btn = PushButton("取消", dialog)
        cancel_btn.clicked.connect(dialog.reject)
        
        confirm_btn = PrimaryPushButton("确认", dialog)
        confirm_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        
        # 添加按钮布局
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 显示对话框
        if dialog.exec_():
            name = name_edit.text().strip()
            if name:
                # 生成一个唯一ID
                import uuid
                person_id = str(uuid.uuid4())
                
                # 添加人员
                if self.config_manager:
                    person_data = {
                        'id': person_id,
                        'name': name,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    if self.config_manager.add_person(person_data):
                        # 重新加载人员列表
                        self.load_people_and_locations()
                        
                        # 选中新添加的人员
                        for i in range(self.people_list.count()):
                            item = self.people_list.item(i)
                            if item.data(Qt.UserRole) == person_id:
                                item.setSelected(True)
                                break
                        
                        InfoBar.success(
                            title="成功",
                            content=f"已添加人员: {name}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                    else:
                        InfoBar.error(
                            title="错误",
                            content="添加人员失败",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=3000
                        )
    
    def add_new_location(self):
        """添加新地点"""
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加新地点")
        dialog.setFixedSize(300, 150)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加提示文本
        prompt_label = StrongBodyLabel("请输入地点名称", dialog)
        layout.addWidget(prompt_label)
        
        # 创建输入框
        name_edit = LineEdit(dialog)
        name_edit.setPlaceholderText("输入地点名称")
        layout.addWidget(name_edit)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加按钮
        cancel_btn = PushButton("取消", dialog)
        cancel_btn.clicked.connect(dialog.reject)
        
        confirm_btn = PrimaryPushButton("确认", dialog)
        confirm_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        
        # 添加按钮布局
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 显示对话框
        if dialog.exec_():
            name = name_edit.text().strip()
            if name:
                # 生成一个唯一ID
                import uuid
                location_id = str(uuid.uuid4())
                
                # 添加地点
                if self.config_manager:
                    location_data = {
                        'id': location_id,
                        'name': name,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    if self.config_manager.add_location(location_data):
                        # 重新加载地点列表
                        self.load_people_and_locations()
                        
                        # 选中新添加的地点
                        index = self.location_list.findText(name)
                        if index >= 0:
                            self.location_list.setCurrentItem(self.location_list.item(index))
                        
                        InfoBar.success(
                            title="成功",
                            content=f"已添加地点: {name}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                    else:
                        InfoBar.error(
                            title="错误",
                            content="添加地点失败",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=3000
                        )
    
    def add_subtask(self):
        """添加子任务"""
        # 创建对话框
        subtask_dialog = QDialog(self)
        subtask_dialog.setWindowTitle("添加子任务")
        subtask_dialog.resize(500, 400)
        
        dialog_layout = QVBoxLayout(subtask_dialog)
        
        # 子任务表单
        form_layout = QVBoxLayout()
        
        # 标题
        title_section = QVBoxLayout()
        title_section.addWidget(StrongBodyLabel("子任务标题:"))
        title_edit = LineEdit(subtask_dialog)
        title_edit.setPlaceholderText("子任务标题")
        title_section.addWidget(title_edit)
        form_layout.addLayout(title_section)
        
        # 描述
        desc_section = QVBoxLayout()
        desc_section.addWidget(StrongBodyLabel("子任务描述:"))
        desc_edit = TextEdit(subtask_dialog)
        desc_edit.setPlaceholderText("子任务详细描述")
        desc_section.addWidget(desc_edit)
        form_layout.addLayout(desc_section)
        
        # 开始日期和时间
        start_section = QVBoxLayout()
        start_section.addWidget(StrongBodyLabel("开始时间:"))
        start_time_layout = QHBoxLayout()
        start_date_picker = CalendarPicker(subtask_dialog)
        start_date_picker.setDate(QDate.currentDate())
        start_time_edit = TimeEdit(subtask_dialog)
        start_time_edit.setTime(QTime.currentTime())
        start_time_layout.addWidget(start_date_picker)
        start_time_layout.addWidget(start_time_edit)
        start_section.addLayout(start_time_layout)
        form_layout.addLayout(start_section)
        
        # 结束日期和时间
        end_section = QVBoxLayout()
        end_section.addWidget(StrongBodyLabel("结束时间:"))
        end_time_layout = QHBoxLayout()
        end_date_picker = CalendarPicker(subtask_dialog)
        end_date_picker.setDate(QDate.currentDate().addDays(1))
        end_time_edit = TimeEdit(subtask_dialog)
        end_time_edit.setTime(QTime.currentTime())
        end_time_layout.addWidget(end_date_picker)
        end_time_layout.addWidget(end_time_edit)
        end_section.addLayout(end_time_layout)
        form_layout.addLayout(end_section)
        
        # 优先级选择
        priority_section = QVBoxLayout()
        priority_section.addWidget(StrongBodyLabel("优先级:"))
        priority_combo = ComboBox(subtask_dialog)
        priority_combo.addItems(["低", "中", "高", "紧急"])
        priority_combo.setCurrentIndex(1)  # 默认为中
        priority_section.addWidget(priority_combo)
        form_layout.addLayout(priority_section)
        
        # 完成状态
        complete_section = QVBoxLayout()
        complete_section.addWidget(StrongBodyLabel("完成状态:"))
        completed_check = CheckBox("已完成", subtask_dialog)
        complete_section.addWidget(completed_check)
        form_layout.addLayout(complete_section)
        
        dialog_layout.addLayout(form_layout)
        
        # 添加状态提示 - 如果主任务未保存
        if not self.task_data or not self.task_data.get('id'):
            status_label = BodyLabel("主任务尚未保存，子任务将暂时存储，并在保存主任务时一同保存。", subtask_dialog)
            status_label.setStyleSheet("color: #FF8C00;") # 暗橙色
            dialog_layout.addWidget(status_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = PushButton("取消", subtask_dialog)
        cancel_btn.clicked.connect(subtask_dialog.reject)
        
        save_btn = PrimaryPushButton("保存", subtask_dialog)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        dialog_layout.addLayout(btn_layout)
        
        # 保存按钮点击事件
        def on_save_clicked():
            title = title_edit.text().strip()
            
            if not title:
                InfoBar.error(
                    title="错误",
                    content="子任务标题不能为空",
                    parent=subtask_dialog,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            description = desc_edit.toPlainText().strip()
            
            # 构建开始时间
            start_date = start_date_picker.getDate()
            start_time = start_time_edit.time()
            start_dt = datetime(
                start_date.year(), start_date.month(), start_date.day(),
                start_time.hour(), start_time.minute(), start_time.second()
            )
            
            # 构建结束时间
            end_date = end_date_picker.getDate()
            end_time = end_time_edit.time()
            end_dt = datetime(
                end_date.year(), end_date.month(), end_date.day(),
                end_time.hour(), end_time.minute(), end_time.second()
            )
            
            # 检查结束时间是否晚于开始时间
            if end_dt <= start_dt:
                InfoBar.error(
                    title="错误",
                    content="结束时间必须晚于开始时间",
                    parent=subtask_dialog,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            # 创建子任务数据
            subtask_data = {
                'title': title,
                'description': description,
                'start_time': start_dt,
                'end_time': end_dt,
                'priority': priority_combo.currentText(),
                'completed': completed_check.isChecked(),
                'temp_id': str(datetime.now().timestamp())  # 临时ID，用于识别临时子任务
            }
            
            # 根据主任务是否已保存，决定如何处理子任务
            if self.task_data and self.task_data.get('id') and self.subtask_manager:
                # 如果主任务已保存，直接添加子任务
                subtask_id = self.subtask_manager.add_subtask(self.task_data['id'], subtask_data)
                if subtask_id:
                    subtask_dialog.accept()
                    self.load_subtasks()  # 重新加载子任务列表
                    
                    InfoBar.success(
                        title="成功",
                        content=f"已添加子任务: {title}",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=2000
                    )
                else:
                    InfoBar.error(
                        title="错误",
                        content="添加子任务失败",
                        parent=subtask_dialog,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
            else:
                # 主任务尚未保存，暂存子任务
                self.temp_subtasks.append(subtask_data)
                subtask_dialog.accept()
                self.load_subtasks()  # 重新加载子任务列表
                
                InfoBar.success(
                    title="成功",
                    content=f"已暂存子任务: {title}，将在保存主任务时一同保存",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
        
        save_btn.clicked.connect(on_save_clicked)
        
        # 显示对话框
        subtask_dialog.exec_()
    
    def edit_subtask(self):
        """编辑子任务"""
        # 获取选中的行
        selected_rows = self.subtasks_table.selectedItems()
        if not selected_rows:
            InfoBar.info(
                title="提示",
                content="请先选择要编辑的子任务",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
            return
        
        # 获取选中行的第一列（标题列）的单元格
        row = selected_rows[0].row()
        title_item = self.subtasks_table.item(row, 0)
        subtask_id = title_item.data(Qt.UserRole)
        
        # 获取子任务数据
        subtask = None
        is_temp = False
        
        if subtask_id and self.subtask_manager:
            # 已保存的子任务
            subtask = self.subtask_manager.get_subtask(subtask_id)
        else:
            # 查找临时子任务
            for temp_subtask in self.temp_subtasks:
                if temp_subtask.get('temp_id') == subtask_id or temp_subtask.get('title') == title_item.text():
                    subtask = temp_subtask
                    is_temp = True
                    break
        
        if not subtask:
            InfoBar.error(
                title="错误",
                content="无法获取子任务信息",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            return
        
        # 创建对话框
        subtask_dialog = QDialog(self)
        subtask_dialog.setWindowTitle("编辑子任务")
        subtask_dialog.resize(500, 400)
        
        dialog_layout = QVBoxLayout(subtask_dialog)
        
        # 子任务表单
        form_layout = QVBoxLayout()
        
        # 标题
        title_section = QVBoxLayout()
        title_section.addWidget(StrongBodyLabel("子任务标题:"))
        title_edit = LineEdit(subtask_dialog)
        title_edit.setText(subtask.get("title", ""))
        title_section.addWidget(title_edit)
        form_layout.addLayout(title_section)
        
        # 描述
        desc_section = QVBoxLayout()
        desc_section.addWidget(StrongBodyLabel("子任务描述:"))
        desc_edit = TextEdit(subtask_dialog)
        desc_edit.setText(subtask.get("description", ""))
        desc_section.addWidget(desc_edit)
        form_layout.addLayout(desc_section)
        
        # 开始日期和时间
        start_section = QVBoxLayout()
        start_section.addWidget(StrongBodyLabel("开始时间:"))
        start_time_layout = QHBoxLayout()
        start_date_picker = CalendarPicker(subtask_dialog)
        start_time_edit = TimeEdit(subtask_dialog)
        
        # 设置开始时间
        start_dt = subtask.get("start_time")
        if start_dt:
            start_date = QDate(start_dt.year, start_dt.month, start_dt.day)
            start_time = QTime(start_dt.hour, start_dt.minute, start_dt.second)
            start_date_picker.setDate(start_date)
            start_time_edit.setTime(start_time)
        else:
            start_date_picker.setDate(QDate.currentDate())
            start_time_edit.setTime(QTime.currentTime())
        
        start_time_layout.addWidget(start_date_picker)
        start_time_layout.addWidget(start_time_edit)
        start_section.addLayout(start_time_layout)
        form_layout.addLayout(start_section)
        
        # 结束日期和时间
        end_section = QVBoxLayout()
        end_section.addWidget(StrongBodyLabel("结束时间:"))
        end_time_layout = QHBoxLayout()
        end_date_picker = CalendarPicker(subtask_dialog)
        end_time_edit = TimeEdit(subtask_dialog)
        
        # 设置结束时间
        end_dt = subtask.get("end_time")
        if end_dt:
            end_date = QDate(end_dt.year, end_dt.month, end_dt.day)
            end_time = QTime(end_dt.hour, end_dt.minute, end_dt.second)
            end_date_picker.setDate(end_date)
            end_time_edit.setTime(end_time)
        else:
            end_date_picker.setDate(QDate.currentDate().addDays(1))
            end_time_edit.setTime(QTime.currentTime())
        
        end_time_layout.addWidget(end_date_picker)
        end_time_layout.addWidget(end_time_edit)
        end_section.addLayout(end_time_layout)
        form_layout.addLayout(end_section)
        
        # 优先级选择
        priority_section = QVBoxLayout()
        priority_section.addWidget(StrongBodyLabel("优先级:"))
        priority_combo = ComboBox(subtask_dialog)
        priority_combo.addItems(["低", "中", "高", "紧急"])
        
        # 设置当前优先级
        priority = subtask.get("priority", "中")
        index = priority_combo.findText(priority)
        if index >= 0:
            priority_combo.setCurrentIndex(index)
        
        priority_section.addWidget(priority_combo)
        form_layout.addLayout(priority_section)
        
        # 完成状态
        complete_section = QVBoxLayout()
        complete_section.addWidget(StrongBodyLabel("完成状态:"))
        completed_check = CheckBox("已完成", subtask_dialog)
        completed_check.setChecked(subtask.get("completed", False))
        complete_section.addWidget(completed_check)
        form_layout.addLayout(complete_section)
        
        dialog_layout.addLayout(form_layout)
        
        # 添加状态提示 - 如果是临时子任务
        if is_temp:
            status_label = BodyLabel("此子任务尚未保存到数据库，将在保存主任务时一同保存。", subtask_dialog)
            status_label.setStyleSheet("color: #FF8C00;") # 暗橙色
            dialog_layout.addWidget(status_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = PushButton("取消", subtask_dialog)
        cancel_btn.clicked.connect(subtask_dialog.reject)
        
        save_btn = PrimaryPushButton("保存", subtask_dialog)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        dialog_layout.addLayout(btn_layout)
        
        # 保存按钮点击事件
        def on_save_clicked():
            title = title_edit.text().strip()
            
            if not title:
                InfoBar.error(
                    title="错误",
                    content="子任务标题不能为空",
                    parent=subtask_dialog,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            description = desc_edit.toPlainText().strip()
            
            # 构建开始时间
            start_date = start_date_picker.getDate()
            start_time = start_time_edit.time()
            start_dt = datetime(
                start_date.year(), start_date.month(), start_date.day(),
                start_time.hour(), start_time.minute(), start_time.second()
            )
            
            # 构建结束时间
            end_date = end_date_picker.getDate()
            end_time = end_time_edit.time()
            end_dt = datetime(
                end_date.year(), end_date.month(), end_date.day(),
                end_time.hour(), end_time.minute(), end_time.second()
            )
            
            # 检查结束时间是否晚于开始时间
            if end_dt <= start_dt:
                InfoBar.error(
                    title="错误",
                    content="结束时间必须晚于开始时间",
                    parent=subtask_dialog,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            # 更新子任务数据
            updated_subtask = subtask.copy()  # 复制原数据，保留其他字段
            updated_subtask.update({
                'title': title,
                'description': description,
                'start_time': start_dt,
                'end_time': end_dt,
                'priority': priority_combo.currentText(),
                'completed': completed_check.isChecked()
            })
            
            # 根据子任务类型进行更新
            if is_temp:
                # 更新临时子任务
                for i, temp_subtask in enumerate(self.temp_subtasks):
                    if temp_subtask.get('temp_id') == subtask.get('temp_id'):
                        self.temp_subtasks[i] = updated_subtask
                        break
                
                subtask_dialog.accept()
                self.load_subtasks()  # 重新加载子任务列表
                
                InfoBar.success(
                    title="成功",
                    content=f"已更新临时子任务: {title}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000
                )
            else:
                # 更新已保存的子任务
                result = self.subtask_manager.update_subtask(subtask_id, updated_subtask)
                if result:
                    subtask_dialog.accept()
                    self.load_subtasks()  # 重新加载子任务列表
                    
                    InfoBar.success(
                        title="成功",
                        content=f"已更新子任务: {title}",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=2000
                    )
                else:
                    InfoBar.error(
                        title="错误",
                        content="更新子任务失败",
                        parent=subtask_dialog,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
        
        save_btn.clicked.connect(on_save_clicked)
        
        # 显示对话框
        subtask_dialog.exec_()
    
    def remove_subtask(self):
        """移除子任务"""
        # 获取选中的行
        selected_rows = self.subtasks_table.selectedItems()
        if not selected_rows:
            InfoBar.info(
                title="提示",
                content="请先选择要删除的子任务",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
            return
        
        # 确认是否删除
        from qfluentwidgets import MessageBox
        
        box = MessageBox(
            "确认删除",
            "确定要删除选中的子任务吗？此操作不可撤销。",
            self
        )
        
        if box.exec_():
            # 获取所有不同行的第一列（标题列）单元格
            processed_rows = set()
            for item in selected_rows:
                row = item.row()
                if row in processed_rows:
                    continue
                
                processed_rows.add(row)
                title_item = self.subtasks_table.item(row, 0)
                subtask_id = title_item.data(Qt.UserRole)
                subtask_title = title_item.text()
                
                if subtask_id and self.subtask_manager:
                    # 删除已保存的子任务
                    if self.subtask_manager.remove_subtask(subtask_id):
                        InfoBar.success(
                            title="成功",
                            content=f"已移除子任务: {subtask_title}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                    else:
                        InfoBar.error(
                            title="错误",
                            content=f"移除子任务失败: {subtask_title}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=3000
                        )
                else:
                    # 删除临时子任务
                    for i, temp_subtask in enumerate(self.temp_subtasks):
                        if temp_subtask.get('temp_id') == subtask_id or temp_subtask.get('title') == subtask_title:
                            del self.temp_subtasks[i]
                            InfoBar.success(
                                title="成功",
                                content=f"已移除临时子任务: {subtask_title}",
                                parent=self,
                                position=InfoBarPosition.TOP_RIGHT,
                                duration=2000
                            )
                            break
            
            # 刷新子任务列表
            self.load_subtasks()
            
    def toggle_subtask_completion(self):
        """切换子任务完成状态"""
        # 获取选中的行
        selected_rows = self.subtasks_table.selectedItems()
        if not selected_rows:
            InfoBar.info(
                title="提示",
                content="请先选择要操作的子任务",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
            return
        
        # 获取所有不同行的第一列（标题列）单元格
        processed_rows = set()
        for item in selected_rows:
            row = item.row()
            if row in processed_rows:
                continue
            
            processed_rows.add(row)
            title_item = self.subtasks_table.item(row, 0)
            subtask_id = title_item.data(Qt.UserRole)
            
            if self.subtask_manager and subtask_id:
                # 获取子任务信息
                subtask = self.subtask_manager.get_subtask(subtask_id)
                if subtask:
                    # 切换完成状态
                    current_status = subtask.get('completed', False)
                    updated_subtask = subtask.copy()
                    updated_subtask['completed'] = not current_status
                    
                    # 更新子任务
                    if self.subtask_manager.update_subtask(subtask_id, updated_subtask):
                        status_text = "已完成" if not current_status else "进行中"
                        InfoBar.success(
                            title="成功",
                            content=f"子任务 {title_item.text()} 状态已更新为: {status_text}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                    else:
                        InfoBar.error(
                            title="错误",
                            content=f"更新子任务状态失败: {title_item.text()}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=3000
                        )
        
        # 刷新子任务列表
        self.load_subtasks()
    
    def add_dependency(self):
        """添加依赖任务"""
        # 检查是否处于编辑模式
        if not self.task_data or not self.task_data.get('id'):
            InfoBar.warning(
                title="提示",
                content="请先保存主任务后再添加依赖关系",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
            return
        
        # 获取所有可用任务
        if self.scheduler_manager:
            all_tasks = self.scheduler_manager.get_all_tasks()
            current_task_id = self.task_data.get('id')
            
            # 排除当前任务和已添加的依赖
            available_tasks = []
            existing_deps = []
            
            # 获取已有依赖
            for i in range(self.dependency_list.count()):
                item = self.dependency_list.item(i)
                existing_deps.append(item.data(Qt.UserRole))
            
            for task in all_tasks:
                task_id = task.get('id')
                if task_id != current_task_id and task_id not in existing_deps:
                    available_tasks.append(task)
            
            # 如果没有可用任务
            if not available_tasks:
                InfoBar.information(
                    title="提示",
                    content="没有可添加的依赖任务",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000
                )
                return
            
            # 创建更高级的依赖任务对话框
            dep_dialog = QDialog(self)
            dep_dialog.setWindowTitle("添加依赖任务")
            dep_dialog.resize(550, 500)
            
            dialog_layout = QVBoxLayout(dep_dialog)
            
            # 标题
            title_label = TitleLabel("添加依赖任务", dep_dialog)
            dialog_layout.addWidget(title_label)
            dialog_layout.addSpacing(10)
            
            # 说明文字
            description_label = BodyLabel("选择当前任务所依赖的其他任务，依赖任务需要在此任务开始前完成。", dep_dialog)
            dialog_layout.addWidget(description_label)
            dialog_layout.addSpacing(20)
            
            # 创建任务列表卡片
            task_card = CardWidget(dep_dialog)
            task_card_layout = QVBoxLayout(task_card)
            
            # 添加搜索框
            search_edit = SearchLineEdit(task_card)
            search_edit.setPlaceholderText("搜索任务...")
            task_card_layout.addWidget(search_edit)
            task_card_layout.addSpacing(10)
            
            # 任务列表
            from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
            tree_widget = QTreeWidget(task_card)
            tree_widget.setHeaderLabels(["任务名称", "开始时间", "结束时间", "优先级"])
            tree_widget.setAlternatingRowColors(True)
            tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
            
            # 填充任务列表，按优先级分组
            priority_groups = {}
            
            for task in available_tasks:
                priority = task.get('priority', '中')
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(task)
            
            # 优先级顺序
            priority_order = {'紧急': 0, '高': 1, '中': 2, '低': 3}
            
            # 按优先级排序并添加到树控件
            for priority in sorted(priority_groups.keys(), key=lambda p: priority_order.get(p, 999)):
                group_item = QTreeWidgetItem(tree_widget)
                group_item.setText(0, f"{priority}优先级 ({len(priority_groups[priority])})")
                group_item.setExpanded(True)
                
                for task in priority_groups[priority]:
                    task_item = QTreeWidgetItem(group_item)
                    task_item.setText(0, task.get('title', '未命名任务'))
                    
                    # 设置开始时间
                    start_time = task.get('start_time')
                    if start_time:
                        start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
                    else:
                        start_time_str = "未设置"
                    task_item.setText(1, start_time_str)
                    
                    # 设置结束时间
                    end_time = task.get('end_time')
                    if end_time:
                        end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
                    else:
                        end_time_str = "未设置"
                    task_item.setText(2, end_time_str)
                    
                    # 设置优先级
                    task_item.setText(3, priority)
                    
                    # 保存任务ID
                    task_item.setData(0, Qt.UserRole, task.get('id'))
            
            # 设置列宽
            tree_widget.setColumnWidth(0, 180)
            tree_widget.setColumnWidth(1, 120)
            tree_widget.setColumnWidth(2, 120)
            tree_widget.setColumnWidth(3, 60)
            
            task_card_layout.addWidget(tree_widget)
            
            # 依赖类型选择
            type_card = CardWidget(dep_dialog)
            type_card_layout = QVBoxLayout(type_card)
            type_card_layout.addWidget(StrongBodyLabel("依赖类型"))
            
            # 依赖类型单选按钮
            from PyQt5.QtWidgets import QRadioButton, QButtonGroup
            dep_type_group = QButtonGroup(type_card)
            
            strong_radio = RadioButton("强依赖 (阻塞)", type_card)
            strong_radio.setChecked(True)
            strong_radio.setToolTip("必须等待依赖任务完成后才能开始当前任务")
            dep_type_group.addButton(strong_radio, 1)
            
            weak_radio = RadioButton("弱依赖 (提醒)", type_card)
            weak_radio.setToolTip("依赖任务未完成时提醒用户，但不阻止当前任务开始")
            dep_type_group.addButton(weak_radio, 2)
            
            type_card_layout.addWidget(strong_radio)
            type_card_layout.addWidget(weak_radio)
            
            # 添加卡片到布局
            dialog_layout.addWidget(task_card)
            dialog_layout.addSpacing(15)
            dialog_layout.addWidget(type_card)
            dialog_layout.addSpacing(15)
            
            # 底部按钮
            btn_layout = QHBoxLayout()
            cancel_btn = PushButton("取消", dep_dialog)
            cancel_btn.clicked.connect(dep_dialog.reject)
            
            add_btn = PrimaryPushButton("添加依赖", dep_dialog)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(add_btn)
            
            dialog_layout.addLayout(btn_layout)
            
            # 实现搜索功能
            def on_search_text_changed(text):
                # 隐藏所有顶级项
                for i in range(tree_widget.topLevelItemCount()):
                    top_item = tree_widget.topLevelItem(i)
                    
                    # 隐藏所有子项
                    visible_children = 0
                    for j in range(top_item.childCount()):
                        child = top_item.child(j)
                        task_title = child.text(0).lower()
                        
                        if text.lower() in task_title:
                            child.setHidden(False)
                            visible_children += 1
                        else:
                            child.setHidden(True)
                    
                    # 如果该分组下有可见的子项，则显示分组
                    top_item.setHidden(visible_children == 0)
                    
                    # 更新分组文字
                    priority = top_item.text(0).split('(')[0].strip()
                    top_item.setText(0, f"{priority} ({visible_children})")
            
            search_edit.textChanged.connect(on_search_text_changed)
            
            # 添加依赖按钮点击事件
            def on_add_clicked():
                selected_items = tree_widget.selectedItems()
                if not selected_items:
                    InfoBar.warning(
                        title="提示",
                        content="请选择一个依赖任务",
                        parent=dep_dialog,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=2000
                    )
                    return
                
                selected_item = selected_items[0]
                
                # 如果选中的是分组项，则不处理
                if selected_item.parent() is None:
                    InfoBar.warning(
                        title="提示",
                        content="请选择具体的任务，而不是分组",
                        parent=dep_dialog,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=2000
                    )
                    return
                
                # 获取选中任务的信息
                task_id = selected_item.data(0, Qt.UserRole)
                task_title = selected_item.text(0)
                
                # 获取依赖类型
                dep_type = "strong" if strong_radio.isChecked() else "weak"
                
                # 添加到依赖列表
                item = QListWidgetItem(task_title)
                item.setData(Qt.UserRole, task_id)
                item.setData(Qt.UserRole + 1, dep_type)  # 保存依赖类型
                
                # 设置图标和工具提示
                if dep_type == "strong":
                    item.setIcon(FluentIcon.LINK.icon())
                    item.setToolTip("强依赖：必须先完成此任务")
                else:
                    item.setIcon(FluentIcon.LINK_SQUARE.icon())
                    item.setToolTip("弱依赖：建议先完成此任务")
                
                self.dependency_list.addItem(item)
                
                dep_dialog.accept()
                
                InfoBar.success(
                    title="成功",
                    content=f"已添加依赖任务: {task_title}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000
                )
            
            add_btn.clicked.connect(on_add_clicked)
            
            # 双击条目快速添加
            def on_item_double_clicked(item):
                # 如果双击的是分组项，则不处理
                if item.parent() is None:
                    return
                
                # 选中该项并触发添加按钮
                tree_widget.setCurrentItem(item)
                on_add_clicked()
            
            tree_widget.itemDoubleClicked.connect(on_item_double_clicked)
            
            # 显示对话框
            dep_dialog.exec_()
    
    def remove_dependency(self):
        """移除依赖任务"""
        selected_items = self.dependency_list.selectedItems()
        if not selected_items:
            InfoBar.info(
                title="提示",
                content="请先选择要删除的依赖关系",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
            return
        
        # 确认是否删除
        from qfluentwidgets import MessageBox
        
        box = MessageBox(
            "确认删除",
            "确定要删除选中的依赖关系吗？",
            self
        )
        
        if box.exec_():
            # 删除选中的依赖
            for item in selected_items:
                row = self.dependency_list.row(item)
                task_title = item.text()
                self.dependency_list.takeItem(row)
                
                InfoBar.success(
                    title="成功",
                    content=f"已移除依赖关系: {task_title}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000
                )
    
    def fill_data_if_edit(self):
        """如果是编辑模式，填充已有数据"""
        try:
            if not self.task_data:
                return
                
            # 基本信息选项卡
            self.title_edit.setText(self.task_data.get("title", ""))
            self.desc_edit.setText(self.task_data.get("description", ""))
            
            # 设置悬浮提示显示任务详情摘要
            task_info = f"""
            <div style='font-family: Microsoft YaHei;'>
                <h3 style='margin: 2px;'>{self.task_data.get("title", "")}</h3>
                <hr style='margin: 2px;'>
                <p><b>描述:</b> {self.task_data.get("description", "无")[:100]}{'...' if len(self.task_data.get("description", "")) > 100 else ''}</p>
                <p><b>优先级:</b> {self.task_data.get("priority", "中")}</p>
                <p><b>紧急程度:</b> {self.task_data.get("urgency", 5)}/10</p>
                <p><b>状态:</b> {"已完成" if self.task_data.get("completed", False) else "进行中"}</p>
            </div>
            """
            self.title_edit.setToolTip(task_info)
            self.desc_edit.setToolTip(task_info)
            
            # 设置开始时间
            start_dt = self.task_data.get("start_time")
            if start_dt:
                try:
                    # 将datetime转换为QDate和QTime
                    start_qdate = QDate(start_dt.year, start_dt.month, start_dt.day)
                    start_qtime = QTime(start_dt.hour, start_dt.minute, start_dt.second)
                    
                    self.start_date_picker.setDate(start_qdate)
                    self.start_time_edit.setTime(start_qtime)
                except Exception as e:
                    print(f"设置开始时间出错: {e}")
                    # 设置为当前日期时间
                    self.start_date_picker.setDate(QDate.currentDate())
                    self.start_time_edit.setTime(QTime.currentTime())
            
            # 设置结束时间
            end_dt = self.task_data.get("end_time")
            if end_dt:
                try:
                    # 将datetime转换为QDate和QTime
                    end_qdate = QDate(end_dt.year, end_dt.month, end_dt.day)
                    end_qtime = QTime(end_dt.hour, end_dt.minute, end_dt.second)
                    
                    self.end_date_picker.setDate(end_qdate)
                    self.end_time_edit.setTime(end_qtime)
                except Exception as e:
                    print(f"设置结束时间出错: {e}")
                    # 设置为当前日期时间加一天
                    self.end_date_picker.setDate(QDate.currentDate().addDays(1))
                    self.end_time_edit.setTime(QTime.currentTime())
            
            # 为时间选择器添加悬浮提示
            time_info = f"""
            <div style='font-family: Microsoft YaHei;'>
                <p><b>开始时间:</b> {start_dt.strftime("%Y-%m-%d %H:%M:%S") if start_dt else "未设置"}</p>
                <p><b>结束时间:</b> {end_dt.strftime("%Y-%m-%d %H:%M:%S") if end_dt else "未设置"}</p>
                <p><b>持续时间:</b> {(end_dt - start_dt).days} 天 {(end_dt - start_dt).seconds // 3600} 小时 {((end_dt - start_dt).seconds % 3600) // 60} 分钟</p>
            </div>
            """ if start_dt and end_dt else "请设置任务时间"
            
            self.start_date_picker.setToolTip(time_info)
            self.start_time_edit.setToolTip(time_info)
            self.end_date_picker.setToolTip(time_info)
            self.end_time_edit.setToolTip(time_info)
            
            # 设置优先级
            priority = self.task_data.get("priority", "中")
            index = self.priority_combo.findText(priority)
            if index >= 0:
                self.priority_combo.setCurrentIndex(index)
                self.update_priority_display(index)
            
            # 设置紧急程度
            urgency = self.task_data.get("urgency", 5)
            self.urgency_slider.setValue(urgency)
            self.update_urgency_display(urgency)
            
            # 为优先级和紧急程度添加悬浮提示
            priority_info = f"""
            <div style='font-family: Microsoft YaHei;'>
                <p><b>优先级:</b> {priority}</p>
                <p><b>紧急程度:</b> {urgency}/10</p>
                <p style='color:#666;font-size:90%;'>优先级表示任务的重要性，紧急程度表示时间紧迫性</p>
            </div>
            """
            self.priority_combo.setToolTip(priority_info)
            self.urgency_slider.setToolTip(priority_info)
            
            # 设置完成状态
            self.completed_check.setChecked(self.task_data.get("completed", False))
            
            # 设置提醒
            self.remind_check.setChecked(self.task_data.get("remind", True))
            self.remind_advance_spin.setValue(self.task_data.get("remind_advance", 15))
            
            # 设置重复
            self.recurrence_check.setChecked(self.task_data.get("recurrence", False))
            recurrence_type = self.task_data.get("recurrence_type", "每天")
            index = self.recurrence_combo.findText(recurrence_type)
            if index >= 0:
                self.recurrence_combo.setCurrentIndex(index)
            
            # 设置人员
            if self.config_manager:
                assigned_people = self.task_data.get("assigned_people", [])
                
                # 获取人员名称列表用于提示
                people_names = []
                
                for i in range(self.people_list.count()):
                    item = self.people_list.item(i)
                    person_id = item.data(Qt.UserRole)
                    if person_id in assigned_people:
                        item.setSelected(True)
                        people_names.append(item.text())
                
                # 为人员列表添加综合悬浮提示
                if people_names:
                    people_info = f"""
                    <div style='font-family: Microsoft YaHei;'>
                        <h3 style='margin: 2px;'>负责人员</h3>
                        <hr style='margin: 2px;'>
                        <ul style='margin-left: 15px; padding-left: 0px;'>
                            {"".join(f"<li>{name}</li>" for name in people_names)}
                        </ul>
                        <p style='color:#666;font-size:90%;'>共 {len(people_names)} 名人员参与此任务</p>
                    </div>
                    """
                    self.people_list.setToolTip(people_info)
            
            # 设置地点
            if self.config_manager:
                location_id = self.task_data.get("location_id")
                location_name = "无指定地点"
                
                if location_id:
                    # 在地点列表中查找并选中
                    for i in range(self.location_list.count()):
                        item = self.location_list.item(i)
                        if item.data(Qt.UserRole) == location_id:
                            self.location_list.setCurrentItem(item)
                            location_name = item.text()
                            break
                else:
                    # 如果没有指定地点，选中"无指定地点"选项
                    self.location_list.setCurrentRow(0)
                
                # 为地点列表添加悬浮提示
                location_info = f"""
                <div style='font-family: Microsoft YaHei;'>
                    <h3 style='margin: 2px;'>任务地点</h3>
                    <hr style='margin: 2px;'>
                    <p><b>当前选择:</b> {location_name}</p>
                </div>
                """
                self.location_list.setToolTip(location_info)
            
            # 设置依赖关系
            dependencies = self.task_data.get("dependencies", [])
            if dependencies and self.scheduler_manager:
                self.dependency_list.clear()
                dep_names = []
                
                for dep_id in dependencies:
                    dep_task = self.scheduler_manager.get_task(dep_id)
                    if dep_task:
                        item = QListWidgetItem(dep_task.get("title", "未命名任务"))
                        item.setData(Qt.UserRole, dep_id)
                        
                        # 为依赖任务添加悬浮提示
                        dep_info = f"""
                        <div style='font-family: Microsoft YaHei;'>
                            <h3 style='margin: 2px;'>{dep_task.get("title", "未命名任务")}</h3>
                            <hr style='margin: 2px;'>
                            <p><b>ID:</b> {dep_id[:8]}...</p>
                            <p><b>优先级:</b> {dep_task.get("priority", "中")}</p>
                            <p><b>状态:</b> {"已完成" if dep_task.get("completed", False) else "进行中"}</p>
                            <p style='color:#666;font-size:90%;'>此任务需要在"{dep_task.get("title", "未命名任务")}"完成后才能开始</p>
                        </div>
                        """
                        item.setToolTip(dep_info)
                        
                        self.dependency_list.addItem(item)
                        dep_names.append(dep_task.get("title", "未命名任务"))
                
                # 为依赖列表添加综合悬浮提示
                if dep_names:
                    deps_info = f"""
                    <div style='font-family: Microsoft YaHei;'>
                        <h3 style='margin: 2px;'>任务依赖关系</h3>
                        <hr style='margin: 2px;'>
                        <p>此任务依赖于以下任务完成:</p>
                        <ul style='margin-left: 15px; padding-left: 0px;'>
                            {"".join(f"<li>{name}</li>" for name in dep_names)}
                        </ul>
                    </div>
                    """
                    self.dependency_list.setToolTip(deps_info)
            
            # 更新信息显示
            self.update_info_display()
        except Exception as e:
            print(f"填充任务数据出错: {e}")
            # 发生错误时使用默认值
    
    def save_task(self):
        """保存任务数据"""
        try:
            # 获取表单数据
            title = self.title_edit.text().strip()
            description = self.desc_edit.toPlainText().strip()
            
            if not title:
                InfoBar.error(
                    title="错误",
                    content="任务标题不能为空",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            # 构建开始时间和结束时间
            start_date = self.start_date_picker.getDate()
            start_time = self.start_time_edit.time()
            start_dt = datetime(
                start_date.year(), start_date.month(), start_date.day(),
                start_time.hour(), start_time.minute(), start_time.second()
            )
            
            end_date = self.end_date_picker.getDate()
            end_time = self.end_time_edit.time()
            end_dt = datetime(
                end_date.year(), end_date.month(), end_date.day(),
                end_time.hour(), end_time.minute(), end_time.second()
            )
            
            # 检查结束时间是否晚于开始时间
            if end_dt <= start_dt:
                InfoBar.error(
                    title="错误",
                    content="结束时间必须晚于开始时间",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                return
            
            # 获取选中的人员
            assigned_people = []
            for item in self.people_list.selectedItems():
                person_id = item.data(Qt.UserRole)
                if person_id:
                    assigned_people.append(person_id)
            
            # 获取选中的地点
            location_id = None
            selected_location_items = self.location_list.selectedItems()
            if selected_location_items:
                location_id = selected_location_items[0].data(Qt.UserRole)
            
            # 获取依赖关系
            dependencies = []
            for i in range(self.dependency_list.count()):
                item = self.dependency_list.item(i)
                dep_id = item.data(Qt.UserRole)
                if dep_id:
                    dependencies.append(dep_id)
            
            # 创建任务数据
            task_data = {
                "title": title,
                "description": description,
                "start_time": start_dt,
                "end_time": end_dt,
                "priority": self.priority_combo.currentText(),
                "urgency": self.urgency_slider.value(),
                "completed": self.completed_check.isChecked(),
                "remind": self.remind_check.isChecked(),
                "remind_advance": self.remind_advance_spin.value(),
                "recurrence": self.recurrence_check.isChecked(),
                "recurrence_type": self.recurrence_combo.currentText(),
                "assigned_people": assigned_people,
                "location_id": location_id,
                "dependencies": dependencies
            }
            
            # 如果是编辑模式，保留ID和创建时间
            if self.task_data:
                task_data["id"] = self.task_data.get("id")
                task_data["created_at"] = self.task_data.get("created_at")
                
                # 保留子任务列表
                if "subtasks" in self.task_data:
                    task_data["subtasks"] = self.task_data["subtasks"]
                
                # 如果完成状态变更，记录完成时间
                old_completed = self.task_data.get("completed", False)
                new_completed = task_data["completed"]
                
                if old_completed != new_completed:
                    if new_completed:
                        task_data["completion_time"] = datetime.now()
                    else:
                        task_data.pop("completion_time", None)
            
            # 保存任务
            if self.scheduler_manager:
                result = False
                task_id = None
                
                if "id" in task_data:
                    # 更新任务
                    result = self.scheduler_manager.update_task(task_data)
                    task_id = task_data["id"]
                    
                    if result:
                        InfoBar.success(
                            title="成功",
                            content="任务已更新",
                            parent=self.parent(),
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                else:
                    # 添加新任务
                    task_id = self.scheduler_manager.add_task(task_data)
                    result = task_id is not None
                    
                    if result:
                        InfoBar.success(
                            title="成功",
                            content="任务已添加",
                            parent=self.parent(),
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                
                # 保存临时子任务
                if result and task_id and self.temp_subtasks and self.subtask_manager:
                    success_count = 0
                    error_count = 0
                    
                    for temp_subtask in self.temp_subtasks:
                        # 删除临时ID
                        if 'temp_id' in temp_subtask:
                            del temp_subtask['temp_id']
                        
                        # 添加子任务
                        subtask_id = self.subtask_manager.add_subtask(task_id, temp_subtask)
                        if subtask_id:
                            success_count += 1
                        else:
                            error_count += 1
                    
                    if success_count > 0:
                        InfoBar.success(
                            title="成功",
                            content=f"已保存 {success_count} 个临时子任务",
                            parent=self.parent(),
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000
                        )
                    
                    if error_count > 0:
                        InfoBar.warning(
                            title="警告",
                            content=f"{error_count} 个临时子任务保存失败",
                            parent=self.parent(),
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=3000
                        )
                    
                    # 清空临时子任务列表
                    self.temp_subtasks = []
                
                if result:
                    self.accept()
                else:
                    InfoBar.error(
                        title="错误",
                        content="保存任务失败",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
        except Exception as e:
            print(f"保存任务时出错: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title="错误",
                content=f"保存任务时出错: {e}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            ) 
    
    def on_priority_changed(self, index):
        """处理优先级变更，自动调整紧急程度建议值
        
        参数:
            index: 优先级索引(0=低, 1=中, 2=高, 3=紧急)
        """
        # 根据优先级自动调整紧急程度建议值
        # 仅当用户没有手动调整过紧急程度时执行
        suggested_urgency = {
            0: 2,    # 低优先级 -> 紧急程度2
            1: 5,    # 中优先级 -> 紧急程度5
            2: 7,    # 高优先级 -> 紧急程度7
            3: 9,    # 紧急优先级 -> 紧急程度9
        }.get(index, 5)
        
        # 显示紧急程度调整建议
        InfoBar.info(
            title="紧急程度建议",
            content=f"根据优先级，建议将紧急程度调整为{suggested_urgency}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )