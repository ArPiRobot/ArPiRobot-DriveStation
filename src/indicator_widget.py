from PySide6.QtCore import Signal, Qt, QPoint
from PySide6.QtGui import QContextMenuEvent, QAction, QPaintEvent, QPainter, QMouseEvent, QCursor
from PySide6.QtWidgets import QWidget, QMenu, QStyleOption, QStyle
from ui_indicator_widget import Ui_InidicatorWidget
from enum import Enum, auto


# Some code in this widget is from or based on code from
# https://wiki.qt.io/Widget-moveable-and-resizeable
# https://github.com/korabelnikov/moveable-and-resize-qt-widget-on-python
class IndicatorWidget(QWidget):

    # Only support horizontal (width) resize
    class Mode(Enum):
        NoMode = auto()
        Move = auto()
        ResizeR = auto()
        ResizeL = auto()

    deleted = Signal(str)               # Args: key
    value_changed = Signal(str, str)    # Args: key, value

    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_InidicatorWidget()
        self.ui.setupUi(self)

        # Allow focusing the overall widget
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # Trigger events when mouse moves, even if no buttons pressed
        self.setMouseTracking(True)

        # Don't pass mouse events to label
        self.ui.lbl_key.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Detect text changed events
        self.ui.txt_value.editingFinished.connect(self.line_edit_changed)

        # Track mouse event positions
        self.position = QPoint()
        self.mode = IndicatorWidget.Mode.NoMode

    def line_edit_changed(self):
        self.value_changed.emit(self.key, self.ui.txt_value.text())

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
        if action == delete_action:
            self.deleted.emit(self.key)

    def paintEvent(self, event: QPaintEvent) -> None:
        # Reimplementing this function is necessary for stylesheet functionality
        super().paintEvent(event)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

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

    def mousePressEvent(self, event: QMouseEvent):
        self.position = QPoint(event.globalX() - self.geometry().x(),
                               event.globalY() - self.geometry().y())
        if not self.hasFocus():
            return
        if not event.buttons() and Qt.MouseButton.LeftButton:
            self.set_cursor_shape(event.pos())

    def set_cursor_shape(self, e_pos: QPoint):
        diff = 5

        if (((e_pos.y() > self.y() + self.height() - diff) and  # Bottom
             (e_pos.x() < self.x() + diff)) or  # Left
                # Right-Bottom
                ((e_pos.y() > self.y() + self.height() - diff) and  # Bottom
                 (e_pos.x() > self.x() + self.width() - diff)) or  # Right
                # Left-Top
                ((e_pos.y() < self.y() + diff) and  # Top
                 (e_pos.x() < self.x() + diff)) or  # Left
                # Right-Top
                (e_pos.y() < self.y() + diff) and  # Top
                (e_pos.x() > self.x() + self.width() - diff)):  # Right
            # This does not support vertical resizing
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.mode = IndicatorWidget.Mode.Move
        elif ((e_pos.x() < self.x() + diff) or  # Left
              (e_pos.x() > self.x() + self.width() - diff)):  # Right
            if e_pos.x() < self.x() + diff:  # Left
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
                self.mode = IndicatorWidget.Mode.ResizeL
            else:  # Right
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
                self.mode = IndicatorWidget.Mode.ResizeR
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.mode = IndicatorWidget.Mode.Move

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if not self.hasFocus():
            return
        if not event.buttons() and Qt.MouseButton.LeftButton:
            p = QPoint(event.x() + self.geometry().x(),
                       event.y() + self.geometry().y())
            self.set_cursor_shape(p)
            return

        # Moving with mouse
        if (self.mode == IndicatorWidget.Mode.Move or self.mode == IndicatorWidget.Mode.NoMode) and \
                event.buttons() and Qt.MouseButton.LeftButton:
            to_move = event.globalPos() - self.position
            if to_move.x() < 0:
                to_move.setX(0)
            if to_move.y() < 0:
                to_move.setY(0)
            if to_move.x() > self.parentWidget().width() - self.width():
                to_move.setX(self.parentWidget().width() - self.width())
            if to_move.y() > self.parentWidget().height() - self.height():
                to_move.setY(self.parentWidget().height() - self.height())
            self.move(to_move)
            self.parentWidget().repaint()

        # Resizing with mouse
        elif (self.mode != IndicatorWidget.Mode.Move) and event.buttons() and Qt.MouseButton.LeftButton:
            if self.mode == IndicatorWidget.Mode.ResizeL:  # Left
                new_width = event.globalX() - self.position.x() - self.geometry().x()
                to_move = event.globalPos() - self.position
                if to_move.x() < 0:
                    # Trying to resize off left edge
                    return
                new_width = self.geometry().width() - new_width
                if new_width < self.minimumWidth():
                    # Enforce minimum size. No resize should occur
                    return
                self.resize(new_width, self.height())
                self.move(to_move.x(), self.y())
            elif self.mode == IndicatorWidget.Mode.ResizeR:  # Right
                if self.geometry().x() + event.x() > self.parentWidget().width():
                    # Trying to resize off right edge
                    return
                self.resize(event.x(), self.height())
            self.parentWidget().repaint()
