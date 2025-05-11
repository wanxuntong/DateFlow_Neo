#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
流程图视图模块
以流程图方式展示任务之间的依赖关系
"""

import math
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QGraphicsScene, QGraphicsView,
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsPathItem, QGraphicsProxyWidget,
    QMenu, QComboBox
)

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, IconWidget, 
    ComboBox, LineEdit, ToolButton, CheckBox,
    InfoBar, InfoBarPosition
)

from ui.task_dialog import TaskDialog

class FlowTaskNode(QGraphicsRectItem):
    """流程图中的任务节点"""
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setRect(0, 0, 200, 80)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        
        # 根据优先级设置颜色
        priority = task_data.get("priority", "中")
        if priority == "低":
            self.bg_color = QColor(200, 230, 201)
            self.border_color = QColor(76, 175, 80)
        elif priority == "中":
            self.bg_color = QColor(187, 222, 251)
            self.border_color = QColor(33, 150, 243)
        elif priority == "高":
            self.bg_color = QColor(255, 224, 178)
            self.border_color = QColor(255, 152, 0)
        else:  # 紧急
            self.bg_color = QColor(255, 205, 210)
            self.border_color = QColor(244, 67, 54)
            
        # 创建文本项
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(task_data.get("title", "无标题"))
        self.title_item.setPos(10, 5)
        self.title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        # 创建时间项
        start_time = task_data.get("start_time")
        end_time = task_data.get("end_time")
        time_text = f"开始: {start_time.strftime('%Y-%m-%d %H:%M')}\n结束: {end_time.strftime('%Y-%m-%d %H:%M')}"
        
        self.time_item = QGraphicsTextItem(self)
        self.time_item.setPlainText(time_text)
        self.time_item.setPos(10, 30)
        self.time_item.setFont(QFont("Microsoft YaHei", 8))
        
        # 记录连接点
        self.source_point = QPointF(0, 40)
        self.target_point = QPointF(200, 40)
        
    def paint(self, painter, option, widget):
        """绘制任务节点"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.setBrush(QBrush(self.bg_color))
        pen = QPen(self.border_color, 2)
        painter.setPen(pen)
        
        if self.isSelected():
            # 选中状态使用虚线
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
        painter.drawRoundedRect(self.rect(), 5, 5)
            
    def mouseDoubleClickEvent(self, event):
        """双击处理：打开任务编辑对话框"""
        # 寻找主窗口和流程图视图
        window = self.window()
        
        # 正确获取scheduler_manager
        flow_view = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'scheduler_manager'):
                flow_view = parent
                break
            parent = parent.parent()
        
        if flow_view and hasattr(flow_view, 'scheduler_manager'):
            dialog = TaskDialog(window, flow_view.scheduler_manager, self.task_data)
            if dialog.exec_():
                # 编辑成功后刷新视图
                flow_view.refresh()
        else:
            # 回退方案：直接从父视图获取scheduler_manager
            from ui.main_window import SchedulerMainWindow
            if isinstance(window, SchedulerMainWindow):
                dialog = TaskDialog(window, window.scheduler_manager, self.task_data)
                if dialog.exec_():
                    # 找到FlowView并刷新
                    flow_view = window.findChild(QWidget, "flowView")
                    if flow_view and hasattr(flow_view, 'refresh'):
                        flow_view.refresh()

