# Raspberry Pi 4 — Deploy as an App

Run these steps directly on the Raspberry Pi. Assumes the project is already
on the Pi (e.g. at `~/tech`) and a venv with `requirements.txt` already
installed exists there.

## 1. Activate the existing venv and add PyInstaller

```bash
cd ~/tech
source <your-venv>/bin/activate
pip install pyinstaller
```

## 2. Build the standalone executable

```bash
pyinstaller --clean --noconfirm main.spec
```

Produces `dist/main` — a single self-contained binary that doesn't need the
venv at runtime.

## 3. Copy config next to it

```bash
cp config.json dist/config.json
deactivate
```

## 4. Confirm GPIO/serial groups

Only needed if not already done on this Pi:

```bash
sudo usermod -aG gpio,dialout $USER
```

If you just ran that, log out/in (or reboot) before testing.

## 5. Set the camera's serial port

```bash
ls /dev/ttyUSB*
nano ~/tech/dist/config.json
```

## 6. Install the desktop launcher

```bash
cd ~/tech
sed -i "s|/home/pi/tech|$HOME/tech|g" deploy/production-app.desktop
mkdir -p ~/.local/share/applications
cp deploy/production-app.desktop ~/.local/share/applications/
cp deploy/production-app.desktop ~/Desktop/
chmod +x ~/Desktop/production-app.desktop
```

## 7. Test

```bash
~/tech/dist/main
```

Confirm the window opens, serial connects, and GPIO OK/NG behaves correctly.

## 8. Use it

Double-click **Production Line Monitor** on the Desktop (or find it in the
applications menu) from now on.

## 9. Boot straight into the app (kiosk mode)

Skip the desktop and login screen entirely, and launch the app as soon as
the Pi powers on.

**Enable desktop auto-login:**

```bash
sudo raspi-config
```

`System Options` → `Boot / Auto Login` → `Desktop Autologin`.

**Auto-start the app when the desktop session starts:**

```bash
mkdir -p ~/.config/autostart
cp ~/.local/share/applications/production-app.desktop ~/.config/autostart/
```

The app opens in real fullscreen and covers the taskbar/panel - this is what
the client sees. **F11** drops it back to a normal window (title bar,
taskbar/panel visible again, raspberry menu/file manager reachable); **F11**
or **Esc** returns to fullscreen. Don't mention this shortcut to the client -
it's the admin way back into the desktop, not a documented feature.

Reboot to confirm: the Pi should power on straight into the app, fullscreen,
with no login prompt and no desktop visible first.

## 9a. Confirm autostart is actually firing under LXDE (X11)

This Pi runs the X11/LXDE desktop (`lxsession` + `lxpanel`, not the
Wayland/`labwc` stack some newer Raspberry Pi OS images default to).
`lxsession` fully implements the XDG autostart spec, so it should source
`.desktop` files from `~/.config/autostart/` on its own - that's what step
9 relies on. Verify it's actually happening rather than assuming:

```bash
# confirm lxsession is the running session manager
pgrep -a lxsession

# confirm the app is running right after boot
pgrep -af dist/main
```

Reboot, then run the second command again. If `dist/main` shows up, step 9
is working as-is and nothing else is needed.

**If it doesn't show up**, launch it directly from lxsession's own
autostart file instead, which always runs at session start regardless of
XDG support. `@`-prefixed lines are both autostarted and respawned if they
exit, which suits an app meant to stay running:

```bash
mkdir -p ~/.config/lxsession/LXDE-pi
[ -f ~/.config/lxsession/LXDE-pi/autostart ] || cp /etc/xdg/lxsession/LXDE-pi/autostart ~/.config/lxsession/LXDE-pi/autostart
echo '@/home/pi/tech/dist/main' >> ~/.config/lxsession/LXDE-pi/autostart
```

Reboot again and re-check with `pgrep -af dist/main`.

## 9b. Clean up the desktop (only the app icon, wallpaper stays)

The client only ever sees the fullscreen app, but this makes the desktop
underneath clean too, for whenever the app is escaped out of (F11).

Hides the Trash/Documents/mounted-drive icons pcmanfm shows by default,
without touching the wallpaper setting already in that file:

