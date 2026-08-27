#!/usr/bin/env bash
# Builds a standalone ARM64 executable of this app. Run this ON the
# Raspberry Pi 4 itself (64-bit Raspberry Pi OS), not on a dev machine -
# PyInstaller bundles whatever shared libraries/architecture it is run
# with, it does not cross-compile.
#
# Usage (from the project root, i.e. the folder containing main.py):
#   bash deploy/build_on_pi.sh
#
# Result: dist/main - a single executable, plus config.json copied
# next to it so the camera serial port can be edited without rebuilding.

set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$(uname -m)" != "aarch64" ]; then
    echo "Warning: this is not an aarch64 (64-bit) system (uname -m = $(uname -m))." >&2
    echo "Make sure you are running this on the Pi's 64-bit Raspberry Pi OS." >&2
fi

echo "==> Installing system packages (sudo required)"
sudo apt-get update
sudo apt-get install -y \
    python3-venv \
    python3-pip \
    build-essential \
    libgpiod-dev \
    gpiod \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libfontconfig1 \
    libegl1 \
    libgles2 \
    fonts-dejavu-core

echo "==> Adding $USER to gpio/dialout groups (GPIO + serial access without sudo)"
sudo usermod -aG gpio,dialout "$USER" || true

echo "==> Creating build venv (.venv-build)"
python3 -m venv .venv-build
source .venv-build/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "==> Running PyInstaller"
pyinstaller --clean --noconfirm main.spec

echo "==> Copying config.json next to the built executable"
cp -n config.json dist/config.json 2>/dev/null || true

deactivate

echo
echo "Build complete: dist/main"
echo "Run it with: ./dist/main"
echo
echo "If you were just added to the gpio/dialout groups, log out and back"
echo "in (or reboot) first, otherwise GPIO/serial access will fail."
