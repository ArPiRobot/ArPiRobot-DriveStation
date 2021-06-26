
from model import Controller, ControllerListModel
from settings_dialog import SettingsDialog
from PySide6.QtWidgets import QAbstractItemView, QMainWindow
from PySide6.QtGui import QColor
from PySide6.QtCore import QFile, QIODevice
from ui_drive_station import Ui_DriveStationWindow

from enum import Enum


class State(Enum):
    NoNetwork = 0
    NoRobotProgram = 1
    Disabled = 2
    Enabled = 3


class DriveStationWindow(QMainWindow):

    # Battery level colors
    COLOR_BAT_HIGH = QColor(0, 200, 0)
    COLOR_BAT_MED_HIGH = QColor(230, 230, 0)
    COLOR_BAT_MED_LOW = QColor(255, 153, 0)

    # Network and robot program indicator colors
    COLOR_STATUS_BAD = QColor(255, 0, 0)
    COLOR_STATUS_GOOD = QColor(0, 255, 0)

    # State messages
    MSG_STATE_NO_NETWORK = "Could not connect to robot at {0}."
    MSG_STATE_NO_PROGRAM = "No program running on robot."
    MSG_STATE_DISABLED = "Robot disabled."
    MSG_STATE_ENABLED = "Robot enabled."

    DEFAULT_ROBOT_ADDRESS = "192.168.10.1"


    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)
        ########################################################################
        # UI Setup
        ########################################################################

        self.ui = Ui_DriveStationWindow()
        self.ui.setupUi(self)
        
        # Append version to about label
        version_file = QFile(":/version.txt")
        if(version_file.open(QIODevice.ReadOnly)):
            ver = bytes(version_file.readLine()).decode().replace("\n", "").replace("\r", "")
            self.setWindowTitle(self.windowTitle() + " v" + ver)
    
        self.state: State = None
        self.set_state_no_network()

        # TODO: Load this from some setting, along with robot address
        self.set_battery_voltage(0.0, 7.2)  

        self.controller_model = ControllerListModel(self.ui.lst_controllers)
        self.ui.lst_controllers.setModel(self.controller_model)

        self.ui.lst_controllers.setDragEnabled(True)
        self.ui.lst_controllers.viewport().setAcceptDrops(True)
        self.ui.lst_controllers.setAcceptDrops(True)
        self.ui.lst_controllers.setDropIndicatorShown(True)
        self.ui.lst_controllers.setDragDropMode(QAbstractItemView.InternalMove)

        for i in range(5):
            c = Controller("Controller", i)
            self.controller_model.add_controller(c)

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
        if(self.state == State.Enabled or self.state == State.Disabled):
            # TODO: Send disable command to robot
            self.set_state_disabled()
        else:
            # Clicking the button toggles the checked state.
            # Always run the set_state function to ensure the UI is in the correct state
            self.set_current_state()

    def enable_clicked(self):
        # If connected to the robot, send enable command.
        if(self.state == State.Enabled or self.state == State.Disabled):
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
        self.ui.statusbar.showMessage(self.tr(self.MSG_STATE_NO_NETWORK).format(self.DEFAULT_ROBOT_ADDRESS))
        self.set_network_good(False)
        self.set_robot_program_good(False)
        
    
    def set_state_no_program(self):
        self.state = State.NoRobotProgram

        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.ui.statusbar.showMessage(self.tr(self.MSG_STATE_NO_PROGRAM))
        self.set_network_good(True)
        self.set_robot_program_good(False)
        
    
    def set_state_disabled(self):
        self.state = State.Disabled

        self.ui.btn_disable.setChecked(True)
        self.ui.btn_enable.setChecked(False)

        self.ui.statusbar.showMessage(self.tr(self.MSG_STATE_DISABLED))
        self.set_network_good(True)
        self.set_robot_program_good(True)
        

    def set_state_enabled(self):
        self.state = State.Enabled

        self.ui.btn_disable.setChecked(False)
        self.ui.btn_enable.setChecked(True)

        self.ui.statusbar.showMessage(self.tr(self.MSG_STATE_ENABLED))
        self.set_network_good(True)
        self.set_robot_program_good(True)
    

    def set_battery_voltage(self, voltage: float, nominal_bat_voltage: float):
        if(voltage >= nominal_bat_voltage):
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_green")
        elif (voltage >= nominal_bat_voltage * 0.85):
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_yellow")
        elif(voltage >= nominal_bat_voltage * 0.7):
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_orange")
        else:
            self.ui.pnl_bat_bg.setObjectName("pnl_bat_bg_red")
        self.ui.lbl_bat_voltage.setText("{:.2f} V".format(voltage))
    

    def set_network_good(self, good: bool):
        if(good):
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_green")
        else:
            self.ui.pnl_net_bg.setObjectName("pnl_net_bg_red")


    def set_robot_program_good(self, good: bool):
        if(good):
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
        res = dialog.exec_()