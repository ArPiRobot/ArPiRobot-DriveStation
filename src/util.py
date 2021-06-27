from typing import List

from PySide6.QtCore import QSize, QFile, QIODevice, QDirIterator, QFileInfo
from PySide6.QtGui import QTextDocument, QAbstractTextDocumentLayout
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle


class HTMLDelegate(QStyledItemDelegate):
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
        # if option.state & QStyle.State_Selected:
        #     ctx.palette.setColor(QPalette.Text, option.palette.color(
        #         QPalette.Active, QPalette.HighlightedText))
        # else:
        #    ctx.palette.setColor(QPalette.Text, option.palette.color(
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


class ThemeManager:
    __BASE_STYLESHEET = ":/stylesheet.qss"
    __THEME_PATH = ":/stylesheet-vars/"
    __themes: List[str] = []

    @staticmethod
    def load_themes():
        # Load a list of theme names, but do not generate stylesheets yet.
        # Pre-generating multiple stylesheets wastes memory
        iterator = QDirIterator(ThemeManager.__THEME_PATH)
        while iterator.hasNext():
            info = QFileInfo(iterator.next())
            if info.completeSuffix().lower() == "csv":
                ThemeManager.__themes.append(info.baseName())

    @staticmethod
    def themes() -> List[str]:
        return ThemeManager.__themes.copy()

    @staticmethod
    def apply_theme(app: QApplication, theme: str) -> bool:
        if theme not in ThemeManager.__themes:
            print("A")
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
        dark_file = QFile(f"{ThemeManager.__THEME_PATH}/{theme}.csv")
        if dark_file.open(QIODevice.ReadOnly):
            for line in bytes(dark_file.readAll()).decode().splitlines(False):
                # Index 0 = variable, Index 1 = value
                parts = line.replace(", ", ",").split(",")
                stylesheet_str = stylesheet_str.replace(f"@{parts[0]}@", parts[1])
        else:
            return False

        app.setStyleSheet(stylesheet_str)

        return True


