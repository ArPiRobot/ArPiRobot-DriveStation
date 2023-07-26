
import sys
import os
import platform
import multiprocessing
import subprocess

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QFile, QIODevice
from PySide6.QtGui import QPalette, QColor, QGuiApplication

from drive_station import DriveStationWindow
from util import logger


QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

# TODO: Stdout and Stderr redirect to log file (along with log data shown in DS log window)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except AttributeError:
    pass

app = None

# Fix gnome wayland things
if platform.system() == "Linux":
    # QGuiApplication.platformName() is empty until app instantiated
    # So need to create app first, but need to change things before app create
    # Logical solution is to create app, read platform, then destroy app
    # But this is impossible with PySide...
    # And multiple apps is not allowed
    # So instead, use a subprocess. Killing subprocess kills it's app
    def mp_target(argv, return_dict):
        tmp = QApplication(argv)
        return_dict['plat_name'] = QGuiApplication.platformName()
        tmp.quit()
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=mp_target, daemon=True, args=(sys.argv, return_dict))
    p.start()
    p.join()
    plat_name = return_dict['plat_name']
    if plat_name == "wayland" and os.environ['XDG_CURRENT_DESKTOP'].find("GNOME") != -1:
        # Running with wayland platform plugin in a gnome session
        cursor_size = int(subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "cursor-size"]))
        text_scale_factor = float(subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "text-scaling-factor"]))
        cursor_theme = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"]).decode()
        if 'QT_FONT_DPI' not in os.environ:
            os.environ['QT_FONT_DPI'] = str(int(text_scale_factor * 96))
        if 'XCURSOR_SIZE' not in os.environ:
            os.environ['XCURSOR_SIZE'] = str(cursor_size)
        if 'XCURSOR_THEME' not in os.environ:
            os.environ['XCURSOR_THEME'] = cursor_theme[1:-2]

app = QApplication(sys.argv)
app.setStyle("Fusion")

# Theme fixes (only needed for dark theme; light always works properly)
if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
    if platform.system() == "Windows":
        # Somehow, this fixes checkboxes being blue on windows dark theme.
        # Not really sure why, but it does.
        app = QApplication.instance()
        p = app.palette()
        for cg in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Current, QPalette.ColorGroup.Disabled, QPalette.ColorGroup.Inactive]:
            p.setColor(cg, QPalette.ColorRole.Base, p.color(cg, QPalette.ColorRole.Base))
        app.setPalette(p)
    elif platform.system() == "Darwin":
        # TODO: Button text color wrong when inactive
        pass
    else:
        is_plasma = os.environ['XDG_CURRENT_DESKTOP'].find("KDE") != -1
        is_lxqt = os.environ['XDG_CURRENT_DESKTOP'].find("LXQt") != -1

        if not is_lxqt and not is_plasma:
            # Some disabled and inactive colors are wrong on gtk desktops
            # This does not impact plasma (and presumably would not impact LXQt)
            # https://bugreports.qt.io/browse/QTBUG-113486
            p = app.palette()
            p.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Button))
            p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Button).lighter())
            # TODO: Button borders
            app.setPalette(p)

            # TODO: Sometimes (manjaro but not ubuntu), inactive text color (buttontext) is wrong like macos
            pass

ds = DriveStationWindow()

logger.set_ds(ds)

ds.show()
app.exec()
