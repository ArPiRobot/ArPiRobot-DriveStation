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

BUILD_TAR="ask"
BUILD_DEB="ask"
BUILD_RUN="ask"
PYTHON="python"

while true; do
  case "$1" in
    --tar ) BUILD_TAR="$2"; shift 2 ;;
    --deb ) BUILD_DEB="$2"; shift 2 ;;
    --python ) PYTHON="$2"; shift 2 ;;
    --run ) BUILD_RUN="$2"; shift 2 ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

DIR=$(realpath $(dirname $0))
pushd "$DIR" > /dev/null

VERSION=`head -1 ../res/version.txt`


################################################################################
# Compile UI and resources
################################################################################
echo "**Compiling QT Resources and UI**"
pushd ../ > /dev/null
"$PYTHON" compile.py || fail
popd > /dev/null


################################################################################
# Create folder structure
################################################################################
echo "**Creating Package Structure**"
rm -rf build/ || fail
rm -rf dist/ArPiRobot-DriveStation || fail

mkdir -p ./dist/ArPiRobot-DriveStation/

cp -r ../src/ ./dist/ArPiRobot-DriveStation/
cp ../requirements.txt ./dist/ArPiRobot-DriveStation/
cp -r ../res/icon.png ./dist/ArPiRobot-DriveStation/
cp ../COPYING ./dist/ArPiRobot-DriveStation
cp ../COPYING.LESSER ./dist/ArPiRobot-DriveStation
cp linux_source/install.sh ./dist/ArPiRobot-DriveStation
cp linux_source/uninstall.sh ./dist/ArPiRobot-DriveStation
cp linux_source/start.sh ./dist/ArPiRobot-DriveStation

# Remove pyinstaller from requirements.txt
sed -i "s/pyinstaller.*//g" ./dist/ArPiRobot-DriveStation/requirements.txt

################################################################################
# Tarball package
################################################################################
if [ "$BUILD_TAR" == "ask" ]; then
    if confirm "Create tar.gz package?"; then
        BUILD_TAR="yes"
    fi
fi
if [ "$BUILD_TAR" == "yes" ]; then
    echo "**Creating tar.gz package**"
    pushd dist > /dev/null
    tar -zcvf ArPiRobot-DriveStation-Linux-Any.tar.gz ArPiRobot-DriveStation/ || fail
    popd > /dev/null
fi


################################################################################
# Self-extracting package (.run)
################################################################################
if [ "$BUILD_RUN" == "ask" ]; then
    if confirm "Create self extracting .run package?"; then
        BUILD_RUN="yes"
    fi
fi
if [ "$BUILD_RUN" == "yes" ]; then
    echo "**Creating .run package**"
    wget https://github.com/megastep/makeself/releases/download/release-2.5.0/makeself-2.5.0.run
    chmod +x ./makeself-2.5.0.run
    ./makeself-2.5.0.run
    pushd dist > /dev/null
    ../makeself-2.5.0/makeself.sh --target /opt/ArPiRobot-DriveStation/ --needroot --gzip ArPiRobot-DriveStation ArPiRobot-DriveStation.run "ArPiRobot Drive Station Installer" ./install.sh
    popd > /dev/null
fi


################################################################################
# Deb package
################################################################################
if [ "$BUILD_DEB" == "ask" ]; then
    if confirm "Create deb package?"; then
        BUILD_DEB="yes"
    fi
fi
if [ "$BUILD_DEB" == "yes" ]; then
    echo "**Creating deb package**"

    pushd dist > /dev/null

    # Setup folder structure
    mkdir arpirobot-drivestation_$VERSION
    mkdir arpirobot-drivestation_$VERSION/DEBIAN
    mkdir arpirobot-drivestation_$VERSION/opt
    mkdir arpirobot-drivestation_$VERSION/opt/ArPiRobot-DriveStation
    mkdir -p arpirobot-drivestation_$VERSION/usr/share/doc/arpirobot-drivestation/
    mkdir -p arpirobot-drivestation_$VERSION/usr/share/metainfo/

    # Copy files
    cp ../linux_source/arpirobot-drivestation.appdata.xml ./arpirobot-drivestation_$VERSION/usr/share/metainfo/
    cp ./ArPiRobot-DriveStation/COPYING ./arpirobot-drivestation_$VERSION/usr/share/doc/arpirobot-drivestation/copyright
    cp -r ./ArPiRobot-DriveStation/* ./arpirobot-drivestation_$VERSION/opt/ArPiRobot-DriveStation/
    cp ../linux_source/deb_control ./arpirobot-drivestation_$VERSION/DEBIAN/control
    cp ../linux_source/deb_prerm ./arpirobot-drivestation_$VERSION/DEBIAN/prerm
    cp ../linux_source/deb_postinst ./arpirobot-drivestation_$VERSION/DEBIAN/postinst
    chmod 755 ./arpirobot-drivestation_$VERSION/DEBIAN/*

    # Generate package
    dpkg-deb --build arpirobot-drivestation_$VERSION || fail
    mv arpirobot-drivestation_$VERSION.deb ArPiRobot-DriveStation-Ubuntu-Any.deb

    rm -rf ./arpirobot-drivestation_$VERSION/

    popd > /dev/null
fi


################################################################################
# Cleanup
################################################################################

rm -rf build/
rm -rf dist/ArPiRobot-DriveStation/

popd > /dev/null