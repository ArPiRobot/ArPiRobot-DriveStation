#!/usr/bin/env bash

DIR=$(realpath $(dirname "$0"))
pushd "$DIR" > /dev/null
./AppRunOrig src/main.py -name ArPiRobot-DriveStation
popd > /dev/null

