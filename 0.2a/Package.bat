@echo off
title Edgar AI Build System
color 0A

REM Path to PyInstaller if not in PATH
set pyinstallerPath=%USERPROFILE%\AppData\Roaming\Python\Python312\Scripts\pyinstaller.exe

REM Path to Python DLL (adjust if Python installed elsewhere)
set pythonDLL=%LOCALAPPDATA%\Programs\Python\Python312\python312.dll

echo ========================================
echo     Edgar AI Application Builder
echo ========================================
echo.
echo Choose build system:
echo   1 - Nuitka (Optimized, smaller, uses MinGW)
echo   2 - PyInstaller (Simpler, may be larger)
echo.

set /p builder="Enter choice (1 or 2): "

if "%builder%"=="1" (
    set buildTool=nuitka
    set toolName=Nuitka
) else (
    set buildTool=pyinstaller
    set toolName=PyInstaller
)

echo.
echo Choose build type:
echo   1 - Single EXE (Onefile, may trigger antivirus)
echo   2 - Folder Build (Safer, separate files)
echo.

set /p buildType="Enter choice (1 or 2): "

if "%buildType%"=="1" (
    set onefileFlag=--onefile
    set buildMode=Single EXE
) else (
    set onefileFlag=
    set buildMode=Folder Build
)

echo.
echo Choose build configuration:
echo   1 - Release (Optimized, smaller, no debug info)
echo   2 - Debug (Slower, includes debug symbols)
echo.

set /p buildConfig="Enter choice (1 or 2): "

if "%buildConfig%"=="1" (
    set configFlags=--lto=yes --remove-output
    set configMode=Release
) else (
    set configFlags=--debug --show-scons
    set configMode=Debug
)

echo.
echo ========================================
echo Building Edgar AI Applications...
echo Tool: %toolName%
echo Mode: %buildMode%
echo Configuration: %configMode%
echo ========================================
echo.

echo Cleaning previous builds...
if exist build rmdir /s /q build

if "%builder%"=="1" (
    REM ========================
    REM === Build with Nuitka ===
    REM ========================
    echo Building with Nuitka...

    REM ===== Build AI Engine GUI =====
    python -m nuitka ^
     --standalone %onefileFlag% ^
     --windows-console-mode=disable ^
     --output-dir=build ^
     --output-filename=Edgar_AI_GUI.exe ^
     --include-package=core ^
     --enable-plugin=tk-inter ^
     --mingw64 ^
     %configFlags% ^
     main.py

    REM ===== Build Training GUI =====
    python -m nuitka ^
     --standalone %onefileFlag% ^
     --windows-console-mode=disable ^
     --output-dir=build ^
     --output-filename=Edgar_Training.exe ^
     --enable-plugin=tk-inter ^
     --include-package=training ^
     --mingw64 ^
     %configFlags% ^
     training/train.py

) else (
    REM ==========================
    REM === Build with PyInstaller ===
    REM ==========================
    echo Building with PyInstaller...

    if "%buildType%"=="1" (
        set pyFlags=--onefile
        set addDLL=
    ) else (
        set pyFlags=
        REM Include python DLL for folder builds
        set addDLL=--add-binary "%pythonDLL%;."
    )

    if "%buildConfig%"=="1" (
        set pyConfig=--clean --noconfirm
    ) else (
        set pyConfig=--debug=all
    )

    REM Use full path to PyInstaller
    "%pyinstallerPath%" ^
     %pyFlags% %pyConfig% %addDLL% ^
     --windowed ^
     --name Edgar_AI_GUI ^
     --distpath build ^
     main.py

    "%pyinstallerPath%" ^
     %pyFlags% %pyConfig% %addDLL% ^
     --windowed ^
     --name Edgar_Training ^
     --distpath build ^
     training/train.py
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo Executables are in the 'build' folder:
echo   - Edgar_AI_GUI.exe
echo   - Edgar_Training.exe
echo Tool: %toolName%
echo Mode: %buildMode%
echo Configuration: %configMode%
echo ========================================
pause
