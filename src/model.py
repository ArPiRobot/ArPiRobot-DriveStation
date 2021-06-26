
from typing import List, Optional
from PySide6 import QtGui
from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Qt

################################################################################
# Controller List Model
################################################################################

class Controller:
    def __init__(self, name: str, internal_id: int):
        self.name = name
        self.internal_id = internal_id
        self.checked = False


class ControllerListModel(QAbstractListModel):
    def __init__(self, parent: Optional[QObject]) -> None:
        super().__init__(parent=parent)
        self.__controllers: List[Controller] = []
    
    def add_controller(self, controller: Controller):
        if controller not in self.__controllers:
            self.beginInsertRows(QModelIndex(), len(self.__controllers), len(self.__controllers))
            self.__controllers.append(controller)
            self.endInsertRows()
    
    def get_controller(self, row: int) -> Controller:
        return self.__controllers[row]
    
    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.__controllers)
    
    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        row = index.row()
        item = self.__controllers[row]
        if role == Qt.DisplayRole:
            return f"{row}: {item.name}"
        elif role == Qt.CheckStateRole:
            return item.checked
        return None
    
    def setData(self, index: QModelIndex, value, role: int) -> bool:
        if not index.isValid():
            return
        row = index.row()
        item = self.__controllers[row]
        if role == Qt.CheckStateRole:
            item.checked = value
            return True
        return super().setData(index, value, role)
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsDragEnabled

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.CopyAction | Qt.MoveAction

