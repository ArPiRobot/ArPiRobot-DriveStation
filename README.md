# ArPiRobot-Drive Station

## Building and Running

First, make sure python3 is installed. On windows, the executable name may be `python` not `python3`.


**Create a Virtual Environment**
```sh
python3 -m venv env
```

**Activate the environment**

- On Windows (powershell)
    ```sh
    .\env\Scripts\Activate.Ps1
    ```

- On Windows (cmd)
    ```sh
    env\Scripts\activate.bat
    ```

- On Linux or macOS (or Git Bash in Windows)
    ```sh
    source env/bin/activate
    ```

**Install Required Libraries**
```sh
python -m pip install -r requirements.txt
```

**Compiling UI and Resource Files**

```sh
# Both UI and Resources
python compile.py
```

**Running**

```sh
python src/main.py
```


## Packaging

*NOTE: It is only supported to build a package for the same OS as you are using.*

**Changing Version Number**:

```sh
python change-version.py NEW_VERSION
```

*Inno Setup must be installed to create installer.*

**Windows**:

```shell
cd packaging
pyinstaller windows.spec
C:/"Program Files (x86)"/"Inno Setup 6"/Compil32.exe /cc win_installer.iss
```

**macOS**:

```shell
cd packaging
pyinstaller macos.spec
cd dist
VERSION=`head -1 ../../res/version.txt`
zip -r ArPiRobot-DriveStation-$VERSION.app.zip ArPiRobot-DriveStation.app
```


**Linux (PyInstaller)**:

*Not recommended as binary size is large and compatibility across distributions is hard. It is best to do this build on a older distribution to maximize compatibility. This produces a standalone executable and bundles python with the program and its dependencies (including QT). No dependencies on system packages exist (aside from C runtime libraries that every distro should have).*

```shell
cd packaging
pyinstaller linux.spec
cd dist
VERSION=`head -1 ../../res/version.txt`
tar -zcvf ArPiRobot-DriveStation-$VERSION.tar.gz ArPiRobot-DriveStation
```

**Linux (Generic Package)**:

*This method will bundle the source code with a script to install the program. This script will create a python environment for this program and install required libraries. This is used as a temporary measure as most distributions do not yet (at time of writing this) include QT6 packages. As such, it is necessary to install dependencies using pip. The install script requires that python be installed using the distribution's package manager.*

```shell
cd packaging
./linux_generic.sh
```


**Linux (Debian Package)**:

*This method is recommended for Debian based distributions (ex Ubuntu). This will create a deb package that includes the source and other assets contained in the generic package, however, by packaging in a deb package, dependencies can be specified and will be managed when installing the package.*

```shell
# TODO: Cannot do yet. Ubuntu 21.04/21.10 does not have QT6 / PySide6 packages.
```
