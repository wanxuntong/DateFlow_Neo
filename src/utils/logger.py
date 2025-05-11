#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块
提供基于structlog的日志记录功能
"""

import os
import sys
import time
import logging
import structlog
import atexit
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

# 定义日志级别
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 日志文件路径
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")

# 全局变量以跟踪日志系统状态
_logging_configured = False
_log_handlers = []

# 安全的过滤器函数
def safe_filter_by_level(logger, method_name, event_dict):
    """安全的日志级别过滤器，处理logger为None的情况"""
    try:
        if logger is None:
            return event_dict
        
        level = getattr(logging, method_name.upper(), None)
        if level is None:
            return event_dict
            
        if not logger.isEnabledFor(level):
            raise structlog.DropEvent
        
        return event_dict
    except structlog.DropEvent:
        raise
    except Exception:
        # 错误时也返回事件字典，保证日志流程不中断
        return event_dict

def ensure_dict_processor(logger, method_name, event_dict):
    """确保事件字典是字典类型

    处理不同类型的日志输入:
    - 如果是元组: 将第一个元素作为事件名称，其他元素作为额外信息
    - 如果是字符串: 将其作为事件名称
    - 如果是字典: 保持不变
    """
    # 如果传入的是元组，将其转换为字典
    if isinstance(event_dict, tuple):
        try:
            # 获取元组的第一个元素作为事件
            event = event_dict[0] if event_dict else "unknown_event"
            # 构建一个新的字典，把事件作为键
            if isinstance(event, str):
                return {"event": event}
            elif isinstance(event, dict):
                return event
            else:
                return {"event": str(event)}
        except Exception as e:
            return {"event": f"Error processing tuple: {str(e)}"}
    
    # 如果传入的是字符串，将其转换为字典
    elif isinstance(event_dict, str):
        return {"event": event_dict}
    
    # 如果不是字典类型，尝试转换
    elif not isinstance(event_dict, dict):
        try:
            return {"event": str(event_dict)}
        except:
            return {"event": "unknown_event"}
    
    return event_dict

def safe_remove_processors_meta(logger, method_name, event_dict):
    """安全地移除处理器元数据"""
    # 确保我们处理的是字典
    if not isinstance(event_dict, dict):
        event_dict = ensure_dict_processor(logger, method_name, event_dict)
    
    # 安全地删除键，防止KeyError
    event_dict.pop("_from_structlog", None)
    event_dict.pop("_record", None)
    event_dict.pop("stack", None)
    return event_dict

def add_timestamp(logger, method_name, event_dict):
    """添加时间戳到日志事件中"""
    # 确保我们处理的是字典
    if not isinstance(event_dict, dict):
        event_dict = ensure_dict_processor(logger, method_name, event_dict)
    
    event_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return event_dict

def add_app_info(logger, method_name, event_dict):
    """添加应用信息到日志事件中"""
    # 确保我们处理的是字典
    if not isinstance(event_dict, dict):
        event_dict = ensure_dict_processor(logger, method_name, event_dict)
    
    event_dict["app"] = "InfoFlow"
    return event_dict

def handle_exception(logger, method_name, event_dict):
    """处理可能的异常"""
    # 确保我们处理的是字典
    if not isinstance(event_dict, dict):
        event_dict = ensure_dict_processor(logger, method_name, event_dict)
    
    # 如果有exc_info，则添加异常信息
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        if exc_info is True:
            import sys
            exc_info = sys.exc_info()
        
        try:
            import traceback
            tb_lines = traceback.format_exception(*exc_info)
            event_dict["exception"] = "".join(tb_lines)
        except:
            event_dict["exception"] = "Error formatting exception"
    
    return event_dict

def configure_logging(
    console_level: str = "info",
    file_level: str = "debug",
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    配置日志记录系统
    
    参数:
        console_level: 控制台日志级别
        file_level: 文件日志级别
        log_dir: 日志文件目录，默认为项目根目录下的logs目录
        log_file: 日志文件名，默认为当前日期的年月日
    """
    global _logging_configured, _log_handlers
    
    # 避免重复配置
    if _logging_configured:
        return
    
    # 确保日志目录存在
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志文件名
    if log_file is None:
        log_file = f"{time.strftime('%Y%m%d')}.log"
    
    log_file_path = os.path.join(log_dir, log_file)
    
    # 获取日志级别
    console_level = LOG_LEVEL_MAP.get(console_level.lower(), logging.INFO)
    file_level = LOG_LEVEL_MAP.get(file_level.lower(), logging.DEBUG)
    
    # 配置structlog处理器，确保ensure_dict_processor在最前面处理
    processors = [
        ensure_dict_processor,  # 确保是字典类型，放在最前面
        safe_filter_by_level,  # 使用安全的过滤器
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    
    # 标准输出处理器
    console_processor = structlog.dev.ConsoleRenderer(colors=True)
    
    # 配置日志格式
    formatter = structlog.stdlib.ProcessorFormatter(
        # 文件日志使用JSON格式
        foreign_pre_chain=processors,
        processors=[
            safe_remove_processors_meta,  # 安全地移除处理器元数据
            structlog.processors.JSONRenderer()
        ]
    )
    
    # 配置控制台日志处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=processors,
            processors=[
                safe_remove_processors_meta,  # 安全地移除处理器元数据
                console_processor
            ]
        )
    )
    
    # 配置文件日志处理器
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    
    # 保存处理器引用
    _log_handlers = [console_handler, file_handler]
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 配置structlog
    structlog.configure(
        processors=[
            ensure_dict_processor,  # 确保字典类型处理器放在最前面
            safe_filter_by_level,  # 使用安全的过滤器
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_timestamp,
            add_app_info,
            handle_exception,
            safe_remove_processors_meta,  # 安全移除元数据
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 设置配置标志
    _logging_configured = True
    
    # 注册应用程序退出时的清理函数
    def cleanup_logging():
        for handler in _log_handlers:
            handler.flush()
            handler.close()
    
    atexit.register(cleanup_logging)


class SafeLogger:
    """当structlog不可用时的安全logger"""
    def __init__(self, name):
        self.name = name
    
    def debug(self, msg, *args, **kwargs):
        """调试级别日志"""
        print(f"DEBUG [{self.name}]: {msg}")
        
    def info(self, msg, *args, **kwargs):
        """信息级别日志"""
        print(f"INFO [{self.name}]: {msg}")
        
    def warning(self, msg, *args, **kwargs):
        """警告级别日志"""
        print(f"WARNING [{self.name}]: {msg}")
        
    def error(self, msg, *args, **kwargs):
        """错误级别日志"""
        print(f"ERROR [{self.name}]: {msg}")
        
    def critical(self, msg, *args, **kwargs):
        """严重错误级别日志"""
        print(f"CRITICAL [{self.name}]: {msg}")
        
    def exception(self, msg, *args, **kwargs):
        """异常级别日志"""
        print(f"EXCEPTION [{self.name}]: {msg}")
        import traceback
        traceback.print_exc()
    
    def bind(self, **kwargs):
        """兼容structlog的bind方法"""
        return self
    
    def __getattr__(self, name):
        """返回无操作函数"""
        def noop(*args, **kwargs):
            pass
        return noop


def get_logger(name: str, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    """
    获取一个配置好的日志记录器
    
    参数:
        name: 日志记录器名称
        initial_values: 初始绑定值
        
    返回:
        配置好的structlog日志记录器
    """
    try:
        # 确保日志系统已配置
        if not _logging_configured:
            # 使用默认设置配置日志系统
            configure_logging()
        
        # 获取标准日志记录器，用于直接调用
        std_logger = logging.getLogger(name)
        
        # 创建直接使用标准日志记录器的简单包装
        class SimpleLogger:
            def __init__(self, logger):
                self._logger = logger
                
            def debug(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.debug(msg, *args, **args_dict)
                
            def info(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.info(msg, *args, **args_dict)
                
            def warning(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.warning(msg, *args, **args_dict)
                
            def error(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.error(msg, *args, **args_dict)
                
            def critical(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.critical(msg, *args, **args_dict)
                
            def exception(self, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                args_dict['exc_info'] = True  # 确保异常信息被记录
                self._logger.error(msg, *args, **args_dict)
                
            def log(self, level, msg, *args, **kwargs):
                # 过滤掉标准logger不支持的关键字参数
                args_dict = {k: v for k, v in kwargs.items() 
                            if k in ['exc_info', 'stack_info', 'stacklevel', 'extra']}
                self._logger.log(level, msg, *args, **args_dict)
                
            def bind(self, **kwargs):
                # 返回自身，忽略bind参数
                return self
        
        # 返回使用标准日志记录器的简单包装
        return SimpleLogger(std_logger)
        
    except Exception as e:
        # 如果配置失败，打印错误并返回安全的日志记录器
        print(f"获取日志记录器失败: {str(e)}，使用安全日志记录器")
        return SafeLogger(name) 