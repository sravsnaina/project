from PySide6.QtCore import QObject, Signal, QTimer,Slot          # Qt base class, signals, polling timer, slot decorator

try:
    import gpiod                                                  # Linux GPIO character-device library
    from gpiod.line import Direction, Value                       # pin direction / active-low value helpers
    GPIOD_AVAILABLE = True                                        # library present - real GPIO can be used
except ImportError:
    GPIOD_AVAILABLE = False                                       # not on a Pi / lib missing - GPIO stays disabled


class GPIOController(QObject):

    # --------------------------------------------------
    # SIGNALS
    # --------------------------------------------------

    sensorDetected = Signal()                                     # emitted when the part sensor triggers

    cameraTriggered = Signal()                                    # emitted when the conveyor-shorten pin fires
    # backward-compatible alias for QML/other code that may expect the old signal name
    conveyorShorten = cameraTriggered                              # same Signal object under its old name
    okSignal = Signal()                                            # emitted when an OK result is set
    ngSignal = Signal()                                            # emitted when an NG result is set

    # --------------------------------------------------
    # GPIO PINS
    # --------------------------------------------------

    SENSOR_PIN = 17                                                # part-present sensor input
    CONVEYOR_SHORTEN_PIN = 24                                      # conveyor-shorten output
    OK_PIN = 22                                                    # OK result output
    NG_PIN = 23                                                    # NG result output
    CONVEYOR_PIN=27                                                # conveyor run output
    # Pulse time
    PULSE_TIME_MS = 100                                            # (currently unused - pulse-off calls are disabled below)

    def __init__(self, enable_gpio=True):

        super().__init__()                                        # initialize QObject (needed for Signals)

        self.enable_gpio = enable_gpio                             # master switch - False lets the app run off-Pi
        self.request = None                                        # gpiod line request handle, set once GPIO opens
        self.result_active=False                                   # True while an OK/NG output is being held active

        # Previous sensor state
        self.lastSensorState = True                                # last polled raw sensor reading
        self.sensorTriggered =False                                # True while a part is currently under the sensor

        # --------------------------------------------------
        # GPIO DISABLED
        # --------------------------------------------------

        if not self.enable_gpio:                                  # caller explicitly disabled GPIO

            print("GPIO disabled - running without Raspberry Pi GPIO")

            return                                                  # skip all hardware setup below

        # --------------------------------------------------
        # CHECK GPIOD
        # --------------------------------------------------

        if not GPIOD_AVAILABLE:                                    # gpiod import failed earlier

            print("gpiod not installed - GPIO disabled")

            self.enable_gpio = False                                # fall back to disabled mode

            return                                                   # skip hardware setup below

        # --------------------------------------------------
        # INITIALIZE GPIO
        # --------------------------------------------------

        try:

            self.request = gpiod.request_lines(
                "/dev/gpiochip0",                                    # the Pi's main GPIO chip device

                consumer="production-system",                        # label shown to other gpiod consumers

                config={

                    # Sensor
                    self.SENSOR_PIN: gpiod.LineSettings(
                        direction=Direction.INPUT                     # sensor pin reads external state
                    ),

                    # Conveyor shorten (previously camera trigger)
                    self.CONVEYOR_SHORTEN_PIN: gpiod.LineSettings(
                        direction=Direction.OUTPUT,                    # drives the conveyor-shorten line
                        output_value=Value.ACTIVE                       # starts inactive (ACTIVE = idle/high here)
                    ),

                    # OK
                    self.OK_PIN: gpiod.LineSettings(
                        direction=Direction.OUTPUT,                     # drives the OK output line
                        output_value=Value.ACTIVE                        # starts inactive (ACTIVE = idle/high here)
                    ),

                    # NG
                    self.NG_PIN: gpiod.LineSettings(
                        direction=Direction.OUTPUT,                     # drives the NG output line
                        output_value=Value.ACTIVE                        # starts inactive (ACTIVE = idle/high here)
                    ),

                    #CONVEYOR_PIN
                     self.CONVEYOR_PIN: gpiod.LineSettings(
                        direction=Direction.OUTPUT,                      # drives the conveyor-run line
                        output_value=Value.ACTIVE                         # starts inactive (ACTIVE = idle/high here)
                    )


                }
            )

            print("GPIO initialized successfully")

            # --------------------------------------------------
            # SENSOR POLLING TIMER
            # --------------------------------------------------

            self.sensorTimer = QTimer()                              # drives periodic sensor checks

            self.sensorTimer.timeout.connect(
                self.checkSensor                                       # poll callback
            )

            # Check sensor every 50 ms
            self.sensorTimer.start(50)                                 # begin polling

        except Exception as e:

            print("GPIO initialization error:", e)

            self.enable_gpio = False                                   # fall back to disabled mode on any failure

    # ==================================================
    # SENSOR
    # ==================================================

    def read_sensor(self):

        if not self.enable_gpio:                                       # GPIO disabled - nothing to read
            return False

        try:

            value = self.request.get_value(
                self.SENSOR_PIN                                          # current level of the sensor pin
            )

            return value == Value.ACTIVE                                 # True when sensor line is active

        except Exception as e:

            print("Sensor read error:", e)

            return False                                                  # treat read failure as "not detected"

    # --------------------------------------------------
    # CHECK SENSOR
    # --------------------------------------------------

    def checkSensor(self):

        if not self.enable_gpio:                                          # GPIO disabled - nothing to poll
            return

        sensorState = self.read_sensor()                                   # current raw sensor reading

        # New product detected:
        # LOW -> HIGH
        if not sensorState and not self.sensorTriggered:                    # part just arrived under the sensor

            print("================================")
            print("SENSOR DETECTED")
            print("GPIO 17 = HIGH")
            print("================================")

            #QTimer.singleShot(100,self.confirmSensor)

            self.sensorTriggered=True                                        # mark part as currently present
            # Tell Backend
            self.sensorDetected.emit()                                       # notify listeners a part was detected

            # Trigger conveyor-shorten GPIO
            self.conveyor_shorten_on()                                        # engage conveyor-shorten output

        elif sensorState:                                                     # sensor currently reads clear/inactive

            if self.sensorTriggered:                                         # part just left the sensor
                self.sensorTriggered=False                                    # clear the "part present" flag
                self.conveyor_shorten_off()                                   # release conveyor-shorten output


            if self.result_active:                                           # an OK/NG output was being held
                self.request.set_value(self.OK_PIN,Value.ACTIVE)              # release OK pin back to idle
                self.request.set_value(
                    self.NG_PIN,
                    Value.ACTIVE)                                              # release NG pin back to idle

                # emit conveyorShorten as legacy hook (no-op alias)
                #self.conveyorShorten

                self.result_active=False                                       # OK/NG hold is over


        # Save current state
        self.lastSensorState = sensorState                                     # remember this reading for next poll

    # ==================================================
    # CAMERA TRIGGER
    # ==================================================

    def conveyor_shorten_on(self):

        if not self.enable_gpio:                                               # GPIO disabled - just log

            print("[GPIO OFF] Camera trigger")

            return

        try:

            print("CONVEYOR SHORTEN ON")
            print(f"GPIO {self.CONVEYOR_SHORTEN_PIN} = HIGH")
            if self.sensorTriggered == True:                                     # part still present under sensor
                self.request.set_value(
                    self.CONVEYOR_SHORTEN_PIN,
                    Value.INACTIVE)                                                # engage the conveyor-shorten output
                self.conveyorShorten.emit()                                        # notify listeners
            else:                                                                  # part already cleared the sensor
                self.request.set_value(
                    self.CONVEYOR_SHORTEN_PIN,
                    Value.ACTIVE)                                                   # leave/return it idle
                print(f"GPIO {self.CONVEYOR_SHORTEN_PIN} = LOW")
                print("sensor detected conveyor shorted")


        except Exception as e:

            print("Camera trigger error:", e)

    # --------------------------------------------------
    # CAMERA TRIGGER OFF
    # --------------------------------------------------

    def conveyor_shorten_off(self):

        if not self.enable_gpio:                                                    # GPIO disabled - nothing to do
            return

        try:

            self.request.set_value(
                self.CONVEYOR_SHORTEN_PIN,
                Value.ACTIVE)                                                        # return the pin to idle
            self.conveyorShorten.emit()                                             # notify listeners

            print("CONVEYOR SHORTEN OFF")
            print(f"GPIO {self.CONVEYOR_SHORTEN_PIN} = LOW")

        except Exception as e:

            print("Camera trigger OFF error:", e)



    # ==================================================
    # OK OUTPUT
    # ==================================================

    def set_ok(self):

        if not self.enable_gpio:                                                     # GPIO disabled - just log

            print("[GPIO OFF] OK signal")

            return

        try:

            # NG must be OFF
            self.request.set_value(
                self.NG_PIN,
                Value.ACTIVE                                                          # ensure NG pin is idle
            )

            print("================================")
            print("OK RESULT RECEIVED")
            print("GPIO 22 = HIGH")
            print("GPIO 23 = LOW")
            print("================================")

            self.request.set_value(
                self.OK_PIN,
                Value.INACTIVE                                                         # drive OK pin active
            )
            self.result_active=True                                                    # hold until sensor clears (see checkSensor)

            self.okSignal.emit()                                                        # notify listeners

            # Turn OFF after pulse
           # QTimer.singleShot(
            #    self.PULSE_TIME_MS,
          #      self.ok_off
           # )


        except Exception as e:

            print("OK GPIO error:", e)

    # --------------------------------------------------
    # OK OFF
    # --------------------------------------------------

    def ok_off(self):

        if not self.enable_gpio:                                                        # GPIO disabled - nothing to do
            return

        try:

            self.request.set_value(
                self.OK_PIN,
                Value.ACTIVE                                                              # return OK pin to idle
            )

            print("OK GPIO OFF")
            print("GPIO 22 = LOW")

        except Exception as e:

            print("OK GPIO OFF error:", e)

    # ==================================================
    # NG OUTPUT
    # ==================================================

    def set_ng(self):

        if not self.enable_gpio:                                                          # GPIO disabled - just log

            print("[GPIO OFF] NG signal")

            return

        try:

            # OK must be OFF
            self.request.set_value(
                self.OK_PIN,
                Value.ACTIVE            )                                                   # ensure OK pin is idle

            print("================================")
            print("NG RESULT RECEIVED")
            print("GPIO 23 = HIGH")
            print("GPIO 22 = LOW")
            print("================================")

            self.request.set_value(
                self.NG_PIN,
                Value.INACTIVE                                                              # drive NG pin active
            )
            self.result_active=True                                                         # hold until sensor clears (see checkSensor)


            self.ngSignal.emit()                                                             # notify listeners

            # Turn OFF after pulse
            #QTimer.singleShot(
            #    self.PULSE_TIME_MS,
           #     self.ng_off
           # )

        except Exception as e:

            print("NG GPIO error:", e)

    # --------------------------------------------------
    # NG OFF
    # --------------------------------------------------

    def ng_off(self):

        if not self.enable_gpio:                                                             # GPIO disabled - nothing to do
            return

        try:

            self.request.set_value(
                self.NG_PIN,
                Value.ACTIVE                                                                   # return NG pin to idle
            )

            print("NG GPIO OFF")
            print("GPIO 23 = LOW")

        except Exception as e:

            print("NG GPIO OFF error:", e)


      # ==================================================
    # conveyor OUTPUT
    # ==================================================
    @Slot()
    def conveyor_on(self):

        if not self.enable_gpio:                                                               # GPIO disabled - just log

            print("[GPIO OFF] convyor signal")

            return

        try:

            # conveyor must be OFF
            self.request.set_value(
                self.CONVEYOR_PIN,
                Value.INACTIVE)                                                                  # drive conveyor pin active (running)

            print("================================")
            print("Conveyor pin")
            print(f"GPIO {self.CONVEYOR_PIN} = HIGH")
            print("================================")

        except Exception as e:

            print("conveyor GPIO error:", e)

    # --------------------------------------------------
    # CONVEYOR OFF
    # --------------------------------------------------
    @Slot()
    def conveyor_off(self):

        if not self.enable_gpio:                                                                  # GPIO disabled - nothing to do
            return

        try:

            self.request.set_value(
                self.CONVEYOR_PIN,
                Value.ACTIVE                                                                        # return conveyor pin to idle (stopped)
            )

            print("conveyor OFF")
            print(f"GPIO {self.CONVEYOR_PIN} = LOW")

        except Exception as e:

            print("conveyor GPIO OFF error:", e)

    # ==================================================
    # ALL OUTPUTS OFF
    # ==================================================

    def all_off(self):

        if not self.enable_gpio:                                                                    # GPIO disabled - nothing to do
            return

        try:

            self.request.set_value(
                self.CONVEYOR_SHORTEN_PIN,
                Value.ACTIVE                                                                          # idle the conveyor-shorten pin
            )

            self.request.set_value(
                self.OK_PIN,
                Value.ACTIVE                                                                           # idle the OK pin
            )

            self.request.set_value(
                self.NG_PIN,
                Value.ACTIVE                                                                            # idle the NG pin
            )

            self.request.set_value(
                self.CONVEYOR_PIN,
                Value.ACTIVE                                                                             # idle the conveyor pin
            )

            print("All GPIO outputs OFF")

        except Exception as e:

            print("GPIO OFF error:", e)

    # ==================================================
    # CLEANUP
    # ==================================================

    def cleanup(self):

        if not self.enable_gpio:                                                                          # GPIO disabled - nothing to release
            return

        try:

            if hasattr(self, "sensorTimer"):                                                              # timer only exists if init got that far
                self.sensorTimer.stop()                                                                     # stop polling before releasing lines

            self.all_off()                                                                                  # idle every output pin

            if self.request:                                                                                # a line request is open

                self.request.release()                                                                       # release the gpiod line request

                self.request = None                                                                           # drop the handle

            print("GPIO cleanup completed")

        except Exception as e:

            print("GPIO cleanup error:", e)
