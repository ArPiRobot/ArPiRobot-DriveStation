## Packaging for macOS

Packaging for macOS uses pyinstaller to create the app. The app is then zipped for distribution. Since pyinstaller is used, this process must be performed on a mac. Furthermore, building native apps for an arm (Apple Silicon) mac is currently not supported (at time of writing pyinstaller has support but some dependency python packages do not have native arm build for macOS available).

TODO