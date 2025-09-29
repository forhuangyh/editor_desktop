from PyQt6.QtWidgets import QMessageBox, QDialog, QProgressDialog, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
import os
import constants
from xc_service.book_service import book_service
from xc_gui.q_message_box import CustomMessageBox
from xc_gui.progress_dialog import UploadProgressDialog


def handle_book_upload(main_window, file_path):
    """处理书籍上传的核心逻辑（增加进度遮罩和状态轮询）"""
    try:
        # 提取文件名和初始cp_book_id
        file_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        initial_cp_book_id = file_name_without_ext.split('_')[0]

        if not initial_cp_book_id:
            CustomMessageBox.warning(
                main_window, "警告", "无法从文件名解析平台书籍ID", 400, 120
            )
            return

        # 【第一处使用公共组件】查询书籍信息遮罩
        info_dialog = UploadProgressDialog(main_window, file_name)
        info_dialog.update_status("查询书籍信息中", "正在请求网络数据...")  # 现在会调用公共组件的 update_status 方法
        info_dialog.setModal(True)
        info_dialog.show()
        # 强制刷新UI，确保遮罩框显示（关键修复）
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()  # 立即处理UI渲染事件
        try:
            # 验证书籍信息
            book_info = book_service.get_book_info(initial_cp_book_id)

            if not book_info:
                info_dialog.close()  # 新增：关闭查询遮罩

                CustomMessageBox.warning(
                    main_window, "书籍信息不存在",
                    f"未找到平台书籍ID为「{initial_cp_book_id}」的书籍信息", 450, 150
                )
                return

            actual_cp_book_id = book_info.get("oper_book_id")
            if not actual_cp_book_id:
                info_dialog.close()  # 新增：关闭查询遮罩

                CustomMessageBox.warning(
                    main_window, "数据异常", "获取的书籍信息中缺少平台书籍ID", 400, 120
                )
                return
        except Exception as e:
            info_dialog.close()  # 新增：关闭查询遮罩

            CustomMessageBox.warning(
                main_window, "数据异常", "请求书籍信息失败", 400, 120
            )

        finally:
            info_dialog.close()

        # 显示上传确认窗
        message = f'<html>确定要上传并覆盖编辑系统上的书籍（<b><font color="red">ID: {actual_cp_book_id}</font></b>）:<br><br>「<b><font color="red">{file_name}</font></b>」吗？</html>'
        reply = CustomMessageBox.question(main_window, "确认上传覆盖", message, 480, 200)

        if reply != QDialog.DialogCode.Accepted:
            main_window.display.repl_display_message("用户取消上传", message_type=constants.MessageType.WARNING)
            return

        # 【第二处使用公共组件】上传进度遮罩（轮询期间保持）
        upload_dialog = UploadProgressDialog(main_window, file_name)
        upload_dialog.update_status("书籍覆盖", "上传覆盖文件读取本地文件中...")  # 动态更新文本
        upload_dialog.setModal(True)
        upload_dialog.show()
        # 强制刷新UI，确保遮罩框显示（关键修复）
        QApplication.processEvents()  # 立即处理UI渲染事件

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # 【新增】更新状态为"上传文件中"
        upload_dialog.update_status("书籍覆盖", "读取本地文件完成，上传服务器中...")
        QApplication.processEvents()  # 刷新UI显示新状态
        # 调用上传服务
        upload_success, db_task_id = book_service.upload_book(actual_cp_book_id, file_content, file_name)

        if not upload_success:
            upload_dialog.close()  # 修正：变量名应为upload_dialog而非progress_dialog
            CustomMessageBox.critical(main_window, "上传失败", "文件上传请求提交失败", 400, 120)
            return
        upload_dialog.update_status("书籍覆盖", "上传文件完成，获取覆盖任务状态中...")
        QApplication.processEvents()  # 刷新UI显示新状态
        # 验证db_task_id有效性
        if not db_task_id:
            upload_dialog.close()  # 修正：变量名应为upload_dialog而非progress_dialog
            CustomMessageBox.warning(
                main_window,
                "警告",
                "无法获取任务ID，无法跟踪上传进度",
                450, 150
            )
            return
        # 设置定时器轮询任务状态
        timer = QTimer()
        task_status = 0  # 0:进行中, 2:成功, 3:失败

        # 轮询任务状态时更新遮罩文本
        def check_task_status():
            nonlocal task_status
            task_info = book_service.get_book_overwrite_task(db_task_id)

            if not task_info:
                upload_dialog.update_status("上传覆盖文件中", "查询任务状态失败")  # 使用公共组件的更新方法
                return

            task_status = task_info.get("task_status", 0)
            if task_status == 2:  # 成功
                timer.stop()
                upload_dialog.close()
                CustomMessageBox.information(  # 恢复被省略的成功逻辑代码
                    main_window, "上传成功", f"文件 '{file_name}' 已成功上传", 400, 120
                )
                # main_window.display.repl_display_success(f"文件 '{file_name}' 上传成功")
            elif task_status == 3:  # 失败
                timer.stop()
                upload_dialog.close()
                fail_reason = task_info.get("task_fail_reason", "未知原因")
                CustomMessageBox.critical(
                    main_window, "上传失败", f"文件上传失败: {fail_reason}", 450, 150
                )
                # main_window.display.repl_display_error(f"文件 '{file_name}' 上传失败: {fail_reason}")
        # 设置定时器每秒查询一次
        timer.timeout.connect(check_task_status)
        timer.start(2000)  # 1000ms = 1秒
        check_task_status()  # 立即执行一次
    except Exception as e:
        CustomMessageBox.critical(
            main_window, "上传失败", f"文件上传失败", 450, 150
        )
        # main_window.display.repl_display_error(f"上传处理异常: {str(e)}")
