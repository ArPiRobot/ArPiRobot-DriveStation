
from PySide6.QtWidgets import QDialog
from ui_settings_dialog import Ui_SettingsDialog
from util import settings_manager


class SettingsDialog(QDialog):
    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.ui.txt_robot_address.setText(settings_manager.robot_address)
        self.ui.txt_bat_voltage.setText(str(settings_manager.vbat_main))
        self.ui.txt_robot_address.setFocus()

        self.ui.chbox_larger_font.setChecked(settings_manager.larger_fonts)

    def save_settings(self):
        settings_manager.robot_address = self.ui.txt_robot_address.text()
        settings_manager.vbat_main = float(self.ui.txt_bat_voltage.text())
        settings_manager.larger_fonts = self.ui.chbox_larger_font.isChecked()
