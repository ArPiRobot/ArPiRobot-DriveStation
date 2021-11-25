
from enum import Enum
from abc import ABC, abstractmethod

from PySide6.QtCore import QObject, QProcess, QTime, QTimer, Signal
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket, QUdpSocket

import platform

# Networking protocol
# The drive station uses four ports to communicate with the robot.
# Controller Port  (UDP 8090):
#     Data is only received from the DS. Data is not sent from the robot to the DS on this port.
#     The controller port is a UDP port on port 8090. It is used to send controller data in the following packet format
#     [controllerNumber,axisCount,buttonCount,dpadCount,axis1_h,axis1_l,...,buttons1,buttons2,...,dpads1,dpads2,...,\n]
    
#     - The controller number and counts are 8 bit integers (unsigned)
#     - axes are sent as signed 16-bit integers (high byte, low byte)
#     - buttons are 1 (pressed) or 0 (not pressed) Each button byte encodes the state of eight buttons.
#           The most significant bit is the smallest numbered button. For example in the first 
#           button byte sent (buttons1) the most significant bit is button #0's state. The MSB of the
#           second byte (buttons2) is the 9th button's state.
#     - the dpad is 0 (no direction) or 1-8 (where 1 is up rotate clockwise)
#                     8  1  2
#                     7  0  3
#                     6  5  4
#           Two dpads are sent per byte. As with the buttons the most significant 4 bits represent 
#           the lowest numbered dpad.
# Command port (TCP 8091):
#     Data is only received from the DS. Data is not sent from the robot to the DS on this port. Commands end with a newline.
#     Commands are sent to the robot on this port as ASCII strings
#     Some commands include:
#     "ENABLE" = Enable the robot
#     "DISABLE" = Disable the robot
#     "NT_SYNC" = Start network table sync (always triggered by drive station)
# Net Table port (TCP 8092):
#     Data is sent and received on the net table port.
#     New keys are sent to the drive station in the format shown below
#     "[KEY]",255,"[VALUE]"
#     Key and value are ASCII text. 255 is an unsigned int (this is used because it is not a valid ASCII character)
#     Data received from the DS is in the same format and will cause the robot's net table to 
#     set the given key to the given value.
#     During a sync (sync must be started from the drive station by sending a command to the robot) 
#     the robot sends the net table sync start sequence then sends all key/value pairs followed by the
#     net table sync stop sequence. The robot then waits for the drive station to send any key/value pairs
#     that the robot is missing. The drive station then sends the net table sync stop sequence and the robot
#     then "ends" the sync.
# Log port  (TCP 8093):
#     Log messages are sent as strings from the robot to the drive station on this port. No data is sent to the robot
#     from the drive station on this port.


