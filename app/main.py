
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import QFile, QIODevice, Qt

from .drive_station import DriveStationWindow


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

ds = DriveStationWindow()
ds.show()
app.exec_()
