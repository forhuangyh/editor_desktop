from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem


class ExtendedTableWidget(QTableWidget):
    def __init__(self, rows=0, cols=0, headers=None, parent=None):
        """扩展的表格控件，集成了统一样式管理

        Args:
            rows: 初始行数
            cols: 初始列数
            headers: 表头标签列表，如果提供则设置表头
            parent: 父控件
        """
        super().__init__(rows, cols, parent)

        # 存储行数据的字典
        self._row_data = {}

        # 设置统一样式
        self.setAlternatingRowColors(True)  # 交替行颜色
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # 选择整行
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 不可编辑

        # 如果提供了表头，则设置表头
        if headers:
            self.setHorizontalHeaderLabels(headers)

            # 设置列宽调整模式
            header = self.horizontalHeader()
            # 默认所有列为自动调整内容宽度
            for i in range(len(headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def setRowData(self, row, data):
        """存储与行关联的数据

        Args:
            row: 行索引
            data: 要存储的数据
        """
        self._row_data[row] = data

    def rowData(self, row):
        """获取与行关联的数据

        Args:
            row: 行索引

        Returns:
            与行关联的数据，如果不存在则返回None
        """
        return self._row_data.get(row)

    def setColumnResizeMode(self, column, mode):
        """设置指定列的宽度调整模式

        Args:
            column: 列索引
            mode: QHeaderView.ResizeMode枚举值
        """
        if 0 <= column < self.columnCount():
            header = self.horizontalHeader()
            header.setSectionResizeMode(column, mode)

    def setStretchColumns(self, columns):
        """设置指定列为伸展模式

        Args:
            columns: 列索引列表
        """
        for col in columns:
            self.setColumnResizeMode(col, QHeaderView.ResizeMode.Stretch)

    def applyBookTableStyle(self):
        """应用书籍表格特定样式（针对6列表格）"""
        if self.columnCount() >= 6:
            # 设置第0列和第2列为伸展模式
            self.setColumnResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.setColumnResizeMode(2, QHeaderView.ResizeMode.Stretch)
            # 其他列为自动调整内容宽度
            for i in [1, 3, 4, 5]:
                self.setColumnResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def clearAllData(self):
        """清除所有表格数据和关联的行数据"""
        self.clearContents()
        self.setRowCount(0)
        self._row_data.clear()

    def appendRow(self, item_list=None):
        """添加一行并可选地设置单元格内容

        Args:
            item_list: 单元格内容列表，如果提供则设置单元格

        Returns:
            新添加行的索引
        """
        row = self.rowCount()
        self.insertRow(row)

        # 如果提供了单元格内容，则设置它们
        if item_list:
            for col, item in enumerate(item_list):
                if col < self.columnCount():
                    # 检查item是否已经是QTableWidgetItem实例
                    if isinstance(item, QTableWidgetItem):
                        self.setItem(row, col, item)
                    else:
                        # 否则创建一个新的QTableWidgetItem
                        cell_item = QTableWidgetItem(str(item))
                        self.setItem(row, col, cell_item)
        return row

    def removeSelectedRows(self):
        """删除选中的行"""
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())

        # 从大到小排序，确保删除时索引不会变化
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)
            # 同时从行数据字典中删除
            if row in self._row_data:
                del self._row_data[row]

        # 重新索引行数据字典
        new_row_data = {}
        for i in range(self.rowCount()):
            if i in self._row_data:
                new_row_data[i] = self._row_data[i]
        self._row_data = new_row_data