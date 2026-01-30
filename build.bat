@echo off
echo Building Clipboard Image Viewer...
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

REM Build the executable
echo Creating executable...
pyinstaller --onefile --windowed --name "ClipboardImageViewer" --icon=icon.ico main.py 2>nul

REM If no icon.ico exists, build without icon
if errorlevel 1 (
    echo Building without custom icon...
    pyinstaller --onefile --windowed --name "ClipboardImageViewer" main.py
)

echo.
if exist "dist\ClipboardImageViewer.exe" (
    echo Build successful!
    echo Executable location: dist\ClipboardImageViewer.exe
) else (
    echo Build may have failed. Check the output above for errors.
)

echo.
pause
