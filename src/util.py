from typing import Dict, List

from PySide6.QtCore import QSize, QFile, QIODevice, QDirIterator, QFileInfo, QDir, QSettings, Qt
from PySide6.QtGui import QTextDocument, QAbstractTextDocumentLayout, QPalette, QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle, QStyleFactory


class ThemeManager:
    def __init__(self) -> None:
        self.app = None
        self.system_theme = "Fusion"
    
    def set_app(self, app: QApplication) -> None:
        self.app = app
        self.system_theme = self.app.style().name()
    
    @property
    def themes(self):
        return ["Custom Light", "Custom Dark", "Fusion Light", "Fusion Dark", "System"]
    
    def apply_theme(self, theme: str):
        style = QStyleFactory.create("Fusion")
        stylesheet = ""
        palette = QPalette()

        if theme == "Custom Light" or theme == "Custom Dark":
            # Load stylesheet
            stylesheet_file = QFile(":/custom-theme/stylesheet.qss")
            if stylesheet_file.open(QIODevice.ReadOnly):
                stylesheet = bytes(stylesheet_file.readAll()).decode()
                stylesheet_file.close()
            
                # Make substitutions from csv file to use correct variant
                vars_file = QFile(":/custom-theme/{0}.csv".format("light" if theme == "Custom Light" else "dark"))
                if vars_file.open(QIODevice.ReadOnly):
                    for line in bytes(vars_file.readAll()).decode().splitlines(False):
                        # Index 0 = variable, Index 1 = value
                        parts = line.replace(", ", ",").split(",")
                        stylesheet = stylesheet.replace("@{0}@".format(parts[0]), parts[1])
                    vars_file.close()
            style = QStyleFactory.create("Fusion")
            palette = style.standardPalette()
        elif theme == "Fusion Light" or theme == "Fusion Dark":
            style = QStyleFactory.create("Fusion")
            stylesheet = ""
            palette = QPalette()
            if theme == "Fusion Dark":
                palette.setColor(QPalette.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.WindowText, Qt.white)
                palette.setColor(QPalette.Base, QColor(25, 25, 25))
                palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.ToolTipBase, Qt.white)
                palette.setColor(QPalette.ToolTipText, Qt.white)
                palette.setColor(QPalette.Text, Qt.white)
                palette.setColor(QPalette.Button, QColor(53, 53, 53))
                # palette.setColor(QPalette.Disabled, QPalette.Button, QColor(94, 94, 94))
                palette.setColor(QPalette.ButtonText, Qt.white)
                palette.setColor(QPalette.BrightText, Qt.red)
                palette.setColor(QPalette.Link, QColor(42, 130, 218))
                palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
                palette.setColor(QPalette.HighlightedText, Qt.black)
        else:
            style = QStyleFactory.create(self.system_theme)
            stylesheet = ""
            palette = style.standardPalette()
        
        # This seems overly complicated, but ensures any order of theme changes works
        # Switching between stylesheets and palette based themes has some bugs...
        self.app.setStyleSheet("")
        self.app.setPalette(self.app.style().standardPalette())
        self.app.style().unpolish(self.app)
        self.app.style().polish(self.app)
        self.app.style().unpolish(self.app)
        self.app.setStyleSheet(stylesheet)
        self.app.setStyle(style)
        self.app.setPalette(palette)
        self.app.style().unpolish(self.app)
        self.app.style().polish(self.app)

        # Adjust font size
        # font = QApplication.font()
        # font.setPointSize(self.default_font_size + 2 if settings_manager.larger_fonts else self.default_font_size)
        # QApplication.setFont(font)


