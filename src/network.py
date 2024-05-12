
from enum import Enum
from typing import Dict, List

from util import logger

from PySide6.QtCore import QObject, QProcess, QTimer, Signal
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
#     "TEST" = Sent from DS to robot to check if TCP still alive (on some OSes this requires an attempted write)
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
    nt_sync_started = Signal()          # Used by UI to disable indicator panel
    nt_sync_finished = Signal()         # Used by UI to enable indicator panel (could be finish or abort)

    has_log_data = Signal(str)


    # Constants
    CONTROLLER_PORT = 8090
    COMMAND_PORT = 8091
    NET_TABLE_PORT = 8092
    LOG_PORT = 8093

    SHORT_RECONNECT = 1500
    LONG_RECONNECT = 5000

    CMD_ENABLE = b'ENABLE\n'
    CMD_DISABLE = b'DISABLE\n'
    CMD_NT_SYNC = b'NT_SYNC\n'
    CMD_TEST = b'TEST\n'

    NT_SYNC_START_DATA = b'\xff\xff\n'
    NT_SYNC_STOP_DATA = b'\xff\xff\xff\n'

    ############################################################################
    # External facing functions
    ############################################################################

    def __init__(self):
        super().__init__()
        self.__state = NetworkManager.State.Init
        self.__robot_address = ""
        self.__net_table: Dict[str, str] = {}
        self.__nt_modifiable = True
        self.__sync_keys: List[str] = []
        self.__sync_values: List[str] = []
        self.__net_table_read_buf = bytearray()
        self.__log_read_buf = bytearray()
        
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

    @property
    def current_state(self) -> State:
        return self.__state

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

        # Could have been mid sync. Make sure it is aborted before connecting next time.
        self.__nt_abort_sync()

        # Set state to no network
        self.__change_state(NetworkManager.State.NoNetwork)

        # Change robot address
        self.__robot_address = robot_address

        logger.log_info(f"Looking for robot at '{self.__robot_address}'")

        # Attempt a connect now
        self.__connect_retry_timer.start(0)

    def send_enable_command(self):
        if self.__is_connected():
            self.__cmd_socket.write(self.CMD_ENABLE)

    def send_disable_command(self):
        if self.__is_connected():
            self.__cmd_socket.write(self.CMD_DISABLE)

    def send_test_command(self):
        if self.__is_connected():
            self.__cmd_socket.write(self.CMD_TEST)

    def send_controller_data(self, controller_data: bytes):
        if self.__is_connected():
            self.__controller_socket.writeDatagram(controller_data, QHostAddress(self.__robot_address), 8090)

    def set_net_table(self, key: str, value: str) -> bool:
        # THIS IS A SET FROM THE UI IN THE DRIVE STATION
        # DO NOT CALL THIS FUNCTION FOR THINGS WHERE THE ROBOT CHANGED NET TABLE DATA
        # THIS WILL NOT EMIT A DATA CHANGED EVENT

        # robotstate and vbat0 are special values. Do not allow direct set from ui.
        if key == "robotstate" or key == "vbat0":
            return False

        if self.__nt_modifiable:
            self.__net_table[key] = value
            self.__send_nt_key(key)
            return True
        return False
    
    def __nt_set_from_robot(self, key: str, value: str):
        # robotstate is special key used to tell the DS what state the robot is in
        if key == "robotstate":
            if value == "DISABLED":
                self.__change_state(NetworkManager.State.Disabled)
            elif value == "ENABLED":
                self.__change_state(NetworkManager.State.Enabled)
            return

        self.__net_table[key] = value
        self.nt_data_changed.emit(key, value)
    
    def get_net_table(self, key: str) -> str:
        if key not in self.__net_table:
            return ""
        return self.__net_table[key]
    
    def has_net_table(self, key: str) -> bool:
        return key in self.__net_table

    ############################################################################
    # Network Table
    ############################################################################

    def __nt_start_sync(self):
        if not self.__nt_modifiable:
            return # Already syncing
        self.nt_sync_started.emit()
        logger.log_info("Starting network table sync.")
        self.__nt_modifiable = False
    
    def __nt_finish_sync(self, keys: List[str], values: List[str]):
        
        # First, set or add the values from the robot.
        # The list of keys is everything the robot has in its network table
        for i in range(len(keys)):
            key = keys[i]
            value = values[i]
            self.__nt_set_from_robot(key, value)

        logger.log_debug(f"Got {len(keys)} entries from robot.")
        logger.log_debug("Done syncing keys from robot to DS. Syncing from DS to robot.")

        # Next, send anything the robot was missing (that the DS has) to the robot.
        # Only send the robot keys it did not have
        for key in self.__net_table.keys():
            if key not in keys:
                self.__send_nt_key(key)
        
        logger.log_debug("Done syncing data from DS to robot.")

        # Send sync stop data to finish sync
        self.__send_nt_raw(self.NT_SYNC_STOP_DATA)

        # Make sure network table is modifiable again
        self.__nt_modifiable = True

        self.nt_sync_finished.emit()

        # Emit signal after everything complete
        logger.log_info("Network table sync complete.")

    def __nt_abort_sync(self):
        if self.__nt_modifiable:
            return # Not syncing
        
        if self.__is_connected():
            # If sync failed for any reason other than a disconnect send the 
            # sync end data to unlock the robot's net table
            self.__send_nt_raw(self.NT_SYNC_STOP_DATA)
        
        self.nt_sync_finished.emit()

        # Inform DS (so it can log and unlock indicator panel)
        logger.log_warning("Network table sync aborted.")

        # Allow modifications again
        self.__nt_modifiable = True


    def __send_nt_key(self, key: str):
        if self.__is_connected():
            data = bytearray()
            data.extend(key.encode())
            data.extend(b'\xff')
            data.extend(self.__net_table[key].encode())
            data.extend(b'\n')
            self.__net_table_socket.write(bytes(data))

    def __send_nt_raw(self, data: bytes):
        if self.__is_connected():
            self.__net_table_socket.write(data)

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

            # If the state was previously NoNetwork this is the first time ping succeeded. Log.
            if self.__state == NetworkManager.State.NoNetwork:
                logger.log_info(f"Found robot at '{self.__robot_address}'")
                logger.log_info("Attempting to connect to robot program.")

            # Something found at the robot address. Attempt to connect.
            self.__change_state(NetworkManager.State.NoRobotProgram)
            
            # Enforce connection timeout (5 second)
            self.__connect_timeout_timer.start(5000)

            # Attempt connection (see TCP slots below for event handling)
            addr = QHostAddress(self.__robot_address)
            self.__cmd_socket.connectToHost(addr, self.COMMAND_PORT)
            self.__net_table_socket.connectToHost(addr, self.NET_TABLE_PORT)
            self.__log_socket.connectToHost(addr, self.LOG_PORT)
        else:

            # If the state was previously NoRobotProgram, this indicates that a 
            # network error has occurred and caused communication between PC and robot to fail.
            # Log
            if self.__state == NetworkManager.State.NoRobotProgram:
                logger.log_error(f"No longer able to find robot at '{self.__robot_address}'")

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
        self.__connect_retry_timer.start(self.SHORT_RECONNECT)
    
    def __retry_connect_long(self):
        # Retry the connection after a "longer" duration
        self.__connect_retry_timer.start(self.LONG_RECONNECT)

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

            logger.log_info("Connected to robot.")

            # Request the robot begin a net table sync
            self.__cmd_socket.write(self.CMD_NT_SYNC)

            # Connected to the robot. The robot is disabled until an enable command is sent.
            self.__change_state(NetworkManager.State.Disabled)

    def __tcp_error_occurred(self, socket: QTcpSocket, sock_error: QAbstractSocket.SocketError):
        if sock_error == QAbstractSocket.SocketError.ConnectionRefusedError:
            # Robot refused connection. Program not running (or more likely this address is not the robot)
            self.__tcp_cancel_connect()
        elif sock_error == QAbstractSocket.SocketError.RemoteHostClosedError:
            # This will likely occur at the same time for all TCP sockets. Only handle for the first one
            if self.__is_connected():

                logger.log_warning("Lost connection to robot")

                # If any socket is disconnected disconnect all sockets
                self.__cmd_socket.disconnectFromHost()
                self.__net_table_socket.disconnectFromHost()
                self.__log_socket.disconnectFromHost()

                # Connection could have been lost during sync
                self.__nt_abort_sync()

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

    ############################################################################
    # Incoming data handlers
    ############################################################################

    def __net_table_ready_read(self):
        new_data = bytes(self.__net_table_socket.readAll().data())
        self.__net_table_read_buf.extend(new_data)

        # Data is encoded as
        # key_utf8,255,value_utf8,\n
        # This could be repeated multiple times in the buffer

        end_pos = -1

        # There could be multiple key / value pairs in this array. Handle all of them
        while True:
            end_pos = self.__net_table_read_buf.find(b'\n')
            if end_pos == -1:
                break

            # Subset is one message
            subset = self.__net_table_read_buf[0 : end_pos + 1]

            # Handle the single message
            if subset == self.NT_SYNC_START_DATA:
                self.__sync_keys = []
                self.__sync_values = []
                self.__nt_start_sync()
            elif subset == self.NT_SYNC_STOP_DATA:
                self.__nt_finish_sync(self.__sync_keys, self.__sync_values)
            else:
                # Make sure the message has a key/value delimiter
                delim_pos = subset.find(b'\xff')
                if delim_pos > -1:
                    # Data is valid. Get key and value
                    key = subset[0:delim_pos].decode()
                    value = subset[delim_pos + 1 : len(subset) - 1].decode()

                    if self.__nt_modifiable:
                        # Not in sync. Set now
                        self.__nt_set_from_robot(key, value)
                    else:
                        # In sync. Store for when sync is done.
                        self.__sync_keys.append(key)
                        self.__sync_values.append(value)

            # Remove the subset that has already been handled from the buffer
            self.__net_table_read_buf = self.__net_table_read_buf[end_pos+1:len(self.__net_table_read_buf)]



    def __log_ready_read(self):
        # Append data until there is a complete line
        new_data = bytes(self.__log_socket.readAll().data())
        self.__log_read_buf.extend(new_data)

        if(self.__log_read_buf.find(b'\n') != -1):

            # Could be multiple newlines
            lines = self.__log_read_buf.split(b'\n')

            # If buffer ends with newline no data to leave in the buffer
            if self.__log_read_buf.endswith(b'\n'):
                self.__log_read_buf = bytearray()

                # If it ended with a newline the lines array will end with b''. 
                # This should not be logged.
                del lines[len(lines) - 1]
            else:
                last_newline = self.__log_read_buf.rfind(b'\n')
                self.__log_read_buf = self.__log_read_buf[last_newline+1:len(self.__log_read_buf)]
                print(self.__log_read_buf)

            for line in lines:
                logger.log_from_robot(line.decode())
