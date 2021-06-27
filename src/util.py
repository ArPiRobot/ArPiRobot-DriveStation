from typing import List

from PySide6.QtCore import QSize, QFile, QIODevice, QDirIterator, QFileInfo, QStandardPaths, QDir, QSettings
from PySide6.QtGui import QTextDocument, QAbstractTextDocumentLayout, QPalette
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle, QStyleFactory


class HTMLDelegate(QStyledItemDelegate):
    """
    Item delegate for ListWidget, ListView, etc that renders rich text from HTML strings
    """
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__(parent)
        self.doc = QTextDocument(self)

    def paint(self, painter, option, index):
        painter.save()
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        self.doc.setHtml(options.text)
        options.text = ""
        style = QApplication.style() if options.widget is None \
            else options.widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter, options.widget)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Not needed. Handled by stylesheet
        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, option.palette.color(
                QPalette.Active, QPalette.HighlightedText))
        else:
            ctx.palette.setColor(QPalette.Text, option.palette.color(
               QPalette.Active, QPalette.Text))

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options, None)
        if index.column() != 0:
            text_rect.adjust(5, 0, 0, 0)
        constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2
        margin = margin - constant
        text_rect.setTop(text_rect.top() + margin)

        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(self.doc.idealWidth(), self.doc.size().height())


class ThemeManager:
    """
    Handles managing custom stylesheet supporting multiple "color themes".
    Custom stylesheet uses placeholder variables (@var_name@). There are several
    CSV files containing mappings for these placeholder variables.
    Each is considered its own "color theme".
    This class manages loading the template stylesheet and substituting values from CSV files.
    """
    def __init__(self):
        self.__BASE_STYLESHEET = ":/stylesheet.qss"
        self.__THEME_PATH = ":/stylesheet-vars/"
        self.__themes: List[str] = []
        self.__app: QApplication = None

    def set_app(self, app: QApplication):
        self.__app = app
        # Custom stylesheet used is designed for fusion base
        self.__app.setStyle(QStyleFactory.create("Fusion"))

    def load_themes(self):
        # Load a list of theme names, but do not generate stylesheets yet.
        # Pre-generating multiple stylesheets wastes memory
        self.__themes.clear()
        iterator = QDirIterator(self.__THEME_PATH)
        while iterator.hasNext():
            info = QFileInfo(iterator.next())
            if info.completeSuffix().lower() == "csv":
                self.__themes.append(info.baseName())

    def themes(self) -> List[str]:
        return self.__themes.copy()

    def apply_theme(self, theme: str) -> bool:
        if theme is None:
            self.__app.setStyleSheet("")
            return True

        if theme not in self.__themes:
            return False

        # Load stylesheet. This is a stylesheet with placeholders. It cannot be used directly
        stylesheet_str = ""
        stylesheet_file = QFile(":/stylesheet.qss")
        if stylesheet_file.open(QIODevice.ReadOnly):
            stylesheet_str = bytes(stylesheet_file.readAll()).decode()
        else:
            return False
        stylesheet_file.close()

        # Substitute values for placeholders in stylesheet
        dark_file = QFile(f"{self.__THEME_PATH}/{theme}.csv")
        if dark_file.open(QIODevice.ReadOnly):
            for line in bytes(dark_file.readAll()).decode().splitlines(False):
                # Index 0 = variable, Index 1 = value
                parts = line.replace(", ", ",").split(",")
                stylesheet_str = stylesheet_str.replace(f"@{parts[0]}@", parts[1])
        else:
            return False

        self.__app.setStyleSheet(stylesheet_str)

        return True


class SettingsManager:
    """
    Thin wrapper over QSettings object to manage drive station settings
    """
    def __init__(self):
        # Constants
        self.__SETTING_FILE = QDir.homePath() + "/.arpirobot/drivestation.ini"

        self.__ROBOT_IP_KEY = "robot-address"
        self.__VBAT_MAIN_KEY = "vbat-main"

        self.__DEFAULT_ROBOT_IP = "192.168.10.1"
        self.__DEFAULT_VBAT_MAIN = 7.5

        # Setup
        self.__settings = QSettings(self.__SETTING_FILE, QSettings.IniFormat)

    @property
    def robot_address(self) -> str:
        return self.__settings.value(self.__ROBOT_IP_KEY, self.__DEFAULT_ROBOT_IP)

    @robot_address.setter
    def robot_address(self, value: str):
        self.__settings.setValue(self.__ROBOT_IP_KEY, value)

    @property
    def vbat_main(self) -> float:
        return self.__settings.value(self.__VBAT_MAIN_KEY, self.__DEFAULT_VBAT_MAIN)

    @vbat_main.setter
    def vbat_main(self, value: float):
        self.__settings.setValue(self.__VBAT_MAIN_KEY, value)


theme_manager: ThemeManager = ThemeManager()
settings_manager: SettingsManager = SettingsManager()
