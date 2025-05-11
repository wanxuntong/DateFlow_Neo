#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
structlog使用示例
展示如何在项目模块中使用结构化日志
"""

from utils.logger import get_logger

# 创建模块级别的日志记录器
logger = get_logger("Example", module="utils.logging_example")

def basic_logging_example():
    """基本日志记录示例"""
    # 记录不同级别的日志
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误信息")

def structured_logging_example():
    """结构化日志记录示例"""
    # 结构化日志 - 添加上下文信息
    logger.info("用户登录成功", user_id=10001, username="test_user", ip="192.168.1.100")
    
    # 记录操作执行时间
    import time
    start_time = time.time()
    time.sleep(0.1)  # 模拟操作
    end_time = time.time()
    logger.info("操作完成", 
               operation="data_processing", 
               duration_ms=round((end_time - start_time) * 1000, 2))
    
    # 记录异常信息
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("操作失败", 
                        operation="division", 
                        error_type=type(e).__name__)

def context_logging_example():
    """上下文绑定日志记录示例"""
    # 创建带有上下文的日志记录器
    request_logger = logger.bind(
        request_id="req-1234",
        session_id="sess-5678",
        user_agent="Mozilla/5.0"
    )
    
    # 使用这个记录器记录整个请求过程
    request_logger.info("收到请求")
    
    # 处理过程中可以添加更多上下文
    process_logger = request_logger.bind(process_id="proc-9012")
    process_logger.info("处理请求")
    
    # 完成请求
    request_logger.info("请求处理完成", response_code=200, response_time_ms=42)

if __name__ == "__main__":
    # 注意：在实际使用中，确保在应用入口点已调用configure_logging()
    # 这个示例假设main.py已经进行了配置
    
    # 运行示例
    basic_logging_example()
    structured_logging_example()
    context_logging_example() 