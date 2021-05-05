
from PySide2.QtWidgets import QApplication, QListWidgetItem, QMainWindow
from PySide2.QtGui import QColor, QIcon, QPalette
from PySide2.QtCore import QFile, QIODevice, QStringListModel, Qt
from .ui_drive_station import Ui_DriveStationWindow

class DriveStationWindow(QMainWindow):

    # Battery level colors
    COLOR_BAT_HIGH = QColor(0, 200, 0)
    COLOR_BAT_MED_HIGH = QColor(230, 230, 0)
    COLOR_BAT_MED_LOW = QColor(255, 153, 0)
    COLOR_BAT_LOW = QColor(200, 0, 0)

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

        # Set icon from resources
        self.setWindowIcon(QIcon(':/icon.png'))
    
        # TODO: Load this from preferences file
        self.ui.txtRobotIp.setText(self.DEFAULT_ROBOT_ADDRESS)

        self.set_state_no_network()
        self.set_battery_voltage(5.0, 7.2)
    

    # TODO: General custom stylesheet...

    ############################################################################
    # Connection/Robot States
    ############################################################################

    # TODO: Better way to do this color change...
    def set_network_label_color(self, color: QColor):
        self.ui.lblNetworkStatus.setStyleSheet("padding: 2px; background-color: {0}".format(color.name()))
    
    def set_robot_program_label_color(self, color: QColor):
        self.ui.lblRobotProgram.setStyleSheet("padding: 2px; background-color: {0}".format(color.name()))
    

    def set_state_no_network(self):
        self.ui.statusbar.showMessage(self.MSG_STATE_NO_NETWORK)
        self.ui.btnDisable.setEnabled(False)
        self.ui.btnEnable.setEnabled(False)
        self.set_network_label_color(self.COLOR_STATUS_BAD)
        self.set_robot_program_label_color(self.COLOR_STATUS_BAD)
    
    def set_state_no_program(self):
        self.ui.statusbar.showMessage(self.MSG_STATE_NO_NETWORK)
        self.ui.btnDisable.setEnabled(False)
        self.ui.btnEnable.setEnabled(False)
        self.set_network_label_color(self.COLOR_STATUS_GOOD)
        self.set_robot_program_label_color(self.COLOR_STATUS_BAD)
    
    def set_state_disabled(self):
        self.ui.statusbar.showMessage(self.MSG_STATE_NO_NETWORK)
        self.ui.btnDisable.setEnabled(False)
        self.ui.btnEnable.setEnabled(True)
        self.set_network_label_color(self.COLOR_STATUS_GOOD)
        self.set_robot_program_label_color(self.COLOR_STATUS_GOOD)

    def set_state_enabled(self):
        self.ui.statusbar.showMessage(self.MSG_STATE_NO_NETWORK)
        self.ui.btnDisable.setEnabled(True)
        self.ui.btnEnable.setEnabled(False)
        self.set_network_label_color(self.COLOR_STATUS_GOOD)
        self.set_robot_program_label_color(self.COLOR_STATUS_GOOD)
    
    def set_battery_voltage(self, voltage: float, nominal_bat_voltage: float):
        if(voltage >= nominal_bat_voltage):
            color = self.COLOR_BAT_HIGH
        elif (voltage >= nominal_bat_voltage * 0.85):
            color = self.COLOR_BAT_MED_HIGH
        elif(voltage >= nominal_bat_voltage * 0.7):
            color = self.COLOR_BAT_MED_LOW
        else:
            color = self.COLOR_BAT_LOW

        # TODO: Do this in a better way...
        self.ui.pnlBatBg.setStyleSheet("background-color: {0}".format(color.name()))
        self.ui.lblBatteryVoltage.setText("{:.2f} V".format(voltage))