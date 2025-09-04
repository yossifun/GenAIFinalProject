@echo off
REM Run install.bat first
call "%~dp0install.bat"

REM If install succeeded, open a new console window for run.bat and close this one
if %errorlevel%==0 (
    echo Installation successful.
    echo Launching run.bat in a new window with arguments: %*
    echo Closing this window in 3 seconds...
    timeout /t 3 /nobreak >nul
    start cmd /k call "%~dp0run.bat" %*
    exit
) else (
    echo Installation failed with error code %errorlevel%.
    pause
)
