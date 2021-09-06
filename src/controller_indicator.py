from typing import Optional
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QProgressBar, QStyle, QStyleOption, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget

import re
import string
import hashlib
import time


class ControllerIndicator(QOpenGLWidget):
    def __init__(self, parent: Optional[QWidget] = None, f: Qt.WindowFlags = Qt.Widget) -> None:
        super().__init__(parent=parent, f=f)

        self.__value = 0
        self.__min = -100
        self.__max = 100
        self.__label = ""

        # Caching for selecting chunk color from stylesheet and border radius from stylesheet
        self.__old_md5 = hashlib.md5(b"")
        self.__chunk_color = QColor(255, 0, 0)
        self.__border_radius = 0.0
    
    # def paintGL(self) -> None:
    #     p = QPainter(self)
    #     p.beginNativePainting()
    #     end_x = ((self.__value - self.__min) / (self.__max - self.__min)) * self.width()
    #     p.fillRect(0, 0, end_x, self.height(), Qt.red)
    #     p.fillRect(end_x, 0, self.width() - end_x, self.height(), Qt.black)
    #     p.endNativePainting()
    #     p.end()

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        p.beginNativePainting()
        p.setRenderHint(QPainter.Antialiasing)
        s = self.style()

        # First, draw background
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self)

        # Draw filled part of indicator, matching style of progress bar
        # This is done by manually parsing the stylesheet
        self.update_values_from_stylesheet()
        end_x = ((self.__value - self.__min) / (self.__max - self.__min)) * self.width()
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, end_x, self.height()), 
                self.__border_radius, self.__border_radius)
        p.fillPath(path, self.__chunk_color)

        # Draw text last, so it is on top
        s.drawItemText(p, QRect(0, 0, self.width(), self.height()), Qt.AlignHCenter | Qt.AlignVCenter, self.palette(), True, self.__label)

        p.endNativePainting()
        p.end()

    def update_values_from_stylesheet(self):
        stylesheet = QApplication.instance().styleSheet()
        current_md5 = hashlib.md5(stylesheet.encode())
        if current_md5 != self.__old_md5:
            # Update chunk color
            matches = re.findall('QProgressBar::chunk{(.*)}', stylesheet, re.DOTALL)
            for match in matches:
                match = match.translate(str.maketrans('', '', string.whitespace))
                start = match.find("background-color:")
                if start != -1:
                    end = match.find(";", start)
                    if end != -1:
                        self.__chunk_color = QColor(match[start+17:end])
            
            # Update border radius
            matches = re.findall('ControllerIndicator{(.*)}', stylesheet, re.DOTALL)
            for match in matches:
                match = match.translate(str.maketrans('', '', string.whitespace))
                start = match.find("border-radius:")
                if start != -1:
                    end = match.find(";", start)
                    if end != -1:
                        self.__border_radius = float(match[start+14:end].replace("px", ""))
            self.__old_md5 = current_md5

    def setValue(self, value: int):
        if isinstance(value, int):
            self.__value = value
            self.update()

    def value(self) -> int:
        return self.__value

    def setMin(self, min: int):
        if isinstance(min, int):
            self.__min = min
            self.update()

    def min(self) -> int:
        return self.__min

    def setMax(self, max: int):
        if isinstance(max, int):
            self.__max = max
            self.update()

    def max(self) -> int:
        return self.__max

    def setLabel(self, label: str):
        if isinstance(label, str):
            self.__label = label
            self.update()

    def label(self) -> str:
        return self.__label 