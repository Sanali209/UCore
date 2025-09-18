from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QPersistentModelIndex
from .base import ObservableList

class ObservableListModel(QAbstractListModel):
    """Qt ListModel that reflects an ObservableList."""
    def __init__(self, data: ObservableList):
        super().__init__()
        self._data = data
        self._data.add_handler(self._on_list_changed)

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def data(self, index, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if role == int(Qt.ItemDataRole.DisplayRole) and index.isValid():
            return str(self._data[index.row()])
        return None

    def _on_list_changed(self, action, value):
        if action == 'append':
            self.beginInsertRows(QModelIndex(), len(self._data)-1, len(self._data)-1)
            self.endInsertRows()
        elif action == 'remove':
            # For simplicity, refresh all
            self.beginResetModel()
            self.endResetModel()
        elif action == 'clear':
            self.beginResetModel()
            self.endResetModel()
