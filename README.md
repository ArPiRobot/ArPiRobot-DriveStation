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

**Packaging**

TODO