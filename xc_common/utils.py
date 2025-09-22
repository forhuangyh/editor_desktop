# http post 获取get 请求
import requests
import json


# HTTP 请求相关工具函数

def http_get(url, headers=None, params=None, timeout=60):
    """
    发送HTTP GET请求

    Args:
        url: 请求的URL地址
        headers: 请求头字典
        params: URL参数字典
        timeout: 请求超时时间（秒）

    Returns:
        字典格式的响应数据，如果请求失败则返回None
    """
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout
        )
        response.raise_for_status()  # 如果状态码不是200，抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP GET 请求失败: {url}, 错误: {str(e)}")
        return None
    except json.JSONDecodeError:
        print(f"HTTP GET 响应解析失败: {url}")
        return None


def http_post(url, data=None, json_data=None, headers=None, timeout=60):
    """
    发送HTTP POST请求

    Args:
        url: 请求的URL地址
        data: 表单数据（字典）
        json_data: JSON数据（字典）
        headers: 请求头字典
        timeout: 请求超时时间（秒）

    Returns:
        字典格式的响应数据，如果请求失败则返回None
    """
    try:
        response = requests.post(
            url,
            data=data,
            json=json_data,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()  # 如果状态码不是200，抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP POST 请求失败: {url}, 错误: {str(e)}")
        return None
    except json.JSONDecodeError:
        print(f"HTTP POST 响应解析失败: {url}")
        return None


# 添加专门的表单请求函数
def http_form_post(url, form_data, headers=None, timeout=120):
    """
    专门用于发送表单请求的函数

    Args:
        url: 请求的URL地址
        form_data: 表单数据（字典）
        headers: 额外的请求头字典
        timeout: 请求超时时间（秒）

    Returns:
        字典格式的响应数据，如果请求失败则返回None
    """
    try:
        # 参数校验
        if not url:
            print("HTTP 表单请求失败: URL不能为空")
            return None

        if form_data is not None and not isinstance(form_data, dict):
            print("HTTP 表单请求失败: 表单数据必须是字典类型")
            return None

        # 创建请求头副本，避免修改传入的字典
        request_headers = headers.copy() if headers else {}

        # 设置表单请求头
        request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # 发送请求
        response = requests.post(
            url,
            data=form_data,
            headers=request_headers,
            timeout=timeout
        )

        # 检查响应状态码
        response.raise_for_status()

        # 尝试解析JSON响应
        try:
            return response.json()
        except json.JSONDecodeError:
            # 如果响应不是有效的JSON，但请求成功，可以返回一个默认的成功响应
            print(f"HTTP 表单请求成功，但响应不是有效的JSON: {url}")
            # 尝试从响应文本中提取有用信息
            return {
                'success': True,
                'message': '请求成功',
                'status_code': response.status_code,
                'raw_text': response.text
            }

    except requests.exceptions.Timeout:
        print(f"HTTP 表单请求超时: {url}, 超时时间: {timeout}秒")
        return {'success': False, 'error': '请求超时'}

    except requests.exceptions.ConnectionError:
        print(f"HTTP 表单请求连接错误: {url}")
        return {'success': False, 'error': '网络连接错误'}

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP 表单请求错误: {url}, 状态码: {e.response.status_code}"
        print(error_msg)
        # 尝试从错误响应中获取JSON数据
        try:
            error_data = e.response.json()
            error_data['success'] = False
            error_data['status_code'] = e.response.status_code
            return error_data
        except (ValueError, AttributeError):
            return {
                'success': False,
                'error': error_msg,
                'status_code': e.response.status_code if hasattr(e, 'response') else None
            }

    except Exception as e:
        print(f"HTTP 表单请求发生未知错误: {url}, 错误: {str(e)}")
        return {'success': False, 'error': f'未知错误: {str(e)}'}
