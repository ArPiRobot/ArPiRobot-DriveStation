from PySide6.QtCore import QObject, Signal, QFile, QTemporaryFile, QDir
from threading import Thread
import sdl2
import time


class GamepadManager(QObject):

    connected = Signal(int, str)               # device_id, device_name
    disconnected = Signal(int)                 # device_id
    axis_moved = Signal(int, int, int)         # device_id, axis_num, axis_value
    button_changed = Signal(int, int, bool)    # device_id, button_num, is_pressed

    def __init__(self, event_poll_delay: float = 0.01, mappings_file: str = ""):
        super().__init__()
        self.event_poll_delay = event_poll_delay
        self.mappings_file = mappings_file
        self.running = False
        self.event_thread = None
        self.open_devices = {}

    def __del__(self):
        self.stop()

    def start(self):
        self.running = True
        self.event_thread = Thread(target=self.event_loop)
        self.event_thread.start()

    def stop(self):
        self.running = False
        self.event_thread.join()

    def event_loop(self):
        # Init here b/c on some platforms controller events only work if processed
        # on the same thread that called sdl init

        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_ACCELEROMETER_AS_JOYSTICK, b"0")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_MAC_BACKGROUND_APP, b"1")

        error = sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
        if error != 0:
            print("ERROR")
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

        # TODO: Logging

        while self.running:
            event = sdl2.SDL_Event()
            if sdl2.SDL_PollEvent(event) != 0:
                if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                    # "which" is a joystick index
                    dev = sdl2.SDL_GameControllerOpen(event.cdevice.which)
                    if dev is not None:
                        device_id = sdl2.SDL_JoystickInstanceID(sdl2.SDL_GameControllerGetJoystick(dev))
                        device_name = sdl2.SDL_GameControllerName(dev)
                        self.open_devices[device_id] = dev
                        self.connected.emit(device_id, device_name.decode())
                elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                    # "which" is an instance id
                    if event.cdevice.which in self.open_devices:
                        sdl2.SDL_GameControllerClose(self.open_devices[event.cdevice.which])
                        del self.open_devices[event.cdevice.which]
                    self.disconnected.emit(event.cdevice.which)
                elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                    # "which" is an instance id
                    self.axis_moved.emit(event.caxis.which, event.caxis.axis, event.caxis.value)
                elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                    # "which" is an instance id
                    self.button_changed.emit(event.cbutton.which, event.cbutton.button, True)
                elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                    # "which" is an instance id
                    self.button_changed.emit(event.cbutton.which, event.cbutton.button, False)
            else:
                time.sleep(self.event_poll_delay)
        sdl2.SDL_Quit()
