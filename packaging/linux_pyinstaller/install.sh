#!/usr/bin/env bash

DIR=$(realpath $(dirname $0))

pushd "$DIR" > /dev/null

if touch test.txt; then
    rm test.txt
else
    echo "Run as root."
    exit 2
fi

# Desktop menu entry
xdg-desktop-menu uninstall ArPiRobot-DriveStation.desktop > /dev/null 2>&1
echo "Adding desktop menu entry"
printf "[Desktop Entry]\nVersion=1.1\nType=Application\nTerminal=false\nName=ArPiRobot Drive Station\nComment=PC-side robot control software for ArPiRobot robots.\nIcon=$DIR/icon.png\nExec=$DIR/ArPiRobot-DriveStation\nActions=\nCategories=Development;\nStartupNotify=true\nStartupWMClass=com-arpirobot-drivestation-DriveStation\n" > ArPiRobot-DriveStation.desktop
xdg-desktop-menu install --novendor ArPiRobot-DriveStation.desktop

popd > /dev/null
