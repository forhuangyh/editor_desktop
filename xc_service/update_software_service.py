import sys
import data
import platform
import settings
import os
import shutil
import zipfile
import requests
import tempfile
import qt
from hy.models import Object
from xc_common.utils import http_form_post, http_file_post
from xc_common.logger import get_logger
from settings.constants import version_type
from packaging import version
# 获取模块专属logger
logger = get_logger("update_software_service")
exco_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(exco_path)
class UpdateSoftwareService(Object):
    # 加入初始化方法
    def __init__(self):
        # 初始化连接
        self.base_url = settings.get("editor_api_base_url")
        self.headers = {
        }
        # 获取env配置
        self.env_config = f"{self.base_url}/api/editor_v1/editor_desktop/env_configs"

    def check_response(self, response):
        """
        统一校验结果
        :param response:
        :return:
        """
        if response and "code" in response and response["code"] == 0:
            return True
        return False

    def install_update(self, download_url, parent_window=None):
        """
        根据下载链接下载安装zip包，展示下载进度条，然后解压到当前目录里覆盖同名文件夹
        :param download_url: 下载链接
        :param parent_window: 父窗口，用于显示进度条对话框
        """
        logger.info(f"开始下载更新包: {download_url}")

        try:
            # 获取当前工作目录作为解压目标路径
            target_dir = os.getcwd()
            logger.info(f"解压目标目录: {target_dir}")

            # 创建临时文件来保存下载的zip包
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                zip_path = temp_file.name

            # 下载文件并显示进度条
            self._download_with_progress(download_url, zip_path, parent_window)

            # 解压文件到当前目录，覆盖同名文件夹
            self._unzip_file(zip_path, target_dir, parent_window)

            # 删除临时zip文件
            os.remove(zip_path)
            logger.info("更新包解压完成，临时文件已删除")

        except Exception as e:
            logger.error(f"安装更新失败: {str(e)}")
            # 确保临时文件被清理
            if 'zip_path' in locals() and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            raise

    def _download_with_progress(self, url, save_path, parent_window=None):
        """
        下载文件并显示进度条
        :param url: 下载链接
        :param save_path: 保存路径
        :param parent_window: 父窗口，用于显示进度条对话框
        """
        # 发送请求获取文件大小
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 如果请求失败，抛出异常

        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))

        # 创建Qt进度条对话框
        progress_dialog = qt.QProgressDialog("下载更新包...", "取消", 0, total_size, parent_window)
        progress_dialog.setWindowTitle("更新下载")
        progress_dialog.setWindowModality(qt.Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)  # 立即显示进度条
        progress_dialog.setValue(0)

        # 下载文件并更新进度条
        with open(save_path, 'wb') as file:
            downloaded_size = 0
            for data_chunk in response.iter_content(chunk_size=8192):
                if progress_dialog.wasCanceled():
                    response.close()
                    raise InterruptedError("下载被用户取消")

                file.write(data_chunk)
                downloaded_size += len(data_chunk)
                progress_dialog.setValue(downloaded_size)

                # 更新进度信息
                progress_percent = int((downloaded_size / total_size) * 100) if total_size > 0 else 0
                progress_dialog.setLabelText(
                    f"下载更新包... {progress_percent}% ({self._format_size(downloaded_size)} / {self._format_size(total_size)})")

                # 处理Qt事件，确保进度条响应
                qt.QApplication.processEvents()

        logger.info(f"更新包下载完成，保存路径: {save_path}")

    def _unzip_file(self, zip_path, target_dir, parent_window=None):
        """
        解压zip文件到目标目录，覆盖同名文件夹
        :param zip_path: zip文件路径
        :param target_dir: 目标目录
        :param parent_window: 父窗口，用于显示进度条对话框
        """
        # 确保目标目录存在
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 解压zip文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取zip文件中的所有文件和目录
            all_members = zip_ref.namelist()

            # 检查zip文件是否有单层根目录结构
            # 例如: zip文件中所有内容都在一个名为"app_v1.0"的根目录下
            root_dirs = set()
            for member in all_members:
                # 分割路径，获取第一个目录
                parts = member.split('/')
                if len(parts) > 1 and parts[0] and not parts[0].startswith('.'):
                    root_dirs.add(parts[0])

            # 判断是否存在单一的根目录
            has_single_root_dir = len(root_dirs) == 1 and all(
                member.startswith(list(root_dirs)[0] + '/') for member in all_members if member not in root_dirs)

            # 创建Qt进度条对话框
            progress_dialog = qt.QProgressDialog("解压更新包...", "取消", 0, len(all_members), parent_window)
            progress_dialog.setWindowTitle("更新解压")
            progress_dialog.setWindowModality(qt.Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)  # 立即显示进度条
            progress_dialog.setValue(0)

            for i, member in enumerate(all_members):
                if progress_dialog.wasCanceled():
                    raise InterruptedError("解压被用户取消")

                # 处理有单一根目录的情况
                if has_single_root_dir:
                    root_dir = list(root_dirs)[0]
                    # 如果成员路径以根目录开头，则移除根目录部分
                    if member.startswith(root_dir + '/'):
                        # 计算新的成员路径（去掉根目录）
                        relative_path = member[len(root_dir) + 1:]
                        # 如果去掉根目录后路径为空，则跳过（这是根目录本身）
                        if not relative_path:
                            progress_dialog.setValue(i + 1)
                            qt.QApplication.processEvents()
                            continue
                        # 构造目标路径
                        target_path = os.path.join(target_dir, relative_path)
                    else:
                        # 不处理根目录本身
                        progress_dialog.setValue(i + 1)
                        qt.QApplication.processEvents()
                        continue
                else:
                    # 没有单一根目录的情况，直接使用原始路径
                    target_path = os.path.join(target_dir, member)

                # 确保目录存在
                parent_dir = os.path.dirname(target_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)

                # 检查是否为目录（以/结尾的通常是目录）
                if member.endswith('/'):
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                else:
                    # 读取zip中的文件内容并写入目标文件，覆盖现有文件
                    try:
                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    except Exception as e:
                        logger.warning(f"解压文件 {member} 到 {target_path} 失败: {str(e)}")
                        # 继续解压其他文件，不中断整个过程

                # 更新进度条
                progress_dialog.setValue(i + 1)
                progress_dialog.setLabelText(f"解压更新包... {i + 1}/{len(all_members)} 文件")

                # 处理Qt事件，确保进度条响应
                qt.QApplication.processEvents()

        logger.info(f"更新包解压完成，解压到: {target_dir}")

    def _format_size(self, size_bytes):
        """\格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def _get_os_type(self):
        """检测当前操作系统类型"""
        system = platform.system().lower()
        if "windows" in system:
            return "windows"
        elif "darwin" in system:  # macOS的内核名称是Darwin
            return "macos"
        else:
            return "other"

    def check_update(self):
        """
        获取AWS配置
        """
        form_data = {}
        # 发送请求
        response = http_form_post(self.env_config, form_data=form_data, headers=self.headers)
        # 检查响应
        if self.check_response(response):
            # 解析数据
            result_list = []
            # 检查是否有body字段且是列表
            if "body" in response and isinstance(response["body"], list):
                # 遍历body中的每个元素
                for item in response["body"]:
                    # 提取所需字段，创建新的字典对象
                    extracted_item = {
                        "id": item.get("id"),
                        "environment": item.get("environment"),
                        "version_old": item.get("version_old"),
                        "version_new": item.get("version_new"),
                        "down_load_url": item.get("down_load_url"),
                        "is_active": item.get("is_active")
                    }
                    result_list.append(extracted_item)
                # 获取当前的环境 version_type 一致后， 再判断版本号，如果服务器上的 version_new 大于当前版本号，说明有新的版本，返回下载地址
                # 过滤出 version_type 一致的项
                filtered_list = [item for item in result_list if item["environment"] == version_type]
                # 检查是否有新的版本
                if filtered_list:
                    # 取版本号最大的项
                    latest_item = max(filtered_list, key=lambda x: x["version_new"])
                    # 比较版本号 这个版本号是在 data.py 里的 version 变量
                    application_version = data.application_version
                    latest_version = latest_item["version_new"]
                    # 版本号是 1.2 、1.0 、2.0 比较大小
                    if version.parse(latest_version) > version.parse(application_version):
                        # 有新版本
                        logger.info(f"发现新版本，当前版本: {application_version}, 最新版本: {latest_version}")
                        return latest_item["down_load_url"], latest_version
                    else:
                        # 没有新版本
                        logger.info(f"当前版本: {application_version}, 最新版本: {latest_version}，没有新版本")
                        return None
        return None

