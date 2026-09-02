@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Checking Python...
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% --version >nul 2>nul
if errorlevel 1 goto :python_error

echo [2/4] Preparing the isolated environment...
if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :build_error
)

echo [3/4] Installing build dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-dev.txt
if errorlevel 1 goto :build_error

echo [4/4] Building EduSysInfo.exe...
".venv\Scripts\python.exe" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name EduSysInfo ^
    main.py
if errorlevel 1 goto :build_error

if not exist "dist\EduSysInfo.exe" goto :build_error

echo.
echo Build completed successfully.
echo Executable: %cd%\dist\EduSysInfo.exe
pause
exit /b 0

:python_error
echo.
echo Python 3 was not found.
echo Install it from https://www.python.org/downloads/windows/ and try again.
pause
exit /b 1

:build_error
echo.
echo The build failed. Review the messages above.
pause
exit /b 1
