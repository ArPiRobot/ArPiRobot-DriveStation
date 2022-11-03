#!/usr/bin/env bash

# Work in linux_appimage directory
DIR=$(realpath $(dirname "$0"))
pushd "$DIR/linux_appimage"> /dev/null

# Remove previously extracted resources and appimages
rm -f ArPirobot-DriveStation.appimage
rm -rf AppDir squashfs-root

# Download python appimage if one does not already exist
if [[ ! -f python.appimage ]]; then
    wget $(python3 "$DIR/linux_appimage/get_download.py") -O python.appimage
fi

# Download appimagetool appimage if one does not already exist
if [[ ! -f appimagetool.appimage ]]; then
    wget https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage -O appimagetool.appimage
fi

# Extract base python appimage
chmod +x python.appimage
./python.appimage --appimage-extract
mv squashfs-root AppDir

# Replace desktop and appdata with correct ones for this app
rm AppDir/*.desktop
cp arpirobot-drivestation.desktop AppDir/
cp ../../res/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/arpirobot-drivestation.png
ln -s usr/share/icons/hicolor/256x256/apps/arpirobot-drivestation.png AppDir/arpirobot-drivestation.png
cp arpirobot-drivestation.appdata.xml AppDir/

# Install requirements, compile resources, and copy sources to appimage
AppDir/AppRun -m pip install -U -r ../../requirements.txt --ignore-installed
PATH=AppDir/usr/bin:$PATH AppDir/AppRun ../../compile.py
cp -r ../../src AppDir/src

# Change apprun script
mv AppDir/AppRun AppDir/AppRunOrig
cp start.sh AppDir/AppRun
chmod +x AppDir/AppRun

# Remove old icon
rm AppDir/python.png
rm AppDir/usr/share/icons/hicolor/256x256/apps/python.png

# Create appimage file
chmod +x ./appimagetool.appimage
mkdir -p ../dist
ARCH=x86_64 ./appimagetool.appimage --no-appstream AppDir ../dist/ArPirobot-DriveStation-Linux-x64.AppImage

popd > /dev/null

