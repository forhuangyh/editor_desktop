import os
import concurrent.futures
from xc_common.utils import http_form_post
from xc_entity.account import user_info
import settings
from xc_service.sqlite_service import sqlite_service


class BookService:
    # 加入初始化方法
    def __init__(self):
        # 初始化连接
        self.base_url = settings.get("editor_api_base_url")
        self.account_id = user_info.user_id
        self.headers = {
            "Authorization": f"Token {user_info.token}",
        }

        # 替换词记录添加
        self.api_replace_add = f"{self.base_url}/api/editor/book/content_replace_add"
        # 替换词记录列表
        self.api_replace_list = f"{self.base_url}/api/editor/book/content_replace_list"
        # 书籍基本信息
        self.api_book_info = f"{self.base_url}/api/editor_v1/book/get_book_info"
        # 章节信息列表
        self.api_chapter_info = f"{self.base_url}/api/editor_v1/chapter/get_all_chapters"
        # 单章节内容下载
        self.api_chapter_content = f"{self.base_url}/api/editor_v1/chapter/chapter_content"

    # 统一校验结果
    def check_response(self, response):
        """
        统一校验结果
        :param response:
        :return:
        """
        if response and "code" in response and response["code"] == 0:
            return True
        return False

    # 保存替换词记录
    def save_replace_record(self, form_data):
        """
        保存替换词记
        :param :form_data 包含的key: book_title,old_text,new_text,cp_book_id
        :return:
        """
        form_data["account_id"] = self.account_id
        # 发送请求
        response = http_form_post(self.api_replace_add, form_data=form_data, headers=self.headers)
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
                        "cp_book_id": item.get("cp_book_id"),
                        "account_id": item.get("account_id"),
                        "book_title": item.get("book_title"),
                        "old_text": item.get("old_text"),
                        "new_text": item.get("new_text")
                    }
                    result_list.append(extracted_item)
                return result_list
        return None

    def replace_record_list(self, form_data):
        """
        获取替换词记录列表
        :param :form_data 包含的key: cp_book_id,book_title
        :return:
        """
        # 发送请求
        response = http_form_post(self.api_replace_list, form_data=form_data, headers=self.headers)
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
                        "cp_book_id": item.get("cp_book_id"),
                        "account_id": item.get("account_id"),
                        "book_title": item.get("book_title"),
                        "old_text": item.get("old_text"),
                        "new_text": item.get("new_text")
                    }
                    result_list.append(extracted_item)
                return result_list
        return False

    # 获取书籍基本信息和章节列表
    def book_info(self, cp_book_id):
        """
        获取书籍基本信息和章节列表
        :param :form_data 包含的key: cp_book_id
        :return:
        """
        form_data = {"book_id": cp_book_id}
        # 发送请求
        response = http_form_post(self.api_book_info, form_data=form_data, headers=self.headers)
        # 检查响应
        if self.check_response(response):
            # 解析数据
            result = {}
            # 检查是否有body字段
            if "body" in response and isinstance(response["body"], dict):
                # 提取所需字段，创建新的字典对象
                result = {
                    "book_id": response["body"].get("book_id"),
                    "cp_book_id": response["body"].get("oper_book_id"),
                    "title": response["body"].get("title"),
                    "language": response["body"].get("language"),
                    "cover_url": response["body"].get("cover_url"),
                    "intro": response["body"].get("intro")
                }

                # 如果存在result
                if result:
                    # 查询章节列表接口
                    book_id = response["body"].get("book_id")
                    account_id = self.account_id
                    page = 1
                    limit = 10000
                    chapter_form_data = {"book_id": book_id, "account_id": account_id, "page": page, "limit": limit}
                    # 发送请求
                    chapter_response = http_form_post(self.api_chapter_info, form_data=chapter_form_data,
                                                      headers=self.headers)
                    # 检查响应
                    if self.check_response(chapter_response):
                        # 解析数据
                        chapter_result_list = []
                        # 检查是否有body字段且是列表
                        if "body" in chapter_response and isinstance(chapter_response["body"], list):
                            # 遍历body中的每个元素
                            for item in chapter_response["body"]:
                                # 提取所需字段，创建新的字典对象
                                extracted_item = {
                                    "chapter_id": item.get("chapter_id"),
                                    "book_id": item.get("book_id"),
                                    "chapter_title": item.get("chapter_title"),
                                    "cp_book_id": item.get("oper_book_id"),
                                    "index": item.get("index"),
                                    "oss_url": item.get("oss_url"),
                                }
                                chapter_result_list.append(extracted_item)
                        if not chapter_result_list:
                            print(f"书籍ID:{cp_book_id}未获取到书籍章节基本信息数据")
                            return None
                        result["chapter_list"] = chapter_result_list
                        result["total_chapters"] = len(chapter_result_list)
                        return result
                else:
                    print(f"书籍ID:{cp_book_id}未获取到书籍基本信息数据")
                    return None
        print(f"书籍ID:{cp_book_id}未获取到书籍基本信息数据")
        return None

        # 完善目录检查方法（确保正确创建文件夹）

    def check_download_dir(self, book_id, cp_book_id):
        """检查并创建下载目录（仅保留down_load_books根目录）"""
        exco_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco')
        # 仅创建down_load_books根目录，不添加书籍子目录
        download_dir = os.path.join(exco_dir, 'down_load_books')

        print(f"【下载目录】检查 | 目标根目录: '{download_dir}'")

        # 确保根目录存在（递归创建所有不存在的父目录）
        os.makedirs(download_dir, exist_ok=True)
        print(f"【下载目录】根目录准备完成 | 路径: '{download_dir}'")

        return download_dir

    def download_book(self, id):
        import json
        from xc_service.sqlite_service import SQLiteService
        print(f"\n【下载】开始下载书籍 | 本地记录ID: {id}")

        try:
            # 获取本地书籍记录
            db_service = SQLiteService()
            record = db_service.get_book_by_id(id)
            db_service.close()

            if not record:
                print(f"【下载】失败 | 本地记录ID: {id} | 记录不存在")
                return False

            book_id = record.get("book_id")
            cp_book_id = record.get("cp_book_id")
            title = record.get("title", "未知标题")
            print(f"【下载】本地记录加载成功 | 本地ID: {id} | 书籍ID: {book_id} | 来源ID: {cp_book_id} | 标题: '{title}'")

            # 检查文件是否已存在
            # 新增：调用目录检查方法，确保文件夹存在
            download_dir = self.check_download_dir(book_id, cp_book_id)  # 假设新增此方法参数
            file_name = f"{cp_book_id}_{id}.txt"
            file_path = os.path.join(download_dir, file_name)  # 使用检查后的目录

            if os.path.exists(file_path):
                print(f"【下载】文件已存在 | 跳过下载 | 路径: '{file_path}'")
                return True
            print(
                f"【下载】目标文件路径: '{file_path}' | 文件大小: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} bytes")

            # 解析章节列表
            chapter_list_str = record.get('chapter_list', '[]')
            chapter_list = json.loads(chapter_list_str) if chapter_list_str else []
            if not chapter_list:
                print(f"【下载】章节列表为空 | 本地ID: {id}")
                return False
            print(
                f"【下载】章节列表解析完成 | 章节总数: {len(chapter_list)} | 最小索引: {min((c.get('index') for c in chapter_list), default=0)} | 最大索引: {max((c.get('index') for c in chapter_list), default=0)}")

            # 过滤需要下载的章节
            chapters_to_download = []
            for idx, chapter in enumerate(chapter_list):
                chapter_id = chapter.get("chapter_id")
                index = chapter.get("index")
                if not chapter_id or index is None:
                    print(f"【下载】章节过滤失败 | 本地ID: {id} | 章节索引: {idx} | 缺少chapter_id/index")
                    return False
                chapters_to_download.append({'chapter': chapter, 'index': index})
            print(f"【下载】章节过滤完成 | 待下载章节数: {len(chapters_to_download)}")

            # 章节下载函数
            def download_single_chapter(chapter_info):
                chapter = chapter_info['chapter']
                chapter_id = chapter.get("chapter_id")
                index = chapter_info['index']
                chapter_title = chapter.get("chapter_title", f"第{index}章")
                print(f"【下载】章节开始 | 章节ID: {chapter_id} | 索引: {index} | 标题: '{chapter_title}'")

                try:
                    response = http_form_post(
                        self.api_chapter_content,
                        form_data={"book_id": book_id, "chapter_id": chapter_id, "account_id": self.account_id},
                        headers=self.headers
                    )

                    if not self.check_response(response) or "body" not in response:
                        print(f"【下载】章节失败 | 章节ID: {chapter_id} | 响应无效: {response}")
                        return False

                    content = response["body"].get("content", "").strip()
                    if not content:
                        print(f"【下载】章节内容为空 | 章节ID: {chapter_id} | 标题: '{chapter_title}'")
                        return False

                    print(
                        f"【下载】章节成功 | 章节ID: {chapter_id} | 标题: '{chapter_title}' | 内容长度: {len(content)} bytes")
                    return (index, chapter_title, content)
                except Exception as e:
                    print(f"【下载】章节异常 | 章节ID: {chapter_id} | 错误: {str(e)}")
                    return False

            # 多线程下载与合并
            success = True
            chapters_content = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(download_single_chapter, info): info for info in chapters_to_download}
                for future in concurrent.futures.as_completed(futures):
                    if not success:
                        future.cancel()
                        continue
                    result = future.result()
                    if result is False:
                        success = False
                        print(f"【下载】章节批量失败 | 取消剩余下载")
                    else:
                        chapters_content.append(result)

            if not success or len(chapters_content) != len(chapters_to_download):
                print(f"【下载】合并失败 | 成功下载: {len(chapters_content)}/{len(chapters_to_download)}章节")
                return False

            # 排序并合并内容
            chapters_content.sort(key=lambda x: x[0])
            full_content = "\n\n".join([f"{title}\n{content}" for idx, title, content in chapters_content])
            print(f"【下载】内容合并完成 | 总章节: {len(chapters_content)} | 合并后大小: {len(full_content)} bytes")

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            print(
                f"【下载】成功完成 | 本地ID: {id} | 文件路径: '{file_path}' | 文件大小: {os.path.getsize(file_path)} bytes")
            return True

        except json.JSONDecodeError as e:
            print(f"【下载】JSON解析失败 | 本地ID: {id} | 错误: {str(e)} | 章节列表: {record.get('chapter_list', '')}")
        except Exception as e:
            print(f"【下载】总异常 | 本地ID: {id} | 错误类型: {type(e).__name__} | 详情: {str(e)}")
        return False


