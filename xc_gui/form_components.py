from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QLayout


class SimpleInputForm(QFrame):
    """简单的输入表单组件

    封装了一个标签、一个输入框和一个确认按钮的常见输入模式
    """

    def __init__(self, label_text="", placeholder_text="", button_text="确认",
                 parent=None, horizontal=True, on_confirm_callback=None):
        """
        Args:
            label_text: 标签文本
            placeholder_text: 输入框占位符文本
            button_text: 按钮文本
            parent: 父控件
            horizontal: 是否使用水平布局（True）或垂直布局（False）
            on_confirm_callback: 确认按钮点击的回调函数
        """
        super().__init__(parent)

        # 设置框架样式
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")

        # 创建布局
        if horizontal:
            self.layout = QHBoxLayout(self)
        else:
            self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        if horizontal:
            self.layout.setSpacing(10)
        else:
            self.layout.setSpacing(5)

        # 创建标签
        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.label)

        # 创建输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder_text)
        self.input_field.setMinimumWidth(200)
        # 假设StyleSheetLineEdit在其他文件中定义，这里简化处理
        self.input_field.setStyleSheet("border: 1px solid #ccc; border-radius: 3px; padding: 3px;")
        self.layout.addWidget(self.input_field)

        # 创建按钮
        self.confirm_button = QPushButton(button_text)
        self.confirm_button.setStyleSheet(
            "background-color: #4a90e2; color: white; border-radius: 3px; padding: 2px 15px;")
        self.confirm_button.setFixedHeight(25)  # 设置固定高度
        self.layout.addWidget(self.confirm_button)

        # 添加伸展空间，使组件靠左对齐
        if horizontal:
            self.layout.addStretch(1)

        # 连接信号和槽
        if on_confirm_callback:
            self.confirm_button.clicked.connect(on_confirm_callback)

    def get_value(self):
        """获取输入框的值"""
        return self.input_field.text()

    def set_value(self, value):
        """设置输入框的值"""
        self.input_field.setText(value)

    def clear(self):
        """清空输入框"""
        self.input_field.clear()

    def set_enabled(self, enabled):
        """设置组件是否可用"""
        self.label.setEnabled(enabled)
        self.input_field.setEnabled(enabled)
        self.confirm_button.setEnabled(enabled)


class MultiFieldForm(QFrame):
    """多字段表单组件

    支持添加多个输入字段，可以灵活组合表单
    """

    def __init__(self, parent=None, horizontal=True):
        """
        Args:
            parent: 父控件
            horizontal: 是否使用水平布局
        """
        super().__init__(parent)

        # 设置框架样式
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")

        # 创建布局
        if horizontal:
            self.layout = QHBoxLayout(self)
        else:
            self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # 存储字段和按钮的字典
        self.fields = {}
        self.buttons = {}

    def add_field(self, name, label_text, placeholder_text="", minimum_width=200):
        """添加一个输入字段

        Args:
            name: 字段名称，用于后续引用
            label_text: 标签文本
            placeholder_text: 占位符文本
            minimum_width: 输入框最小宽度
        """
        # 创建字段容器
        field_container = QFrame()
        field_layout = QVBoxLayout(field_container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(3)

        # 创建标签
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold;")
        field_layout.addWidget(label)

        # 创建输入框
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)
        input_field.setMinimumWidth(minimum_width)
        input_field.setStyleSheet("border: 1px solid #ccc; border-radius: 3px; padding: 3px;")
        field_layout.addWidget(input_field)

        # 添加到主布局
        self.layout.addWidget(field_container)

        # 存储字段引用
        self.fields[name] = input_field

        return input_field

    def add_button(self, name, text, callback=None):
        """添加一个按钮

        Args:
            name: 按钮名称，用于后续引用
            text: 按钮文本
            callback: 点击回调函数
        """
        button = QPushButton(text)
        button.setStyleSheet(
            "background-color: #4a90e2; color: white; border-radius: 3px; padding: 2px 15px;")
        button.setFixedHeight(25)

        if callback:
            button.clicked.connect(callback)

        self.layout.addWidget(button)
        self.buttons[name] = button

        return button

    def add_stretch(self):
        """添加伸展空间"""
        self.layout.addStretch(1)

    def get_value(self, field_name):
        """获取指定字段的值

        Args:
            field_name: 字段名称

        Returns:
            字段值或None（如果字段不存在）
        """
        if field_name in self.fields:
            return self.fields[field_name].text()
        return None

    def set_value(self, field_name, value):
        """设置指定字段的值

        Args:
            field_name: 字段名称
            value: 要设置的值
        """
        if field_name in self.fields:
            self.fields[field_name].setText(value)

    def clear_all(self):
        """清空所有字段"""
        for field in self.fields.values():
            field.clear()
