
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QIODevice, Qt

from .drive_station import DriveStationWindow


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except ImportError:
    pass

app = QApplication(sys.argv)

app_stylesheet = QFile(":/theme.css")
if(app_stylesheet.open(QIODevice.ReadOnly)):
    app.setStyleSheet(bytes(app_stylesheet.readAll()).decode())

ds = DriveStationWindow()
ds.show()
app.exec_()
