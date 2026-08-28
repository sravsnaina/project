import json                                                  # stdlib JSON parsing, used for config.json
import logging                                                # stdlib logging framework for app.log
import os                                                     # used to set QT_QUICK_CONTROLS_STYLE env var
import sys                                                    # argv, exit, stdout/stderr redirection, excepthook
import traceback                                              # formats uncaught exception tracebacks for the log
from logging.handlers import RotatingFileHandler              # size-capped, auto-rotating log file handler
from pathlib import Path                                      # filesystem path handling

from PySide6.QtGui import QGuiApplication                     # Qt Quick application object
from PySide6.QtQml import QQmlApplicationEngine                # loads and runs the QML UI

from backend import Backend                                   # app-level backend exposed to QML
from Production_model import ProductionModel                  # production counts/log model
from serial_receiver import SerialReceiver                    # background serial read thread
from gpio_controller import GPIOController                    # OK/NG GPIO I/O
from LogModel import LogModel                                 # last-5-results list model for QML
from paths import app_dir                                     # resolves app directory (dev vs packaged)

# Registers the qrc:/ resources (e.g. images/Ensteinlogo.png) compiled
# from tech/image.qrc. Importing it runs its qInitResources() call.
sys.path.insert(0, str(Path(__file__).parent / "tech"))       # add tech/ to import path so rc_image.py can be found

//changes
class _StreamToLog:
    """Mirrors writes to the original stream (so a terminal run still
    shows live output) and to the log file, so nothing is lost when the
    app runs unattended (autostart, no visible console)."""

    def __init__(self, logger, level, original_stream):
        self.logger = logger                                  # logger to mirror writes into
        self.level = level                                     # log level (INFO for stdout, ERROR for stderr)
        self.original_stream = original_stream                 # real stdout/stderr, or None if unavailable

    def write(self, message):
        if self.original_stream:                               # only write through if a real stream exists
            self.original_stream.write(message)                # preserve normal terminal output

        message = message.strip()                              # drop the trailing newline print() adds
        if message:                                             # skip logging blank writes (e.g. bare "\n")
            self.logger.log(self.level, message)                # record the line in app.log

    def flush(self):
        if self.original_stream:                                # only flush if a real stream exists
            self.original_stream.flush()                        # forward the flush call


def setup_error_log():
    """Every print() across the app (GPIO/serial/backend status and
    errors) plus any uncaught exception is written to a rotating file
    next to the app, so issues can be diagnosed after the fact."""

    log_dir = app_dir() / "logs"                                # logs/ next to the app (or bundled dir)
    log_dir.mkdir(exist_ok=True)                                # create it if this is the first run

    handler = RotatingFileHandler(
        log_dir / "app.log",                                    # target log file
        maxBytes=2 * 1024 * 1024,                                # rotate at 2 MB
        backupCount=3                                            # keep 3 rotated backups
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"                # timestamp + level + message per line
    ))

    logger = logging.getLogger("app")                           # named logger for the whole app
    logger.setLevel(logging.INFO)                                # capture INFO and above
    logger.addHandler(handler)                                  # write through the rotating file handler

    sys.stdout = _StreamToLog(logger, logging.INFO, sys.stdout)  # redirect print() to log at INFO
    sys.stderr = _StreamToLog(logger, logging.ERROR, sys.stderr) # redirect stderr writes to log at ERROR

    def log_uncaught(exc_type, exc_value, exc_tb):
        logger.error(
            "Uncaught exception:\n"
            + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))  # full formatted traceback
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)          # still call the default handler (prints to stderr)

    sys.excepthook = log_uncaught                                # install as the global exception hook


def load_config():
    """Reads config.json next to the app (editable without a rebuild -
    e.g. when the camera's USB-serial adapter shows up on a different
    /dev path)."""

    config = {"serial_port": "/dev/ttyUSB0", "baudrate": 9600}   # fallback defaults if config.json is missing/bad

    config_path = app_dir() / "config.json"                     # expected location of the config file

    if config_path.exists():                                     # only attempt to load if the file is present
        try:
            with open(config_path) as f:                         # open config.json for reading
                config.update(json.load(f))                      # merge parsed JSON over the defaults
        except (json.JSONDecodeError, OSError) as e:              # malformed JSON or unreadable file
            print("config.json error, using defaults:", e)        # log the problem, keep running with defaults

    return config                                                 # merged config dict


if __name__ == "__main__":

    setup_error_log()                                             # start mirroring stdout/stderr to app.log

    # "Basic" is the lightest Qt Quick Controls style (no native theming
    # engine to spin up) - cuts startup time noticeably on the Pi 4 vs
    # the platform-default style. Must be set before QGuiApplication().
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")     # only sets it if not already set externally

    app = QGuiApplication(sys.argv)                               # create the Qt application instance

    engine = QQmlApplicationEngine()                               # create the QML engine that will load the UI

    config = load_config()                                         # read serial_port/baudrate from config.json

    # Create ProductionModel
    productionModel = ProductionModel()                            # loads/holds counts.json production log

    # Create SerialReceiver
    serialReceiver = SerialReceiver(
        port=config["serial_port"],                                # serial device path from config
        baudrate=config["baudrate"]                                 # serial baud rate from config
    )

    # Create GPIO Controller
    gpiocontroller = GPIOController()                               # sets up OK/NG output pins and sensor input

    # Create Log Model (last 5 results)
    logModel = LogModel()                                           # empty list model, populated below

    # Seed with the last 5 results already stored in counts.json
    for log in productionModel.logs[-5:]:                           # iterate the last 5 persisted results

        logModel.addLog(
            log["time"],                                            # timestamp of that result
            f"Part {log['part']}",                                  # part label built from stored part number
            log["status"]                                            # OK/NG status of that result
        )

    # Create Backend
    backend = Backend(
        productionModel,                                            # wired in so Backend can read/update counts
        serialReceiver,                                              # wired in so Backend can react to serial data
        gpiocontroller,                                              # wired in so Backend can drive GPIO
        logModel                                                     # wired in so Backend can push new log rows
    )

    # Connect to serial device
    serialReceiver.connectSerial()                                   # opens the serial port and starts reading

    # Cleanly stop the serial background thread on exit - otherwise Qt
    # aborts the process because the thread is still running when
    # destroyed.
    app.aboutToQuit.connect(serialReceiver.disconnectSerial)         # stop serial thread before Qt tears down
    app.aboutToQuit.connect(gpiocontroller.cleanup)                  # release GPIO resources before exit

    # Make Backend available to QML
    engine.rootContext().setContextProperty(
        "backend",                                                   # QML-visible property name
        backend                                                       # the Backend instance
    )

    # Make GPIO controller available to QML
    engine.rootContext().setContextProperty(
        "gpiocontroller",                                             # QML-visible property name
        gpiocontroller                                                 # the GPIOController instance
    )

    # Make ProductionModel available to QML
    engine.rootContext().setContextProperty(
        "productionModel",                                            # QML-visible property name
        productionModel                                                 # the ProductionModel instance
    )

    # Make LogModel available to QML
    engine.rootContext().setContextProperty(
        "logModel",                                                    # QML-visible property name
        logModel                                                        # the LogModel instance
    )

    engine.addImportPath(
        Path(__file__).parent                                          # lets QML `import tech` resolve locally
    )

    engine.loadFromModule(
        "tech",                                                        # QML module name (tech/qmldir)
        "Main"                                                         # root component to load (Main.qml)
    )

    if not engine.rootObjects():                                       # QML failed to load (syntax/binding error)
        sys.exit(-1)                                                    # exit with failure status

    sys.exit(app.exec())                                                # run the Qt event loop until quit
