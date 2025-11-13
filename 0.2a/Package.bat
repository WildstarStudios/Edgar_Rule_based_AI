@echo off
title Edgar AI Build System
color 0A

:MAIN_MENU
cls
echo ========================================
echo     Edgar AI Application Builder
echo ========================================
echo.
echo Choose build system:
echo   1 - Nuitka (Optimized, smaller)
echo   2 - PyInstaller (Simpler)
echo   3 - Exit
echo.

set /p builder="Enter choice (1-3): "
if "%builder%"=="3" exit /b 0
if "%builder%" neq "1" if "%builder%" neq "2" goto MAIN_MENU

if "%builder%"=="1" (
    set toolName=Nuitka
    set buildTool=nuitka
) else (
    set toolName=PyInstaller
    set buildTool=pyinstaller
)

REM Check if builder is available
if "%builder%"=="1" (
    python -m nuitka --version >nul 2>&1
    if errorlevel 1 (
        set needNuitka=1
        echo Nuitka not found - will install if confirmed
    ) else (
        set needNuitka=0
        echo Nuitka is available
    )
) else (
    pyinstaller --version >nul 2>&1
    if errorlevel 1 (
        set needPyInstaller=1
        echo PyInstaller not found - will install if confirmed
    ) else (
        set needPyInstaller=0
        echo PyInstaller is available
    )
)

:BUILD_TYPE
echo.
echo Build Type:
echo   1 - Single EXE (one file)
echo   2 - Folder Build (multiple files)
echo.

set /p buildType="Enter choice (1-2): "
if "%buildType%"=="1" (
    set onefileFlag=--onefile
    set buildMode=Single EXE
) else if "%buildType%"=="2" (
    set onefileFlag=
    set buildMode=Folder Build
) else (
    goto BUILD_TYPE
)

:COMPILER_SETUP
if "%builder%"=="2" goto CONFIRM_SCREEN

:COMPILER_MENU
cls
echo ========================================
echo        Compiler Selection
echo ========================================
echo.
echo Choose compiler for Nuitka:
echo   1 - MinGW64 (Recommended)
echo   2 - MSVC
echo.

set /p compiler="Enter choice (1-2): "
if "%compiler%"=="1" (
    set compilerFlag=--mingw64
    set compilerName=MinGW64
    
    REM Check if MinGW is available
    where gcc >nul 2>&1
    if errorlevel 1 (
        echo.
        echo MinGW64 not found. It is required for Nuitka.
        echo.
        echo Please download and install MinGW64 from:
        echo https://github.com/brechtsanders/winlibs_mingw/releases/latest
        echo.
        echo What would you like to do?
        echo   1 - Open download page and continue
        echo   2 - Choose different compiler
        echo.
        set /p choice="Enter choice (1-2): "
        if "%choice%"=="1" (
            start https://github.com/brechtsanders/winlibs_mingw/releases/latest
            echo.
            echo After installation, make sure to add MinGW to your PATH.
            echo.
            pause
        )
        goto COMPILER_MENU
    ) else (
        echo MinGW64 is available.
        goto COMPILER_SELECTED
    )
) else if "%compiler%"=="2" (
    set compilerFlag=
    set compilerName=MSVC
    
    REM Check if MSVC is available - loop until installed or user switches
    :CHECK_MSVC
    where cl >nul 2>&1
    if errorlevel 1 (
        echo.
        echo MSVC not found. Visual Studio Build Tools required.
	start https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
        echo.
        echo What would you like to do?
        echo   1 - Open download page and test again
        echo   2 - Choose different compiler
        echo.
        set /p choice="Enter choice (1-2): "
        if "%choice%"=="1" (
            start https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
            echo.
            echo Download page opened!
            echo.
            echo Please install Visual Studio Build Tools with C++ support:
            echo 1. Make sure to install the "C++ build tools" workload
            echo 2. You may need to restart your command prompt
            echo 3. Or run from "Developer Command Prompt for VS 2022"
            echo.
            echo Press any key to test MSVC installation...
            pause >nul
            goto CHECK_MSVC
        ) else if "%choice%"=="2" (
            goto COMPILER_MENU
        ) else (
            goto CHECK_MSVC
        )
    ) else (
        echo MSVC is available.
        goto COMPILER_SELECTED
    )
) else (
    goto COMPILER_MENU
)

