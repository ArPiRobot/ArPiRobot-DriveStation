#!/usr/bin/env bash

set -e

################################################################################
# Setup
################################################################################

function fail(){
    echo "**Failed!**"
    exit 1
}


DIR=$(realpath $(dirname $0))
pushd "$DIR" > /dev/null

VERSION=`head -1 ../res/version.txt`


################################################################################
# Compile UI and resources
################################################################################
echo "**Compiling QT Resources and UI**"
pushd ../ > /dev/null
python compile.py || fail
popd > /dev/null


################################################################################
# Create pyinstaller binary
################################################################################
echo "**Creating PyInstaller Binary**"
rm -rf linux/build/ || fail
rm -rf linux/dist/ArPiRobot-DriveStation/ || fail
cd linux/
pyinstaller linux.spec || fail
cd ..


################################################################################
# Create AppImage
################################################################################
echo "**Creating AppImage**"
wget https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage -O appimagetool
chmod +x ./appimagetool
pushd linux/ > /dev/null
cp io.github.arpirobot.DriveStation.desktop dist/ArPiRobot-DriveStation
cp io.github.arpirobot.DriveStation.appdata.xml dist/ArPiRobot-DriveStation
mkdir -p dist/ArPiRobot-DriveStation/usr/share/icons/hicolor/256x256/apps/
cp ../../res/icon.png dist/ArPiRobot-DriveStation/usr/share/icons/hicolor/256x256/apps/arpirobot-drivestation.png
ln -s ./usr/share/icons/hicolor/256x256/apps/arpirobot-drivestation.png dist/ArPiRobot-DriveStation/arpirobot-drivestation.png
mv dist/ArPiRobot-DriveStation/ArPiRobot-DriveStation dist/ArPiRobot-DriveStation/AppRun
mkdir -p ../dist/
dd if=/dev/zero bs=1 count=3 seek=8 conv=notrunc of=../appimagetool
../appimagetool --appimage-extract-and-run dist/ArPiRobot-DriveStation ../dist/ArPiRobot-DriveStation-Liunx-x64.AppImage
popd > /dev/null

################################################################################
# Cleanup
################################################################################

rm -rf linux/build/
rm -rf linux/dist/ArPiRobot-DriveStation/
rm -f appimagetool

popd > /dev/null