@echo off

cd %~dp0

for  %%f in (".\src\rc_*.py") do (
    del %%f
)

setlocal enabledelayedexpansion
for  %%f in (".\res\*.qrc") do (
    set FILE_NAME=%%~nf
    set "message=[Compiling]: !FILE_NAME!.qrc ---> rc_!FILE_NAME!.py"
    echo !message!
    pyside2-rcc %%f -o "./src/rc_!FILE_NAME!.py"
)
endlocal