:COMPILER_SELECTED
echo.
echo Compiler selected: %compilerName%
goto CONFIRM_SCREEN

:CONFIRM_SCREEN
cls
echo ========================================
echo        Build Configuration
echo ========================================
echo.
echo Builder:      %toolName%
echo Build Type:   %buildMode%
if "%builder%"=="1" echo Compiler:     %compilerName%
echo.

REM Show installation requirements
set installSteps=
if "%builder%"=="1" (
    if "%needNuitka%"=="1" (
        echo [INSTALL] Nuitka
        set installSteps=1
    )
    if "%compiler%"=="1" (
        where gcc >nul 2>&1
        if errorlevel 1 (
            echo [INSTALL] MinGW64 Compiler
            set installSteps=1
        )
    ) else if "%compiler%"=="2" (
        where cl >nul 2>&1
        if errorlevel 1 (
            echo [INSTALL] Visual Studio Build Tools
            set installSteps=1
        )
    )
) else (
    if "%needPyInstaller%"=="1" (
        echo [INSTALL] PyInstaller
        set installSteps=1
    )
)

if exist requirements.txt (
    echo [INSTALL] Python requirements from requirements.txt:
    set installSteps=1
    REM Read and display the requirements
    for /f "usebackq delims=" %%i in ("requirements.txt") do (
        echo   - %%i
    )
) else (
    echo No requirements.txt found.
)

if "%installSteps%"=="1" (
    echo.
    echo The following will be installed/configured:
) else (
    echo No additional installations needed.
)

echo.
set /p confirm="Proceed with build? (Y/N): "
if /i "%confirm%" neq "Y" goto MAIN_MENU

:INSTALLATION_PHASE
echo.
echo ========================================
echo        Installation Phase
echo ========================================
echo.

REM Install Nuitka if needed
if "%builder%"=="1" (
    if "%needNuitka%"=="1" (
        echo Installing Nuitka...
        pip install nuitka
        echo.
    )
)

REM Install PyInstaller if needed
if "%builder%"=="2" (
    if "%needPyInstaller%"=="1" (
        echo Installing PyInstaller...
        pip install pyinstaller
        echo.
    )
)

REM Install requirements if present
if exist requirements.txt (
    echo Installing Python requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Warning: Some requirements may have failed to install.
    )
    echo.
)

:BUILD_PHASE
echo ========================================
echo          Building Applications
echo ========================================
echo.

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec 2>nul

set buildSuccess=1

if "%builder%"=="1" (
    echo Building with Nuitka (%compilerName%)...
    
    echo Building Edgar_AI_GUI.exe...
    python -m nuitka --standalone %onefileFlag% --windows-console-mode=disable --output-dir=build --output-filename=Edgar_AI_GUI.exe --include-package=core --enable-plugin=tk-inter %compilerFlag% main.py
    if errorlevel 1 set buildSuccess=0
    
    if "%buildSuccess%"=="1" (
        echo Building Edgar_Training.exe...
        python -m nuitka --standalone %onefileFlag% --windows-console-mode=disable --output-dir=build --output-filename=Edgar_Training.exe --enable-plugin=tk-inter --include-package=training %compilerFlag% training/train.py
        if errorlevel 1 set buildSuccess=0
    )
) else (
    echo Building with PyInstaller...
    
    if "%buildType%"=="1" (
        set pyFlags=--onefile
    ) else (
        set pyFlags=
    )
    
    echo Building Edgar_AI_GUI.exe...
    pyinstaller %pyFlags% --windowed --name Edgar_AI_GUI --distpath build main.py
    if errorlevel 1 set buildSuccess=0
    
    if "%buildSuccess%"=="1" (
        echo Building Edgar_Training.exe...
        pyinstaller %pyFlags% --windowed --name Edgar_Training --distpath build training/train.py
        if errorlevel 1 set buildSuccess=0
    )
)

echo.
echo ========================================
if "%buildSuccess%"=="1" (
    echo BUILD COMPLETE!
    echo.
    echo Executables in 'build' folder:
    echo   - Edgar_AI_GUI.exe
    echo   - Edgar_Training.exe
) else (
    echo BUILD FAILED!
    echo Check errors above.
)
echo ========================================
echo.

pause
goto MAIN_MENU