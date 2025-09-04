@echo off
setlocal enabledelayedexpansion

REM --- Get directory of this script ---
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM --- Check if we're already inside GenAIFinalProject ---
for %%F in ("%SCRIPT_DIR%") do set CURRENT_DIR_NAME=%%~nxF

if /i "%CURRENT_DIR_NAME%"=="GenAIFinalProject" (
    echo Running inside GenAIFinalProject directory.
    cd /d "%SCRIPT_DIR%"
) else (
    if exist "%SCRIPT_DIR%\GenAIFinalProject" (
        echo Found GenAIFinalProject folder. Entering it...
        cd /d "%SCRIPT_DIR%\GenAIFinalProject"
    ) else (
        echo GenAIFinalProject not found. Cloning...
        cd /d "%SCRIPT_DIR%"
        git clone https://github.com/LiamNomad/GenAIFinalProject
        cd GenAIFinalProject
    )
)

REM --- Prepare secrets directory ---
if not exist secrets mkdir secrets
echo Looking for secret files...
set MISSING_SECRETS=0

REM --- Handle each secret file independently ---
set "FILES=openai_api_key.txt openai_fine_tune_model.txt"

for %%F in (%FILES%) do call :HandleSecret "%%F"

REM --- Warn if any defaults were used ---
if %MISSING_SECRETS%==1 (
    echo.
    echo WARNING: One or more secret files are missing; placeholders were created instead.
    echo Please update the secret files in the secrets folder before running the project.
    echo Then run the project with this command: streamlit run streamlit/streamlit_main.py
    exit /b 1
)

REM --- Create virtual environment ---
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists. Skipping creation.
)

REM --- Activate environment ---
call .venv\Scripts\activate
echo Virtual environment activated.

REM --- Install dependencies ---
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Dependencies installed.
echo Setup complete. You can now run the project with run.bat
exit /b 0

REM --- Subroutine to handle each secret ---
:HandleSecret
set "F=%~1"
set "DEST=secrets\%F%"

if exist "%DEST%" (
    echo %F% already exists in secrets. Skipping.
    goto :eof
)

if exist "%SCRIPT_DIR%\secrets\%F%" (
    copy "%SCRIPT_DIR%\secrets\%F%" "%DEST%" >nul
    echo Copied %F% from script's secrets folder.
    goto :eof
)

if exist "%SCRIPT_DIR%\%F%" (
    copy "%SCRIPT_DIR%\%F%" "%DEST%" >nul
    echo Copied %F% from script directory.
    goto :eof
)

REM Create default secret file
if "%F%"=="openai_api_key.txt" (
    echo Replace this with your Open AI API key (sk-XXXX) > "%DEST%"
) else if "%F%"=="openai_fine_tune_model.txt" (
    echo Replace this with your Open AI fine tuned model id > "%DEST%"
)

echo Created default %F%
set MISSING_SECRETS=1
goto :eof
