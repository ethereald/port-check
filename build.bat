@echo off
REM Build portcheck.exe using PyInstaller

setlocal enabledelayedexpansion

REM Check if pyinstaller is available
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller is not installed or not in PATH
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

echo Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__\" rmdir /s /q "__pycache__"

echo Building portcheck.exe with PyInstaller...
cmd /c pyinstaller --clean --onefile --console portcheck.py > "%TEMP%\build.log" 2>&1

set build_result=%errorlevel%

if %build_result% equ 0 (
    echo.
    echo Build successful!
    echo Executable created: dist\portcheck.exe
    
    if exist "dist\portcheck.exe" (
        wmic process where name="pyinstaller*" | findstr "name" | del /q "%TEMP%\build.log" 2>nul
        pause
    ) else (
        copy /b /a nul >nul 2>&1
        echo.
        type "%TEMP%\build.log"
        pause
    )
) else (
    echo.
    echo Build failed! Check log: %TEMP%\build.log
    type "%TEMP%\build.log"
    pause
)
