## Packaging for Linux

Packaging for linux can be done one of two ways. The first way uses pyinstaller to create a binary. The second is by bundling the sources and using an installation script to setup a virtual environment.

The first method creates a program that has no system dependencies (aside from c runtime libraries), but is a large package. The second method creates a small package, but relies on the system having python3 installed.

Either method results in a package that can be compressed as a gzipped tarball or optionally turned into a distribution specific package (deb, rpm, etc).

## PyInstaller Method

*To ensure compatibility with the most possible distributions, it is recommended to perform this build on an older linux distro (older glibc). Ubuntu 14.04 or 16.04 is recommended, however a newer version of python3 will likely be needed (either build from source or use unofficial ppa) as Pyside6 does not support anything older than python 3.6 (at time of writing). Since pyinstaller is used, this must be performed on a linux system.

```shell
source env/bin/activate
cd packaging
./linux_pyinstaller.sh
```

## Source Method
