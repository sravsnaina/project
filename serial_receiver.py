import queue                                                      # thread-safe queue for pending serial writes
import threading                                                  # guards shared access to the serial handle
import time                                                        # monotonic clock for cooldowns/watchdog timing

import serial                                                      # pyserial - the actual RS232/USB-serial driver
from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer  # Qt threading/signal/timer primitives


SCHEMES = {
    1: "S PART1",                                                  # command sent to switch the camera to part 1
    2: "S PART2",                                                  # command sent to switch the camera to part 2
    3: "S PART3",                                                  # command sent to switch the camera to part 3
    4: "S PART4"                                                   # command sent to switch the camera to part 4
}


class SerialWorker(QObject):
    """Runs on a background thread and owns the actual serial.Serial
    object. All blocking I/O happens here so a wedged USB-serial
    adapter can never freeze the GUI thread."""

    connected = Signal()                                            # emitted once the port opens successfully
    disconnected = Signal(str)                                      # emitted when the port closes/fails (reason)
    lineReceived = Signal(str)                                      # emitted with each decoded line read
    heartbeat = Signal()                                            # emitted on every loop pass (I/O is alive)
    workerFinished = Signal()                                       # emitted when run() returns, to stop the thread

    def __init__(self, port, baudrate):
        super().__init__()                                          # initialize QObject (needed for Signals)

        self.port = port                                            # serial device path (e.g. /dev/ttyUSB0)
        self.baudrate = baudrate                                    # serial baud rate
        self.serial = None                                          # the open serial.Serial handle, or None

        self._running = False                                       # main-loop control flag
        self._forceReconnect = False                                # set by kick() to force a fresh reconnect
        self._lock = threading.Lock()                                # protects self.serial across threads

        # Writes are queued and sent from this thread only, so a slow/
        # wedged write can never block the GUI, and reads/writes never
        # race each other on the same fd.
        self._writeQueue = queue.Queue()                             # pending outgoing commands

    # --------------------------------------------------
    # MAIN LOOP (runs on the worker thread)
    # --------------------------------------------------

    def run(self):

        self._running = True                                        # allow the loop below to run

        self._open()                                                 # attempt the initial connection

        while self._running:

            with self._lock:
                ser = self.serial                                    # snapshot the current handle under the lock

            if ser is None:                                           # not connected - retry periodically
                self._sleep(1.5)

                if self._running:                                     # stop() may have fired during the sleep
                    self._open()

                continue

            if not self._flushPendingWrites(ser):                     # a queued write failed and closed the port
                continue

            try:
                line = ser.readline().decode(
                    errors="ignore"                                    # drop undecodable bytes instead of raising
                ).strip()

            except Exception as e:                                     # read failed - port likely gone

                self._forceReconnect = False                            # this is a real error, not a watchdog kick

                self._close(str(e))

                continue

            # Watchdog forced a cancel_read() to unstick a wedged port -
            # the fd is suspect, so reconnect instead of reusing it.
            if self._forceReconnect:                                    # kick() was called since the last read

                self._forceReconnect = False                             # clear the flag now that it's handled

                self._close(
                    "Watchdog: no response from serial port, reconnecting"
                )

                continue

            self.heartbeat.emit()                                        # I/O is alive - reset the watchdog clock

            if line:                                                     # ignore blank reads (timeout with no data)
                self.lineReceived.emit(line)

        self.workerFinished.emit()                                       # loop exited (stop() was called)

    def _sleep(self, seconds):

        end = time.monotonic() + seconds                                 # absolute wake time

        while self._running and time.monotonic() < end:                  # wake early if stop() is called
            time.sleep(0.1)

    def _flushPendingWrites(self, ser):
        """Sends any queued commands (trigger/scheme switch) before the
        next blocking read. Returns False if a write failed and the
        port was closed, so the caller should loop back and reconnect."""

        while True:

            try:
                data = self._writeQueue.get_nowait()                       # next queued command, if any
            except queue.Empty:
                return True                                                 # nothing left to send

            try:
                ser.reset_input_buffer()                                    # drop any stale bytes before writing
                ser.write(data)                                             # send the command
                ser.flush()                                                 # ensure it's actually transmitted

            except Exception as e:                                         # write failed - port likely gone

                self._forceReconnect = False                                # this is a real error, not a watchdog kick

                self._close(str(e))

                return False                                                 # signal the caller to reconnect

    # --------------------------------------------------
    # OPEN / CLOSE
    # --------------------------------------------------

    def _open(self):

        try:

            ser = serial.Serial(
                port=self.port,                                            # device path to open
                baudrate=self.baudrate,                                    # configured baud rate
                bytesize=serial.EIGHTBITS,                                 # 8 data bits
                parity=serial.PARITY_NONE,                                 # no parity bit
                stopbits=serial.STOPBITS_ONE,                              # 1 stop bit
                timeout=0.2                                                 # read timeout, so the loop can poll _running
            )

            with self._lock:
                self.serial = ser                                          # publish the new handle under the lock

            self.connected.emit()                                          # notify the main thread

        except Exception as e:                                             # port missing/busy/permission denied

            with self._lock:
                self.serial = None                                          # stay in "not connected" state

            self.disconnected.emit(str(e))                                  # notify the main thread with the reason

    def _close(self, reason=""):

        with self._lock:
            ser, self.serial = self.serial, None                            # grab and clear the handle atomically

        if ser:
            try:
                ser.close()                                                  # release the OS file descriptor
            except Exception:
                pass                                                          # already gone - nothing more to do

        self.disconnected.emit(reason)                                       # notify the main thread

    # --------------------------------------------------
    # CALLED FROM THE MAIN THREAD
    # --------------------------------------------------

    def stop(self):

        self._running = False                                               # let the run() loop exit

        with self._lock:
            ser = self.serial                                               # snapshot the current handle

        if ser:
            try:
                ser.cancel_read()                                            # unblock a pending readline() call
            except Exception:
                pass                                                          # nothing to cancel / already closed

    def kick(self):
        """Watchdog calls this when no heartbeat has arrived in too
        long. cancel_read()/cancel_write() use a self-pipe that
        select() also watches, so they unblock a stuck call even if
        the serial fd itself is completely wedged at the driver level."""

        self._forceReconnect = True                                          # force a reconnect on the next loop pass

        with self._lock:
            ser = self.serial                                                # snapshot the current handle

        if ser:
            try:
                ser.cancel_read()                                             # unblock a stuck read
            except Exception:
                pass                                                           # nothing to cancel / already closed
            try:
                ser.cancel_write()                                             # unblock a stuck write
            except Exception:
                pass                                                           # nothing to cancel / already closed

    def queueWrite(self, data: bytes):
        """Thread-safe: queues a command to be sent by the worker
        thread, so callers on the GUI thread never block on I/O."""

        self._writeQueue.put(data)                                            # worker thread sends it on its next pass


