
import sys
import os
import platform
import multiprocessing
import subprocess

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt, QFile, QIODevice
from PySide6.QtGui import QPalette, QColor, QGuiApplication

from drive_station import DriveStationWindow
from util import theme_manager, settings_manager, logger


QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

# TODO: Stdout and Stderr redirect to log file (along with log data shown in DS log window)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.arpirobot.arpirobot-drivestation")
except AttributeError:
    pass

app = None

# QT 6.4 introduced experimental support for dark mode on windows
# Note that the windows them is terrible for now, but Fusion looks good
if platform.system() == "Windows":
    import winreg
    path = winreg.HKEY_CURRENT_USER
    try:
        key = winreg.OpenKeyEx(path, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize")
        value = winreg.QueryValueEx(key, r"AppsUseLightTheme")
        if value[0] == 0:
            # TODO: When QT 6.5 released, there should be better support for this
            #       Probably a new dark / light mode API
            #       Also windowsvista theme should support dark mode
            #       Will likely also be auto detected / applied
            #       In other words, all of this is probably removed with QT 6.5
            sys.argv += ['-platform', 'windows:darkmode=2']
            app = QApplication(sys.argv)
            app.setStyle("Fusion")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            app.setPalette(dark_palette)
            app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
        if key:
            winreg.CloseKey(key)
    except:
        pass

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


# Nothing special for app creation needed. Create as usual.
if app is None:
    app = QApplication(sys.argv)

theme_manager.set_app(app)
theme_manager.apply_theme(settings_manager.theme, settings_manager.larger_fonts)

ds = DriveStationWindow()

logger.set_ds(ds)

ds.show()
app.exec()
