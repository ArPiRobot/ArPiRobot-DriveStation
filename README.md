# ArPiRobot-Drive Station

## Building

### Required Tools
- Cmake
- VCPKG (optional, but recommended)
- Visual Studio (if using VCPKG on Windows)
- A C++ Toolchain

### Dependencies
- Qt5
- ASIO
- SDL2

Install with vcpkg

```sh
vcpkg install asio sdl2 qt5-base --triplet=TRIPLET
```

Common triplets:
- Windows MSVC (x64): `x64-windows`
- Windows MSVC (x86): `x86-windows`
- Windows MinGW (x64): `x64-mingw-dynamic`
- Windows MinGW (x86): `x86-mingw-dynamic`
- macOS (x64): `x64-osx-dyanmic`
- Linux (x64): `x64-linux`


### Build using VCPKG for Libraries

*Note: You will need to change the vcpkg path to match where you installed vcpkg.*

#### Windows x86 (MSVC)

```powershell
cmake .. `
    -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake" `
    -DVCPKG_TARGET_TRIPLET=x86-windows `
    -A Win32
cmake --build . --config Release
```

#### Windows x64 (MSVC)

```powershell
cmake .. `
    -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake" `
    -DVCPKG_TARGET_TRIPLET=x64-windows `
    -A x64
cmake --build . --config Release
```

#### macOS (x64)

```sh
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE="~/vcpkg/scripts/buildsystems/vcpkg.cmake" \
    -DVCPKG_TARGET_TRIPLET=x64-osx-dynamic \
    -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

#### Linux (x64)

```sh
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE="~/vcpkg/scripts/buildsystems/vcpkg.cmake" \
    -DVCPKG_TARGET_TRIPLET=x64-linux \
    -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

#### Cross Compilation
- See `build_all.sh` for examples. This can be done by using `-DVCPKG_CHAINLOAD_TOOLCHAIN_FILE=my_toolchain.cmake` to specify a cmake toolchain file for the cross compiler.

- If using Linux (including WSL) you can use the `build_all.sh` script to build for
    - Windows x86
    - Windows x64
    - macOS x64
    - Linux x64
- This requires that minGW-w64 and osxcross are installed, as long as a native linux compiler, cmake, and vcpkg (must be in the path).

### Build without VCPKG

- This can be done as a normal CMake build. Make sure all dependencies are installed in a way that CMake's `find_package` can locate them.
- Generally, this is difficult unless using Linux, but even then this is not recommended as incompatible library versions may be used.