class SerialReceiver(QObject):

    resultReceived = Signal(str, str)                                         # emitted with (part, status) on a result
    errorOccurred = Signal(str)                                               # emitted with a human-readable error

    # Emitted false the moment a scheme switch is sent, true once the
    # switch cooldown has passed - lets the UI show a "switching" state.
    switchReady = Signal(bool)

    # Emitted true once the serial port is open, false when it drops -
    # lets the UI show a "not connected" state.
    connectionChanged = Signal(bool)

    # How long to ignore results / hold "not ready" after a scheme switch
    SWITCH_COOLDOWN_SECONDS = 0.5

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        super().__init__()                                                    # initialize QObject (needed for Signals/Slots)

        self.port = port                                                      # serial device path, kept for logging

        # Currently selected scheme/part
        self.currentScheme = 1                                                # part number the camera is set to inspect

        # Ignore incoming results until this monotonic time has passed
        # (avoids counting a scheme-switch ack/echo as an inspection result)
        self.suppressResultsUntil = 0.0                                       # monotonic deadline, 0 = no suppression

        self.isReady = True                                                    # False right after a scheme switch
        self.isConnected = False                                               # mirrors the worker's connection state

        # --------------------------------------------------
        # Background thread doing the actual serial I/O
        # --------------------------------------------------

        self._thread = QThread()                                               # dedicated Qt thread for serial I/O
        self._worker = SerialWorker(port, baudrate)                            # owns the actual serial.Serial object
        self._worker.moveToThread(self._thread)                                # run the worker's slots on that thread

        self._thread.started.connect(self._worker.run)                        # kick off the read loop when started
        self._worker.workerFinished.connect(self._thread.quit)                 # stop the thread once run() returns

        self._worker.connected.connect(self._onConnected)                      # update state on successful open
        self._worker.disconnected.connect(self._onDisconnected)                # update state on close/failure
        self._worker.lineReceived.connect(self._onLine)                        # parse each incoming line
        self._worker.heartbeat.connect(self._onHeartbeat)                      # reset the watchdog clock

        # --------------------------------------------------
        # Watchdog: if the read loop stops heartbeating, the port
        # is wedged (blocked read/write, not a thrown error) - kick it.
        # Heartbeats happen every ~0.2s in normal operation regardless
        # of camera traffic, so this is purely a "is I/O frozen" check,
        # not tied to how long a scheme switch takes.
        # --------------------------------------------------

        self.watchdogTimeoutSeconds = 30.0                                      # how long without a heartbeat is "stuck"

        self._lastHeartbeat = time.monotonic()                                  # time of the most recent heartbeat

        self._watchdog = QTimer()                                               # periodic check for a frozen worker
        self._watchdog.setInterval(1000)                                        # check once per second
        self._watchdog.timeout.connect(self._checkWatchdog)                     # run the staleness check

    # ==================================================
    # CONNECT / DISCONNECT
    # ==================================================

    @Slot()
    def connectSerial(self):

        self._lastHeartbeat = time.monotonic()                                   # avoid an immediate false-positive kick

        self._thread.start()                                                     # start the background I/O thread

        self._watchdog.start()                                                    # begin monitoring for a stuck port

    @Slot()
    def disconnectSerial(self):

        self._watchdog.stop()                                                     # stop monitoring, we're shutting down

        if self._thread.isRunning():                                              # only touch the thread if it's alive

            self._worker.stop()                                                    # ask the worker loop to exit

            self._thread.quit()                                                     # ask the Qt event loop to stop
            self._thread.wait(2000)                                                 # wait up to 2s for a clean exit

        print("Serial disconnected")

    def _onConnected(self):
        print("Serial connected:", self.port)

        self.isConnected = True                                                     # mirror the worker's new state

        self.connectionChanged.emit(True)                                            # notify QML

    def _onDisconnected(self, reason):

        if reason:                                                                    # empty reason means a clean stop()
            print("Serial connection lost:", reason)
            self.errorOccurred.emit(reason)                                            # surface the error to QML

        self.isConnected = False                                                       # mirror the worker's new state
        self.connectionChanged.emit(False)                                             # notify QML

    def _onHeartbeat(self):
        self._lastHeartbeat = time.monotonic()                                          # record that I/O is still alive

    def _checkWatchdog(self):

        if time.monotonic() - self._lastHeartbeat > self.watchdogTimeoutSeconds:        # too long since last heartbeat

            print(
                f"Watchdog: no response from serial port in "
                f"{self.watchdogTimeoutSeconds:.0f}s, forcing reconnect"
            )

            self._worker.kick()                                                          # unstick the worker's read/write

            # Avoid re-kicking every tick while reconnect is in progress
            self._lastHeartbeat = time.monotonic()                                        # reset so we wait a full cycle again

    # ==================================================
    # READ CAMERA RESULT (data already decoded/stripped by the worker)
    # ==================================================

    def _onLine(self, data):

        print("Received:", repr(data))

        # ------------------------------------------
        # SWITCH ACK
        # The first line received after a scheme switch is the
        # camera's ack/echo for the switch itself, not an
        # inspection result - however long it takes to arrive.
        # ------------------------------------------

        if not self.isReady:                                                              # waiting on the switch ack

            print(
                "Ignoring (scheme-switch ack):",
                repr(data)
            )

            self.isReady = True                                                            # ack received, ready again

            self.switchReady.emit(True)                                                     # notify QML

            return

        # ------------------------------------------
        # IGNORE RESULTS RIGHT AFTER A SCHEME SWITCH
        # (extra safety window for any stray echoes right
        # after the ack itself - must not be counted)
        # ------------------------------------------

        if time.monotonic() < self.suppressResultsUntil:                                    # still within the cooldown window

            print(
                "Ignoring (scheme-switch cooldown):",
                repr(data)
            )

            return

        # ------------------------------------------
        # CAMERA RETURNS "1;" FOR OK
        #
        # Literal "OK" text is NOT treated as a result -
        # that's the switch command's own ack/echo, not
        # an inspection result, and counting it caused
        # false OK counts right after a scheme switch.
        # ------------------------------------------

        if data == "1;":                                                                     # camera's OK result marker

            part = str(self.currentScheme)                                                    # which part is being inspected

            print("Part:", part, "Result: OK")

            self.resultReceived.emit(part, "OK")                                               # notify Backend

        # ------------------------------------------
        # CAMERA RETURNS NG = NG
        # ------------------------------------------

        elif data.upper() == "NG":                                                             # camera's NG result marker

            part = str(self.currentScheme)                                                      # which part is being inspected

            print("Part:", part, "Result: NG")

            self.resultReceived.emit(part, "NG")                                                 # notify Backend

        # ------------------------------------------
        # OLD FORMAT SUPPORT
        #
        # Example:
        # 1,OK
        # 2,NG
        # ------------------------------------------

        else:                                                                                     # try the legacy "part,status" format

            parts = data.split(",")

            if len(parts) == 2:                                                                   # looks like "part,status"

                part = parts[0].strip()                                                            # part number text
                status = parts[1].strip().upper()                                                   # normalized status text

                if (
                    part in ["1", "2", "3", "4"]                                                     # only known part numbers
                    and status in ["OK", "NG"]                                                       # only recognized statuses
                ):

                    self.resultReceived.emit(part, status)                                            # notify Backend

    # ==================================================
    # SELECT SCHEME
    # ==================================================

    @Slot(int)
    def selectScheme(self, schemeNumber):

        if schemeNumber not in SCHEMES:                                                               # unknown part/scheme number

            self.errorOccurred.emit("Invalid scheme")

            return

        command = SCHEMES[schemeNumber]                                                                # command string to send

        # Save currently selected scheme
        self.currentScheme = schemeNumber                                                              # used to tag future results

        # Queued, not sent directly - the worker thread does the actual
        # write so a slow/stuck port can never freeze the GUI here.
        self._worker.queueWrite(command.encode())                                                       # hand off to the worker thread

        # Camera may echo/ack the switch itself right after - don't
        # let that be counted as a real inspection result.
        self.suppressResultsUntil = time.monotonic() + self.SWITCH_COOLDOWN_SECONDS                     # start the ignore window

        self.isReady = False                                                                             # block results until the ack arrives
        self.switchReady.emit(False)                                                                      # notify QML we're "switching"

        print("Switching to:", command)

    # ==================================================
    # CAMERA TRIGGER
    # ==================================================

    @Slot()
    def trigger(self):

        self._worker.queueWrite(b"T")                                                                     # ask the camera to capture/inspect

        print("Camera trigger queued")

    # ==================================================
    # TESTING WITHOUT RASPBERRY PI
    # ==================================================

    @Slot(str, str)
    def simulateResult(self, part, status):

        print("SIMULATED:", part, status)

        self.resultReceived.emit(part, status)                                                             # inject a fake result, as if from the camera
