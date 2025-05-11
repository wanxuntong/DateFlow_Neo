#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调度管理器模块
负责任务的管理、持久化存储和提醒功能
"""

import os
import json
import time
import uuid
from datetime import datetime, timedelta

class SchedulerManager:
    """调度管理器类，负责任务的管理和存储"""
    
    def __init__(self, data_file=None, plugin_manager=None):
        """
        初始化调度管理器
        
        参数:
            data_file: 数据文件路径，默认为None，将使用默认路径
            plugin_manager: 插件管理器实例，用于触发任务相关事件
        """
        # 保存插件管理器引用
        self.plugin_manager = plugin_manager
        
        # 设置数据文件路径
        if data_file is None:
            # 默认数据文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, 'data', 'tasks.json')
        else:
            self.data_file = data_file
            
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # 加载任务数据
        self.tasks = []
        self.load_tasks()
        
        # 检查任务到期状态
        self.check_overdue_tasks()
        
        # 自动根据时间更新任务状态
        self.auto_update_task_status()
        
        # 启动定时器，定期检查任务状态
        self.setup_timer()
    
    def load_tasks(self):
        """从文件加载任务
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 如果文件不存在，创建空文件
            if not os.path.exists(self.data_file):
                print(f"任务数据文件不存在，创建新文件: {self.data_file}")
                # 确保目录存在
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    f.write('[]')  # 写入空列表
                self.tasks = []
                return True
            
            # 读取任务文件
            with open(self.data_file, 'r', encoding='utf-8') as f:
                try:
                    loaded_data = json.load(f)
                    
                    # 确认加载的数据是列表
                    if not isinstance(loaded_data, list):
                        print(f"警告：加载的数据不是列表格式，而是 {type(loaded_data)}")
                        if isinstance(loaded_data, dict):
                            # 如果是旧格式（字典），转换为列表
                            print("将旧格式(字典)转换为列表格式")
                            loaded_data = list(loaded_data.values())
                        else:
                            print("无法处理的数据格式，创建空列表")
                            loaded_data = []
                    
                    # 处理任务数据
                    self.tasks = []
                    for task in loaded_data:
                        if not isinstance(task, dict):
                            print(f"警告：跳过非字典任务: {task}")
                            continue
                            
                        # 转换ISO格式字符串为datetime对象
                        if 'start_time' in task and isinstance(task['start_time'], str):
                            try:
                                task['start_time'] = datetime.fromisoformat(task['start_time'])
                            except ValueError as e:
                                print(f"解析开始时间出错: {e}, 使用当前时间")
                                task['start_time'] = datetime.now()
                                
                        if 'end_time' in task and isinstance(task['end_time'], str):
                            try:
                                task['end_time'] = datetime.fromisoformat(task['end_time'])
                            except ValueError as e:
                                print(f"解析结束时间出错: {e}, 使用当前时间")
                                task['end_time'] = datetime.now()
                                
                        if 'created_at' in task and isinstance(task['created_at'], str):
                            try:
                                task['created_at'] = datetime.fromisoformat(task['created_at'])
                            except ValueError as e:
                                print(f"解析创建时间出错: {e}, 使用当前时间")
                                task['created_at'] = datetime.now()
                        
                        # 确保任务有ID
                        if 'id' not in task or not task['id']:
                            import uuid
                            task['id'] = str(uuid.uuid4())
                            print(f"为缺少ID的任务生成新ID: {task['id']}")
                        
                        self.tasks.append(task)
                        
                    print(f"成功加载 {len(self.tasks)} 个任务")
                    
                    # 自动更新任务状态（基于当前时间）
                    self.auto_update_task_status()
                    
                    return True
                except json.JSONDecodeError as e:
                    print(f"解析JSON失败: {e}")
                    # 如果文件是空的或格式无效，返回空列表
                    self.tasks = []
                    return False
        except Exception as e:
            print(f"加载任务时出错: {e}")
            import traceback
            traceback.print_exc()
            self.tasks = []
            return False
    
    def save_tasks(self):
        """保存任务到文件
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 确保json模块已导入
            import json
            
            # 检查任务列表中是否有非字典对象，并尝试修复
            for i, task in enumerate(self.tasks):
                if not isinstance(task, dict):
                    print(f"警告：发现非字典任务对象，类型={type(task)}")
                    try:
                        if isinstance(task, str):
                            self.tasks[i] = json.loads(task)
                            print(f"成功将字符串任务转换为字典: {self.tasks[i]}")
                        else:
                            # 如果不是字符串也不是字典，移除这个任务
                            print(f"移除无效任务: {task}")
                            self.tasks[i] = None
                    except Exception as e:
                        print(f"无法修复任务数据: {e}, 任务: {task}")
                        self.tasks[i] = None
            
            # 过滤掉None值
            self.tasks = [task for task in self.tasks if task is not None]

            # 保存任务到文件
            with open(self.data_file, 'w', encoding='utf-8') as f:
                # 将日期时间对象转换为ISO格式字符串
                serializable_tasks = []
                
                for task in self.tasks:
                    if not isinstance(task, dict):
                        print(f"警告：跳过非字典任务: {task}")
                        continue
                        
                    task_copy = task.copy()
                    
                    # 遍历所有字段，转换日期时间对象
                    for key, value in list(task_copy.items()):
                        # 转换datetime对象为ISO格式字符串
                        if isinstance(value, datetime):
                            try:
                                task_copy[key] = value.isoformat()
                            except Exception as e:
                                print(f"转换日期时间出错: {e}, 使用字符串表示")
                                task_copy[key] = str(value)
                        # 验证所有字符串字段是否为UTF-8
                        elif isinstance(value, str):
                            try:
                                # 尝试编码为UTF-8以验证
                                value.encode('utf-8')
                            except UnicodeEncodeError:
                                print(f"警告：字段 {key} 包含无效的UTF-8字符，将替换为空字符串")
                                task_copy[key] = ""
                    
                    serializable_tasks.append(task_copy)
                
                # 写入文件
                json.dump(serializable_tasks, f, ensure_ascii=False, indent=2)
                print(f"成功保存 {len(serializable_tasks)} 个任务到 {self.data_file}")
                
            return True
        except Exception as e:
            print(f"保存任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_task(self, task_data):
        """添加新任务
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            str: 新任务的ID，失败返回None
        """
        try:
            # 生成任务ID
            import uuid
            task_id = str(uuid.uuid4())
            
            # 确保task_data是字典
            if not isinstance(task_data, dict):
                print(f"任务数据必须是字典类型，而不是 {type(task_data)}")
                return None
            
            # 设置任务ID和创建时间
            task_data['id'] = task_id
            task_data['created_at'] = datetime.now()
            
            # 添加到任务列表
            self.tasks.append(task_data)
            
            # 保存到文件
            if self.save_tasks():
                print(f"成功添加任务: {task_id}")
                
                # 如果有插件管理器，触发任务创建事件
                if self.plugin_manager:
                    self.plugin_manager.dispatch_event(
                        self.plugin_manager.EVENT_TASK_CREATED,
                        task_data
                    )
                    
                return task_id
            else:
                print("保存任务失败")
                return None
        except Exception as e:
            print(f"添加任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_task(self, task_data):
        """更新任务
        
        Args:
            task_data: 要更新的任务数据
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            # 获取任务ID
            task_id = task_data.get("id")
            if not task_id:
                print("无效的任务ID")
                return False
                
            # 用新数据更新任务
            found = False
            for i, task in enumerate(self.tasks):
                # 确保task是字典，而不是字符串
                if isinstance(task, str):
                    try:
                        # 尝试解析字符串为字典
                        import json
                        self.tasks[i] = json.loads(task)
                        task = self.tasks[i]
                        print(f"将字符串任务转换为字典: {task}")
                    except Exception as e:
                        print(f"无法解析任务字符串: {e}")
                        continue
                
                # 现在检查ID是否匹配
                if task.get("id") == task_id:
                    # 保存旧的任务数据用于比较
                    old_task = task.copy()
                    
                    # 检查状态是否变化
                    old_status = old_task.get("status", "未开始")
                    new_status = task_data.get("status", "未开始")
                    status_changed = old_status != new_status
                    
                    # 更新任务数据
                    self.tasks[i] = task_data
                    
                    # 保存到文件
                    self.save_tasks()
                    
                    # 检查时间是否发生变化
                    time_changed = (old_task.get("start_time") != task_data.get("start_time") or
                                   old_task.get("end_time") != task_data.get("end_time"))
                    
                    # 广播任务变更通知到所有视图
                    self.notify_task_update(task_data, time_changed)
                    
                    # 如果插件管理器存在且状态发生变化，触发状态相关事件
                    if self.plugin_manager and status_changed:
                        # 任务暂停事件
                        if new_status == "已暂停" and old_status != "已暂停":
                            self.plugin_manager.dispatch_event(
                                self.plugin_manager.EVENT_TASK_PAUSED, 
                                task_data
                            )
                        # 任务恢复事件
                        elif old_status == "已暂停" and new_status != "已暂停":
                            self.plugin_manager.dispatch_event(
                                self.plugin_manager.EVENT_TASK_RESUMED, 
                                task_data
                            )
                    
                    found = True
                    return True
            
            if not found:
                print(f"找不到ID为 {task_id} 的任务")
                # 打印所有任务的ID和类型，用于调试
                for i, task in enumerate(self.tasks):
                    if isinstance(task, dict):
                        print(f"任务 {i}: ID={task.get('id')}, 类型={type(task)}")
                    else:
                        print(f"任务 {i}: 类型={type(task)}, 值={task}")
            return False
        except Exception as e:
            print(f"更新任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def notify_task_update(self, task_data, time_changed=False):
        """通知所有视图任务已更新
        
        Args:
            task_data: 更新后的任务数据
            time_changed: 时间是否变更
        """
        # 从主窗口查找所有相关视图
        try:
            # 导入正确的主窗口类
            from ui.main_window import SchedulerMainWindow
            
            # 尝试获取主窗口实例
            import sys
            app = sys.modules.get('PyQt5.QtWidgets').QApplication.instance()
            if not app:
                print("无法获取QApplication实例")
                return
            
            # 更新所有主窗口中的视图
            for window in app.topLevelWidgets():
                if isinstance(window, SchedulerMainWindow):
                    # 如果时间变更了，我们需要更新日历视图
                    if time_changed:
                        calendar_view = window.find_calendar_view()
                        if calendar_view:
                            calendar_view.refresh()
                    
                    # 检查是否需要刷新甘特图(虽然甘特图已在自己的代码中处理更新)
                    gantt_view = window.find_gantt_view()
                    if gantt_view:
                        # 甘特图视图在update_task方法中已经自行更新了，无需再次调用
                        pass
                    
        except Exception as e:
            print(f"通知视图更新失败: {e}")
            print("这是一个非关键错误，任务数据已保存")
    
    def delete_task(self, task_id):
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            # 查找任务
            task_to_delete = None
            for task in self.tasks:
                if isinstance(task, dict) and task.get("id") == task_id:
                    task_to_delete = task
                    break
            
            if not task_to_delete:
                print(f"找不到ID为 {task_id} 的任务")
                return False
            
            # 从列表中删除任务
            self.tasks.remove(task_to_delete)
            
            # 保存到文件
            if self.save_tasks():
                print(f"成功删除任务: {task_id}")
                
                # 如果有插件管理器，触发任务删除事件
                if self.plugin_manager:
                    self.plugin_manager.dispatch_event(
                        self.plugin_manager.EVENT_TASK_DELETED,
                        task_to_delete
                    )
                    
                return True
            else:
                print("保存任务失败")
                return False
        except Exception as e:
            print(f"删除任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_task(self, task_id):
        """获取指定ID的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务数据，如果不存在则返回None
        """
        try:
            # 在任务列表中查找匹配的任务
            for task in self.tasks:
                if isinstance(task, dict) and task.get('id') == task_id:
                    return task
            
            # 如果任务不存在
            print(f"找不到任务: {task_id}")
            return None
        except Exception as e:
            print(f"获取任务时出错: {e}")
            return None
    
    def get_all_tasks(self):
        """获取所有任务
        
        Returns:
            list: 所有任务的列表
        """
        # 确保所有任务都是字典格式
        valid_tasks = []
        for task in self.tasks:
            if isinstance(task, dict):
                valid_tasks.append(task)
            else:
                print(f"跳过无效任务: {task}")
        
        return valid_tasks
    
    def get_tasks_by_date(self, date):
        """获取指定日期的任务
        
        Args:
            date: 日期对象或日期字符串
            
        Returns:
            list: 指定日期的任务列表
        """
        # 确保日期是datetime.date对象
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date).date()
            except ValueError:
                print(f"无效的日期格式: {date}")
                return []
        elif isinstance(date, datetime):
            date = date.date()
        
        # 查找日期范围内的任务
        result = []
        for task in self.get_all_tasks():
            start_time = task.get('start_time')
            end_time = task.get('end_time')
            
            # 确保时间字段是datetime对象
            if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                print(f"任务时间格式错误，跳过: {task}")
                continue
            
            # 检查任务日期是否包含指定日期
            task_start_date = start_time.date()
            task_end_date = end_time.date()
            
            if task_start_date <= date <= task_end_date:
                result.append(task)
        
        return result
    
    def get_tasks_by_date_range(self, start_date, end_date):
        """获取指定日期范围内的任务
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 日期范围内的任务列表
        """
        # 确保日期是datetime.date对象
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date).date()
            except ValueError:
                print(f"无效的开始日期格式: {start_date}")
                return []
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                print(f"无效的结束日期格式: {end_date}")
                return []
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        
        # 查找日期范围内的任务
        result = []
        for task in self.get_all_tasks():
            start_time = task.get('start_time')
            end_time = task.get('end_time')
            
            # 确保时间字段是datetime对象
            if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                print(f"任务时间格式错误，跳过: {task}")
                continue
            
            # 检查任务日期范围是否与指定日期范围重叠
            task_start_date = start_time.date()
            task_end_date = end_time.date()
            
            # 任务在指定日期范围内的条件:
            # 1. 任务开始日期在范围内，或
            # 2. 任务结束日期在范围内，或
            # 3. 任务跨越整个范围（开始日期在范围开始之前且结束日期在范围结束之后）
            if (start_date <= task_start_date <= end_date or
                start_date <= task_end_date <= end_date or
                (task_start_date <= start_date and task_end_date >= end_date)):
                result.append(task)
        
        return result
    
    def get_reminders(self, current_time):
        """获取需要提醒的任务
        
        Args:
            current_time: 当前时间
            
        Returns:
            list: 需要提醒的任务列表
        """
        # 查找即将开始的任务（提前15分钟提醒）
        reminders = []
        for task in self.get_all_tasks():
            start_time = task.get('start_time')
            if not isinstance(start_time, datetime):
                continue
                
            # 检查是否提醒过
            if task.get('reminded', False):
                continue
                
            # 计算时间差（分钟）
            time_diff = (start_time - current_time).total_seconds() / 60
            
            # 如果任务在未来5-15分钟内开始，需要提醒
            if 5 <= time_diff <= 15:
                # 标记为已提醒
                task['reminded'] = True
                reminders.append(task)
        
        # 保存状态
        if reminders:
            self.save_tasks()
            
        return reminders
    
    def reorder_tasks(self, tasks):
        """重新排序任务列表
        
        Args:
            tasks: 重排序后的任务列表
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 更新内部任务列表
            self.tasks = tasks
            
            # 保存到文件
            self.save_tasks()
            
            return True
        except Exception as e:
            print(f"任务重排序时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_overdue_tasks(self):
        """
        检查并更新已到期但未完成的任务状态为"进行中"
        """
        try:
            current_time = datetime.now()
            updated = False
            
            for task in self.tasks:
                # 检查任务是否有到期日期
                if not isinstance(task, dict) or 'due_date' not in task:
                    continue
                    
                # 解析到期日期
                due_date = None
                if isinstance(task['due_date'], str):
                    try:
                        due_date = datetime.fromisoformat(task['due_date'])
                    except ValueError:
                        print(f"无法解析任务 {task.get('id')} 的到期日期: {task['due_date']}")
                        continue
                elif isinstance(task['due_date'], datetime):
                    due_date = task['due_date']
                else:
                    continue
                
                # 检查任务是否到期但未完成且未在进行中
                is_completed = task.get('completed', False)
                status = task.get('status', '未开始')
                
                if not is_completed and status not in ['进行中', '已完成'] and due_date <= current_time:
                    print(f"任务已到期自动设置为进行中: {task.get('title')} (ID: {task.get('id')})")
                    task['status'] = '进行中'
                    updated = True
            
            # 如果有任务被更新，保存更改
            if updated:
                print("检测到过期任务并更新了状态，保存更改")
                self.save_tasks()
                
            return updated
        except Exception as e:
            print(f"检查过期任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_task_time_status(self, task):
        """根据任务时间自动设置任务状态
        
        Args:
            task: 任务数据
            
        Returns:
            str: 应该设置的任务状态
        """
        # 如果任务已完成，则不改变状态
        if task.get('completed', False):
            return "已完成"
        
        # 如果处于暂停状态，保持不变
        current_status = task.get('status', '未开始')
        if current_status == "已暂停":
            return "已暂停"
        
        # 获取任务时间
        start_time = task.get('start_time')
        end_time = task.get('end_time')
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            return current_status  # 时间格式有误，保持现状
        
        # 获取当前时间（精确到分钟）
        current_time = datetime.now()
        
        # 根据时间判断状态
        if current_time < start_time:
            return "未开始"
        elif current_time <= end_time:
            # 当前时间在任务时间范围内，设置为进行中
            return "进行中"
        else:
            # 任务已过期但未完成
            return current_status
    
    def setup_timer(self):
        """设置定时器，每分钟检查任务状态"""
        try:
            import threading
            
            def check_timer():
                # 更新所有任务状态
                self.auto_update_task_status()
                
                # 重新设置定时器（每分钟执行一次）
                self.timer = threading.Timer(60, check_timer)
                self.timer.daemon = True  # 设为守护线程，随主进程退出
                self.timer.start()
                
            # 初始启动定时器
            self.timer = threading.Timer(60, check_timer)
            self.timer.daemon = True
            self.timer.start()
            print("任务状态定时检查已启动（每分钟检查一次）")
            
        except Exception as e:
            print(f"设置定时器时出错: {e}")
            import traceback
            traceback.print_exc()
            
    def stop_timer(self):
        """停止定时器"""
        try:
            if hasattr(self, 'timer') and self.timer:
                self.timer.cancel()
                print("任务状态定时检查已停止")
        except Exception as e:
            print(f"停止定时器时出错: {e}")
    
    def auto_update_task_status(self, task_id=None):
        """根据时间自动更新任务状态
        
        Args:
            task_id: 可选，指定任务ID。如果为None，则更新所有任务
            
        Returns:
            bool: 是否有任务状态被更新
        """
        updated = False
        
        # 确定要处理的任务列表
        tasks_to_update = []
        if task_id:
            # 查找特定任务
            for task in self.tasks:
                if isinstance(task, dict) and task.get('id') == task_id:
                    tasks_to_update.append(task)
                    break
        else:
            # 处理所有任务
            tasks_to_update = [task for task in self.tasks if isinstance(task, dict)]
        
        # 更新任务状态
        for task in tasks_to_update:
            # 跳过已完成的任务
            if task.get('completed', False):
                continue
                
            # 获取当前状态
            current_status = task.get('status', '未开始')
            
            # 根据时间判断应有状态
            new_status = self.check_task_time_status(task)
            
            # 如果状态需要改变
            if current_status != new_status:
                # 记录日志（只记录日志，不显示弹窗）
                print(f"任务 '{task.get('title')}' 状态自动从 '{current_status}' 更新为 '{new_status}'")
                
                # 更新状态
                task['status'] = new_status
                updated = True
        
        # 如果有任务被更新，保存更改
        if updated:
            self.save_tasks()
            
        return updated 