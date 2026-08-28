import os                                                        # for env var filtering in restartApp
import subprocess                                                # to launch sudo shutdown/reboot and app relaunch
import sys                                                       # frozen check, executable path, argv
from datetime import datetime                                    # timestamps for log rows

from PySide6.QtCore import QObject, Property, QCoreApplication, Signal, Slot  # Qt/QML integration primitives
//this are the changes i have done
//change in branch
class Backend(QObject):                                          # central object exposed to QML as `backend`

    schemeReadyChanged = Signal(bool)                             # QML-bound: camera scheme ready to trigger
    connectedChanged = Signal(bool)                                # QML-bound: serial port connected state

    part1OkChanged = Signal(int)                                  # QML-bound: part 1 OK count
    part1NgChanged = Signal(int)                                  # QML-bound: part 1 NG count
    part1TotalChanged = Signal(int)                                # QML-bound: part 1 total count

    part2OkChanged = Signal(int)                                  # QML-bound: part 2 OK count
    part2NgChanged = Signal(int)                                  # QML-bound: part 2 NG count
    part2TotalChanged = Signal(int)                                # QML-bound: part 2 total count

    part3OkChanged = Signal(int)                                  # QML-bound: part 3 OK count
    part3NgChanged = Signal(int)                                  # QML-bound: part 3 NG count
    part3TotalChanged = Signal(int)                                # QML-bound: part 3 total count

    part4OkChanged = Signal(int)                                  # QML-bound: part 4 OK count
    part4NgChanged = Signal(int)                                  # QML-bound: part 4 NG count
    part4TotalChanged = Signal(int)                                # QML-bound: part 4 total count

    def __init__(self, productionModel, serialReceiver, gpioController, logModel):
        super().__init__()                                        # initialize QObject (needed for Signals/Slots)

        self.productionModel = productionModel                    # counts/log storage
        self.serialReceiver = serialReceiver                      # camera serial link
        self.gpioController = gpioController                      # OK/NG/sensor GPIO
        self.logModel = logModel                                  # last-5-results QML list model

        self._schemeReady = serialReceiver.isReady                 # mirrors SerialReceiver's initial ready state
        self._connected = serialReceiver.isConnected                # mirrors SerialReceiver's initial connection state

        # --------------------------------------------------
        # Production model changes
        # --------------------------------------------------

        self.productionModel.dataChanged.connect(
            self.emitSignals                                       # push updated counts out to QML
        )

        # --------------------------------------------------
        # Scheme switch ready/not-ready -> QML
        # --------------------------------------------------

        self.serialReceiver.switchReady.connect(
            self._onSchemeReadyChanged                              # update local ready flag and notify QML
        )

        # --------------------------------------------------
        # Serial port connected/disconnected -> QML
        # --------------------------------------------------

        self.serialReceiver.connectionChanged.connect(
            self._onConnectionChanged                                # update local connected flag and notify QML
        )

        # --------------------------------------------------
        # Camera result from RS232
        # --------------------------------------------------

        self.serialReceiver.resultReceived.connect(
            self.addResult                                            # record the OK/NG result and log row
        )

        # --------------------------------------------------
        # Camera result -> OK/NG GPIO
        # --------------------------------------------------

        self.serialReceiver.resultReceived.connect(
            self.handleGPIOResult                                      # drive the OK/NG output pins
        )

        # --------------------------------------------------
        # Sensor GPIO -> Backend
        # --------------------------------------------------

        self.gpioController.sensorDetected.connect(
            self.handleSensor                                           # trigger the camera when a part arrives
        )

        print("Backend initialized")

    # --------------------------------------------------
    # GET OK
    # --------------------------------------------------

    @Slot(int, result=int)
    def getOk(self, part):

        return self.productionModel.getOK(part)                        # OK count for this part number, for QML

    # --------------------------------------------------
    # GET NG
    # --------------------------------------------------

    @Slot(int, result=int)
    def getNg(self, part):

        return self.productionModel.getNG(part)                        # NG count for this part number, for QML

    # --------------------------------------------------
    # GET TOTAL
    # --------------------------------------------------

    @Slot(int, result=int)
    def getTotal(self, part):

        return self.productionModel.getTotal(part)                     # total count for this part number, for QML

    # --------------------------------------------------
    # CAMERA RESULT
    # --------------------------------------------------

    @Slot(str, str)
    def addResult(self, part, status):

        print(
            "Backend received:",
            part,                                                        # part number/id from the camera
            status                                                        # OK/NG status from the camera
        )

        self.productionModel.addLog(
            part,                                                         # persist this part number
            status                                                         # persist this OK/NG status
        )

        self.logModel.addLog(
            datetime.now().strftime("%H:%M:%S"),                          # current time as HH:MM:SS
            f"Part {part}",                                                # human-readable event label
            status                                                         # OK/NG status
        )

    # --------------------------------------------------
    # SENSOR DETECTED
    # --------------------------------------------------

    @Slot()
    def handleSensor(self):

        print("Backend: Sensor detected")

        # Trigger camera through SerialReceiver
        self.serialReceiver.trigger()                                       # send the capture command over serial

    # --------------------------------------------------
    # GPIO OK / NG
    # --------------------------------------------------

    @Slot(str, str)
    def handleGPIOResult(self, part, status):

        print(
            "GPIO result:",
            part,                                                            # part number/id from the camera
            status                                                            # OK/NG status from the camera
        )

        if status == "OK":                                                    # camera reported a good part

            self.gpioController.set_ok()                                      # drive the OK output pin

        elif status == "NG":                                                  # camera reported a bad part

            self.gpioController.set_ng()                                      # drive the NG output pin

    # --------------------------------------------------
    # SELECT CAMERA SCHEME
    # --------------------------------------------------

    @Slot(int)
    def selectScheme(self, schemeNumber):

        self.serialReceiver.selectScheme(
            schemeNumber                                                       # part/scheme number to switch to
        )

    # --------------------------------------------------
    # SCHEME READY (true once the post-switch cooldown ends)
    # --------------------------------------------------

    def _onSchemeReadyChanged(self, ready):

        self._schemeReady = ready                                              # store the raw ready flag

        self.schemeReadyChanged.emit(self.schemeReady)                         # notify QML with the combined property

    @Property(bool, notify=schemeReadyChanged)
    def schemeReady(self):

        return self._schemeReady and self._connected                            # ready only if switched AND connected

    # --------------------------------------------------
    # SERIAL CONNECTED (USB0 present/absent)
    # --------------------------------------------------

    def _onConnectionChanged(self, connected):

        self._connected = connected                                              # store the raw connected flag

        self.connectedChanged.emit(connected)                                     # notify QML of connection change
        self.schemeReadyChanged.emit(self.schemeReady)                            # schemeReady may also have changed

    @Property(bool, notify=connectedChanged)
    def connected(self):

        return self._connected                                                    # exposed to QML as `backend.connected`

    # --------------------------------------------------
    # MANUAL CAMERA TRIGGER
    # --------------------------------------------------

    @Slot()
    def triggerCamera(self):

        self.serialReceiver.trigger()                                              # manual capture request from QML

    # --------------------------------------------------
    # SYSTEM POWER CONTROLS (require passwordless sudo for
    # shutdown/reboot - see PI_SETUP_STEPS.md)
    # --------------------------------------------------

    @Slot()
    def shutdownSystem(self):

        print("Backend: shutdown requested")

        subprocess.Popen(["sudo", "shutdown", "-h", "now"])                         # power off the Pi

    @Slot()
    def rebootSystem(self):

        print("Backend: reboot requested")

        subprocess.Popen(["sudo", "reboot"])                                        # reboot the Pi

    # Not wired up to the UI right now - relaunching this frozen build
    # crashes (PyInstaller onefile self-extraction race, still being
    # tracked down). Left here so it's ready once that's resolved.
    @Slot()
    def restartApp(self):

        print("Backend: app restart requested")

        # PyInstaller onefile builds record their self-extracted temp
        # dir in internal _MEI*/_PYI* env vars. A relaunched copy
        # inherits them and reuses this process's temp dir instead of
        # extracting its own - which this process's bootloader deletes
        # on exit, crashing the new copy with "base_library.zip not
        # found". Stripping them forces the new copy to extract its own.
        env = {
            key: value for key, value in os.environ.items()                          # copy the current environment
            if not key.startswith(("_MEI", "_PYI"))                                   # drop PyInstaller's extraction markers
        }

        if getattr(sys, "frozen", False):                                             # running as a packaged executable
            subprocess.Popen([sys.executable] + sys.argv[1:], env=env)                # relaunch the executable directly
        else:                                                                          # running as a plain Python script
            subprocess.Popen([sys.executable] + sys.argv, env=env)                    # relaunch via the Python interpreter

        QCoreApplication.instance().quit()                                             # exit this process's event loop

    # --------------------------------------------------
    # UPDATE QML SIGNALS
    # --------------------------------------------------

    def emitSignals(self):

        # --------------------------------------------------
        # Part 1
        # --------------------------------------------------

        self.part1OkChanged.emit(
            self.productionModel.getOK(1)                                              # latest OK count for part 1
        )

        self.part1NgChanged.emit(
            self.productionModel.getNG(1)                                              # latest NG count for part 1
        )

        self.part1TotalChanged.emit(
            self.productionModel.getTotal(1)                                           # latest total count for part 1
        )

        # --------------------------------------------------
        # Part 2
        # --------------------------------------------------

        self.part2OkChanged.emit(
            self.productionModel.getOK(2)                                              # latest OK count for part 2
        )

        self.part2NgChanged.emit(
            self.productionModel.getNG(2)                                              # latest NG count for part 2
        )

        self.part2TotalChanged.emit(
            self.productionModel.getTotal(2)                                           # latest total count for part 2
        )



        # --------------------------------------------------
        # Part 3
        # --------------------------------------------------

        self.part3OkChanged.emit(
            self.productionModel.getOK(3)                                              # latest OK count for part 3
        )

        self.part3NgChanged.emit(
            self.productionModel.getNG(3)                                              # latest NG count for part 3
        )

        self.part3TotalChanged.emit(
            self.productionModel.getTotal(3)                                           # latest total count for part 3
        )

        # --------------------------------------------------
        # Part 4
        # --------------------------------------------------

        self.part4OkChanged.emit(
            self.productionModel.getOK(4)                                              # latest OK count for part 4
        )

        self.part4NgChanged.emit(
            self.productionModel.getNG(4)                                              # latest NG count for part 4
        )

        self.part4TotalChanged.emit(
            self.productionModel.getTotal(4)                                           # latest total count for part 4
        )
