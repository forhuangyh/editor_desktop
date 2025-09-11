from common.utils import http_form_post
from entity.account import user_info
import settings

class BookService:
    # 加入初始化方法
    def __init__(self):
        # 初始化连接
        self.base_url = settings.get("editor_api_base_url")
        # 替换词记录添加
        self.api_replace_add = f"{self.base_url}/api/editor/book/content_replace_add"
        # 替换词记录列表
        self.api_replace_list = f"{self.base_url}/api/editor/book/content_replace_list"


    # 保存替换词记录
    # 保存替换词记录
    def save_replace_record(self, form_data):
        """
        保存替换词记
        :param :form_data 包含的key: book_title,old_text,new_text,cp_book_id
        :return:
        """
        account_id = user_info.user_id()
        form_data["account_id"] = account_id
        # 发送请求
        response = http_form_post(self.api_replace_add, form_data=form_data)
        # 检查响应
        if response and "code" in response and response["code"] == 0:
            # 解析数据
            result_list = []
            # 检查是否有body字段且是列表
            if "body" in response and isinstance(response["body"], list):
                # 遍历body中的每个元素
                for item in response["body"]:
                    # 提取所需字段，创建新的字典对象
                    extracted_item = {
                        "id": item.get("id"),
                        "cp_book_id": item.get("cp_book_id"),
                        "account_id": item.get("account_id"),
                        "book_title": item.get("book_title"),
                        "old_text": item.get("old_text"),
                        "new_text": item.get("new_text")
                    }
                    result_list.append(extracted_item)
            return result_list
        return False

    def replace_record_list(self, form_data):
        """
        获取替换词记录列表
        :param :form_data 包含的key: cp_book_id,book_title
        :return:
        """
        # 发送请求
        response = http_form_post(self.api_replace_list, form_data=form_data)
        # 检查响应
        if response and "code" in response and response["code"] == 0:
            # 解析数据
            result_list = []
            # 检查是否有body字段且是列表
            if "body" in response and isinstance(response["body"], list):
                # 遍历body中的每个元素
                for item in response["body"]:
                    # 提取所需字段，创建新的字典对象
                    extracted_item = {
                        "id": item.get("id"),
                        "cp_book_id": item.get("cp_book_id"),
                        "account_id": item.get("account_id"),
                        "book_title": item.get("book_title"),
                        "old_text": item.get("old_text"),
                        "new_text": item.get("new_text")
                    }
                    result_list.append(extracted_item)
            return result_list
        return False


