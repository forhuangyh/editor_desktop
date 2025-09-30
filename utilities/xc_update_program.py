#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新程序 - 负责下载和解压更新包，然后重新启动主程序
"""
import os
import sys
import logging
import tempfile
import time
import zipfile
import shutil
import subprocess
import requests


# 设置日志配置 - 确保在任何环境下都能正确记录日志
def setup_logging():
    # 获取当前执行文件的目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的程序，使用可执行文件所在目录
        current_dir = os.path.dirname(sys.executable)
    else:
        # 否则使用脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

    # 定义日志目录优先级，添加当前执行文件目录下的.exco/logs
    log_dirs = [
        os.path.join(current_dir, "updatelogs", "log"),  # 当前执行文件目录下的.exco/logs
        os.path.join(os.path.expanduser("~"), ".exco_editor", "logs"),  # 用户目录
        os.path.join(os.getenv("TEMP", "."), ".exco_editor", "logs"),  # 临时目录
        os.path.join(os.getcwd(), "logs")  # 当前目录
    ]

    log_file = None
    for log_dir in log_dirs:
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "update.log")
            print(f"日志文件将保存在: {log_file}")
            break
        except Exception as e:
            print(f"无法在 {log_dir} 创建日志目录: {str(e)}")

    # 如果所有目录都失败，使用当前目录下的简单文件名
    if log_file is None:
        log_file = "update.log"
        print(f"使用备用日志文件: {log_file}")

    # 配置日志同时输出到文件和控制台
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成")
    logger.debug(f"当前工作目录: {os.getcwd()}")
    logger.debug(f"Python解释器: {sys.executable}")
    logger.debug(f"命令行参数: {sys.argv}")
    logger.debug(f"当前执行文件目录: {current_dir}")

    # 检查是否在PyInstaller打包环境中
    if getattr(sys, 'frozen', False):
        logger.debug(f"正在运行打包后的程序，临时目录: {sys._MEIPASS}")

    return logger


# 初始化日志系统
logger = setup_logging()


# 下载更新包
def download_update(download_url, save_path):
    """
    下载更新包
    :param download_url: 更新包下载链接
    :param save_path: 保存路径
    """
    try:
        logger.info(f"开始下载更新包: {download_url}")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(save_path, 'wb') as file:
            for data_chunk in response.iter_content(chunk_size=8192):
                if data_chunk:
                    file.write(data_chunk)
                    downloaded_size += len(data_chunk)

                    # 显示下载进度
                    if total_size > 0:
                        progress = int((downloaded_size / total_size) * 100)
                        print(f"下载进度: {progress}%", end='\r')

        print("\n下载完成")
        logger.info(f"更新包下载完成，保存路径: {save_path}")
        return True
    except Exception as e:
        logger.error(f"下载更新包失败: {str(e)}")
        return False


# 解压更新包
def unzip_update(zip_path, extract_dir):
    """
    解压更新包，智能处理ZIP内部目录结构
    特别处理：.dll库文件发现重名时不覆盖，其他文件正常覆盖
    增加：打印覆盖文件名称及覆盖状态
    :param zip_path: 压缩包路径
    :param extract_dir: 解压目录
    """
    try:
        logger.info(f"开始解压更新包: {zip_path}")
        logger.info(f"解压到: {extract_dir}")

        # 确保解压目录存在
        os.makedirs(extract_dir, exist_ok=True)

        # 用于记录成功覆盖和失败覆盖的文件
        successfully_overwritten = []
        failed_overwritten = []
        skipped_dll_files = []

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取zip中的所有文件和目录
            zip_contents = zip_ref.namelist()

            # 检查ZIP文件是否只有一个顶层目录
            top_level_dirs = set()
            for item in zip_contents:
                # 获取顶级目录名称（去掉文件名和路径分隔符）
                if '/' in item or '\\' in item:
                    first_part = item.split('/')[0] if '/' in item else item.split('\\')[0]
                    if first_part:
                        top_level_dirs.add(first_part)

            # 判断是否需要扁平化目录结构
            flatten_structure = len(top_level_dirs) == 1 and any(item.startswith(next(iter(top_level_dirs)) + '/') or \
                                                                 item.startswith(next(iter(top_level_dirs)) + '\\') \
                                                                 for item in zip_contents)

            if flatten_structure:
                logger.info(f"检测到ZIP文件包含单一顶层目录，将直接解压内容到目标目录")
                main_dir = next(iter(top_level_dirs))
                # 只解压主目录下的内容
                for item in zip_contents:
                    if item.startswith(main_dir + '/') or item.startswith(main_dir + '\\'):
                        # 去掉主目录前缀
                        target_name = item[len(main_dir) + 1:]
                        if target_name:  # 确保不是空字符串
                            target_path = os.path.join(extract_dir, target_name)

                            # 检查是否是目录
                            if item.endswith('/') or item.endswith('\\'):
                                os.makedirs(target_path, exist_ok=True)
                            else:
                                # 检查文件是否为.dll，且已存在
                                is_dll_file = target_path.lower().endswith('.dll')
                                if is_dll_file and os.path.exists(target_path):
                                    logger.info(f"跳过覆盖已存在的.dll文件: {target_path}")
                                    skipped_dll_files.append(target_path)
                                    continue

                                # 检查文件是否存在（用于记录覆盖信息）
                                file_exists = os.path.exists(target_path)
                                if file_exists:
                                    logger.info(f"准备覆盖文件: {target_path}")

                                # 确保目标文件的目录存在
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                                # 解压文件（带重试机制）- 非.dll文件或.dll文件不存在
                                max_retries = 3
                                retry_count = 0
                                success = False

                                while retry_count < max_retries and not success:
                                    try:
                                        with zip_ref.open(item) as source, open(target_path, 'wb') as target:
                                            shutil.copyfileobj(source, target)
                                        success = True
                                        if file_exists:
                                            logger.info(f"文件覆盖成功: {target_path}")
                                            successfully_overwritten.append(target_path)
                                        else:
                                            logger.info(f"文件创建成功: {target_path}")
                                    except PermissionError as e:
                                        retry_count += 1
                                        if retry_count >= max_retries:
                                            logger.error(f"无法解压文件: {target_path}，权限被拒绝")
                                            failed_overwritten.append((target_path, "权限被拒绝"))
                                            # 遇到权限错误直接抛出异常，导致解压失败
                                            raise
                                        else:
                                            logger.warning(
                                                f"解压文件失败，正在重试 ({retry_count}/{max_retries}): {target_path}")
                                            time.sleep(1)  # 等待1秒后重试
                                    except Exception as e:
                                        logger.error(f"解压文件时出错: {target_path} - {str(e)}")
                                        failed_overwritten.append((target_path, str(e)))
                                        # 遇到其他异常直接失败
                                        raise
                logger.info(f"成功解压ZIP文件内容（跳过单一顶层目录）")
            else:
                # 使用原始逻辑，直接解压所有文件
                # 解压前检查冲突文件
                for file_name in zip_contents:
                    # 跳过目录
                    if file_name.endswith('/') or file_name.endswith('\\'):
                        continue

                    target_path = os.path.join(extract_dir, file_name)
                    # 检查是否为.dll文件且已存在
                    is_dll_file = target_path.lower().endswith('.dll')
                    if is_dll_file and os.path.exists(target_path):
                        logger.info(f"跳过覆盖已存在的.dll文件: {target_path}")
                        skipped_dll_files.append(target_path)

                # 解压所有文件（不覆盖.dll文件）
                try:
                    # 先收集所有不是.dll或.dll不存在的文件
                    files_to_extract = []
                    for file_name in zip_contents:
                        if file_name.endswith('/') or file_name.endswith('\\'):  # 总是解压目录
                            files_to_extract.append(file_name)
                        else:
                            target_path = os.path.join(extract_dir, file_name)
                            is_dll_file = target_path.lower().endswith('.dll')
                            if not is_dll_file or not os.path.exists(target_path):
                                files_to_extract.append(file_name)

                    # 逐个解压文件
                    for file_name in files_to_extract:
                        if not file_name.endswith('/') and not file_name.endswith('\\'):  # 不是目录
                            target_path = os.path.join(extract_dir, file_name)
                            # 检查文件是否存在（用于记录覆盖信息）
                            file_exists = os.path.exists(target_path)
                            if file_exists:
                                logger.info(f"准备覆盖文件: {target_path}")

                            max_retries = 3
                            retry_count = 0
                            success = False
                            while retry_count < max_retries and not success:
                                try:
                                    zip_ref.extract(file_name, extract_dir)
                                    success = True
                                    if file_exists:
                                        logger.info(f"文件覆盖成功: {target_path}")
                                        successfully_overwritten.append(target_path)
                                    else:
                                        logger.info(f"文件创建成功: {target_path}")
                                except PermissionError:
                                    retry_count += 1
                                    if retry_count >= max_retries:
                                        logger.error(f"无法解压文件: {target_path}")
                                        failed_overwritten.append((target_path, "权限被拒绝"))
                                        # 遇到权限错误直接抛出异常，导致解压失败
                                        raise
                                    else:
                                        time.sleep(1)
                    logger.info(f"成功解压 {len(files_to_extract)} 个文件")
                except PermissionError as e:
                    logger.error(f"解压文件时权限被拒绝: {str(e)}")
                    failed_overwritten.append((target_path, str(e)))
                    # 直接抛出异常导致解压失败
                    raise
                except Exception as e:
                    logger.error(f"解压文件时出错: {str(e)}")
                    failed_overwritten.append((target_path, str(e)))
                    raise

        # 打印覆盖结果统计
        logger.info("===== 解压更新结果统计 ====")
        logger.info(f"成功覆盖的文件数量: {len(successfully_overwritten)}")
        for file_path in successfully_overwritten:
            logger.info(f"✓ {file_path}")

        if skipped_dll_files:
            logger.info(f"跳过覆盖的.dll文件数量: {len(skipped_dll_files)}")
            for file_path in skipped_dll_files:
                logger.info(f"↗ {file_path}")

        if failed_overwritten:
            logger.error(f"覆盖失败的文件数量: {len(failed_overwritten)}")
            for file_path, error in failed_overwritten:
                logger.error(f"✗ {file_path} - {error}")

        logger.info("========================")
        logger.info("更新包解压完成")

        return True
    except Exception as e:
        logger.error(f"解压更新包失败: {str(e)}")
        return False


# 获取主程序路径
def get_main_program_path():
    """\获取主程序路径"""
    # 假设主程序与更新程序在同一目录下
    main_program = "EditorDesktop.exe"
    main_program_path = os.path.join(os.getcwd(), main_program)

    # 检查主程序是否存在
    if os.path.exists(main_program_path):
        return main_program_path

    logger.warning(f"未找到主程序: {main_program_path}")
    return None

# 重启主程序
def restart_main_program():
    """重启主程序"""
    main_program_path = get_main_program_path()
    if main_program_path:
        try:
            logger.info(f"重启主程序: {main_program_path}")
            subprocess.Popen([main_program_path])
            return True
        except Exception as e:
            logger.error(f"重启主程序失败: {str(e)}")
    return False


# 修改主程序入口部分，替换临时目录的使用
if __name__ == '__main__':
    # 如果有测试参数，执行简单测试
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("执行测试模式...")
        print("=== 更新程序测试模式 ===")
        print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"命令行参数: {sys.argv}")
        print("测试完成，请检查日志文件。")
        print("按回车键退出...")
        input()
    else:
        # 完整的更新逻辑
        logger.info("更新程序启动")

        # 检查命令行参数
        if len(sys.argv) < 2:
            logger.error("缺少更新包下载链接参数")
            print("用法: update_program.exe <更新包下载链接>")
            input("按回车键退出...")
            sys.exit(1)

        download_url = sys.argv[1]
        logger.info(f"获取到更新包下载链接: {download_url}")

        # 获取update_program.exe所在目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            program_dir = os.path.dirname(sys.executable)
        else:
            # 否则使用脚本所在目录
            program_dir = os.path.dirname(os.path.abspath(__file__))

        logger.info(f"程序所在目录: {program_dir}")

        # 不再使用C盘临时目录，而是在程序所在目录创建临时文件夹
        temp_dir = os.path.join(program_dir, "update_temp")
        try:
            # 创建临时目录
            os.makedirs(temp_dir, exist_ok=True)
            logger.info(f"创建临时目录: {temp_dir}")

            # 下载更新包到程序所在目录的临时文件夹
            update_zip_path = os.path.join(temp_dir, "update.zip")
            if not download_update(download_url, update_zip_path):
                logger.error("更新失败: 下载更新包失败")
                input("按回车键退出...")
                sys.exit(1)

            # 解压更新包到程序所在目录
            if not unzip_update(update_zip_path, program_dir):
                logger.error("更新失败: 解压更新包失败")
                input("按回车键退出...")
                sys.exit(1)

        finally:
            # 清理临时目录
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"已清理临时目录: {temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {str(e)}")

        # 重启主程序
        logger.info("更新完成，准备重启主程序")
        if not restart_main_program():
            logger.error("重启主程序失败，请手动启动")

        logger.info("更新程序执行完毕")
        print("更新完成！")
        # 给用户时间查看消息
        time.sleep(2)