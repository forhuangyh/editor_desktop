from xc_common.utils import http_post, http_form_post
from xc_entity.account import user_info
import settings
from xc_common.logger import get_logger
# 获取模块专属logger
logger = get_logger("account_service")

class AccountService:

    # 加入初始化函数
    def __init__(self):
        # 初始化连接
        self.base_url = settings.get("editor_api_base_url")
        # 登录接口
        self.api_login = f"{self.base_url}/api/editor/login"

    def login(self, username, password):
        """
        实现用户登录功能

        Args:
            username: 用户名
            password: 密码

        Returns:
            tuple: (是否成功, 错误信息或None)
        """
        if not username or not password:
            return False, "用户名和密码不能为空"

        try:
            # 准备登录请求数据
            login_data = {
                "editor_name": username,
                "editor_password": password
            }

            # 发送登录请求
            response = http_form_post(self.api_login, form_data=login_data)

            # 检查响应 - 修改为新的响应格式判断
            if response and "code" in response and response["code"] == 0:
                # 登录成功，从body中更新全局用户信息
                body = response.get("body", {})
                user_info.token = body.get("token", "")
                user_info.user_id = body.get("user_id", "")
                user_info.user_name = body.get("user_name", "")
                user_info.is_webeditor = body.get("is_webeditor", "")
                user_info.permissions = body.get("permissions", [])
                logger.info(f"登录成功 | 用户名: {username} | 用户ID: {user_info.user_id}")
                # 保存token等信息到本地设置
                # settings.set("auth_token", user_info.token)
                # settings.set("user_id", user_info.user_id)
                # settings.set("user_name", user_info.user_name)
                return True, None
            else:
                # 登录失败，返回错误信息
                error_message = response.get("message", "登录失败，请检查用户名和密码")
                logger.warning(f"登录失败 | 用户名: {username} | 错误信息: {error_message}")
                return False, error_message
        except Exception as e:
            # 处理其他异常
            logger.error(f"登录过程中发生错误: {str(e)}")
            return False, f"登录失败: {str(e)}"
