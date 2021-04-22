cmake_minimum_required(VERSION 3.4)

# Support versions in VCPKG manifest
# If vcpkg is not used, this will be ignored
if(${CMAKE_TOOLCHAIN_FILE} MATCHES "vcpkg.cmake$")
    set(VCPKG_FEATURE_FLAGS "versions")
endif()


project(ArPiRobot-DriveStation CXX)
set (CMAKE_CXX_STANDARD 11)

# Enable automatic handling of resource and UI files
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# If using VCPKG, set correct uic and rcc paths
# If not using VCPKG, these should be in the path
if(${CMAKE_TOOLCHAIN_FILE} MATCHES "vcpkg.cmake$")
    set(AUTORCC_EXECUTABLE ${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/tools/qt5/bin/rcc)
    set(AUTOUIC_EXECUTABLE ${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/tools/qt5/bin/uic)
endif()

################################################################################
# Compiler / Platform Specific Settings
################################################################################

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_BINARY_DIR}/bin)

# MSVC Settings
if(MSVC)
    # Ignore MSVC when it complains that the "secure" variants of functions are not used
    set(-D_CRT_SECURE_NO_WARNINGS)
    
    # Enable multiprocessor builds with Visual Studio/MSVC
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")

    # Add resource file
    set(OTHER_SRC ${OTHER_SRC} ${PROJECT_SOURCE_DIR}/res/win_res.rc)

    # Use the manifest as a source file so it is merged with Visual Studio's generated manifest 
    # Not supported with mingw so workaround in win_res_mingw.rc is used
    set(OTHER_SRC ${OTHER_SRC} ${PROJECT_SOURCE_DIR}/res/winmanifest.manifest)

endif()

# MinGW Settings
if(MINGW)
    # Statically link GNU toolchain libs
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static")

    # Add resource file
    set(OTHER_SRC ${OTHER_SRC} ${PROJECT_SOURCE_DIR}/res/win_res_mingw.rc)
endif()

if(APPLE)
    # This should include all resources to be included in the bundle
    set(MAC_RES ${MAC_RES} ${PROJECT_SOURCE_DIR}/icons/icon.icns)
    set(OTHER_SRC ${OTHER_SRC} ${MAC_RES})
endif()

# Setup defines for version in windows resource file
if(WIN32)
    file(STRINGS ${PROJECT_SOURCE_DIR}/res/version.txt VER_STR)
    string(REPLACE "." ";" VERSION_LIST ${VER_STR})
    string(REPLACE "\n" "" VER_STR ${VER_STR})
    string(REPLACE "\r" "" VER_STR ${VER_STR})

    list(GET VERSION_LIST 0 VER_MAJ)
    list(GET VERSION_LIST 1 VER_MIN)
    list(GET VERSION_LIST 2 VER_PAT)

    
    set_source_files_properties(${MY_RC_FILE} COMPILE_DEFINITIONS "RC_DEF")

    add_definitions(-DWIN_RC_VER_MAJ=${VER_MAJ})
    add_definitions(-DWIN_RC_VER_MIN=${VER_MIN})
    add_definitions(-DWIN_RC_VER_PAT=${VER_PAT})
    add_definitions(-DWIN_RC_VER_STR=${VER_STR})
endif()



################################################################################
# Find Dependencies
################################################################################
find_package(Qt5Core CONFIG REQUIRED)
find_package(Qt5Gui CONFIG REQUIRED)
find_package(SDL2 CONFIG REQUIRED)
find_package(asio CONFIG REQUIRED)


################################################################################
# Targets
################################################################################

file(GLOB_RECURSE SOURCES
    "src/*.cpp"
    "src/*.c"
    "res/*.qrc"
    "ui/*.ui"
)

add_executable(ArPiRobot-DriveStation WIN32 MACOSX_BUNDLE ${SOURCES} ${OTHER_SRC})
target_compile_definitions(ArPiRobot-DriveStation PUBLIC WIN_RC_VER_MAJ=1)
target_include_directories(ArPiRobot-DriveStation PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(ArPiRobot-DriveStation Qt5::Core Qt5::Gui SDL2::SDL2 asio asio::asio)


################################################################################
# CPack
################################################################################
# TODO
