"""
日志管理模块，负责配置和提供日志记录功能
"""
import os
import logging
import datetime
import data
import sys
from functions import create_directory


class LoggerManager:
    """日志管理器，负责配置和获取logger实例"""

    def __init__(self):
        # 确保日志目录存在
        self.log_directory = os.path.join(data.settings_directory, "logs").replace("\\", "/")
        create_directory(self.log_directory)

        # 配置根日志记录器
        self._configure_root_logger()

    def _configure_root_logger(self):
        """配置根日志记录器"""
        # 获取当前日期，用于日志文件名
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        log_filename = f"editor_desktop_{current_date}.log"
        log_file_path = os.path.join(self.log_directory, log_filename).replace("\\", "/")

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if data.debug_mode else logging.INFO)

        # 移除已存在的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # 定义日志格式
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # 只有当sys.stdout存在时才创建控制台处理器
        if hasattr(sys, 'stdout') and sys.stdout is not None:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

    def get_logger(self, name):
        """获取指定名称的logger实例"""
        return logging.getLogger(name)


# 创建全局日志管理器实例
logger_manager = LoggerManager()


# 提供简便的日志记录函数
def get_logger(name):
    """获取指定名称的logger实例"""
    return logger_manager.get_logger(name)


# 直接提供常用的日志级别函数
def debug(name, message):
    """记录调试信息"""
    get_logger(name).debug(message)


def info(name, message):
    """记录一般信息"""
    get_logger(name).info(message)


def warning(name, message):
    """记录警告信息"""
    get_logger(name).warning(message)


def error(name, message):
    """记录错误信息"""
    get_logger(name).error(message)


def critical(name, message):
    """记录严重错误信息"""
    get_logger(name).critical(message)