
import typing
from PySide2.QtWidgets import QApplication, QMainWindow
import PySide2
from PySide2.QtGui import QColor, QIcon, QPalette
from PySide2.QtCore import QFile, QIODevice
from ui_drive_station import Ui_DriveStation

class DriveStation(QMainWindow):
    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)
        
        ########################################################################
        # Constants
        ########################################################################

        # Status messages to be displayed above connect button
        self.STATUS_NOT_CONNECTED = self.tr("Not Connected")
        self.STATUS_CONNECTED = self.tr("Connected")
        self.STATUS_ENABLED = self.tr("Enabled")
        self.STATUS_DISABLED = self.tr("Disabled")

        # Battery level colors
        self.COLOR_BAT_HIGH = QColor(0, 200, 0)
        self.COLOR_BAT_MED_HIGH = QColor(230, 230, 0)
        self.COLOR_BAT_MED_LOW = QColor(255, 153, 0)
        self.COLOR_BAT_LOW = QColor(200, 0, 0)


        ########################################################################
        # UI Setup
        ########################################################################

        self.ui = Ui_DriveStation()
        self.ui.setupUi(self)

        # White text in progress bars on Windows does not work well...
        if(QApplication.style().metaObject().className().startswith("QWindows")):
            allBars = [
                self.ui.pbarLX, self.ui.pbarLY, self.ui.pbarRX, self.ui.pbarRY, self.ui.pbarL2, self.ui.pbarR2,
                self.ui.pbarA, self.ui.pbarB, self.ui.pbarX, self.ui.pbarY, self.ui.pbarBack, self.ui.pbarGuide, 
                    self.ui.pbarStart, self.ui.pbarL3, self.ui.pbarR3, self.ui.pbarL1, self.ui.pbarL2,
                self.ui.pbarDpadUp, self.ui.pbarDpadDown, self.ui.pbarDpadLeft, self.ui.pbarDpadRight
            ]
            for bar in allBars:
                palette = bar.palette()
                palette.setColor(QPalette.HighlightedText, palette.color(QPalette.Text))
                bar.setPalette(palette)
        
        # Append version to window title
        version_file = QFile(":/version.txt")
        if(version_file.open(QIODevice.ReadOnly)):
            ver = bytes(version_file.readLine()).decode().replace("\n", "").replace("\r", "")
            self.setWindowTitle(self.windowTitle() + " v" + ver)

        # Set initial status message
        self.ui.lblStatus.setText(self.STATUS_NOT_CONNECTED)

        # Set initial battery color
        palette = self.ui.pnlVbatBackground.palette()
        palette.setColor(QPalette.Background, self.COLOR_BAT_LOW)
        self.ui.pnlVbatBackground.setPalette(palette)

        # Set icon from resources
        self.setWindowIcon(QIcon(':/icon.png'))