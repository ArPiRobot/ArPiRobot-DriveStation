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


**Linux**:

TODO