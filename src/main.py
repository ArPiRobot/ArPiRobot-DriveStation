
import sys

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from PySide2.QtWinExtras import QtWin

import rc_resources
from drive_station import DriveStation


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QtWin.setCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
    app = QApplication(sys.argv)
    ds = DriveStation()
    ds.show()
    app.exec_()
