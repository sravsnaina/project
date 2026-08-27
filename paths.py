import sys                                                    # to check sys.frozen (set by PyInstaller)
from pathlib import Path                                      # filesystem path handling


def app_dir() -> Path:
    """Directory the running app lives in - the executable's folder when
    frozen by PyInstaller, otherwise this source file's folder. Used for
    files that must persist next to the app (counts.json, config.json),
    since PyInstaller's bundle extraction dir is read-only/temporary."""

    if getattr(sys, "frozen", False):                          # True only inside a PyInstaller-built executable
        return Path(sys.executable).resolve().parent            # folder containing the built executable

    return Path(__file__).resolve().parent                      # folder containing this source file (dev mode)
