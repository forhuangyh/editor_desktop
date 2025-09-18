import os
import functions
from pathlib import Path
import shutil
import chardet
from datetime import datetime


def copy_file(platform, src_file_path, dst_dir_path):

    # Replace back-slashes to forward-slashes on Windows
    if platform == "Windows":
        dst_dir_path = functions.unixify_path(dst_dir_path)

    if src_file_path == dst_dir_path:
        return dst_dir_path

    dst_path = Path(dst_dir_path)
    # 创建目录
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if dst_path.exists():
        dst_path.unlink()  # 删除目标文件

    shutil.copy2(src_file_path, dst_dir_path)

    return dst_dir_path


def copy_file_and_save_utf(platform, src_file_path, dst_dir):

    file_name = os.path.basename(src_file_path)
    dst_dir_path = os.path.join(dst_dir, file_name)

    # Replace back-slashes to forward-slashes on Windows
    if platform == "Windows":
        dst_dir_path = functions.unixify_path(dst_dir_path)

    if src_file_path == dst_dir_path:
        return dst_dir_path

    dst_path = Path(dst_dir_path)
    # 创建目录
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if dst_path.exists():
        # 获取当前时间戳并格式化为字符串
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 分离文件名和扩展名
        file_stem = dst_path.stem
        file_suffix = dst_path.suffix
        # 构建新文件名：原文件名_时间戳.扩展名
        new_file_name = f"{file_stem}_{timestamp}{file_suffix}"
        new_dst_path = dst_path.parent / new_file_name
        # 重命名原文件
        dst_path.rename(new_dst_path)

    shutil.copy2(src_file_path, dst_dir_path)

    save_as_utf(dst_dir_path)

    return dst_dir_path


def save_as_utf(file_with_path, encoding='utf-8'):
    """
    Read contents of a text file to a single string,
    detecting the encoding automatically.
    """
    try:
        encoding = None
        read_len = 8192
        # Use binary mode to read the file's content
        with open(file_with_path, 'rb') as f:
            raw_data = f.read(read_len)

        # Detect the encoding
        result = chardet.detect(raw_data)
        encoding = result['encoding']

        if encoding == "utf-8":
            text = raw_data.decode(encoding, errors='replace')
            if text.find("\r") > -1:
                # 包含\r, 通常是windows下的文件, 转换为unix格式
                with open(file_with_path, 'r') as f:
                    text = f.read()
                # 包含\r, 通常是windows下的文件, 转换为unix格式
                text = text.replace("\r", "")
                # Write the decoded text back to the file, using UTF-8 encoding
                with open(file_with_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            return encoding

        # If a valid encoding is found, decode the data
        if encoding:
            with open(file_with_path, 'rb') as f:
                raw_data = f.read()
            # Decode the raw data using the detected encoding, with error handling
            text = raw_data.decode(encoding, errors='replace')
            if text.find("\r") > -1:
                # 包含\r, 通常是windows下的文件, 转换为unix格式
                text = text.replace("\r", "")
            # Write the decoded text back to the file, using UTF-8 encoding
            with open(file_with_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return encoding
        else:
            # If chardet couldn't find a valid encoding, return an empty string
            return ""

    except Exception as ex:
        # Catch any other potential errors and print a message
        raise Exception(f"无法识别的编码: encoding={encoding}, {str(ex)}")
