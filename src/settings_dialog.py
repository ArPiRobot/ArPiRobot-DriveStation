
from PySide6.QtWidgets import QDialog
from ui_settings_dialog import Ui_SettingsDialog

class SettingsDialog(QDialog):
    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)