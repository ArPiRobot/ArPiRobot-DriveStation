#!/usr/bin/env bash

DIR=$(realpath $(dirname $0))

pushd "$DIR" > /dev/null

if touch test.txt 2> /dev/null; then
    rm test.txt
else
    echo "Run as root (sudo)."
    exit 2
fi

if ! which python3 > /dev/null; then
    echo "Python 3 must be installed."
    exit 1
fi

if ! ping -c 1 google.com > /dev/null 2>&1; then
    echo "Internet access is required during install!"
    exit 1
fi

# Remove virtual env if one exists
rm -rf env/

# Create and setup python virtual environment
echo "Creating python environment"
if ! python3 -m venv env; then
    echo "Install pyton3 venv package."
    exit 3
fi
source env/bin/activate
python -m pip install -U -r requirements.txt > /dev/null
deactivate

# Desktop menu entry
xdg-desktop-menu uninstall io.github.arpirobot.DriveStation.desktop > /dev/null 2>&1
echo "Adding desktop menu entry"
cat << EOF > io.github.arpirobot.DriveStation.desktop
[Desktop Entry]
Version=1.1
Type=Application
Terminal=false
Name=ArPiRobot Drive Station
Comment=PC-side robot control software for ArPiRobot robots.
Icon=$DIR/icon.png
Exec=$DIR/start.sh
Categories=GNOME;Development;
StartupNotify=true
StartupWMClass=DriveStation
EOF
chmod 755 io.github.arpirobot.DriveStation.desktop
xdg-desktop-menu install --novendor io.github.arpirobot.DriveStation.desktop

# Fix directory permissions so non-root users can read it (and subdirectories)
chmod -R 755 "$DIR"

popd > /dev/null
