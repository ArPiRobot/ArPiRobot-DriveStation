import ctypes
from PySide6.QtCore import QObject, QTimer, Signal, QFile, QTemporaryFile, QDir
from threading import Thread
import sdl2
import time


class GamepadManager(QObject):

    connected = Signal(int, str)               # device_id, device_name
    disconnected = Signal(int)                 # device_id

    def __init__(self, mappings_file: str = ""):
        super().__init__()
        self.mappings_file = mappings_file
        self.running = False
        self.event_thread = None

        self.event_poll_timer = QTimer(self)
        self.event_poll_timer.timeout.connect(self.handle_events)

        # Events are only used to detect connect / disconnect
        # Axis / button state is polled
        # @sdl2.SDL_EventFilter
        # def event_filter(user_data, event):
        #     if event.contents.type == sdl2.SDL_CONTROLLERDEVICEADDED or \
        #             event.contents.type == sdl2.SDL_CONTROLLERDEVICEREMOVED or \
        #             event.contents.type == sdl2.SDL_JOYDEVICEADDED or \
        #             event.contents.type == sdl2.SDL_JOYDEVICEREMOVED:
        #         return 1
        #     return 0
        # self.event_filter = event_filter
        # sdl2.SDL_SetEventFilter(self.event_filter, None)

        # Initialize SDL (on main thread for best cross platform compatibility)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_ACCELEROMETER_AS_JOYSTICK, b"0")
        error = sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
        if error != 0:
            return

        # Load mappings from file after sdl init
        if self.mappings_file.startswith(":"):
            # This is a Qt resource, make a temp copy on filesystem
            temp_path = QDir.tempPath() + "/gamecontrollerdb.txt"
            if QFile.exists(temp_path):
                QFile.remove(temp_path)
            QFile.copy(self.mappings_file, temp_path)
            time.sleep(0.1)  # Not ideal, but waiting for copy to finish
            sdl2.SDL_GameControllerAddMappingsFromFile(temp_path.encode())
            QFile.remove(temp_path)
        elif self.mappings_file != "" and self.mappings_file is not None:
            sdl2.SDL_GameControllerAddMappingsFromFile(self.mappings_file.encode())

    def __del__(self):
        sdl2.SDL_Quit()

    def start(self):
        # Poll every 250ms. These are only connect / disconnect events
        self.event_poll_timer.start(250)

    def stop(self):
        self.event_poll_timer.stop()
    
    def update(self):
        sdl2.SDL_GameControllerUpdate()

    def get_axis(self, device_id: int, axis: int) -> int:
        dev = sdl2.SDL_GameControllerFromInstanceID(device_id)
        return sdl2.SDL_GameControllerGetAxis(dev, axis)
        
    def get_button(self, device_id: int, button: int) -> bool:
        dev = sdl2.SDL_GameControllerFromInstanceID(device_id)
        value = sdl2.SDL_GameControllerGetButton(dev, button)
        return value == 1

    def handle_events(self):
        # Poll events calls pump events, which must be called from thread that ran SDL_Init
        # On some systems, it is necessary to init video if SDL is started on bg thread
        # But on other systems, it is not possible to init video from non main thread
        # Easiest and best supported method is to poll for events on main thread
        event = sdl2.SDL_Event()
        if sdl2.SDL_PollEvent(event) == 1:
            if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                dev = sdl2.SDL_GameControllerOpen(event.cdevice.which)
                if dev is not None:
                    instance_id = sdl2.SDL_JoystickInstanceID(sdl2.SDL_GameControllerGetJoystick(dev))
                    name = sdl2.SDL_GameControllerName(dev)
                    self.connected.emit(instance_id, name.decode())
            elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                sdl2.SDL_GameControllerClose(sdl2.SDL_GameControllerFromInstanceID(event.cdevice.which))
                self.disconnected.emit(event.cdevice.which)