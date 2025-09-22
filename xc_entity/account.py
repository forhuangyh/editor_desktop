# Global signal dispatcher
signal_dispatcher = None

# 定义用户信息数据模型
class UserInfo:
    def __init__(self):
        self.token = ""
        self.user_id = ""
        self.user_name = ""
        self.is_webeditor = ""
        self.permissions = ""

# 全局用户信息实例
user_info = UserInfo()