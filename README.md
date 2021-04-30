# ArPiRobot-Drive Station

## Building and Running

First, make sure python3 is installed. On windows, the executable name may be `python` not `python3`.


**Create a Virtual Environment**
```sh
python3 -m venv --system-site-packages env
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
./compile-all

# Only UI
./compile-ui

# Only Resources
./compile-res
```

**Running**

TODO

## Packaging

Packaging GUI python apps is fairly simple using pyinstaller or other similar tools, however there is one major limitation: no cross building support. This means that each update to the app would require building on each supported OS. This is very inconvenient. 

To address this issue, the app itself is designed as a python module. There is a single python script (`launcher.py`) outside of the `app` module. This script is converted into a platform specific executable (containing python interpreter and required libraries). The code for the `app` module can then be manually copied into the package.

This means that the platform specific code builds using pyinstaller will never need to change, unless dependencies change. Using this configuration, auto-detecting dependencies is not possible. See `launcher.spec` for more details. The packages built with the `launcher` spec file will be referred to as template packages.

### Package Using Existing Templates

Download the existing template zip files for each platform. Extract each to its own directory. Copy the app source folder into the extracted template directories. Then, either re-zip the templates (now they contain a specific version of the app code) or use another tool to generate an installer. For macOS, zipping the .app folder is sufficient. For windows, it is recommended to use Inno Setup to generate an installer using the provided `win_installer.iss` script.

### Building the Templates

***This requires access to Windows, macOS, and Linux systems.***