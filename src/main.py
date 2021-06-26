
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QFile, QIODevice

from drive_station import DriveStationWindow


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except AttributeError:
    pass

app = QApplication(sys.argv)

# Custom stylesheet used in UI files designed for fusion base
app.setStyle(QStyleFactory.create("Fusion"))

stylesheet_file = QFile(":/stylesheet.qss")
if stylesheet_file.open(QIODevice.ReadOnly):
    app.setStyleSheet(bytes(stylesheet_file.readAll()).decode())
stylesheet_file.close()

ds = DriveStationWindow()
ds.show()
app.exec()