```bash
CONF=~/.config/pcmanfm/LXDE-pi/desktop-items-0.conf
mkdir -p "$(dirname "$CONF")"
touch "$CONF"
grep -q '^\[\*\]' "$CONF" || printf '[*]\n' >> "$CONF"

for key in show_documents show_trash show_mounts; do
    if grep -q "^${key}=" "$CONF"; then
        sed -i "s/^${key}=.*/${key}=0/" "$CONF"
    else
        sed -i "/^\[\*\]/a ${key}=0" "$CONF"
    fi
done

# Remove anything on the Desktop except the app launcher itself
find ~/Desktop -mindepth 1 ! -name 'production-app.desktop' -delete

# Apply without a reboot
pcmanfm --reconfigure 2>/dev/null || (killall pcmanfm; pcmanfm --desktop &)
```

Reboot to confirm: escaping the app with F11 shows a desktop with just the
wallpaper and the one app icon - no Trash, no other icons.

## 10. Updating an existing install

Use this when the Pi already has the app set up (steps 1-9 already done)
and you just need to pull in newer code changes.

```bash
cd ~/tech
# copy/pull the updated source files over the existing ones here
# (main.py, tech/Main.qml, etc.) - do NOT overwrite dist/config.json,
# it holds this Pi's tuned serial port

source <your-venv>/bin/activate
pyinstaller --clean --noconfirm main.spec
deactivate
```

`config.json` in the project root is only copied to `dist/config.json` once
(step 3) — if `dist/config.json` already exists on this Pi, leave it alone
so the serial port setting isn't lost.

Autostart (step 9) doesn't need to be redone — it launches
`~/tech/dist/main`, which the rebuild just replaced in place. Reboot to run
the updated app.

## 11. Error log

Every status/error message the app prints (GPIO init, serial connect/
disconnect, camera results, crashes) is written to:

```
~/tech/dist/logs/app.log
```

It auto-rotates at 2MB (keeps 3 backups: `app.log.1`, `app.log.2`,
`app.log.3`), so it's safe to leave running long-term. Check this file
first when something goes wrong and nobody was watching a terminal at the
time — e.g. after autostart/boot.

## 12. Speeding up the ~10s launch

Already done in the code (no action needed, just rebuild with step 10 to
pick these up):

- `main.py` sets `QT_QUICK_CONTROLS_STYLE=Basic` before the app starts -
  the lightest Qt Quick Controls style, skips the heavier default style's
  setup cost.

The rest of that 10s is Qt/PySide6 itself loading its shared libraries and
parsing the QML on the Pi 4's CPU - normal for this kind of app, but two
things on the hardware side make the biggest real difference if it's still
too slow:

- **Boot media**: an SD card is the most common bottleneck on a Pi 4. Moving
  the OS (or at least `~/tech`) to a USB SSD is usually the single biggest
  win for an app this size.
- **GPU acceleration**: confirm `/boot/firmware/config.txt` has
  `dtoverlay=vc4-kms-v3d`. Without it, Qt Quick falls back to software
  rendering, which is much slower to start and run. Check with:
  ```bash
  glxinfo | grep "OpenGL renderer"
  ```
  It should name the Pi's GPU (`V3D` / `VC4`), not `llvmpipe`.

## 13. Hide Raspberry Pi branding during boot

Kiosk mode (step 9) already skips the desktoip and login prompt, but the
Pi's own boot sequence still runs first - rainbow splash, kernel text, and
the Raspberry Pi logo - before the app takes over. This closes that gap so
the screen goes straight from black to the app.

**Turn off the rainbow splash screen:**

```bash
sudo raspi-config
```

`System Options` → `Splash Screen` → `No` (this sets `disable_splash=1` in
`/boot/firmware/config.txt`).

**Suppress kernel boot text and the console logo:**

```bash
sudo nano /boot/firmware/cmdline.txt
```

