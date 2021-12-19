#!/usr/bin/env bash

DIR=$(realpath $(dirname $0))

pushd "$DIR" > /dev/null

echo "Removing virtual environment"
rm -rf env/

echo "Removing pycache"
find src -type d -name __pycache__ -exec rm -r {} \; > /dev/null 2>&1

echo "Removing desktop menu entry"
xdg-desktop-menu uninstall ArPiRobot-DriveStation.desktop > /dev/null 2>&1
rm ArPiRobot-DriveStation.desktop

popd > /dev/null
