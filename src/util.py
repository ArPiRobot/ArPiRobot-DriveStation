
from typing import Optional, Union

from PySide6.QtCore import QSize, QDir, QSettings, QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QTextDocument, QAbstractTextDocumentLayout, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle

class SettingsManager:
    """
    Thin wrapper over QSettings object to manage drive station settings
    """
    def __init__(self):
        # Constants
        self.__SETTING_FILE = QDir.homePath() + "/.arpirobot/drivestation.ini"

        self.__ROBOT_IP_KEY = "robot-address"
        self.__VBAT_MAIN_KEY = "vbat-main"
        self.__LARGE_FONTS_KEY = "larger-fonts"

        self.__DEFAULT_ROBOT_IP = "192.168.10.1"
        self.__DEFAULT_VBAT_MAIN = 7.5
        self.__DEFAULT_LARGE_FONTS = False

        # Setup
        self.__settings = QSettings(self.__SETTING_FILE, QSettings.Format.IniFormat)

        # Setup defaults if settings are missing
        if self.__settings.value(self.__ROBOT_IP_KEY, None) is None:
            self.__settings.setValue(self.__ROBOT_IP_KEY, self.__DEFAULT_ROBOT_IP)
        if self.__settings.value(self.__VBAT_MAIN_KEY, None) is None:
            self.__settings.setValue(self.__VBAT_MAIN_KEY, self.__DEFAULT_VBAT_MAIN)
        if self.__settings.value(self.__LARGE_FONTS_KEY, None) is None:
            self.__settings.setValue(self.__LARGE_FONTS_KEY, self.__DEFAULT_LARGE_FONTS)

    @property
    def robot_address(self) -> str:
        return str(self.__settings.value(self.__ROBOT_IP_KEY, self.__DEFAULT_ROBOT_IP))

    @robot_address.setter
    def robot_address(self, value: str):
        self.__settings.setValue(self.__ROBOT_IP_KEY, value)

    @property
    def vbat_main(self) -> float:
        return float(str(self.__settings.value(self.__VBAT_MAIN_KEY, self.__DEFAULT_VBAT_MAIN)))

    @vbat_main.setter
    def vbat_main(self, value: float):
        self.__settings.setValue(self.__VBAT_MAIN_KEY, value)

    @property
    def larger_fonts(self) -> bool:
        return str(self.__settings.value(self.__LARGE_FONTS_KEY, self.__DEFAULT_LARGE_FONTS)).lower() == "true"

    @larger_fonts.setter
    def larger_fonts(self, value: bool):
        self.__settings.setValue(self.__LARGE_FONTS_KEY, value)


class Logger:
    def __init__(self):
        from drive_station import DriveStationWindow
        self.__ds: Optional[DriveStationWindow] = None
    
    def set_ds(self, ds):
        self.__ds = ds

    def log_debug(self, msg: str):
        if self.__ds is not None:
            self.__ds.log_debug(msg)

    def log_info(self, msg: str):
        if self.__ds is not None:
            self.__ds.log_info(msg)

    def log_warning(self, msg: str):
        if self.__ds is not None:
            self.__ds.log_warning(msg)

    def log_error(self, msg: str):
        if self.__ds is not None:
            self.__ds.log_error(msg)
    
    def log_from_robot(self, msg: str):
        if self.__ds is not None:
            self.__ds.log_from_robot(msg)


settings_manager: SettingsManager = SettingsManager()
logger: Logger = Logger()


class HTMLDelegate(QStyledItemDelegate):
    """
    Item delegate for ListWidget, ListView, etc that renders rich text from HTML strings
    """
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__(parent)
        self.doc = QTextDocument(self)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: Union[QModelIndex, QPersistentModelIndex]):
        painter.save()
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        self.doc.setHtml(options.text)                                                              # type: ignore
        options.text = ""                                                                           # type: ignore       
        style = QApplication.style() if options.widget is None else options.widget.style()          # type: ignore
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter, options.widget)  # type: ignore

        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Not needed. Handled by stylesheet
        # if option.state & QStyle.State_Selected:
        #     ctx.palette.setColor(QPalette.Text, option.palette.color(
        #         QPalette.Active, QPalette.HighlightedText))
        # else:
        #     ctx.palette.setColor(QPalette.Text, option.palette.color(
        #        QPalette.Active, QPalette.Text))

        text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, options, None)
        if index.column() != 0:
            text_rect.adjust(5, 0, 0, 0)
        constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2                         # type: ignore
        margin = margin - constant
        text_rect.setTop(text_rect.top() + margin)

        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(int(self.doc.idealWidth()), int(self.doc.size().height()))