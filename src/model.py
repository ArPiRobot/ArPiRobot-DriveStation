
from typing import List, Optional
from PySide6 import QtGui
from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, QRectF, QSize, Qt
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QStyledItemDelegate

################################################################################
# Controller List Model
################################################################################

class Controller:
    def __init__(self, name: str, internal_id: int):
        self.name = name
        self.internal_id = internal_id


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
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.__controllers[row]
            return f"{row}: {item.name}"
        return None

    

