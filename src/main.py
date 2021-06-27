
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

# Load stylesheet. This is a stylesheet with placeholders. It cannot be used directly
stylesheet_str = ""
stylesheet_file = QFile(":/stylesheet.qss")
if stylesheet_file.open(QIODevice.ReadOnly):
    stylesheet_str = bytes(stylesheet_file.readAll()).decode()
stylesheet_file.close()

# TODO: Generate different stylesheets for each variable set to allow different color schemes
# Substitute values for placeholders in stylesheet
dark_file = QFile(":/stylesheet-vars/dark.csv")
if dark_file.open(QIODevice.ReadOnly):
    for line in bytes(dark_file.readAll()).decode().splitlines(False):
        # Index 0 = variable, Index 1 = value
        parts = line.replace(", ", ",").split(",")
        stylesheet_str = stylesheet_str.replace(f"@{parts[0]}@", parts[1])

app.setStyleSheet(stylesheet_str)

ds = DriveStationWindow()
ds.show()
app.exec()
