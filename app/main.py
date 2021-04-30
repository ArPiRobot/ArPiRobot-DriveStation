
import sys

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt

from . import rc_resources
from .drive_station import DriveStation


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

try:
    from PySide2.QtWinExtras import QtWin
    QtWin.setCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except ImportError:
    pass

app = QApplication(sys.argv)
ds = DriveStation()
ds.show()
app.exec_()
