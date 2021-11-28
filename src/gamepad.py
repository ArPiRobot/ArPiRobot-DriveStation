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
        self.dev_map = {}

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
        # Poll every 16ms (allows updates in UI of approx 60FPS)
        self.event_poll_timer.start(16)

    def stop(self):
        self.event_poll_timer.stop()
    
    def update(self):
        # sdl2.SDL_GameControllerUpdate()
        pass

    def get_axis(self, device_id: int, axis: int) -> int:
        if device_id in self.dev_map:
            return sdl2.SDL_GameControllerGetAxis(self.dev_map[device_id], axis)
        return 0
        
    def get_button(self, device_id: int, button: int) -> bool:
        if device_id in self.dev_map:
            value = sdl2.SDL_GameControllerGetButton(self.dev_map[device_id], button)
            return value == 1
        return False
    
    def get_dpad_pos_num(self, device_id: int) -> int:
        up = self.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP)
        down = self.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN)
        left = self.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT)
        right = self.get_button(device_id, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT)

        if up:
            if right:
                return 2
            if left:
                return 8
            return 1
        elif down:
            if left:
                return 6
            if right:
                return 4
            return 5
        if left:
            return 7
        if right:
            return 3
        return 0

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
                    self.dev_map[instance_id] = dev
                    name = sdl2.SDL_GameControllerName(dev)
                    self.connected.emit(instance_id, name.decode())
            elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                sdl2.SDL_GameControllerClose(self.dev_map[event.cdevice.which])
                del self.dev_map[event.cdevice.which]
                self.disconnected.emit(event.cdevice.which)
            else:
                pass