import os
import concurrent.futures
from xc_common.utils import http_form_post, http_file_post
from xc_entity.account import user_info
import settings
from xc_common.logger import get_logger
from urllib.parse import urlparse
from utilities.aws_s3 import aws_oss_singleton  # 导入全局单例实例
# 获取模块专属logger
logger = get_logger("book_service")

class BookService:
    # 加入初始化方法
    def __init__(self):

        # 设置prefix变量，用于S3路径构建
        self.prefix ='chapter_txt'
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
        # 书籍基本信息列表查下
        self.api_book_info_list = f"{self.base_url}/api/editor_v1/book/get_all_books"
        # 书籍覆盖
        self.api_book_overwrite = f"{self.base_url}/api/editor_v1/book/overwrite_book"
        # 查下任务状态
        self.api_book_overwrite_task = f"{self.base_url}/api/editor_v1/task_list_scope"
        # 获取AWS配置
        self.aws_config = f"{self.base_url}/api/editor_v1/editor_desktop/env_configs"

    def get_aws_configs(self):
        """
        获取AWS配置
        """
        form_data = {"account_id": self.account_id}
        # 发送请求
        response = http_form_post(self.aws_config, form_data=form_data, headers=self.headers)
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
                        "aws_region": item.get("aws_region"),
                        "aws_access_key_id": item.get("aws_access_key_id"),
                        "aws_secret_key": item.get("aws_secret_key"),
                        "aws_fast_url": item.get("aws_fast_url"),
                        "aws_s3_bucket_name": item.get("aws_s3_bucket_name"),
                        "aws_endpoint": item.get("aws_endpoint"),
                        "is_active": item.get("is_active")
                    }
                    result_list.append(extracted_item)
                return result_list
        return None

    # 从s3桶里获取章节文本内容
    def getTxtStrFromS3(self, book_id, chapter_cid):
        path = f"{self.prefix}/{book_id}/{chapter_cid}.txt"
        # 直接使用全局单例实例
        content = aws_oss_singleton.get_s3_content(path)
        return content


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
        bookinfo = self.get_book_info(cp_book_id=cp_book_id)
        if not bookinfo:
            logger.warning(f"【获取书籍基本信息】失败 | 平台书籍ID: {cp_book_id} | 未找到书籍信息")
            return None
        bk_id = bookinfo.get("book_id")
        form_data = {"book_id": bk_id}
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
                                    "chapter_cid": item.get("chapter_cid"),
                                    "book_id": item.get("book_id"),
                                    "chapter_title": item.get("chapter_title"),
                                    "cp_book_id": item.get("oper_book_id"),
                                    "index": item.get("index"),
                                    "oss_url": item.get("oss_url"),
                                }
                                chapter_result_list.append(extracted_item)
                        if not chapter_result_list:
                            logger.info(f"书籍ID:{cp_book_id}未获取到书籍章节基本信息数据")
                            return None
                        result["chapter_list"] = chapter_result_list
                        result["total_chapters"] = len(chapter_result_list)
                        return result
                else:
                    logger.info(f"书籍ID:{cp_book_id}未获取到书籍基本信息数据")
                    return None
        logger.info(f"书籍ID:{cp_book_id}未获取到书籍基本信息数据")
        return None

        # 完善目录检查方法（确保正确创建文件夹）

    def check_download_dir(self, book_id, cp_book_id):
        """检查并创建下载目录（仅保留down_load_books根目录）"""
        exco_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco')
        # 仅创建down_load_books根目录，不添加书籍子目录
        download_dir = os.path.join(exco_dir, 'down_load_books')

        logger.info(f"【下载目录】检查 | 目标根目录: '{download_dir}'")

        # 确保根目录存在（递归创建所有不存在的父目录）
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"【下载目录】根目录准备完成 | 路径: '{download_dir}'")

        return download_dir

    def download_book(self, id):
        import json
        from xc_service.sqlite_service import SQLiteService
        logger.info(f"【下载】开始下载书籍 | 本地记录ID: {id}")

        try:
            # 获取本地书籍记录
            db_service = SQLiteService()
            record = db_service.get_book_by_id(id)
            db_service.close()

            if not record:
                logger.warning(f"【下载】失败 | 本地记录ID: {id} | 记录不存在")
                return False

            book_id = record.get("book_id")
            cp_book_id = record.get("cp_book_id")
            title = record.get("title", "未知标题")
            logger.info(f"【下载】本地记录加载成功 | 本地ID: {id} | 书籍ID: {book_id} | 来源ID: {cp_book_id} | 标题: '{title}'")

            # 检查文件是否已存在
            # 新增：调用目录检查方法，确保文件夹存在
            download_dir = self.check_download_dir(book_id, cp_book_id)  # 假设新增此方法参数
            file_name = f"{cp_book_id}_{id}_{book_id}.txt"
            file_path = os.path.join(download_dir, file_name)  # 使用检查后的目录

            if os.path.exists(file_path):
                logger.warning(f"【下载】文件已存在 | 跳过下载 | 路径: '{file_path}'")
                return True
            logger.info(
                f"【下载】目标文件路径: '{file_path}' | 文件大小: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} bytes")

            # 解析章节列表
            chapter_list_str = record.get('chapter_list', '[]')
            chapter_list = json.loads(chapter_list_str) if chapter_list_str else []
            if not chapter_list:
                logger.error(f"【下载】章节列表为空 | 本地ID: {id}")
                return False
            logger.info(
                f"【下载】章节列表解析完成 | 章节总数: {len(chapter_list)} | 最小索引: {min((c.get('index') for c in chapter_list), default=0)} | 最大索引: {max((c.get('index') for c in chapter_list), default=0)}")

            # 过滤需要下载的章节
            chapters_to_download = []
            for idx, chapter in enumerate(chapter_list):
                chapter_id = chapter.get("chapter_id")
                index = chapter.get("index")
                if not chapter_id or index is None:
                    logger.error(f"【下载】章节过滤失败 | 本地ID: {id} | 章节索引: {idx} | 缺少chapter_id/index")
                    return False
                chapters_to_download.append({'chapter': chapter, 'index': index})
            logger.info(f"【下载】章节过滤完成 | 待下载章节数: {len(chapters_to_download)}")

            # 章节下载函数
            def download_single_chapter(chapter_info):
                chapter = chapter_info['chapter']
                index = chapter['index']
                chapter_cid = chapter['chapter_cid']
                chapter_title = chapter.get("chapter_title", f"第{index}章")

                chapter_id = chapter.get("chapter_id")
                logger.info(f"【下载】章节开始 | 章节ID: {chapter_id} | 索引: {index} | 标题: '{chapter_title}'")

                oss_url = chapter.get("oss_url")  # "oss_url": "https://xcyh-author-staging-txt.s3.amazonaws.com/chapter_txt/3109/wpjMZjB7q8wO2kYL.txt",
                # oss_url 去掉 域名 保留域名后面的
                oss_path = urlparse(oss_url).path if oss_url else ""  # 【新增】解析URL获取域名后的路径（如：/chapter_txt/3109/wpjMZjB7q8wO2kYL.txt）
                if not oss_path:
                    logger.error(f"【下载】解析章节桶路径错误 | 章节ID: {chapter_id} | 标题: '{chapter_title}'")
                    return False

                try:
                    # response = http_form_post(
                    #     self.api_chapter_content,
                    #     form_data={"book_id": book_id, "chapter_id": chapter_id, "account_id": self.account_id},
                    #     headers=self.headers
                    # )
                    #
                    # if not self.check_response(response) or "body" not in response:
                    #     logger.error(f"【下载】章节失败 | 章节ID: {chapter_id} | 响应无效: {response}")
                    #     return False

                    # 调用 AwsOSS get 获取章节内容

                    content = self.getTxtStrFromS3(book_id,chapter_cid)
                    if not content:
                        logger.error(f"【下载】章节内容为空 | 章节ID: {chapter_id} | 标题: '{chapter_title}'")
                        return False

                    logger.info(
                        f"【下载】章节成功 success | 章节ID: {chapter_id} | 标题: '{chapter_title}'")
                    return (index, chapter_title, content)
                except Exception as e:
                    logger.error(f"【下载】章节异常 fail | 章节ID: {chapter_id} | 错误: {str(e)}")
                    return False

            # 多线程下载与合并
            success = True
            chapters_content = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(download_single_chapter, info): info for info in chapters_to_download}
                for future in concurrent.futures.as_completed(futures):
                    if not success:
                        future.cancel()
                        continue
                    result = future.result()
                    if result is False:
                        success = False
                        logger.error(f"【下载】章节批量失败 | 取消剩余下载")
                        # 【新增】取消所有剩余未完成的任务
                        for pending_future in futures:
                            if not pending_future.done():
                                pending_future.cancel()
                        break  # 【新增】跳出循环，不再处理后续任务
                    else:
                        chapters_content.append(result)

            if not success or len(chapters_content) != len(chapters_to_download):
                logger.error(f"【下载】合并失败 | 成功下载: {len(chapters_content)}/{len(chapters_to_download)}章节")
                return False

            # 排序并合并内容
            chapters_content.sort(key=lambda x: x[0])
            full_content = "\n\n".join([f"{title}\n{content}" for idx, title, content in chapters_content])
            logger.info(f"【下载】内容合并完成 | 总章节: {len(chapters_content)} | 合并后大小: {len(full_content)} bytes")

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            logger.info(
                f"【下载】成功完成 | 本地ID: {id} | 文件路径: '{file_path}' | 文件大小: {os.path.getsize(file_path)} bytes")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"【下载】JSON解析失败 | 本地ID: {id} | 错误: {str(e)} | 章节列表: {record.get('chapter_list', '')}")
        except Exception as e:
            logger.error(f"【下载】总异常 | 本地ID: {id} | 错误类型: {type(e).__name__} | 详情: {str(e)}")
        return False

    # 获取书籍基本信息
    def get_book_info(self, cp_book_id):
        """获取书籍基本信息"""
        if not cp_book_id:
            logger.warning(f"【获取书籍基本信息】失败 | 平台书籍ID: {cp_book_id} | 错误: 书籍ID不能为空")
            return None

        response = http_form_post(
            self.api_book_info_list,
            form_data={"book_id": cp_book_id, "account_id": self.account_id},
            headers=self.headers
        )

        if not self.check_response(response) or "body" not in response:
            logger.warning(f"【获取书籍基本信息】失败 | 平台书籍ID: {cp_book_id} | 响应无效: {response}")
            return None

        # 新增：从body中提取items数组并查找匹配记录
        body = response["body"]
        items = body.get("items", [])

        # 验证items是否为列表
        if not isinstance(items, list):
            logger.error(f"【获取书籍基本信息】失败 | 平台书籍ID: {cp_book_id} | 响应items格式错误")
            return None

        # 遍历items查找oper_book_id完全匹配的记录
        for item in items:
            if item.get("oper_book_id") == cp_book_id:
                logger.warning(f"【获取书籍基本信息】成功 | 平台书籍ID: {cp_book_id} | 找到匹配记录")
                return item

        # 未找到匹配记录
        logger.info(f"【获取书籍基本信息】失败 | 平台书籍ID: {cp_book_id} | 未找到匹配书籍")
        return None

    # 上传覆盖书籍
    def upload_book(self, cp_book_id: str, file_content: str, file_name: str) -> bool:
        """上传覆盖书籍
        Args:
            cp_book_id: 平台书籍ID (oper_book_id)
            file_content: 书籍内容字符串
            file_name: 文件名
        Returns:
            bool: 是否上传请求成功提交
        """
        # 判断数据是否存在
        if not cp_book_id or not file_content or not file_name:
            logger.info(f"【上传书籍】失败 | 平台书籍ID: {cp_book_id} | 错误: 书籍ID、文件内容和文件名不能为空")
            return False, ""

        # 获取书籍信息以获取内部book_id
        book_info = self.get_book_info(cp_book_id)
        if not book_info:
            logger.warning(f"【上传书籍】失败 | 平台书籍ID: {cp_book_id} | 错误: 未找到书籍信息")
            return False, ""

        book_id = book_info.get("book_id")
        # 验证book_id是否为有效数字类型
        if not book_id or not isinstance(book_id, (int, float)):
            logger.info(f"【上传书籍】失败 | 平台书籍ID: {cp_book_id} | 错误: 获取到的book_id不是有效数字 (值: {book_id})")
            return False, ""

        try:
            response = http_file_post(
                url=self.api_book_overwrite,
                file_content=file_content,
                filename=file_name,
                form_data={
                    "book_id": book_id,
                    "account_id": str(self.account_id)
                },
                headers=self.headers
            )

            # 检查响应是否有效
            if not response:
                logger.error(f"【上传书籍】失败 | 平台书籍ID: {cp_book_id} | 错误: 未收到有效响应")
                return False, ""

            # 检查响应状态码（使用统一的check_response方法）
            if self.check_response(response):
                # 解析异步任务信息
                task_info = response.get("body", {})
                task_id = task_info.get("celery_task_id", "")
                db_task_id = task_info.get("db_task_id", "")
                task_status = task_info.get("celery_task_status", "")
                logger.info(f"【上传书籍】请求提交成功 | 平台书籍ID: {cp_book_id} | 任务ID: {task_id} | 状态: {task_status}")
                return True, db_task_id
            else:
                error_msg = response.get("message", "未知错误")
                logger.error(f"【上传书籍】失败 | 平台书籍ID: {cp_book_id} | 错误: {error_msg} | 响应码: {response.get('code')}")
                return False, ""

        except Exception as e:
            logger.error(f"【上传书籍】异常 | 平台书籍ID: {cp_book_id} | 错误: {str(e)}")
            return False, ""

    # 查下覆盖任务状态api_book_overwrite_task
    def get_book_overwrite_task(self, task_id):
        """查询覆盖任务状态
        Args:
            task_id: 任务ID（db_task_id）
        Returns:
            任务状态字典，如果查询失败则返回None
        """
        # 参数校验
        if not task_id:
            logger.error(f"【查询任务状态】失败 | 任务ID: {task_id} | 错误: 任务ID不能为空")
            return None

        try:
            # 发送请求（表单数据包含task_id和account_id）
            response = http_form_post(
                self.api_book_overwrite_task,
                form_data={
                    "task_id": str(task_id),
                    "account_id": self.account_id
                },
                headers=self.headers
            )

            # 检查响应是否有效
            if not self.check_response(response):
                error_msg = response.get("message", "未知错误") if response else "未收到响应"
                logger.error(f"【查询任务状态】失败 | 任务ID: {task_id} | 错误: {error_msg}")
                return None

            # 解析响应数据
            body = response.get("body", {})
            task_data_list = body.get("data", [])

            # 验证data字段格式
            if not isinstance(task_data_list, list):
                logger.error(f"【查询任务状态】失败 | 任务ID: {task_id} | 错误: data字段格式不是列表")
                return None

            # 提取任务信息（取第一个匹配任务）
            if task_data_list:
                task_info = task_data_list[0]
                logger.info(
                    f"【查询任务状态】成功 | 任务ID: {task_id} | 状态: {task_info.get('task_status')} | 进度: {task_info.get('task_cur_progress')}/{task_info.get('task_total_progress')}")
                return task_info
            else:
                logger.warning(f"【查询任务状态】失败 | 任务ID: {task_id} | 错误: 未找到任务数据")
                return None

        except Exception as e:
            logger.error(f"【查询任务状态】异常 | 任务ID: {task_id} | 错误: {str(e)}")
            return None
# 创建全局BookService实例
book_service = BookService()