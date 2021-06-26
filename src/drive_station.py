from typing import Any, Callable


from settings_dialog import SettingsDialog
from PySide6.QtWidgets import QMainWindow, QLabel, QListWidgetItem
from PySide6.QtCore import QFile, QIODevice, Qt
from ui_drive_station import Ui_DriveStationWindow
from util import HTMLDelegate

from enum import Enum


class State(Enum):
    NoNetwork = 0
    NoRobotProgram = 1
    Disabled = 2
    Enabled = 3


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
            return f"({idx}) <i>{self.name}</i>"
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
    MSG_STATE_NO_NETWORK = "Could not connect to robot at {0}"
    MSG_STATE_NO_PROGRAM = "No program running on robot."
    MSG_STATE_DISABLED = "Robot disabled."
    MSG_STATE_ENABLED = "Robot enabled."

    DEFAULT_ROBOT_ADDRESS = "192.168.10.1"

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

        self.state: State = State.NoNetwork
        self.set_state_no_network()

        # TODO: Load this from some setting, along with robot address
        self.set_battery_voltage(0.0, 7.2)

        self.ui.lst_controllers.setItemDelegate(HTMLDelegate())
        for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
            self.ui.lst_controllers.addItem(ControllerListItem(f"Controller {i}", -1, self.ui.lst_controllers.row))

        ########################################################################
        # Signal / slot setup
        ########################################################################
        self.ui.btn_disable.clicked.connect(self.disable_clicked)
        self.ui.btn_enable.clicked.connect(self.enable_clicked)
        self.ui.btn_settings.clicked.connect(self.open_settings)

    ############################################################################
    # Event Handlers (slots)
    ############################################################################

    def disable_clicked(self):
        # If connected to the robot, send disable command.
        if self.state == State.Enabled or self.state == State.Disabled:
            # TODO: Send disable command to robot
            self.set_state_disabled()
        else:
            # Clicking the button toggles the checked state.
            # Always run the set_state function to ensure the UI is in the correct state
            self.set_current_state()

    def enable_clicked(self):
        # If connected to the robot, send enable command.
        if self.state == State.Enabled or self.state == State.Disabled:
            # TODO: Send enable command to robot
            self.set_state_enabled()
        else:
            # Clicking the button toggles the checked state.
            # Always run the set_state function to ensure the UI is in the correct state
            self.set_current_state()

    ############################################################################
    # Connection/Robot States
    ############################################################################

    def set_current_state(self):
        if self.state == State.Disabled:
            self.set_state_disabled()
        elif self.state == State.Enabled:
            self.set_state_enabled()
        elif self.state == State.NoNetwork:
            self.set_state_no_network()
        elif self.state == State.NoRobotProgram:
            self.set_state_no_program()

    def set_state_no_network(self):
        self.state = State.NoNetwork

        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        # TODO: Don't use default address. Load from settings
        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_NO_NETWORK).format(self.DEFAULT_ROBOT_ADDRESS))
        self.set_network_good(False)
        self.set_robot_program_good(False)

    def set_state_no_program(self):
        self.state = State.NoRobotProgram

        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_NO_PROGRAM))
        self.set_network_good(True)
        self.set_robot_program_good(False)

    def set_state_disabled(self):
        self.state = State.Disabled

        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.lbl_status_msg.setText(self.tr(self.MSG_STATE_DISABLED))
        self.set_network_good(True)
        self.set_robot_program_good(True)

    def set_state_enabled(self):
        self.state = State.Enabled

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

    ############################################################################
    # Settings
    ############################################################################

    # TODO: Load/save from/to a file
    # TODO: Handle changing settings when settings dialog is closed

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
