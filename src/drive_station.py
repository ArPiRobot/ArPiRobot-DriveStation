from typing import Any, Callable, Dict

from PySide6.QtGui import QCloseEvent

from settings_dialog import SettingsDialog
from PySide6.QtWidgets import QMainWindow, QLabel, QListWidgetItem, QDialog, QInputDialog, QLineEdit
from PySide6.QtCore import QFile, QIODevice, Qt, QRect, QDir

from src.indicator_widget import IndicatorWidget
from ui_drive_station import Ui_DriveStationWindow
from util import HTMLDelegate, settings_manager, theme_manager
from network import State, NetworkManager
from about_dialog import AboutDialog

import json


class ControllerListItem(QListWidgetItem):
    def __init__(self, name: str, handle: int, index_getter: Callable[['ControllerListItem'], int]):
        super().__init__()
        self.name = name
        self.handle = handle
        self.checked = False
        self.__index_getter = index_getter

    def data(self, role: int) -> Any:
        if role == Qt.DisplayRole:
            idx = self.__index_getter(self)
            return f"<p>({idx}) <i>{self.name}</i></p>"
        elif role == Qt.CheckStateRole:
            return self.checked
        return super().data(role)

    def setData(self, role: int, value: Any):
        if role == Qt.CheckStateRole:
            self.checked = value
        else:
            super().setData(role, value)

    def flags(self) -> Qt.ItemFlags:
        return Qt.ItemIsDropEnabled | Qt.ItemIsEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable


