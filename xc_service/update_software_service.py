import data
import platform
import settings
from hy.models import Object
from xc_common.utils import http_form_post, http_file_post
from xc_common.logger import get_logger
from settings.constants import version_type
from packaging import version
# 获取模块专属logger
logger = get_logger("update_software_service")

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

    def install_update(self,download_url):
        print(f"install_update: {download_url}")

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
                        return latest_item["down_load_url"]
                    else:
                        # 没有新版本
                        logger.info(f"当前版本: {application_version}, 最新版本: {latest_version}，没有新版本")
                        return None
        return None

