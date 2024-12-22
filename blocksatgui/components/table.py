import logging

from ..qt import (QAbstractItemView, QAbstractTableModel, QHeaderView,
                  QSizePolicy, Qt, QTableView)

logger = logging.getLogger(__name__)


class Table(QTableView):

    def __init__(self, header, alignment=Qt.AlignRight, behavior="stretch"):
        assert (behavior in ["stretch", "fit"])
        super().__init__()

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        if behavior == "stretch":
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            self.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents)
            self.horizontalHeader().setStretchLastSection(True)

        self.verticalHeader().setVisible(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._model = TableModel(header, alignment=alignment)
        self.setModel(self._model)

    def set_items(self, items):
        """Set a list of items to the table

        Args:
            items (list): List of items to be added to the table.

        """
        assert (len(items[0]) == len(self._model._header))
        self._model.set_data(items)

    def update_item(self, item, i_row):
        """Update the data in a given row

        Args:
            item (list): List with the data to be added to the table.
            i_row (int): Index of the row.

        """
        assert (len(item) == len(self._model._header))
        self._model.update_item(item, i_row)

    def set_item(self, item):
        """Set an items to the table

        Args:
            item (list): List with the data to be added to the table.

        """
        assert (len(item) == len(self._model._header))
        self._model.set_data(self._model._data.append(item))

    def sort_items(self, i_col, order='ascending'):
        """Sort items based on the given column index

        Args:
            i_col: Column index.
            order: Sorting order ('ascending' or 'descending')

        """
        assert (order in ['ascending', 'descending'])
        assert (i_col < len(self._model._header))
        self._model.sort_items(i_col, order)

    def clear(self):
        """Clear all items from the table"""
        self._model.set_data([])

    def get_data(self, row, col):
        """Get data from the given row and column

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            Data from the given row and column.

        """
        return self._model._data[row][col]

    def reset_model(self):
        """Reset the table model"""
        self._model.beginResetModel()
        self._model.endResetModel()


class TableModel(QAbstractTableModel):

    def __init__(self, header, alignment=Qt.AlignCenter):
        super().__init__()

        self._header = header
        self._alignment = alignment
        self._data = []

    def set_data(self, data):
        self._data = data
        self.layoutChanged.emit()

    def update_item(self, item, i_row):
        self._data[i_row] = item
        self.layoutChanged.emit()

    def sort_items(self, i_col, order):
        self._data.sort(key=lambda x: x[i_col], reverse=order == 'descending')
        self.layoutChanged.emit()

    def rowCount(self, _=None):
        return len(self._data)

    def columnCount(self, _=None):
        return len(self._header)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header[section]
            else:
                return None

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        if role == Qt.TextAlignmentRole:
            if isinstance(self._alignment, list):
                return self._alignment[index.column()]
            else:
                return self._alignment
