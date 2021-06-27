
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QFile, QIODevice

from drive_station import DriveStationWindow
from util import theme_manager, settings_manager


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except AttributeError:
    pass

app = QApplication(sys.argv)

theme_manager.set_app(app)
theme_manager.load_themes()
theme_manager.apply_theme(settings_manager.theme, settings_manager.larger_fonts)

ds = DriveStationWindow()
ds.show()
app.exec()
