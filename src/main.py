
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QFile, QIODevice

from drive_station import DriveStationWindow
from src.util import ThemeManager

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except AttributeError:
    pass

app = QApplication(sys.argv)

# Custom stylesheet used is designed for fusion base
app.setStyle(QStyleFactory.create("Fusion"))

ThemeManager.load_themes()
ThemeManager.apply_theme(app, "Dark")

ds = DriveStationWindow()
ds.show()
app.exec()