class NetworkManager(QObject):

    class State(Enum):
        NoNetwork = 0               # No network communication (ping) with given address
        NoRobotProgram = 1          # Can ping, but not connect to program on given address
        Disabled = 2                # Connected to robot. Robot disabled.
        Enabled = 3                 # Connected to robot. Robot enabled.
        Init = 4                    # Initializing network manager (haven't been given robot address yet)

    # Signals
    state_changed = Signal(State)
    nt_data_changed = Signal(str, str)

    ############################################################################
    # External facing functions
    ############################################################################

    def __init__(self):
        super().__init__()
        self.__state = NetworkManager.State.Init
        self.__robot_address = ""
        self.__net_table = {}
        
        # Socket objects
        self.__cmd_socket = QTcpSocket(self)
        self.__net_table_socket = QTcpSocket(self)
        self.__log_socket = QTcpSocket(self)
        self.__controller_socket = QUdpSocket(self)

        # Timers
        self.__connect_timeout_timer = QTimer(self)
        self.__connect_timeout_timer.setSingleShot(True)

        self.__connect_retry_timer = QTimer(self)
        self.__connect_retry_timer.setSingleShot(True)

        # Used to ping robot to determine if it exists
        self.__ping_process = QProcess(self)

        # Signal / Slot setup
        self.__connect_timeout_timer.timeout.connect(self.__tcp_cancel_connect)
        self.__connect_retry_timer.timeout.connect(self.__attempt_connect)
        self.__ping_process.finished.connect(self.__ping_finished)

        self.__cmd_socket.connected.connect(lambda: self.__tcp_connected(self.__cmd_socket))
        self.__net_table_socket.connected.connect(lambda: self.__tcp_connected(self.__net_table_socket))
        self.__log_socket.connected.connect(lambda: self.__tcp_connected(self.__log_socket))

        self.__cmd_socket.errorOccurred.connect(lambda se: self.__tcp_error_occurred(self.__cmd_socket, se))
        self.__net_table_socket.errorOccurred.connect(lambda se: self.__tcp_error_occurred(self.__net_table_socket, se))
        self.__log_socket.errorOccurred.connect(lambda se: self.__tcp_error_occurred(self.__log_socket, se))

        self.__net_table_socket.readyRead.connect(self.__net_table_ready_read)
        self.__log_socket.readyRead.connect(self.__log_ready_read)

    def stop(self):
        # Intended to be called before closing DS application
        self.__cmd_socket.abort()
        self.__net_table_socket.abort()
        self.__log_socket.abort()

    def set_robot_address(self, robot_address: str):
        # Cancel any pending reconnect attempt
        self.__connect_retry_timer.stop()

        # Cancel any pending ping
        self.__ping_process.kill()

        # Ensure not connected to anything currently. 
        if self.__is_connected():
            # If connected, disconnect each cleanly
            self.__cmd_socket.disconnectFromHost()
            self.__net_table_socket.disconnectFromHost()
            self.__log_socket.disconnectFromHost()
        else:
            # If not connected, abort any pending connection that may be happening
            self.__cmd_socket.abort()
            self.__net_table_socket.abort()
            self.__log_socket.abort()

        # Set state to no network
        self.__change_state(NetworkManager.State.NoNetwork)

        # Change robot address
        self.__robot_address = robot_address

        # Attempt a connect now
        self.__connect_retry_timer.start(0)

    def send_controller_data(self, controller_num: int, some_data):
        pass

    def set_net_table(self, key: str, value: str):
        pass

    ############################################################################
    # Internal connection / state functions
    ############################################################################

    def __change_state(self, state: State):
        did_change = self.__state != state
        self.__state = state
        if did_change:
            self.state_changed.emit(self.__state)

    def __attempt_connect(self):
        # Attempt to ping IP (or resolve DNS name then ping IP) to determine if robot exists
        os_name = platform.system()
        if os_name == 'Windows':
            # Windows ping command uses "-n" not "-c" and timeout with "-w [milliseconds]"
            ping_args = ["-n", "1", "-w", "1000"]
        elif os_name == "Linux":
            # Linux ping command uses "-W [seconds]" for response timeout
            ping_args = ["-c", "1", "-W", "1"]
        else:
            # Unix ping command uses "-W [milliseconds]"" for response timeout
            ping_args = ["-c", "1", "-W", "1000"]
        
        ping_args.append(self.__robot_address)

        # When ping finishes, self.__ping_finished will be called
        self.__ping_process.kill()
        self.__ping_process.start("ping", ping_args)

    def __ping_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        if exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            # Something found at the robot address. Attempt to connect.
            self.__change_state(NetworkManager.State.NoRobotProgram)
            
            # Enforce connection timeout (5 second)
            self.__connect_timeout_timer.start(5000)

            # Attempt connection (see TCP slots below for event handling)
            addr = QHostAddress(self.__robot_address)
            self.__cmd_socket.connectToHost(addr, 8091)
            self.__net_table_socket.connectToHost(addr, 8092)
            self.__log_socket.connectToHost(addr, 8093)
        else:
            # Cannot ping the robot address. No robot found at this address.
            self.__change_state(NetworkManager.State.NoNetwork)

            # Retry connect in 5 seconds
            self.__connect_retry_timer.start(5000)
    
    def __tcp_cancel_connect(self):
        # Connect failed due to timeout (or rejection).
        # Unable to connect to robot program.

        # Close all connections (and connection attempts)
        self.__cmd_socket.abort()
        self.__net_table_socket.abort()
        self.__log_socket.abort()

        # Assume the robot can still be pinged.
        self.__change_state(NetworkManager.State.NoRobotProgram)

        # Try connect again later
        self.__retry_connect_long()
    
    def __retry_connect_short(self):
        # Retry the connection after a "short" duration
        self.__connect_retry_timer.start(1500)
    
    def __retry_connect_long(self):
        # Retry the connection after a "longer" duration
        self.__connect_retry_timer.start(5000)

    def __is_connected(self) -> bool:
        # Helper to make next if statement more readable
        def is_connected(sock: QAbstractSocket):
            return sock.state() == QAbstractSocket.SocketState.ConnectedState 

        # Considered connected only if all three TCP sockets are connected
        return is_connected(self.__cmd_socket) and \
                is_connected(self.__net_table_socket) and \
                is_connected(self.__log_socket)

    ############################################################################
    # TCP slots
    ############################################################################

    def __tcp_connected(self, socket: QTcpSocket):
        if self.__is_connected():
            # Cancel the connect timeout timer
            self.__connect_timeout_timer.stop()

            # Connected to the robot. The robot is disabled until an enable command is sent.
            self.__change_state(NetworkManager.State.Disabled)

    def __tcp_error_occurred(self, socket: QTcpSocket, sock_error: QAbstractSocket.SocketError):
        if sock_error == QAbstractSocket.SocketError.ConnectionRefusedError:
            # Robot refused connection. Program not running (or more likely this address is not the robot)
            self.__tcp_cancel_connect()
        elif sock_error == QAbstractSocket.SocketError.RemoteHostClosedError:
            # This will likely occur at the same time for all TCP sockets. Only handle for the first one
            if self.__is_connected():
                # If any socket is disconnected disconnect all sockets
                self.__cmd_socket.disconnectFromHost()
                self.__net_table_socket.disconnectFromHost()
                self.__log_socket.disconnectFromHost()

                # For now, assume the robot can still be pingged
                # All that is known is the connection to running program was lost
                self.__change_state(NetworkManager.State.NoRobotProgram)

                # Was connected to robot. Try to connect again in near future in case the robot is still there.
                self.__retry_connect_short()

        elif sock_error == QAbstractSocket.SocketError.HostNotFoundError:
            # DNS lookup of robot address failed. 
            # If ping succeeded this should never happen here, but revert to NoNetwork anyways.
            self.__change_state(NetworkManager.State.NoNetwork)

            # Try connect again later
            self.__retry_connect_long()

    def __net_table_ready_read(self):
        pass

    def __log_ready_read(self):
        pass
