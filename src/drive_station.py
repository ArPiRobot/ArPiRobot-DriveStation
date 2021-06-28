from typing import Any, Callable


from settings_dialog import SettingsDialog
from PySide6.QtWidgets import QMainWindow, QLabel, QListWidgetItem, QDialog
from PySide6.QtCore import QFile, QIODevice, Qt
from ui_drive_station import Ui_DriveStationWindow
from util import HTMLDelegate, settings_manager, theme_manager
from network import State, NetworkManager
from about_dialog import AboutDialog


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

        # Used to cache battery voltage so main battery nominal
        # voltage can be changed without changing current voltage
        self.voltage: float = 0.0

        self.net_manager = NetworkManager()

        ########################################################################
        # Signal / slot setup
        ########################################################################
        self.ui.btn_disable.clicked.connect(self.disable_clicked)
        self.ui.btn_enable.clicked.connect(self.enable_clicked)
        self.ui.btn_settings.clicked.connect(self.open_settings)
        self.ui.act_about.triggered.connect(self.open_about)

        self.net_manager.nt_data_changed.connect(self.nt_data_changed)
        self.net_manager.state_changed.connect(self.state_changed)

        ########################################################################
        # Initial State
        ########################################################################
        self.state_changed(State.NoNetwork)
        self.set_battery_voltage(0.0, settings_manager.vbat_main)

    ############################################################################
    # Event Handlers (slots)
    ############################################################################

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
            dialog.save_settings()
            # Update robot IP
            # TODO: Go through network manager

            # Update main battery voltage (but don't change current voltage
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
            # TODO: Handle net table update to indicators
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
