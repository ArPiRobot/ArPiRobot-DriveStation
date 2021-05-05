# Packaging

## Using Existing Templates

TODO

## Creating Templates

#### Why Templates

PyInstaller and other tools do not support cross building. Therefore, any change to the application would require rebuilding the application on *all* supported OSes. This is not ideal and complicates development, therefore an alternative approach is used. Since bundling a portable python distribution and all required packages is infeasible for all platforms&ast;, pyinstaller is used to generate a launcher executable. This launcher wraps a python script that imports the `app` module's main script, thus running the actual application. The app module is configured to **not** be included in the executable, so that it can be copied to the package folder later. Thus, it is possible to update the code for the drive station application **without** rebuilding the package for each platform. These platform specific packages for the launcher missing the `app` module are referred to as templates. When a new version of the drive station is to be packaged, the templates can simply be extracted and the `app` module copied into the package directory. The templates will only need to be rebuilt (requiring access to a machine running each supported OS) if the app's dependencies change.

&ast;An embeddable python distribution exists for Windows, however installing packages such as PySide is complicated. In addition, including the entire package for PySide is quite large and includes many binaries that are only needed for development, no to run the application. As such, a tool such as pyinstaller that determines only the required dependencies is useful.


#### Windows Template (x86)
- 64-bit only as PySide6 does not support 32-bit windows

#### macOS Template (x64)
- Currently x64 only. No ARM support is possible as I do not have access to recent mac hardware to build the template on.

#### Generic Linux Template (x64)
TODO
