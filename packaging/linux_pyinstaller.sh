#!/usr/bin/env bash

################################################################################
# Functions
################################################################################

function fail(){
    echo "**Failed!**"
    exit 1
}

function confirm() {
    read -r -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}


################################################################################
# Setup
################################################################################

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
rm -rf build/ || fail
rm -rf dist/ArPiRobot-DriveStation || fail
pyinstaller linux_pyinstaller/linux.spec || fail
cp ../res/icon.png ./dist/ArPiRobot-DriveStation
cp ../COPYING ./dist/ArPiRobot-DriveStation
cp linux_pyinstaller/install.sh ./dist/ArPiRobot-DriveStation
cp linux_pyinstaller/uninstall.sh ./dist/ArPiRobot-DriveStation


################################################################################
# Tarball package
################################################################################
if confirm "Create tar.gz package?"; then
    echo "**Creating tar.gz package**"
    pushd dist > /dev/null
    tar -zcvf ArPiRobot-DriveStation-${VERSION}.tar.gz ./ArPiRobot-DriveStation/ || fail
    popd > /dev/null
fi


################################################################################
# Deb package
################################################################################
if confirm "Create deb package?"; then
    echo "**Creating deb package**"

    pushd dist > /dev/null

    # Setup folder structure
    mkdir arpirobot-drivestation_$VERSION
    mkdir arpirobot-drivestation_$VERSION/DEBIAN
    mkdir arpirobot-drivestation_$VERSION/opt
    mkdir arpirobot-drivestation_$VERSION/opt/ArPiRobot-DriveStation

    # Copy files
    cp -r ./ArPiRobot-DriveStation/* ./arpirobot-drivestation_$VERSION/opt/ArPiRobot-DriveStation/
    cp ../linux_pyinstaller/deb_control ./arpirobot-drivestation_$VERSION/DEBIAN/control
    cp ../linux_pyinstaller/deb_prerm ./arpirobot-drivestation_$VERSION/DEBIAN/prerm
    cp ../linux_pyinstaller/deb_postinst ./arpirobot-drivestation_$VERSION/DEBIAN/postinst
    chmod 755 ./arpirobot-drivestation_$VERSION/DEBIAN/*

    # Generate package
    dpkg-deb --build arpirobot-drivestation_$VERSION || fail

    rm -rf ./arpirobot-drivestation_$VERSION/

    popd > /dev/null
fi


################################################################################
# Cleanup
################################################################################

rm -rf build/
rm -rf dist/ArPiRobot-DriveStation/

popd > /dev/null