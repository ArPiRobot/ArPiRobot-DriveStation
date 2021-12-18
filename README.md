# ArPiRobot-Drive Station

## Installation

Downloads are available on the releases page.

### Windows

For windows, an installer `exe` is provided. Download and run this installer.

### macOS

For macOS, a zipped app is provided. Download the zip, double click it to extract and drag the resulting `.app` file to your `Applications` folder.

### Linux

**Ubuntu & Other Debian Based Distros:** Download and install the `deb` package.

**Other**: Install python 3, pip, and venv using your distribution's package manager or by building from source. Download and extract the `tar.gz` package. Extract it somewhere on your system and run the included `install.sh` script. This script will create a python environment for the program and a desktop menu entry for it. The included `uninstall.sh` script removes these things and should be run before deleting the directory the program is stored in.


## Building and Running

First, make sure python3 is installed. On windows, the executable name may be `python` not `python3`.


### Create a Virtual Environment
```sh
python3 -m venv env
```

### Activate the environment

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

### Install Required Libraries

```sh
python -m pip install -r requirements.txt
```

### Compiling UI and Resource Files

```sh
python compile.py
```

### Running

```sh
python src/main.py
```
