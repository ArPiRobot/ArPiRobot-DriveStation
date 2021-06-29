
from enum import Enum
from abc import ABC, abstractmethod

from PySide6.QtCore import QObject, Signal


class State(Enum):
    NoNetwork = 0
    NoRobotProgram = 1
    Disabled = 2
    Enabled = 3
    Connecting = 4


class NetworkManager(QObject):

    # Signals
    state_changed = Signal(State)
    nt_data_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.__state = State.NoNetwork
        self.__listeners = []

    def connect_to_robot(self) -> bool:
        return False

    def disconnect_from_robot(self):
        # TODO: Disconnect from robot
        self.__state = State.NoNetwork

    def robot_address_changed(self):
        self.disconnect_from_robot()
        self.state_changed.emit(self.__state)
