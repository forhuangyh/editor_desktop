from common.utils import http_post, http_form_post
from entity.account import user_info
import settings

class AccountService:
    # 从settings中获取BASE_URL配置，如果不存在则使用默认值
    @staticmethod
    def get_base_url():
        # 尝试从settings中获取BASE_URL配置
        # 如果配置不存在，则返回默认值
        base_url = settings.get("editor_api_base_url")
        return base_url

    @staticmethod
    def login(username, password):
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
            login_url = f"{AccountService.get_base_url()}/api/editor/login"
            login_data = {
                "editor_name": username,
                "editor_password": password
            }

            # 发送登录请求
            response = http_form_post(login_url, form_data=login_data)

            # 检查响应
            # 检查响应 - 修改为新的响应格式判断
            if response and "code" in response and response["code"] == 0:
                # 登录成功，从body中更新全局用户信息
                body = response.get("body", {})
                user_info.token = body.get("token", "")
                user_info.user_id = body.get("user_id", "")
                user_info.user_name = body.get("user_name", "")
                user_info.is_webeditor = body.get("is_webeditor", "")
                user_info.permissions = body.get("permissions", [])

                # 保存token等信息到本地设置
                # settings.set("auth_token", user_info.token)
                # settings.set("user_id", user_info.user_id)
                # settings.set("user_name", user_info.user_name)
                return True, None
            else:
                # 登录失败，返回错误信息
                error_message = response.get("message", "登录失败，请检查用户名和密码")
                return False, error_message
        except Exception as e:
            # 处理其他异常
            print(f"登录过程中发生错误: {str(e)}")
            return False, f"登录失败: {str(e)}"