class FlowTaskArrow(QGraphicsPathItem):
    """流程图中连接任务的箭头"""
    
    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        self.setZValue(-1)  # 确保箭头在节点下方显示
        self.update_path()
        
    def update_path(self):
        """更新箭头路径"""
        # 计算起点和终点位置
        source_pos = self.start_node.mapToScene(self.start_node.target_point)
        target_pos = self.end_node.mapToScene(self.end_node.source_point)
        
        # 创建路径
        path = QPainterPath()
        path.moveTo(source_pos)
        
        # 计算控制点
        dx = target_pos.x() - source_pos.x()
        control1 = QPointF(source_pos.x() + dx * 0.4, source_pos.y())
        control2 = QPointF(target_pos.x() - dx * 0.4, target_pos.y())
        
        # 绘制贝塞尔曲线
        path.cubicTo(control1, control2, target_pos)
        
        # 添加箭头
        angle = math.atan2(target_pos.y() - control2.y(), target_pos.x() - control2.x())
        arrow_size = 10
        
        arrow_p1 = target_pos - QPointF(math.cos(angle + math.pi/6) * arrow_size,
                                       math.sin(angle + math.pi/6) * arrow_size)
        arrow_p2 = target_pos - QPointF(math.cos(angle - math.pi/6) * arrow_size,
                                       math.sin(angle - math.pi/6) * arrow_size)
        
        path.moveTo(target_pos)
        path.lineTo(arrow_p1)
        path.moveTo(target_pos)
        path.lineTo(arrow_p2)
        
        self.setPath(path)
        
    def paint(self, painter, option, widget):
        """绘制箭头"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置线条样式
        pen = QPen(QColor(100, 100, 100), 2)
        painter.setPen(pen)
        
        # 绘制路径
        painter.drawPath(self.path())

class FlowGraphView(QGraphicsView):
    """流程图绘图视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))
        
        # 设置场景
        self.setScene(QGraphicsScene(self))
        
        # 缩放因子
        self.zoom_factor = 1.2
        
    def wheelEvent(self, event):
        """处理鼠标滚轮事件，实现缩放"""
        if event.modifiers() & Qt.ControlModifier:
            # 控制键加滚轮实现缩放
            if event.angleDelta().y() > 0:
                # 放大
                self.scale(self.zoom_factor, self.zoom_factor)
            else:
                # 缩小
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            event.accept()
        else:
            # 正常滚动
            super().wheelEvent(event)

