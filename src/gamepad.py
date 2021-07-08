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

    def __del__(self):
        self.stop()
        sdl2.SDL_Quit()

    def start(self):
        self.running = True
        self.event_thread = Thread(target=self.event_loop)
        self.event_thread.start()

    def stop(self):
        self.running = False
        if self.event_thread is not None:
            self.event_thread.join()

    def event_loop(self):
        
        # Intitialize SDL
        # The thread handling events should be the thread that inited the video subsystem
        # On some systems, the events do not work properly without video subsytem initialized
        error = sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_VIDEO)
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

        
        while self.running:
            event = sdl2.SDL_Event()
            if sdl2.SDL_PollEvent(event) == 1:
                if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                    dev = sdl2.SDL_GameControllerOpen(event.cdevice.which)
                    if dev is not None:
                        instance_id = sdl2.SDL_JoystickInstanceID(sdl2.SDL_GameControllerGetJoystick(dev))
                        name = sdl2.SDL_GameControllerName(dev)
                        print(f"Added {name} with id {instance_id}")
                elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                    sdl2.SDL_GameControllerClose(sdl2.SDL_GameControllerFromInstanceID(event.cdevice.which))
                    print(f"Removed {event.cdevice.which}")
            else:
                time.sleep(self.event_poll_delay)