class DriveStationWindow(QMainWindow):
    # State messages
    MSG_STATE_NO_NETWORK = "Connecting to robot at '{0}'..."
    MSG_STATE_NO_PROGRAM = "No program running on robot."
    MSG_STATE_DISABLED = "Robot disabled."
    MSG_STATE_ENABLED = "Robot enabled."

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        ########################################################################
        # UI Setup
        ########################################################################

        self.ui = Ui_DriveStationWindow()
        self.ui.setupUi(self)

        # Append version to about label
        version_file = QFile(":/version.txt")
        if version_file.open(QIODevice.ReadOnly):
            ver = bytes(version_file.readLine()).decode().replace("\n", "").replace("\r", "")
            self.setWindowTitle(self.windowTitle() + " v" + ver)
        version_file.close()

        # Configure label for permanent status bar message
        # This is not supported in QT Designer, so done in code
        self.lbl_status_msg = QLabel()
        self.ui.statusbar.addPermanentWidget(self.lbl_status_msg)
        self.ui.statusbar.addPermanentWidget(QLabel(), 1)  # Spacer so msg label is on left

        self.ui.lst_controllers.setItemDelegate(HTMLDelegate())
        for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
            self.ui.lst_controllers.addItem(ControllerListItem(f"Controller {i}", -1, self.ui.lst_controllers.row))

        ########################################################################
        # Non-UI Variables
        ########################################################################

        # Don't need to mutex these. Only accessed from UI thread by using signals/slots
        self.voltage: float = 0.0
        self.net_manager = NetworkManager()
        self.indicators: Dict[str, IndicatorWidget] = {}

        ########################################################################
        # Signal / slot setup
        ########################################################################
        self.ui.btn_disable.clicked.connect(self.disable_clicked)
        self.ui.btn_enable.clicked.connect(self.enable_clicked)
        self.ui.btn_settings.clicked.connect(self.open_settings)
        self.ui.act_about.triggered.connect(self.open_about)
        self.ui.act_add_indicator.triggered.connect(self.add_indicator)
        self.ui.act_clear_indicators.triggered.connect(self.clear_indicators)

        self.net_manager.nt_data_changed.connect(self.nt_data_changed)
        self.net_manager.state_changed.connect(self.state_changed)

        ########################################################################
        # Initial State
        ########################################################################
        self.load_indicators()
        self.state_changed(State.NoNetwork)
        self.set_battery_voltage(0.0, settings_manager.vbat_main)

    def closeEvent(self, event: QCloseEvent):
        self.save_indicators()

    def save_indicators(self):
        try:
            data: Dict[str, Dict] = {}
            for key, ind in self.indicators.items():
                data[ind.key] = {
                    "x": ind.geometry().x(),
                    "y": ind.geometry().y(),
                    "width": ind.geometry().width(),
                    "height": ind.geometry().height()
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
                    self.add_indicator_at(key, QRect(x, y, width, height))
        except:
            pass

    ############################################################################
    # Event Handlers (slots)
    ############################################################################

    def add_indicator(self):
        key, ok = QInputDialog.getText(self, self.tr("Add Indicator"), self.tr("Key:"), QLineEdit.Normal)
        if ok and key != "" and not key in self.indicators:
            self.add_indicator_at(key, None)

    def clear_indicators(self):
        for key, ind in self.indicators.items():
            self.indicators[key].hide()
            self.indicators[key].deleteLater()
        self.indicators.clear()

    def add_indicator_at(self, key: str, geometry: QRect):
        ind = IndicatorWidget(self.ui.pnl_net_table)
        ind.deleted.connect(self.indicator_deleted)
        ind.key = key
        # TODO: Get value from NetworkManager

        if geometry is None:
            # Place indicator in center of panel
            panel_geom = self.ui.pnl_net_table.geometry()
            ind_geom = ind.geometry()
            geometry = QRect()
            geometry.setTop(panel_geom.height() / 2.0 - ind_geom.height() / 2.0)
            geometry.setLeft(panel_geom.width() / 2.0 - ind_geom.width() / 2.0)
            geometry.setWidth(ind_geom.width())
            geometry.setHeight(ind_geom.height())
        ind.setGeometry(geometry)
        ind.show()
        self.indicators[key] = ind

    def indicator_deleted(self, key: str):
        if key in self.indicators:
            self.indicators[key].hide()
            self.indicators[key].deleteLater()
            del self.indicators[key]

    def disable_clicked(self):
        # TODO: Use network manager to disable

        # Don't toggle the checked state of these buttons on click.
        # The checked state will be changed when network manager emits signal for state changed
        self.ui.btn_disable.setChecked(not self.ui.btn_disable.isChecked())

    def enable_clicked(self):
        # TODO: Use network manager to enable

        # Don't toggle the checked state of these buttons on click.
        # The checked state will be changed when network manager emits signal for state changed
        self.ui.btn_enable.setChecked(not self.ui.btn_enable.isChecked())

    def open_settings(self):
        dialog = SettingsDialog(self)
        res = dialog.exec()
        if res == QDialog.Accepted:
            old_address = settings_manager.robot_address

            dialog.save_settings()

            # Update robot address if changed
            if settings_manager.robot_address != old_address:
                self.net_manager.robot_address_changed()

            # Update main battery voltage (but don't change current voltage)
            self.set_battery_voltage(self.voltage, settings_manager.vbat_main)

            # Change theme
            theme_manager.apply_theme(settings_manager.theme, settings_manager.larger_fonts)

    def open_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    ############################################################################
    # Connection/Robot States
    ############################################################################

    # Slot for NetworkManager signal
    def state_changed(self, state):
        if state == State.Disabled:
            self.set_state_disabled()
        elif state == State.Enabled:
            self.set_state_enabled()
        elif state == State.NoNetwork:
            self.set_state_no_network()
        elif state == State.NoRobotProgram:
            self.set_state_no_program()

    # Slot for NetworkManager signal
    def nt_data_changed(self, key: str, value: str):
        if key == "vbat0":
            self.set_battery_voltage(float(value), settings_manager.vbat_main)
        else:
            # TODO: Update any indicators
            pass

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

    def set_network_good(self, good: bool):
        if good:
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_green")
        else:
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_red")

    def set_robot_program_good(self, good: bool):
        if good:
            self.ui.pnl_program_bg.setObjectName("pnl_program_bg_green")
        else:
            self.ui.pnl_program_bg.setObjectName("pnl_program_bg_red")
