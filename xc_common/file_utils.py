import os
import functions
from pathlib import Path
import shutil
import filecmp


def copy_file(platform, src_file_path, dst_dir):

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
        dst_path.unlink()  # 删除目标文件
    shutil.copy2(src_file_path, dst_dir_path)

    return dst_dir_path
