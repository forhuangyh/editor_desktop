import settings
import components.fonts
import os
import data
from qt import QFontDatabase


class FontResizeFunc:
    def __init__(self, main_window):
        self.main_window = main_window
        # 存储所有字体大小菜单项的字典
        self.font_size_actions = {}
        # 存储字体名称菜单项的字典
        self.font_name_actions = {}

    def initialize_font_settings(self):
        """初始化字体设置，确保应用启动时加载用户的字体偏好"""
        # 这个函数会在MainWindow初始化时调用
        self.update_editor_font_size()
        # 存储所有字体大小菜单项的字典
        self.font_size_actions = {}
        self.font_name_actions = {}

    def update_editor_font_size(self):
        """独立更新所有编辑器窗口的字体大小，不影响其他组件"""
        # 获取当前编辑器字体设置
        editor_font = settings.get_editor_font()
        font_name = editor_font.family()
        font_size = editor_font.pointSize()

        # 遍历所有编辑器实例
        for editor in self.main_window.get_all_editors():
            try:
                # 设置编辑器主字体
                editor.setFont(editor_font)
                # 设置边距字体
                editor.setMarginsFont(editor_font)
                # 重置缩放
                editor.zoomTo(0)
                # 应用设置的缩放因子
                editor.zoomTo(settings.get("editor")["zoom_factor"])
                # 使用Scintilla低级API更新默认文本样式的字体
                editor.SendScintilla(editor.SCI_STYLESETFONT, 0, font_name.encode())
                editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, font_size)

                # 更新注释样式的字体
                editor.SendScintilla(editor.SCI_STYLESETFONT, 1, font_name.encode())
                editor.SendScintilla(editor.SCI_STYLESETSIZE, 1, font_size)
            except Exception as e:
                print(f"Error updating editor font: {str(e)}")

    def set_font_size(self, size):
        size = int(size)
        if 6 <= size <= 32:
            settings.set("current_editor_font_size", size)
            # 重置编辑器缩放因子
            settings.set("editor", {**settings.get("editor"), "zoom_factor": 0})
            # 只更新编辑器字体，不影响其他组件
            self.update_editor_font_size()
            # 更新菜单项的勾选状态
            self.update_font_size_check_state()

    def set_font_name(self, font_name):
        """设置编辑器字体名称"""
        # 保存字体设置
        settings.set("current_editor_font_name", font_name)
        # 更新所有编辑器字体
        self.update_editor_font_size()
        # 更新菜单项的勾选状态
        self.update_font_name_check_state()

    def get_resource_fonts(self):
        """从资源目录获取可用的字体"""
        # 检查字体目录是否存在
        if not os.path.exists(data.fonts_directory):
            return []

        # 支持的字体格式
        supported_formats = ['.ttf', '.otf']
        fonts = []

        # 遍历字体目录
        for file in os.listdir(data.fonts_directory):
            # 获取文件扩展名
            _, ext = os.path.splitext(file.lower())
            # 检查是否为支持的字体格式
            if ext in supported_formats:
                # 加载字体到QFontDatabase
                font_id = QFontDatabase.addApplicationFont(os.path.join(data.fonts_directory, file))
                if font_id != -1:
                    # 获取字体族名
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        fonts.append(font_families[0])

        # 去重并排序
        return sorted(list(set(fonts)))

    def get_available_fonts(self):
        """获取所有可用的字体，包括系统字体和资源字体"""
        # 获取系统字体
        system_fonts = sorted(QFontDatabase.families())
        # 获取资源字体
        resource_fonts = self.get_resource_fonts()

        # 合并并去重，确保资源字体在前面
        all_fonts = resource_fonts + [font for font in system_fonts if font not in resource_fonts]
        return all_fonts

    def register_font_size_action(self, size, action):
        """注册字体大小菜单项"""
        # 设置为可勾选
        action.setCheckable(True)
        # 根据当前字体大小设置勾选状态
        current_size = int(settings.get("current_editor_font_size"))
        action.setChecked(size == current_size)
        # 保存到字典以便后续更新勾选状态
        self.font_size_actions[size] = action

    def register_font_name_action(self, font_name, action):
        """注册字体名称菜单项"""
        # 设置为可勾选
        action.setCheckable(True)
        # 根据当前字体设置勾选状态
        current_font = settings.get("current_editor_font_name")
        action.setChecked(font_name == current_font)
        # 保存到字典以便后续更新勾选状态
        self.font_name_actions[font_name] = action

    def update_font_size_check_state(self):
        """更新所有字体大小菜单项的勾选状态"""
        current_size = int(settings.get("current_editor_font_size"))

        # 遍历所有字体大小菜单项
        for size, action in self.font_size_actions.items():
            # 更新勾选状态
            action.setChecked(size == current_size)

    def update_font_name_check_state(self):
        """更新所有字体名称菜单项的勾选状态"""
        current_font = settings.get("current_editor_font_name")

        # 遍历所有字体名称菜单项
        for font_name, action in self.font_name_actions.items():
            # 更新勾选状态
            action.setChecked(font_name == current_font)