@echo off
setlocal enabledelayedexpansion

REM Check if the file cia-helper.py exists, if not download it
if not exist cia-helper.py (
    echo Download cia-helper.py...
    curl -o cia-helper.py https://raw.githubusercontent.com/ghost-land/3dserver/main/CiaMassConvertor/cia-helper.py
)

REM Check whether the file cia-helper.py has been downloaded successfully
if not exist cia-helper.py (
    echo Error: Unable to download cia-helper.py. Check your Internet connection and try again.
    pause
    exit /b
)

REM Gets the current date and time for the log file name
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
    set "date=%%a-%%b-%%c"
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set "time=%%a-%%b"
)
set "timestamp=!date!_!time!"

REM Check if the log folder exists, if not, create it
if not exist log (
    mkdir log
)

REM Check if CIAs folder exists, if not, create it
if not exist CIAs (
    mkdir CIAs
)

REM Create a complete log file with date and time in its name
set "full_log_file=log\FullLog_!timestamp!.log"
echo Traitement commencé à : %timestamp% > %full_log_file%
echo Traitement commencé à : %timestamp%

REM Loop through all .cia files in the current directory
for %%F in (*.cia) do (
    REM Create a log file for each .cia file
    set "log_file=log\%%~nF_!timestamp!.log"
    echo Traitement de %%F à : !time! > !log_file!
    echo Traitement de %%F à : !time!

    REM Execute the Python command for each .cia file
    python cia-helper.py "%%F" >> !log_file! 2>&1
    
    REM Move the processed .cia file to the CIAs folder
    move "%%F" CIAs\
)

echo Processing complete. The .cia files have been moved to the CIAs folder. See full log for details.
echo Processing complete. The .cia files have been moved to the CIAs folder. See full log for details. >> %full_log_file%
pause
