@echo off

cd %~dp0

for  %%f in (".\app\ui_*.py") do (
    del %%f
)

setlocal enabledelayedexpansion
for  %%f in (".\ui\*.ui") do (
    set FILE_NAME=%%~nf
    set "message=[Compiling]: !FILE_NAME!.ui ---> ui_!FILE_NAME!.py"
    echo !message!
    pyside2-uic %%f -o "./app/ui_!FILE_NAME!.py"
)
endlocal