
from PySide6.QtWidgets import QApplication, QListWidgetItem, QMainWindow
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtCore import QFile, QIODevice, QStringListModel, Qt
from .ui_drive_station import Ui_DriveStationWindow

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
    MSG_STATE_NO_NETWORK = "Could not connect to given address."
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
        
        # Append version to window title
        version_file = QFile(":/version.txt")
        if(version_file.open(QIODevice.ReadOnly)):
            ver = bytes(version_file.readLine()).decode().replace("\n", "").replace("\r", "")
            self.setWindowTitle(self.windowTitle() + " v" + ver)
    
        # TODO: Load this from preferences file
        self.ui.txtRobotIp.setText(self.DEFAULT_ROBOT_ADDRESS)

        for i in range(10):
            item = QListWidgetItem("Controller {0}".format(i))
            item.setCheckState(Qt.CheckState.Unchecked)
            self.ui.lstControllers.addItem(item)

        self.state: State = None
        self.set_state_no_network()
        self.set_battery_voltage(7.0, 7.2)
    

    # TODO: General custom stylesheet...

    ############################################################################
    # Connection/Robot States
    ############################################################################   

    def set_state_no_network(self):
        self.state = State.NoNetwork

        self.ui.btnDisable.setChecked(True)
        self.ui.btnEnable.setChecked(False)

        self.ui.statusbar.showMessage(self.MSG_STATE_NO_NETWORK)
        self.set_network_good(False)
        self.set_robot_program_good(False)
        
    
    def set_state_no_program(self):
        self.state = State.NoRobotProgram

        self.ui.btnDisable.setChecked(True)
        self.ui.btnEnable.setChecked(False)

        self.ui.statusbar.showMessage(self.MSG_STATE_NO_PROGRAM)
        self.set_network_good(True)
        self.set_robot_program_good(False)
        
    
    def set_state_disabled(self):
        self.state = State.Disabled

        self.ui.btnDisable.setChecked(True)
        self.ui.btnEnable.setChecked(False)

        self.ui.statusbar.showMessage(self.MSG_STATE_DISABLED)
        self.set_network_good(True)
        self.set_robot_program_good(True)
        

    def set_state_enabled(self):
        self.state = State.Enabled

        self.ui.btnDisable.setChecked(False)
        self.ui.btnEnable.setChecked(True)

        self.ui.statusbar.showMessage(self.MSG_STATE_ENABLED)
        self.set_network_good(True)
        self.set_robot_program_good(True)
    

    def set_battery_voltage(self, voltage: float, nominal_bat_voltage: float):
        if(voltage >= nominal_bat_voltage):
            self.ui.pnlBatBg.setObjectName("pnlBatBgGreen")
        elif (voltage >= nominal_bat_voltage * 0.85):
            self.ui.pnlBatBg.setObjectName("pnlBatBgYellow")
        elif(voltage >= nominal_bat_voltage * 0.7):
            self.ui.pnlBatBg.setObjectName("pnlBatBgOrange")
        else:
            self.ui.pnlBatBg.setObjectName("pnlBatBgRed")
        self.ui.lblBatteryVoltage.setText("{:.2f} V".format(voltage))
    

    def set_network_good(self, good: bool):
        if(good):
            self.ui.pnlNetBg.setObjectName("pnlNetBgGreen")
        else:
            self.ui.pnlNetBg.setObjectName("pnlNetBgRed")


    def set_robot_program_good(self, good: bool):
        if(good):
            self.ui.pnlRobotProgramBg.setObjectName("pnlRobotProgramBgGreen")
        else:
            self.ui.pnlRobotProgramBg.setObjectName("pnlRobotProgramBgRed")