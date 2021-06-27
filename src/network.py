
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
    def __init__(self):
        super().__init__()
        self.__state = State.NoNetwork
        self.__listeners = []

    state_changed = Signal(State)
    nt_data_changed = Signal(str, str)
