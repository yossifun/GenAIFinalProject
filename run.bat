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
		echo ERROR: GenAIFinalProject not found
        exit /b 1
	)
)

REM --- Path to virtual environment activate script ---
if not exist .venv (
	echo ERROR: Virtual environment not found
    exit /b 1
)

REM --- Activate environment ---
call .venv\Scripts\activate
echo Virtual environment activated.

REM --- Check for "clean" argument ---
if /i "%1"=="clean" (
    REM --- Run the cleanup script ---
    echo Running project cleanup...
    python clean_project.py

    REM --- Clear Streamlit cache ---
    echo Clearing Streamlit cache...
    streamlit cache clear
)


REM --- Kill Streamlit processes on default port 8501 ---
echo Checking for Streamlit sessions on port 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo Stopping Streamlit process PID %%a...
    taskkill /f /pid %%a >nul
)

REM --- Launch the Streamlit app ---
echo Launching the Streamlit app...
streamlit run "streamlit\streamlit_main.py"
