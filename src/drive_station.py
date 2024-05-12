from typing import Any, Callable, Dict, Optional
import typing

from PySide6.QtGui import QCloseEvent, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument, QPalette, QIcon
from PySide6.QtWidgets import QApplication

from gamepad import GamepadManager
from settings_dialog import SettingsDialog
from PySide6.QtWidgets import QMainWindow, QLabel, QListWidgetItem, QDialog, QInputDialog, QLineEdit
from PySide6.QtCore import QFile, QIODevice, QRegularExpression, QTimer, Qt, QRect, QDir

from indicator_widget import IndicatorWidget
from ui_drive_station import Ui_DriveStationWindow
from util import HTMLDelegate, settings_manager, logger
from network import NetworkManager
from about_dialog import AboutDialog

import json
import sdl2
import math


class ControllerListItem(QListWidgetItem):
    def __init__(self, name: str, handle: int, index_getter: Callable[['ControllerListItem'], int]):
        super().__init__()
        self.name = name
        self.handle = handle
        self.checked = False
        self.__index_getter = index_getter

    def data(self, role: int) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            idx = self.__index_getter(self)
            return f"<p>({idx}) <i>{self.name}</i></p>"
        elif role == Qt.ItemDataRole.CheckStateRole:
            return self.checked
        return super().data(role)

    def setData(self, role: int, value: Any):
        if role == Qt.ItemDataRole.CheckStateRole:
            self.checked = value
        else:
            super().setData(role, value)

    def flags(self) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEnabled | \
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable


class LogHighlighter(QSyntaxHighlighter):

    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self.fmt_debug = QTextCharFormat()
        self.fmt_info = QTextCharFormat()
        self.fmt_warning = QTextCharFormat()
        self.fmt_error = QTextCharFormat()
        self.construct_format_from_theme()
    
    def construct_format_from_theme(self):
        if QApplication.palette().color(QPalette.ColorRole.Window).valueF() >= 0.5:
            # Light theme highlight colors
            color_debug = "#007800"
            color_info = "#000000"
            color_warning = "#B05700"
            color_error = "#B60000"
        else:
            # Dark theme highlight colors
            color_debug = "#00FF00"
            color_info = "#FFFFFF"
            color_warning = "#FF7F00"
            color_error = "#FF0000"

        self.fmt_debug.setForeground(QColor(color_debug))
        self.fmt_info.setForeground(QColor(color_info))
        self.fmt_warning.setForeground(QColor(color_warning))
        self.fmt_error.setForeground(QColor(color_error))
    
    def highlightBlock(self, text: str) -> None:
        debug_expr = QRegularExpression("^\\[DEBUG\\].*$")
        info_expr = QRegularExpression("^\\[INFO\\].*$")
        warning_expr = QRegularExpression("^\\[WARNING\\].*$")
        error_expr = QRegularExpression("^\\[ERROR\\].*$")

        dbg = debug_expr.globalMatch(text)
        while dbg.hasNext():
            match = dbg.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.fmt_debug)
        
        info = info_expr.globalMatch(text)
        while info.hasNext():
            match = info.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.fmt_info)
        
        warning = warning_expr.globalMatch(text)
        while warning.hasNext():
            match = warning.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.fmt_warning)
        
        error = error_expr.globalMatch(text)
        while error.hasNext():
            match = error.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.fmt_error)



