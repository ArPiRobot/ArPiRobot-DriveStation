#!/usr/bin/env bash

DIR=$(realpath $(dirname $0))

pushd "$DIR"

VERSION=`head -1 ../res/version.txt`

# Create build directory
mkdir ArPiRobot-DriveStation-$VERSION/
pushd ArPiRobot-DriveStation-$VERSION/

# Make sure qt resources and ui files are compiled
pushd ../..
if ! python compile.py; then
    echo "FAILED!!!!!!"
    exit 1
fi


# Copy files to package
popd
cp -r ../../src/ ./
cp ../../requirements.txt ./
cp -r ../../res/icon.png ./
cp ../linux_resources/* ./

# Remove pyinstaller from requirements.txt
sed -i "s/pyinstaller//g" requirements.txt

popd

# Package in tarball
mkdir -p dist
tar -zcvf dist/ArPiRobot-DriveStation-$VERSION.tar.gz ./ArPiRobot-DriveStation-$VERSION/

rm -r ArPiRobot-DriveStation-$VERSION/

popd