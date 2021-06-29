from PySide6.QtGui import QContextMenuEvent, QAction, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget, QMenu, QStyleOption, QStyle
from ui_indicator_widget import Ui_InidicatorWidget


class IndicatorWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_InidicatorWidget()
        self.ui.setupUi(self)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        writable_action = QAction("Editable")
        delete_action = QAction("Delete")
        writable_action.setCheckable(True)
        writable_action.setChecked(not self.ui.txt_value.isReadOnly())
        menu.addActions([writable_action, delete_action])
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == writable_action:
            self.ui.txt_value.setReadOnly(not writable_action.isChecked())

    def paintEvent(self, event: QPaintEvent) -> None:
        # Reimplementing this function is necessary for stylesheet functionality
        super().paintEvent(event)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self)

    @property
    def key(self) -> str:
        return self.ui.lbl_key.text()

    @key.setter
    def key(self, value: str):
        self.ui.lbl_key.setText(value)

    @property
    def value(self) -> str:
        return self.ui.txt_value.text()

    @value.setter
    def value(self, value: str):
        self.ui.txt_value.setText(value)