class DriveStationWindow(QMainWindow):

    ############################################################################
    # Constants
    ############################################################################

    # Status messages
    MSG_STATE_NO_NETWORK = "Connecting to robot at '{0}'..."
    MSG_STATE_NO_PROGRAM = "No program running on robot."
    MSG_STATE_DISABLED = "Robot disabled."
    MSG_STATE_ENABLED = "Robot enabled."

    ############################################################################
    # UI & Navigation
    ############################################################################

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # UI Setup
        self.ui = Ui_DriveStationWindow()
        self.ui.setupUi(self)

        # Append version to about label
        version_file = QFile(":/version.txt")
        if version_file.open(QIODevice.OpenModeFlag.ReadOnly):
            ver = bytes(version_file.readLine().data()).decode().replace("\n", "").replace("\r", "")
            self.setWindowTitle(self.windowTitle() + " v" + ver)
        version_file.close()

        # Configure label for permanent status bar message
        # This is not supported in QT Designer, so done in code
        self.lbl_status_msg = QLabel()
        self.ui.statusbar.addPermanentWidget(self.lbl_status_msg)
        self.ui.statusbar.addPermanentWidget(QLabel(), 1)  # Spacer so msg label is on left

        # Allows controller names to be partially italicized
        self.ui.lst_controllers.setItemDelegate(HTMLDelegate())

        # Handles coloration of log output
        self.ds_log_highlighter = LogHighlighter(self.ui.txt_ds_log.document())
        self.robot_log_highlighter = LogHighlighter(self.ui.txt_robot_log.document())

        # Timer to periodically update the bars for the selected controller
        self.controller_status_timer = QTimer()
        self.controller_status_timer.timeout.connect(self.update_controller_bars)

        # Timer to send controller data to the robot
        self.controller_send_timer = QTimer()
        self.controller_send_timer.timeout.connect(self.send_controller_data)

        # Timer to send TEST command (allows TCP connection dropped to be detected in some circumstances)
        self.test_tcp_timer = QTimer()
        self.test_tcp_timer.timeout.connect(self.do_test_tcp)

        # Non-UI element variables
        self.voltage: float = 0.0
        self.net_manager = NetworkManager()
        self.gamepad_manager = GamepadManager(mappings_file=":/gamecontrollerdb.txt")
        self.indicators: Dict[str, IndicatorWidget] = {}

        # Signal / slot setup
        self.ui.btn_disable.clicked.connect(self.disable_clicked)
        self.ui.btn_enable.clicked.connect(self.enable_clicked)
        self.ui.btn_settings.clicked.connect(self.open_settings)
        self.ui.act_about.triggered.connect(self.open_about)
        self.ui.act_add_indicator.triggered.connect(self.add_indicator)
        self.ui.act_clear_indicators.triggered.connect(self.clear_indicators)

        self.ui.lst_controllers.viewport().installEventFilter(self)

        self.net_manager.nt_data_changed.connect(self.nt_data_changed)
        self.net_manager.state_changed.connect(self.state_changed)
        self.net_manager.nt_sync_started.connect(lambda: self.ui.pnl_net_table.setEnabled(False))
        self.net_manager.nt_sync_finished.connect(lambda: self.ui.pnl_net_table.setEnabled(True))

        self.gamepad_manager.connected.connect(self.gamepad_connected)
        self.gamepad_manager.disconnected.connect(self.gamepad_disconnected)

        # On some systems, fusion theme will only repaint progress bar every several pixels, leading to choppy motion
        # To fix this, force a repaint to happen every time the value changes
        self.force_instant_pbar_updates()

        # Configure initial State
        self.load_indicators()
        self.set_battery_voltage(0, settings_manager.vbat_main)
        self.set_robot_program_good(True)

        # Start gamepad and network managers
        self.gamepad_manager.start()
        QTimer.singleShot(1000, lambda: self.net_manager.set_robot_address(settings_manager.robot_address))

        # Start after gamepad manager
        self.controller_status_timer.start(16)  # ~ 60 updates / second
        self.controller_send_timer.start(20)

        self.test_tcp_timer.start(2000)         # Once every 2 seconds

        self.__set_font_size()
        self.__on_color_change()

    def do_test_tcp(self):
        self.net_manager.send_test_command()

    def __on_color_change(self):
        # Determine if color scheme is light or dark
        # Note: not using QApplication.styleHints().colorScheme()
        # because this doesn't account for actual palette just what system recommends
        # thus if command line flags or environment var are used to alter this (eg -platform windows:darkmode=0)\
        # this would be incorrect. Future QT may introduce colorScheme value to QPalette instead.
        is_dark = QApplication.palette().color(QPalette.ColorRole.Window).valueF() < 0.5
        

        # Pick colors / icons based on light or dark scheme
        color_text = QApplication.palette().color(QPalette.ColorRole.Text).name()
        settings_icon = ":/icons/gear_light.png" if is_dark else ":/icons/gear_dark.png"
        color_disable_btn = "#FF0000" if is_dark else "#990000"
        color_enable_btn = "#00AA00" if is_dark else "#004D00"
        color_status_red = "#800000" if is_dark else "#C80000"
        color_status_green = "#008000" if is_dark else "#00C800"
        color_battery_red = "#800000" if is_dark else "#C80000"
        color_battery_orange = "#B37800" if is_dark else "#E59900"
        color_battery_yellow = "#BCBC00" if is_dark else "#E6E600"
        color_battery_green = "#008000" if is_dark else "#00C800"

        # Indicator panel colors
        self.ui.pnl_bat_bg.setStyleSheet("""
            QWidget#pnl_bat_bg_red{{
                background-color: {red_color};
                border-radius: 3px;
            }}
            QWidget#pnl_bat_bg_orange{{
                background-color: {orange_color};
                border-radius: 3px;
            }}
            QWidget#pnl_bat_bg_yellow{{
                background-color: {yellow_color};
                border-radius: 3px;
            }}
            QWidget#pnl_bat_bg_green{{
                background-color: {green_color};
                border-radius: 3px;
            }}
        """.format(
            red_color=color_battery_red, 
            orange_color=color_battery_orange, 
            yellow_color=color_battery_yellow, 
            green_color=color_battery_green,
            text_color=color_text
        ))
        self.ui.pnl_net_bg.setStyleSheet("""
            QWidget#pnl_net_bg{{
                border: 1px solid {text_color};
                border-radius: 3px;
            }}
            QWidget#pnl_net_bg_red{{
                border: 1px solid {text_color};
                border-radius: 3px;
                background-color: {red_color};
            }}
            QWidget#pnl_net_bg_green{{
                border: 1px solid {text_color};
                border-radius: 3px;
                background-color: {green_color};
            }}
        """.format(
            text_color=color_text,
            red_color=color_status_red,
            green_color=color_status_green
        ))
        self.ui.pnl_program_bg.setStyleSheet("""
            QWidget#pnl_program_bg{{
                border: 1px solid {text_color};
                border-radius: 3px;
            }}
            QWidget#pnl_program_bg_red{{
                border: 1px solid {text_color};
                border-radius: 3px;
                background-color: {red_color};
            }}
            QWidget#pnl_program_bg_green{{
                border: 1px solid {text_color};
                border-radius: 3px;
                background-color: {green_color};
            }}
        """.format(
            text_color=color_text,
            red_color=color_status_red,
            green_color=color_status_green
        ))

        # Icon of settings button
        self.ui.btn_settings.setIcon(QIcon(settings_icon))

        # Text color of Enable / Disable buttons
        self.ui.btn_disable.setStyleSheet("color: {};".format(color_disable_btn))
        self.ui.btn_enable.setStyleSheet("color: {};".format(color_enable_btn))

        # All indicators for network table
        for ind in self.indicators.values():
            ind.setStyleSheet("""
            IndicatorWidget{{
                
            }}
            IndicatorWidget:focus{{
                border: 1px solid {text_color};
                border-radius: 2px;
            }}
            """.format(
                text_color=color_text
            ))

    def __set_font_size(self):
        size = QFont().pointSizeF()
        if settings_manager.larger_fonts:
            size *= 1.2
        app = typing.cast(QApplication, QApplication.instance())
        app.setStyleSheet("{0}\n{1}".format(app.styleSheet(), "*{{font-size: {0}pt}}".format(size)))


    def closeEvent(self, event: QCloseEvent):
        self.save_indicators()
        self.net_manager.stop()
        self.gamepad_manager.stop()

    def open_settings(self):
        dialog = SettingsDialog(self)
        res = dialog.exec()
        if res == QDialog.DialogCode.Accepted:
            old_address = settings_manager.robot_address

            dialog.save_settings()

            # Disconnect if robot address changed
            if settings_manager.robot_address != old_address:
                self.net_manager.set_robot_address(settings_manager.robot_address)

            # Update main battery voltage (but don't change current voltage)
            self.set_battery_voltage(self.voltage, settings_manager.vbat_main)

            # Support larger fonts
            self.__set_font_size()

            # Theme has changed. Re-apply syntax highlighting to logs
            self.ds_log_highlighter.construct_format_from_theme()
            self.robot_log_highlighter.construct_format_from_theme()
            self.ds_log_highlighter.rehighlight()
            self.robot_log_highlighter.rehighlight()


    def open_about(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def force_instant_pbar_updates(self):
        self.ui.pbar_lx.valueChanged.connect(self.ui.pbar_lx.update)
        self.ui.pbar_ly.valueChanged.connect(self.ui.pbar_ly.update)
        self.ui.pbar_rx.valueChanged.connect(self.ui.pbar_rx.update)
        self.ui.pbar_ry.valueChanged.connect(self.ui.pbar_ry.update)
        self.ui.pbar_l2.valueChanged.connect(self.ui.pbar_l2.update)
        self.ui.pbar_r2.valueChanged.connect(self.ui.pbar_r2.update)
        self.ui.pbar_a.valueChanged.connect(self.ui.pbar_a.update)
        self.ui.pbar_b.valueChanged.connect(self.ui.pbar_b.update)
        self.ui.pbar_x.valueChanged.connect(self.ui.pbar_x.update)
        self.ui.pbar_y.valueChanged.connect(self.ui.pbar_y.update)
        self.ui.pbar_back.valueChanged.connect(self.ui.pbar_back.update)
        self.ui.pbar_guide.valueChanged.connect(self.ui.pbar_guide.update)
        self.ui.pbar_start.valueChanged.connect(self.ui.pbar_start.update)
        self.ui.pbar_l3.valueChanged.connect(self.ui.pbar_l3.update)
        self.ui.pbar_r3.valueChanged.connect(self.ui.pbar_r3.update)
        self.ui.pbar_l1.valueChanged.connect(self.ui.pbar_l1.update)
        self.ui.pbar_r1.valueChanged.connect(self.ui.pbar_r1.update)
        self.ui.pbar_dpad_0.valueChanged.connect(self.ui.pbar_dpad_0.update)
        self.ui.pbar_dpad_up.valueChanged.connect(self.ui.pbar_dpad_up.update)
        self.ui.pbar_dpad_down.valueChanged.connect(self.ui.pbar_dpad_down.update)
        self.ui.pbar_dpad_left.valueChanged.connect(self.ui.pbar_dpad_left.update)
        self.ui.pbar_dpad_right.valueChanged.connect(self.ui.pbar_dpad_right.update)

    def log_debug(self, msg: str):
        self.ui.txt_ds_log.append(f"[DEBUG]: {msg}")

    def log_info(self, msg: str):
        self.ui.txt_ds_log.append(f"[INFO]: {msg}")

    def log_warning(self, msg: str):
        self.ui.txt_ds_log.append(f"[WARNING]: {msg}")

    def log_error(self, msg: str):
        self.ui.txt_ds_log.append(f"[ERROR]: {msg}")
    
    def log_from_robot(self, msg: str):
        self.ui.txt_robot_log.append(msg)

    ############################################################################
    # Gamepads
    ############################################################################

    def gamepad_connected(self, device_id: int, device_name: str):
        self.ui.lst_controllers.addItem(ControllerListItem(device_name, device_id, self.ui.lst_controllers.row))

    def gamepad_disconnected(self, device_id: int):
        for i in range(self.ui.lst_controllers.count()):
            item = typing.cast(ControllerListItem, self.ui.lst_controllers.item(i))
            if item.handle == device_id:
                self.ui.lst_controllers.takeItem(i)
                break
        # If a gamepad is disconnected disable the robot
        # Gamepad numbers may have changed
        if self.net_manager.current_state == NetworkManager.State.Enabled:
            logger.log_warning("Gamepad disconnected. Disabling robot as controller numbers may have changed.")
            self.net_manager.send_disable_command()
    
    def update_controller_bars(self):
        selected_rows = [x.row() for x in self.ui.lst_controllers.selectedIndexes()]
        idx = -1
        if len(selected_rows) != 0:
            idx = selected_rows[0]
        if idx == -1:
            self.ui.pbar_lx.setValue(0)
            self.ui.pbar_ly.setValue(0)
            self.ui.pbar_rx.setValue(0)
            self.ui.pbar_ry.setValue(0)
            self.ui.pbar_l2.setValue(0)
            self.ui.pbar_r2.setValue(0)
            self.ui.pbar_a.setValue(0)
            self.ui.pbar_b.setValue(0)
            self.ui.pbar_x.setValue(0)
            self.ui.pbar_y.setValue(0)
            self.ui.pbar_back.setValue(0)
            self.ui.pbar_guide.setValue(0)
            self.ui.pbar_start.setValue(0)
            self.ui.pbar_l3.setValue(0)
            self.ui.pbar_r3.setValue(0)
            self.ui.pbar_l1.setValue(0)
            self.ui.pbar_r1.setValue(0)
            self.ui.pbar_dpad_0.setValue(1)
            self.ui.pbar_dpad_left.setValue(0)
            self.ui.pbar_dpad_right.setValue(0)
            self.ui.pbar_dpad_up.setValue(0)
            self.ui.pbar_dpad_down.setValue(0)
        else:
            device_id =  typing.cast(ControllerListItem, self.ui.lst_controllers.item(idx)).handle
            self.ui.pbar_lx.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_LEFTX))
            self.ui.pbar_ly.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_LEFTY))
            self.ui.pbar_rx.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTX))
            self.ui.pbar_ry.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTY))
            self.ui.pbar_l2.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT))
            self.ui.pbar_r2.setValue(self.gamepad_manager.get_axis(device_id, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT))
            self.ui.pbar_a.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_A) else 0)
            self.ui.pbar_b.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_B) else 0)
            self.ui.pbar_x.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_X) else 0)
            self.ui.pbar_y.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_Y) else 0)
            self.ui.pbar_back.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_BACK) else 0)
            self.ui.pbar_guide.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_GUIDE) else 0)
            self.ui.pbar_start.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_START) else 0)
            self.ui.pbar_l3.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK) else 0)
            self.ui.pbar_r3.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK) else 0)
            self.ui.pbar_l1.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER) else 0)
            self.ui.pbar_r1.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER) else 0)
            self.ui.pbar_dpad_left.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT) else 0)
            self.ui.pbar_dpad_right.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT) else 0)
            self.ui.pbar_dpad_up.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP) else 0)
            self.ui.pbar_dpad_down.setValue(1 if self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN) else 0)
            self.ui.pbar_dpad_0.setValue(0 if (
                self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT) or
                self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT) or
                self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP) or
                self.gamepad_manager.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN)
            ) else 1)

    def send_controller_data(self):
        for i in range(self.ui.lst_controllers.count()):
            item =  typing.cast(ControllerListItem, self.ui.lst_controllers.item(i))
            if item.checkState() == Qt.CheckState.Checked:
                device_id = item.handle
                self.net_manager.send_controller_data(self.get_controller_data(i, device_id))

    def get_controller_data(self, controller_num: int, device_id: int) -> bytes:
        # Constants since these are known for SDL gamepads.
        # If SDL joysticks are ever used these would need to be determined using SDL functions
        axis_count = 6
        button_count = 11
        dpad_count = 1

        # Packet = controller_num, axis_count, button_count, dpad_count, 2 bytes per axis, 1 byte per 8 buttons, 1 byte per two dpads, '\n'
        # Axes are signed 16-bit integers sent across two bytes (big endian)
        # Buttons are 1 bit per button (8 buttons per byte)
        # Dpads are 4 bits per dpad (2 dpads per byte)
        # packet_size = 5 + 2 * axis_count + int(math.ceil(button_count / 8.0)) + int(math.ceil(dpad_count / 2.0))

        buffer = bytearray()

        # Prefix info
        buffer.extend(controller_num.to_bytes(length=1, byteorder='big'))
        buffer.extend(axis_count.to_bytes(length=1, byteorder='big'))
        buffer.extend(button_count.to_bytes(length=1, byteorder='big'))
        buffer.extend(dpad_count.to_bytes(length=1, byteorder='big'))

        # Encode axes
        for i in range(axis_count):
            val = self.gamepad_manager.get_axis(device_id, i)
            buffer.extend(val.to_bytes(length=2, byteorder='big', signed=True))
        
        # Encode buttons
        for i in range(math.ceil(button_count / 8.0)):
            b = 0
            for j in range(8):
                # Shift bits left
                b = (b << 1) & 0xFF

                # If there are still buttons set next bit
                if i * 8 + j < button_count:
                    val = self.gamepad_manager.get_button(device_id, i * 8 + j)
                    b |= 1 if val else 0
            buffer.extend(b.to_bytes(length=1, byteorder='big'))

        # Encode dpad data
        for i in range(math.ceil(dpad_count / 2.0)):
            b = 0
            for j in range(2):
                # Shift bits left
                b = (b << 4) & 0xFF

                # Add data if there are still dpads
                if i * 2 + j < dpad_count:
                    val = self.gamepad_manager.get_dpad_pos_num(device_id)
                    b |= (val & 0x0F)
            buffer.extend(b.to_bytes(length=1, byteorder='big'))

        # End of packet character
        buffer.extend(b'\n')

        return bytes(buffer)



    ############################################################################
    # Indicators & Network Table
    ############################################################################

    def add_indicator(self, key: Optional[str] = None, geometry: Optional[QRect] = None):
        # If no key given, ask the user
        if key is None:
            key, ok = QInputDialog.getText(self, self.tr("Add Indicator"), self.tr("Key:"), QLineEdit.EchoMode.Normal)
            if not ok:
                return
        
        # Make sure there is not already an indicator for the given key
        if key == "" or key in self.indicators:
            return

        # Remove the key from the "Add from robot" menu if needed
        for action in self.ui.act_add_from_robot.actions():
            if action.text() == key:
                self.ui.act_add_from_robot.removeAction(action)

        # Add the indicator
        self.add_indicator_at(key, geometry)

    def clear_indicators(self):
        for key in self.indicators.keys():
            self.indicators[key].hide()
            self.indicators[key].deleteLater()
        self.indicators.clear()

    def add_indicator_at(self, key: str, geometry: Optional[QRect]):
        ind = IndicatorWidget(self.ui.pnl_net_table)
        ind.deleted.connect(self.indicator_deleted)
        ind.value_changed.connect(self.indicator_value_changed)
        ind.key = key
        if self.net_manager.has_net_table(key):
            ind.value = self.net_manager.get_net_table(key)
        else:
            ind.value = ""
        if geometry is None:
            # Place indicator in center of panel
            panel_geom = self.ui.pnl_net_table.geometry()
            ind_geom = ind.geometry()
            geometry = QRect()
            geometry.setTop(int(panel_geom.height() / 2.0 - ind_geom.height() / 2.0))
            geometry.setLeft(int(panel_geom.width() / 2.0 - ind_geom.width() / 2.0))
            geometry.setWidth(ind_geom.width())
            geometry.setHeight(ind_geom.height())
        ind.setGeometry(geometry)

        # Apply correct stylesheet
        color_text = QApplication.palette().color(QPalette.ColorRole.Text).name()
        ind.setStyleSheet("""
        IndicatorWidget{{
            
        }}
        IndicatorWidget:focus{{
            border: 1px solid {text_color};
            border-radius: 2px;
        }}
        """.format(
            text_color=color_text
        ))

        ind.show()
        self.indicators[key] = ind

    def save_indicators(self):
        try:
            data: Dict[str, Dict] = {}
            for key, ind in self.indicators.items():
                data[ind.key] = {
                    "x": ind.geometry().x(),
                    "y": ind.geometry().y(),
                    "width": ind.geometry().width(),
                    "height": ind.geometry().height(),
                    "editable": not ind.ui.txt_value.isReadOnly()
                }
            with open(QDir.homePath() + "/.arpirobot/dsindicators.json", "w") as data_file:
                json.dump(data, data_file)
        except:
            pass

    def load_indicators(self):
        try:
            with open(QDir.homePath() + "/.arpirobot/dsindicators.json", "r") as data_file:
                data: Dict[str, Dict] = json.load(data_file)
                for key, subdata in data.items():
                    x = subdata["x"]
                    y = subdata["y"]
                    width = subdata["width"]
                    height = subdata["height"]
                    self.add_indicator(key, QRect(x, y, width, height))
                    if "editable" in subdata:
                        self.indicators[key].ui.txt_value.setReadOnly(not subdata["editable"])
        except:
            pass

    def indicator_deleted(self, key: str):
        if key in self.indicators:
            self.indicators[key].hide()
            self.indicators[key].deleteLater()
            del self.indicators[key]

            # This indicator will have been added to the robot
            # Or it will be next time a robot is connected to (due to NT sync)
            action = self.ui.act_add_from_robot.addAction(key)
            action.triggered.connect(lambda checked: self.add_indicator(key))

    def indicator_value_changed(self, key: str, value: str):
        self.net_manager.set_net_table(key, value)

    # Slot for NetworkManager signal
    def nt_data_changed(self, key: str, value: str):
        if key == "vbat0":
            self.set_battery_voltage(float(value), settings_manager.vbat_main)
        else:
            # If the key is already in the indicator panel, don't add it to the menu
            if key not in self.indicators:
                # Add to "Add from robot" menu if not already in that menu
                action_found = False
                for action in self.ui.act_add_from_robot.actions():
                    if action.text() == key:
                        action_found = True
                        break
                if not action_found:
                    action = self.ui.act_add_from_robot.addAction(key)
                    action.triggered.connect(lambda checked: self.add_indicator(key))
            else:
                # Inidicator is shown. Update it's value.
                self.indicators[key].value = value

    def set_battery_voltage(self, voltage: float, nominal_bat_voltage: float):
        if voltage >= nominal_bat_voltage:
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_green")
        elif voltage >= nominal_bat_voltage * 0.85:
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_yellow")
        elif voltage >= nominal_bat_voltage * 0.7:
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_orange")
        else:
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_red")
        self.ui.lbl_bat_voltage.setText("{:.2f} V".format(voltage))

        # Force stylesheet to be reapplied due to object name change
        self.ui.pnl_bat_bg.style().unpolish(self.ui.pnl_bat_bg)
        self.ui.pnl_bat_bg.style().polish(self.ui.pnl_bat_bg)

    ############################################################################
    # State Changes
    ############################################################################

    def disable_clicked(self):
        # Don't toggle the checked state of these buttons on click.
        # The checked state will be changed when network manager emits signal for state changed
        self.ui.btn_disable.setChecked(not self.ui.btn_disable.isChecked())

        self.net_manager.send_disable_command()

    def enable_clicked(self):
        # Don't toggle the checked state of these buttons on click.
        # The checked state will be changed when network manager emits signal for state changed
        self.ui.btn_enable.setChecked(not self.ui.btn_enable.isChecked())

        self.net_manager.send_enable_command()

    # Slot for NetworkManager signal
    def state_changed(self, state):
        if state == NetworkManager.State.Disabled:
            self.set_state_disabled()
        elif state == NetworkManager.State.Enabled:
            self.set_state_enabled()
        elif state == NetworkManager.State.NoNetwork:
            self.set_state_no_network()
        elif state == NetworkManager.State.NoRobotProgram:
            self.set_state_no_program()

    def set_state_no_network(self):
        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_NO_NETWORK).format(settings_manager.robot_address))
        self.set_network_good(False)
        self.set_robot_program_good(False)

    def set_state_no_program(self):
        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_NO_PROGRAM))
        self.set_network_good(True)
        self.set_robot_program_good(False)

    def set_state_disabled(self):
        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_DISABLED))
        self.set_network_good(True)
        self.set_robot_program_good(True)

    def set_state_enabled(self):
        self.ui.btn_disable.setChecked(False)
        self.ui.btn_enable.setChecked(True)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_ENABLED))
        self.set_network_good(True)
        self.set_robot_program_good(True)

    def set_network_good(self, good: bool):
        if good:
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_green")
        else:
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_red")

        # Force stylesheet to be reapplied due to object name change
        self.ui.pnl_net_bg.style().unpolish(self.ui.pnl_net_bg)
        self.ui.pnl_net_bg.style().polish(self.ui.pnl_net_bg)

    def set_robot_program_good(self, good: bool):
        if good:
            self.ui.pnl_program_bg.setObjectName("pnl_program_bg_green")
        else:
            self.ui.pnl_program_bg.setObjectName("pnl_program_bg_red")
        # Force stylesheet to be reapplied due to object name change
        self.ui.pnl_program_bg.style().unpolish(self.ui.pnl_program_bg)
        self.ui.pnl_program_bg.style().polish(self.ui.pnl_program_bg)