This is a single line - append to the end of it (don't add a newline):

```
quiet loglevel=0 logo.nologo vt.global_cursor_default=0 systemd.show_status=0
```

`systemd.show_status=0` is needed on top of `quiet`/`loglevel=0` - those
only silence kernel messages, not systemd's own `[ OK ] Started ...` service
status lines.

**If text is still visible after that**, it's a few lines that print before
the kernel even reads `cmdline.txt` - too early to suppress via boot
parameters. Cover it instead with a blank Plymouth splash (the graphical
boot layer that's supposed to hide exactly this, disabled a moment ago when
Splash Screen was turned off in raspi-config):

```bash
sudo mkdir -p /usr/share/plymouth/themes/blank
sudo tee /usr/share/plymouth/themes/blank/blank.plymouth > /dev/null <<'EOF'
[Plymouth Theme]
Name=Blank
Description=Solid black screen, no branding
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/blank
ScriptFile=/usr/share/plymouth/themes/blank/blank.script
EOF

sudo tee /usr/share/plymouth/themes/blank/blank.script > /dev/null <<'EOF'
Window.SetBackgroundTopColor(0, 0, 0);
Window.SetBackgroundBottomColor(0, 0, 0);
EOF

sudo plymouth-set-default-theme -R blank
```

`-R` rebuilds the initramfs so the theme is active from early boot, not
just after the desktop starts.

Then add `splash` back into `/boot/firmware/cmdline.txt` (same line as the
params above) - this is what tells Plymouth to render its theme instead of
falling through to raw text:

```
splash quiet loglevel=0 logo.nologo vt.global_cursor_default=0 systemd.show_status=0
```

Reboot: the screen should now go solid black from very early boot straight
through to the app, no exceptions.

**Change the hostname** (defaults to `raspberrypi`, which can surface in
network device lists, mDNS/`.local` discovery, or an SSH prompt if the
client ever gets a terminal):

```bash
sudo raspi-config
```

`System Options` → `Hostname` → set something client-neutral, e.g.
`station01`.

Reboot to confirm: screen should go black, then straight to the fullscreen
app - no rainbow screen, no scrolling boot text, no login prompt.

## 14. Hide the taskbar/panel itself (not just cover it)

Step 9's fullscreen only covers the panel while the app is running - escape
with F11 and it's back. This disables it outright so it never shows, even
when escaped out to the desktop.

```bash
# 1. Seed your personal autostart config from the system default (if you don't have one yet)
mkdir -p ~/.config/lxsession/LXDE-pi
[ -f ~/.config/lxsession/LXDE-pi/autostart ] || cp /etc/xdg/lxsession/LXDE-pi/autostart ~/.config/lxsession/LXDE-pi/autostart

# 2. Comment out the line that launches lxpanel
sed -i 's/^\(@lxpanel.*\)$/# \1/' ~/.config/lxsession/LXDE-pi/autostart

# 3. Reboot to apply
sudo reboot
```

After reboot, the taskbar/panel won't come back - even if you escape the
fullscreen app with F11, you'll just see the wallpaper (and desktop icons,
unless you've also done step 9b).

**To check it worked:**

```bash
pgrep -a lxpanel
```

No output means it's not running.

**To undo** (bring the panel back):

```bash
sed -i 's/^# \(@lxpanel.*\)$/\1/' ~/.config/lxsession/LXDE-pi/autostart
sudo reboot
```

**Trade-off:** the panel is also where the Raspberry Pi start menu lives, so
disabling it removes that as an admin way back in. Right-click-on-desktop
(via pcmanfm) and SSH still work for getting back in - confirm one of those
suits before relying on this.

## 15. Let the in-app Shutdown/Reboot buttons run without a password prompt

The Home screen's Shutdown/Reboot buttons call `sudo shutdown -h now` and
`sudo reboot` (see `backend.py`). The app has no terminal to type a sudo
password into, so without this step those two buttons do nothing except log
a permission error to `app.log`.

```bash
echo "$USER ALL=(ALL) NOPASSWD: /sbin/shutdown -h now, /sbin/reboot" | sudo tee /etc/sudoers.d/010-tech-power
sudo chmod 440 /etc/sudoers.d/010-tech-power
sudo visudo -c
```

`visudo -c` checks the new file's syntax before it takes effect - fix and
re-run if it reports an error. Scoped to exactly those two commands for this
user only, not a blanket sudo grant.

Test from the app (not a terminal, so the passwordless rule is actually what
runs it): tap Reboot, confirm the dialog, confirm the Pi reboots.
