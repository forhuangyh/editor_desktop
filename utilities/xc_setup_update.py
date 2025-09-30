import os
import sys
import subprocess
import shutil

# 设置打包输出目录为win_update
output_dir = os.path.join(os.path.dirname(__file__), 'win_update', 'dist')
build_dir = os.path.join(os.path.dirname(__file__), 'win_update', 'build')
spec_dir = os.path.join(os.path.dirname(__file__), 'win_update')  # 设置spec文件目录


# 清理旧的打包文件
def clean_old_builds():
    # 清理整个win_update目录
    wionds_dir = os.path.join(os.path.dirname(__file__), 'win_update')
    if os.path.exists(wionds_dir):
        shutil.rmtree(wionds_dir)
        print(f"已清理旧的win_update目录: {wionds_dir}")


# 使用PyInstaller打包
def build_with_pyinstaller():
    # 先清理旧的构建文件
    clean_old_builds()

    # 获取资源目录
    resource_dir = os.path.join(os.path.dirname(__file__), '../resources')

    # 构建PyInstaller命令，添加--specpath参数指定spec文件位置
    command = [
        'pyinstaller',
        '--onefile',  # 生成单个可执行文件
        '--console',  # 使用控制台模式，确保能看到输出
        '--icon', os.path.join(resource_dir, 'exco-icon-win.ico'),  # 设置图标
        '--name', 'update_program',  # 设置输出文件名
        '--add-data', f'{resource_dir};resources',  # 添加资源文件
        '--distpath', output_dir,  # 指定输出目录
        '--workpath', build_dir,  # 指定工作目录
        '--specpath', spec_dir,  # 指定spec文件生成目录
        'xc_update_program.py'  # 要打包的主脚本
    ]

    print(f"执行打包命令: {' '.join(command)}")

    # 执行打包命令
    result = subprocess.run(command, cwd=os.path.dirname(__file__))

    if result.returncode == 0:
        # 使用os.path.join来避免路径反斜杠问题
        executable_path = os.path.join(output_dir, 'update_program.exe')
        spec_path = os.path.join(spec_dir, 'update_program.spec')
        print(f"\n打包成功！可执行文件位于: {executable_path}")
        print(f"spec配置文件位于: {spec_path}")
    else:
        print("打包失败，请查看错误信息。")
        sys.exit(1)


if __name__ == '__main__':
    # 检查是否安装了PyInstaller
    try:
        import PyInstaller

        print(f"已安装PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("未安装PyInstaller，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("PyInstaller安装完成")

    # 开始打包
    build_with_pyinstaller()