class SettingsManager:
    """
    Thin wrapper over QSettings object to manage drive station settings
    """
    def __init__(self):
        # Constants
        self.__SETTING_FILE = QDir.homePath() + "/.arpirobot/drivestation.ini"

        self.__ROBOT_IP_KEY = "robot-address"
        self.__VBAT_MAIN_KEY = "vbat-main"
        self.__THEME_KEY = "theme"
        self.__LARGE_FONTS_KEY = "larger-fonts"

        self.__DEFAULT_ROBOT_IP = "192.168.10.1"
        self.__DEFAULT_VBAT_MAIN = 7.5
        self.__DEFAULT_THEME = "Custom Light"
        self.__DEFAULT_LARGE_FONTS = False

        # Setup
        self.__settings = QSettings(self.__SETTING_FILE, QSettings.IniFormat)

        # Setup defaults if settings are missing
        if self.__settings.value(self.__ROBOT_IP_KEY, None) is None:
            self.__settings.setValue(self.__ROBOT_IP_KEY, self.__DEFAULT_ROBOT_IP)
        if self.__settings.value(self.__VBAT_MAIN_KEY, None) is None:
            self.__settings.setValue(self.__VBAT_MAIN_KEY, self.__DEFAULT_VBAT_MAIN)
        if self.__settings.value(self.__THEME_KEY, None) is None:
            self.__settings.setValue(self.__THEME_KEY, self.__DEFAULT_THEME)
        if self.__settings.value(self.__LARGE_FONTS_KEY, None) is None:
            self.__settings.setValue(self.__LARGE_FONTS_KEY, self.__DEFAULT_LARGE_FONTS)

    @property
    def robot_address(self) -> str:
        return self.__settings.value(self.__ROBOT_IP_KEY, self.__DEFAULT_ROBOT_IP)

    @robot_address.setter
    def robot_address(self, value: str):
        self.__settings.setValue(self.__ROBOT_IP_KEY, value)

    @property
    def vbat_main(self) -> float:
        return float(self.__settings.value(self.__VBAT_MAIN_KEY, self.__DEFAULT_VBAT_MAIN))

    @vbat_main.setter
    def vbat_main(self, value: float):
        self.__settings.setValue(self.__VBAT_MAIN_KEY, value)

    @property
    def theme(self) -> str:
        return self.__settings.value(self.__THEME_KEY, self.__DEFAULT_THEME)

    @theme.setter
    def theme(self, value: str):
        self.__settings.setValue(self.__THEME_KEY, value)

    @property
    def larger_fonts(self) -> bool:
        return str(self.__settings.value(self.__LARGE_FONTS_KEY, self.__DEFAULT_LARGE_FONTS)).lower() == "true"

    @larger_fonts.setter
    def larger_fonts(self, value: bool):
        self.__settings.setValue(self.__LARGE_FONTS_KEY, value)


class Logger:
    def __init__(self):
        self.__ds = None
    
    def set_ds(self, ds):
        self.__ds = ds

    def log_debug(self, msg: str):
        self.__ds.log_debug(msg)

    def log_info(self, msg: str):
        self.__ds.log_info(msg)

    def log_warning(self, msg: str):
        self.__ds.log_warning(msg)

    def log_error(self, msg: str):
        self.__ds.log_error(msg)
    
    def log_from_robot(self, msg: str):
        self.__ds.log_from_robot(msg)


theme_manager: ThemeManager = ThemeManager()
settings_manager: SettingsManager = SettingsManager()
logger: Logger = Logger()


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

        ss = QApplication.instance().styleSheet()
        ss = "{0}\n{1}".format(ss, "*{{font-size: {0}pt}}".format(QApplication.font().pointSize()))
        self.doc.setDefaultStyleSheet(ss)

        self.doc.setHtml(options.text)
        options.text = ""
        style = QApplication.style() if options.widget is None \
            else options.widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter, options.widget)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Not needed. Handled by stylesheet
        # if option.state & QStyle.State_Selected:
        #     ctx.palette.setColor(QPalette.Text, option.palette.color(
        #         QPalette.Active, QPalette.HighlightedText))
        # else:
        #     ctx.palette.setColor(QPalette.Text, option.palette.color(
        #        QPalette.Active, QPalette.Text))

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