#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子任务管理器模块
用于管理任务的层级关系和子任务跟踪
"""

import uuid
from datetime import datetime

class SubtaskManager:
    """子任务管理器类，负责任务的层级关系和子任务跟踪"""
    
    def __init__(self, scheduler_manager):
        """
        初始化子任务管理器
        
        参数:
            scheduler_manager: 调度管理器实例，用于操作任务数据
        """
        self.scheduler_manager = scheduler_manager
    
    def add_subtask(self, parent_task_id, subtask_data):
        """为指定任务添加子任务
        
        Args:
            parent_task_id: 父任务ID
            subtask_data: 子任务数据字典
            
        Returns:
            str: 新子任务的ID，失败返回None
        """
        try:
            # 获取父任务
            parent_task = self.scheduler_manager.get_task(parent_task_id)
            if not parent_task:
                print(f"父任务不存在: {parent_task_id}")
                return None
            
            # 确保子任务数据是字典
            if not isinstance(subtask_data, dict):
                print(f"子任务数据必须是字典类型，而不是 {type(subtask_data)}")
                return None
            
            # 设置子任务属性
            subtask_data['parent_id'] = parent_task_id
            subtask_data['is_subtask'] = True
            
            # 添加子任务到调度管理器
            subtask_id = self.scheduler_manager.add_task(subtask_data)
            if not subtask_id:
                print("添加子任务失败")
                return None
            
            # 更新父任务的子任务列表
            if 'subtasks' not in parent_task:
                parent_task['subtasks'] = []
            
            parent_task['subtasks'].append(subtask_id)
            
            # 更新父任务
            if not self.scheduler_manager.update_task(parent_task):
                print("更新父任务失败")
                # 尝试删除刚添加的子任务
                self.scheduler_manager.delete_task(subtask_id)
                return None
            
            return subtask_id
        except Exception as e:
            print(f"添加子任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def remove_subtask(self, subtask_id, delete_subtask=True):
        """从父任务中移除子任务
        
        Args:
            subtask_id: 子任务ID
            delete_subtask: 是否同时删除子任务，默认为True
            
        Returns:
            bool: 移除成功返回True，失败返回False
        """
        try:
            # 获取子任务
            subtask = self.scheduler_manager.get_task(subtask_id)
            if not subtask:
                print(f"子任务不存在: {subtask_id}")
                return False
            
            # 检查是否是子任务
            if not subtask.get('is_subtask'):
                print(f"指定的任务不是子任务: {subtask_id}")
                return False
            
            # 获取父任务
            parent_id = subtask.get('parent_id')
            if not parent_id:
                print(f"子任务没有指定父任务: {subtask_id}")
                # 如果需要删除
                if delete_subtask:
                    return self.scheduler_manager.delete_task(subtask_id)
                return False
            
            parent_task = self.scheduler_manager.get_task(parent_id)
            if not parent_task:
                print(f"父任务不存在: {parent_id}")
                # 如果需要删除
                if delete_subtask:
                    return self.scheduler_manager.delete_task(subtask_id)
                return False
            
            # 从父任务的子任务列表中移除
            if 'subtasks' in parent_task and subtask_id in parent_task['subtasks']:
                parent_task['subtasks'].remove(subtask_id)
                
                # 更新父任务
                if not self.scheduler_manager.update_task(parent_task):
                    print("更新父任务失败")
                    return False
            
            # 如果需要删除子任务
            if delete_subtask:
                return self.scheduler_manager.delete_task(subtask_id)
            else:
                # 将子任务标记为非子任务，并移除父任务引用
                subtask.pop('parent_id', None)
                subtask['is_subtask'] = False
                return self.scheduler_manager.update_task(subtask)
        except Exception as e:
            print(f"移除子任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_subtask(self, subtask_data):
        """更新子任务
        
        Args:
            subtask_data: 子任务数据
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            # 获取任务ID
            subtask_id = subtask_data.get("id")
            if not subtask_id:
                print("无效的任务ID")
                return False
            
            # 获取当前任务
            current_task = self.scheduler_manager.get_task(subtask_id)
            if not current_task:
                print(f"任务不存在: {subtask_id}")
                return False
            
            # 检查是否是子任务
            if not current_task.get('is_subtask'):
                print(f"指定的任务不是子任务: {subtask_id}")
                return False
            
            # 确保保持子任务标记和父任务引用
            subtask_data['is_subtask'] = True
            subtask_data['parent_id'] = current_task.get('parent_id')
            
            # 检查完成状态是否变化
            old_completed = current_task.get('completed', False)
            new_completed = subtask_data.get('completed', False)
            
            # 更新子任务
            result = self.scheduler_manager.update_task(subtask_data)
            
            # 如果完成状态发生变化
            if result and old_completed != new_completed:
                self._update_parent_progress(subtask_data.get('parent_id'))
            
            return result
        except Exception as e:
            print(f"更新子任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_subtasks(self, parent_task_id):
        """获取指定任务的所有子任务
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            list: 子任务列表
        """
        try:
            # 获取父任务
            parent_task = self.scheduler_manager.get_task(parent_task_id)
            if not parent_task:
                print(f"父任务不存在: {parent_task_id}")
                return []
            
            # 获取子任务ID列表
            subtask_ids = parent_task.get('subtasks', [])
            if not subtask_ids:
                return []
            
            # 获取子任务对象
            subtasks = []
            for subtask_id in subtask_ids:
                subtask = self.scheduler_manager.get_task(subtask_id)
                if subtask:
                    subtasks.append(subtask)
                else:
                    print(f"子任务不存在: {subtask_id}")
            
            return subtasks
        except Exception as e:
            print(f"获取子任务时出错: {e}")
            return []
    
    def _update_parent_progress(self, parent_task_id):
        """更新父任务的进度
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            # 获取父任务
            parent_task = self.scheduler_manager.get_task(parent_task_id)
            if not parent_task:
                print(f"父任务不存在: {parent_task_id}")
                return False
            
            # 获取子任务列表
            subtask_ids = parent_task.get('subtasks', [])
            if not subtask_ids:
                # 没有子任务，默认进度为0%
                parent_task['progress'] = 0
                return self.scheduler_manager.update_task(parent_task)
            
            # 统计完成的子任务数量
            completed_count = 0
            total_count = len(subtask_ids)
            
            for subtask_id in subtask_ids:
                subtask = self.scheduler_manager.get_task(subtask_id)
                if subtask and subtask.get('completed', False):
                    completed_count += 1
            
            # 计算进度百分比
            progress = int((completed_count / total_count) * 100)
            parent_task['progress'] = progress
            
            # 如果所有子任务都完成，则将父任务标记为完成
            if completed_count == total_count:
                parent_task['completed'] = True
                parent_task['completion_time'] = datetime.now()
            else:
                parent_task['completed'] = False
                parent_task.pop('completion_time', None)
            
            # 更新父任务
            return self.scheduler_manager.update_task(parent_task)
        except Exception as e:
            print(f"更新父任务进度时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def convert_to_subtask(self, task_id, parent_task_id):
        """将普通任务转换为子任务
        
        Args:
            task_id: 要转换的任务ID
            parent_task_id: 父任务ID
            
        Returns:
            bool: 转换成功返回True，失败返回False
        """
        try:
            # 获取任务和父任务
            task = self.scheduler_manager.get_task(task_id)
            parent_task = self.scheduler_manager.get_task(parent_task_id)
            
            if not task:
                print(f"任务不存在: {task_id}")
                return False
                
            if not parent_task:
                print(f"父任务不存在: {parent_task_id}")
                return False
            
            # 检查是否已经是子任务
            if task.get('is_subtask'):
                print(f"任务已经是子任务: {task_id}")
                return False
            
            # 检查是否形成循环引用（如果父任务是当前任务的子任务）
            if self._is_subtask_of(parent_task_id, task_id):
                print(f"不能形成循环引用: {task_id} -> {parent_task_id}")
                return False
            
            # 设置子任务属性
            task['is_subtask'] = True
            task['parent_id'] = parent_task_id
            
            # 更新父任务的子任务列表
            if 'subtasks' not in parent_task:
                parent_task['subtasks'] = []
            
            parent_task['subtasks'].append(task_id)
            
            # 保存更改
            if not self.scheduler_manager.update_task(task):
                print(f"更新任务失败: {task_id}")
                return False
                
            if not self.scheduler_manager.update_task(parent_task):
                print(f"更新父任务失败: {parent_task_id}")
                # 回滚任务更改
                task.pop('is_subtask', None)
                task.pop('parent_id', None)
                self.scheduler_manager.update_task(task)
                return False
            
            # 更新父任务进度
            self._update_parent_progress(parent_task_id)
            
            return True
        except Exception as e:
            print(f"转换为子任务时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _is_subtask_of(self, potential_child_id, parent_id):
        """检查一个任务是否是另一个任务的子任务（或递归子任务）
        
        Args:
            potential_child_id: 潜在子任务ID
            parent_id: 父任务ID
            
        Returns:
            bool: 如果是子任务则返回True，否则返回False
        """
        if potential_child_id == parent_id:
            return True
            
        parent_task = self.scheduler_manager.get_task(parent_id)
        if not parent_task:
            return False
            
        subtask_ids = parent_task.get('subtasks', [])
        if not subtask_ids:
            return False
            
        if potential_child_id in subtask_ids:
            return True
            
        # 递归检查
        for subtask_id in subtask_ids:
            if self._is_subtask_of(potential_child_id, subtask_id):
                return True
                
        return False
        
    def get_task_hierarchy(self, task_id, include_completed=True):
        """获取任务的完整层次结构（包括所有子任务和递归子任务）
        
        Args:
            task_id: 任务ID
            include_completed: 是否包含已完成的任务，默认为True
            
        Returns:
            dict: 任务层次结构树
        """
        task = self.scheduler_manager.get_task(task_id)
        if not task:
            return None
            
        # 如果不包含已完成任务，且任务已完成，则返回None
        if not include_completed and task.get('completed', False):
            return None
            
        result = task.copy()
        
        # 获取子任务
        subtask_ids = task.get('subtasks', [])
        if subtask_ids:
            result['children'] = []
            for subtask_id in subtask_ids:
                child = self.get_task_hierarchy(subtask_id, include_completed)
                if child:
                    result['children'].append(child)
        
        return result
    
    def get_all_root_tasks(self, include_completed=True):
        """获取所有根任务（非子任务的顶级任务）
        
        Args:
            include_completed: 是否包含已完成的任务，默认为True
            
        Returns:
            list: 根任务列表
        """
        try:
            all_tasks = self.scheduler_manager.get_all_tasks()
            root_tasks = []
            
            for task in all_tasks:
                # 如果不是子任务，则是根任务
                if not task.get('is_subtask'):
                    # 如果不包含已完成任务，且任务已完成，则跳过
                    if not include_completed and task.get('completed', False):
                        continue
                    root_tasks.append(task)
            
            return root_tasks
        except Exception as e:
            print(f"获取根任务时出错: {e}")
            return []
    
    def update_dependencies(self, task_id, dependent_task_ids):
        """更新任务的依赖关系
        
        Args:
            task_id: 任务ID
            dependent_task_ids: 依赖的任务ID列表
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            # 获取任务
            task = self.scheduler_manager.get_task(task_id)
            if not task:
                print(f"任务不存在: {task_id}")
                return False
            
            # 检查所有依赖任务是否存在
            for dep_id in dependent_task_ids:
                if not self.scheduler_manager.get_task(dep_id):
                    print(f"依赖任务不存在: {dep_id}")
                    return False
            
            # 更新依赖关系
            task['dependencies'] = dependent_task_ids
            
            # 保存更改
            return self.scheduler_manager.update_task(task)
        except Exception as e:
            print(f"更新任务依赖关系时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_dependency_status(self, task_id):
        """检查任务的依赖任务完成状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 如果所有依赖任务都已完成，则返回True，否则返回False
        """
        try:
            # 获取任务
            task = self.scheduler_manager.get_task(task_id)
            if not task:
                print(f"任务不存在: {task_id}")
                return False
            
            # 获取依赖任务列表
            dependencies = task.get('dependencies', [])
            if not dependencies:
                # 没有依赖，默认为已满足
                return True
            
            # 检查所有依赖任务是否已完成
            for dep_id in dependencies:
                dep_task = self.scheduler_manager.get_task(dep_id)
                if not dep_task or not dep_task.get('completed', False):
                    return False
            
            return True
        except Exception as e:
            print(f"检查任务依赖状态时出错: {e}")
            return False 