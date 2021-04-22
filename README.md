# ArPiRobot-Drive Station

## Building

### Requirements
- Cmake
- VCPKG (optional, but recommended)
- Visual Studio (if using VCPKG on Windows)

### Build using VCPKG for Libraries

*Note: You will need to change the vcpkg path to match where you installed vcpkg.*

#### Windows x86 (MSVC)

```powershell
cmake .. `
    -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake" `
    -DVCPKG_TARGET_TRIPLET=x86-windows `
    -A Win32
```

#### Windows x64 (MSVC)

```powershell
cmake .. `
    -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake" `
    -DVCPKG_TARGET_TRIPLET=x64-windows `
    -A x64
```

#### macOS (x64)

```sh
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE="~/vcpkg/scripts/buildsystems/vcpkg.cmake" \
    -DVCPKG_TARGET_TRIPLET=x64-osx-dynamic \
```

#### Linux (x64)

```sh
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE="~/vcpkg/scripts/buildsystems/vcpkg.cmake" \
    -DVCPKG_TARGET_TRIPLET=x64-linux \
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