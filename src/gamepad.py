from PySide6.QtCore import QObject, Signal, QFile, QTemporaryFile, QDir
from threading import Thread
import sdl2
import time


class GamepadManager(QObject):

    connected = Signal(int, str)               # device_id, device_name
    disconnected = Signal(int)                 # device_id
    axis_moved = Signal(int, int, int)         # device_id, axis_num, axis_value
    button_changed = Signal(int, int, bool)    # device_id, button_num, is_pressed

    def __init__(self, event_poll_delay: float = 0.01):
        super().__init__()
        self.event_poll_delay = event_poll_delay
        self.running = True
        self.event_thread = Thread(target=self.event_loop)
        self.event_thread.start()

    def __del__(self):
        self.running = False
        self.event_thread.join()

    def event_loop(self):
        # Init here b/c on some platforms controller events only work if processed
        # on the same thread that called sdl init
        error = sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
        if error != 0:
            return

        while self.running:
            event = sdl2.SDL_Event()
            if sdl2.SDL_PollEvent(event) != 0:
                if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                    pass
                elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                    pass
                elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                    pass
                elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                    pass
                elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                    pass
            else:
                time.sleep(self.event_poll_delay)
            sdl2.SDL_Quit()

    def add_mappings_from_file(self, file_path: str) -> int:
        if file_path.startswith(":"):
            # This is a Qt resource, make a temp copy on filesystem
            temp_path = QDir.tempPath() + "/gamecontrollerdb.txt"
            if QFile.exists(temp_path):
                QFile.remove(temp_path)
            QFile.copy(file_path, temp_path)
            time.sleep(0.1)  # Not ideal, but waiting for copy to finish
            res = sdl2.SDL_GameControllerAddMappingsFromFile(temp_path.encode())
            QFile.remove(temp_path)
            return res
        else:
            return sdl2.SDL_GameControllerAddMappingsFromFile(file_path.encode())