class FlowView(ScrollArea):
    """流程图视图"""
    
    def __init__(self, scheduler_manager, parent=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.is_updating = False  # 添加标志以防止递归
        
        # 初始化界面
        self.init_ui()
        
        # 加载任务
        self.load_tasks()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setObjectName("flowView")
        self.setWidgetResizable(True)
        
        # 创建主窗口
        self.main_widget = QWidget(self)
        self.setWidget(self.main_widget)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # 添加顶部工具栏
        self.toolbar_layout = QHBoxLayout()
        
        # 添加布局类型选择
        self.layout_label = QLabel("布局方式:", self)
        self.toolbar_layout.addWidget(self.layout_label)
        
        self.layout_combo = ComboBox(self)
        self.layout_combo.addItems(["层次布局", "水平布局", "垂直布局"])
        self.layout_combo.setCurrentIndex(0)
        self.layout_combo.currentIndexChanged.connect(self.on_layout_changed)
        self.toolbar_layout.addWidget(self.layout_combo)
        
        # 添加间隔
        self.toolbar_layout.addStretch(1)
        
        # 添加缩放控制
        self.zoom_out_btn = ToolButton(FluentIcon.REMOVE, self)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.toolbar_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_in_btn = ToolButton(FluentIcon.ADD, self)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.toolbar_layout.addWidget(self.zoom_in_btn)
        
        self.reset_view_btn = ToolButton(FluentIcon.SEARCH, self)
        self.reset_view_btn.clicked.connect(self.reset_view)
        self.toolbar_layout.addWidget(self.reset_view_btn)
        
        self.main_layout.addLayout(self.toolbar_layout)
        
        # 添加分隔线
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(line)
        
        # 创建流程图视图
        self.graph_view = FlowGraphView(self)
        self.main_layout.addWidget(self.graph_view)
    
    def load_tasks(self):
        """加载任务并创建流程图"""
        if self.is_updating:  # 如果已经在更新中，则直接返回
            return
            
        self.is_updating = True  # 设置更新标志
        
        try:
            # 清除旧的图形项
            self.graph_view.scene().clear()
            
            # 获取所有任务
            tasks = self.scheduler_manager.get_all_tasks()
            
            if not tasks:
                # 如果没有任务，显示提示
                text_item = self.graph_view.scene().addText("没有任务数据，请先添加任务")
                text_item.setFont(QFont("Microsoft YaHei", 12))
                text_item.setPos(0, 0)
                return
                
            # 根据开始时间排序任务
            tasks.sort(key=lambda x: x["start_time"])
            
            # 创建节点
            nodes = {}
            for task in tasks:
                node = FlowTaskNode(task)
                self.graph_view.scene().addItem(node)
                nodes[task.get("id")] = node
                
            # 按照时间顺序布局节点并添加连接线
            # 这里使用简化的布局算法，实际中可以使用更复杂的布局算法
            layout_type = self.layout_combo.currentText()
            self.apply_layout(nodes, tasks, layout_type)
            
            # 创建依赖关系箭头（简化：按照时间顺序连接任务）
            for i in range(len(tasks) - 1):
                current_node = nodes[tasks[i].get("id")]
                next_node = nodes[tasks[i + 1].get("id")]
                
                arrow = FlowTaskArrow(current_node, next_node)
                self.graph_view.scene().addItem(arrow)
            
            # 调整视图
            self.graph_view.setSceneRect(self.graph_view.scene().itemsBoundingRect())
            self.graph_view.fitInView(self.graph_view.scene().sceneRect(), Qt.KeepAspectRatio)
        finally:
            self.is_updating = False  # 清除更新标志
    
    def apply_layout(self, nodes, tasks, layout_type):
        """应用不同的布局算法"""
        if layout_type == "水平布局":
            # 水平布局: 任务按开始时间从左到右排列
            spacing_x = 250
            y = 50
            
            for i, task in enumerate(tasks):
                node = nodes[task.get("id")]
                node.setPos(i * spacing_x, y)
                
        elif layout_type == "垂直布局":
            # 垂直布局: 任务按开始时间从上到下排列
            x = 50
            spacing_y = 120
            
            for i, task in enumerate(tasks):
                node = nodes[task.get("id")]
                node.setPos(x, i * spacing_y)
                
        else:  # 层次布局
            # 层次布局: 按优先级和时间进行分层布局
            priority_levels = {"紧急": 0, "高": 1, "中": 2, "低": 3}
            
            # 先按优先级分组
            priority_groups = {}
            for task in tasks:
                priority = task.get("priority", "中")
                level = priority_levels.get(priority, 2)
                if level not in priority_groups:
                    priority_groups[level] = []
                priority_groups[level].append(task)
            
            # 计算每组中的位置
            x = 50
            spacing_y = 120
            for level in sorted(priority_groups.keys()):
                group_tasks = priority_groups[level]
                group_tasks.sort(key=lambda x: x["start_time"])
                
                # 计算当前层的垂直起点
                y = 50 + level * spacing_y * 1.5
                
                # 在当前层内水平排列
                spacing_x = 250
                for i, task in enumerate(group_tasks):
                    node = nodes[task.get("id")]
                    node.setPos(i * spacing_x, y)
    
    def on_layout_changed(self, index):
        """布局方式变化事件处理"""
        if self.is_updating:
            return
        self.load_tasks()
    
    def zoom_in(self):
        """放大视图"""
        if self.is_updating:
            return
        self.graph_view.scale(1.2, 1.2)
    
    def zoom_out(self):
        """缩小视图"""
        if self.is_updating:
            return
        self.graph_view.scale(1/1.2, 1/1.2)
    
    def reset_view(self):
        """重置视图"""
        if self.is_updating:
            return
        self.graph_view.resetTransform()
        self.graph_view.fitInView(self.graph_view.scene().sceneRect(), Qt.KeepAspectRatio)
    
    def refresh(self):
        """刷新视图"""
        if not self.is_updating:
            self.load_tasks()

