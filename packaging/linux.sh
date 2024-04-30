#!/usr/bin/env bash

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
cp ../../res/icon.png dist/ArPiRobot-DriveStation
mv dist/ArPiRobot-DriveStation/ArPiRobot-DriveStation dist/ArPiRobot-DriveStation/AppRun
mkdir ../dist/
../appimagetool dist/ArPiRobot-DriveStation ../dist/ArPiRobot-DriveStation-Liunx-x64.AppImage
popd > /dev/null

################################################################################
# Cleanup
################################################################################

rm -rf linux/build/
rm -rf linux/dist/ArPiRobot-DriveStation/
rm -f appimagetool

popd > /dev/null
