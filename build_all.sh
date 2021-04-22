#!/bin/bash


################################################################################
# Check for dependencies
################################################################################

# CMake - build system
# VCPKG - library manager
# MinGW - Windows Cross Compiler
# OSXCross - macOS Cross Compiler
# GNU Toolchain - Linux (Native) Compiler

if [-z $(which cmake)]
    echo "cmake not found."
    exit 1
fi

if [-z $(which vcpkg)]
    echo "vcpkg not found."
    exit 1
fi

if [-z $(which i686-w64-mingw32-g++)]
    echo "MinGW-w64 (x86) not found."
    exit 1
fi

if [-z $(which x86_64-w64-mingw32-g++)]
    echo "MinGW-w64 (x64) not found."
    exit 1
fi

if [-z $(which osxcross-conf)]
    echo "osxcross not found."
    exit 1
fi

if [-z $(which g++)]
    echo "Native C++ compiler not found."
    exit 1
fi


################################################################################
# Install Libraries for all Platforms
################################################################################


################################################################################
# Build for all Platforms
################################################################################
# -DVCPKG_CHAINLOAD_TOOLCHAIN_FILE=my_toolchain.cmake
