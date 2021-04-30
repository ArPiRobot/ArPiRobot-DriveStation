
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import rc_resources
from drive_station import DriveStation


if __name__ == "__main__":
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
