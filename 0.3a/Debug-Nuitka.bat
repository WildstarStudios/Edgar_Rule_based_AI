@echo off

REM ============================================================
REM Find Nuitka in virtual environment
REM ============================================================
set "VENV_DIR=C:\Users\aayde\Documents\GitHub\Edgar_Rule_based_AI\0.3a\.venv"
set "NUITKA=%VENV_DIR%\Scripts\nuitka"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"

REM Check if Nuitka exists, if not try python -m nuitka
if not exist "%NUITKA%.exe" (
    echo Nuitka executable not found, using python -m nuitka...
    set "NUITKA_CMD=%PYTHON% -m nuitka"
) else (
    set "NUITKA_CMD=%NUITKA%"
)

set PACKAGE_DIR=dist\package
set ICON_DIR=icon

REM ============================================================
REM Clean previous builds and create directories
REM ============================================================
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
if exist "*.build" rmdir /s /q "*.build"
if exist "*.dist" rmdir /s /q "*.dist"
if exist "dist" rmdir /s /q "dist"
del /q *.spec 2>nul

REM Create dist directory for initial builds
mkdir "dist"
mkdir "%PACKAGE_DIR%"

REM ============================================================
REM Shared BS4 imports (added to all apps using web queries)
REM ============================================================
set BS4_IMPORTS=^
  --include-package=bs4 ^
  --include-package=bs4.element ^
  --include-package=bs4.builder

REM ============================================================
REM Build chat.exe from main.py (GUI app) for 0.3a
REM ============================================================
echo Building chat-0.3a.exe...
%NUITKA_CMD% --onefile ^
  --output-dir="dist" ^
  --output-filename="chat-0.3a.exe" ^
  --windows-icon-from-ico="%ICON_DIR%\chat.ico" ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --include-package=configparser ^
  --include-package=core.modules.weather ^
  --include-package=core.modules.time ^
  --include-package=core.modules.search ^
  --include-package=fuzzywuzzy ^
  --include-package=fuzzywuzzy.process ^
  --include-package=fuzzywuzzy.fuzz ^
  --include-package=pytz ^
  --include-package=requests ^
  --include-package=Levenshtein ^
  %BS4_IMPORTS% ^
  --include-data-dir=resources=resources ^
  --include-data-dir=models=models ^
  --include-data-dir=core=core ^
  ui\main.py

if errorlevel 1 (
    echo ERROR: Failed to build chat-0.3a.exe
    pause
    exit /b 1
)

REM ============================================================
REM Build tty.exe from tty.py (Terminal app) for 0.3a
REM ============================================================
echo Building tty-0.3a.exe...
%NUITKA_CMD% --onefile ^
  --output-dir="dist" ^
  --output-filename="tty-0.3a.exe" ^
  --windows-icon-from-ico="%ICON_DIR%\tty.ico" ^
  --windows-console-mode=force ^
  --include-package=configparser ^
  --include-package=core.modules.weather ^
  --include-package=core.modules.time ^
  --include-package=core.modules.search ^
  --include-package=fuzzywuzzy ^
  --include-package=fuzzywuzzy.process ^
  --include-package=fuzzywuzzy.fuzz ^
  --include-package=pytz ^
  --include-package=requests ^
  --include-package=Levenshtein ^
  %BS4_IMPORTS% ^
  --include-data-dir=resources=resources ^
  --include-data-dir=models=models ^
  --include-data-dir=core=core ^
  ui\tty.py

if errorlevel 1 (
    echo ERROR: Failed to build tty-0.3a.exe
    pause
    exit /b 1
)

REM ============================================================
REM Build train.exe from training/train.py (GUI app) for 0.3a
REM ============================================================
echo Building train-0.3a.exe...
%NUITKA_CMD% --onefile ^
  --output-dir="dist" ^
  --output-filename="train-0.3a.exe" ^
  --windows-icon-from-ico="%ICON_DIR%\train.ico" ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --include-package=configparser ^
  --include-package=fuzzywuzzy ^
  --include-package=fuzzywuzzy.process ^
  --include-package=fuzzywuzzy.fuzz ^
  %BS4_IMPORTS% ^
  --include-data-dir=resources=resources ^
  --include-data-dir=models=models ^
  --include-data-dir=core=core ^
  --include-data-dir=training=training ^
  training\train.py

if errorlevel 1 (
    echo ERROR: Failed to build train-0.3a.exe
    pause
    exit /b 1
)

REM ============================================================
REM Build route-trainer.exe from route trainer.py for 0.3a
REM ============================================================
echo Building route-trainer-0.3a.exe...
%NUITKA_CMD% --onefile ^
  --output-dir="dist" ^
  --output-filename="route-trainer-0.3a.exe" ^
  --windows-icon-from-ico="%ICON_DIR%\route-trainer.ico" ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --include-package=fuzzywuzzy ^
  --include-package=fuzzywuzzy.process ^
  --include-package=fuzzywuzzy.fuzz ^
  %BS4_IMPORTS% ^
  --include-data-dir=resources=resources ^
  --include-data-dir=core=core ^
  "route trainer.py"

if errorlevel 1 (
    echo ERROR: Failed to build route-trainer-0.3a.exe
    pause
    exit /b 1
)

REM ============================================================
REM Build webui.exe from webui.py (Web interface app) for 0.3a
REM ============================================================
echo Building webui-0.3a.exe...
%NUITKA_CMD% --onefile ^
  --output-dir="dist" ^
  --output-filename="webui-0.3a.exe" ^
  --windows-icon-from-ico="%ICON_DIR%\webui.ico" ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --include-package=fuzzywuzzy ^
  --include-package=fuzzywuzzy.process ^
  --include-package=fuzzywuzzy.fuzz ^
  --include-package=pytz ^
  --include-package=requests ^
  --include-package=Levenshtein ^
  %BS4_IMPORTS% ^
  --include-data-dir=resources=resources ^
  --include-data-dir=models=models ^
  --include-data-dir=core=core ^
  --include-data-dir=webui=webui ^
  ui\webui.py

if errorlevel 1 (
    echo ERROR: Failed to build webui-0.3a.exe
    pause
    exit /b 1
)

REM ============================================================
REM Copy final executables and resources to package directory
REM ============================================================
echo Copying final executables to package directory...
copy "dist\chat-0.3a.exe" "%PACKAGE_DIR%\"
copy "dist\tty-0.3a.exe" "%PACKAGE_DIR%\"
copy "dist\train-0.3a.exe" "%PACKAGE_DIR%\"
copy "dist\route-trainer-0.3a.exe" "%PACKAGE_DIR%\"
copy "dist\webui-0.3a.exe" "%PACKAGE_DIR%\"

echo Copying resource files...
copy "config.cfg" "%PACKAGE_DIR%\"
xcopy "resources" "%PACKAGE_DIR%\resources\" /E /I /Y
xcopy "models" "%PACKAGE_DIR%\models\" /E /I /Y
xcopy "%ICON_DIR%" "%PACKAGE_DIR%\%ICON_DIR%\" /E /I /Y

REM ============================================================
REM Create README file for the distribution
REM ============================================================
echo Creating README...
(
echo Edgar AI Assistant v0.3a
echo ========================
echo.
echo Distribution Package
echo.
echo Included Files:
echo - chat-0.3a.exe      - Main Edgar AI application (GUI)
echo - tty-0.3a.exe       - Terminal/Command Line interface
echo - train-0.3a.exe     - Training application
echo - route-trainer-0.3a.exe - Routing configuration tool
echo - webui-0.3a.exe     - Web interface application
echo - config.cfg         - Configuration file (shared by all apps)
echo - resources\         - Routing configuration and resources
echo - models\            - AI model data
echo - icon\              - Application icons
echo.
echo Usage:
echo 1. Run chat-0.3a.exe to start the main AI assistant (GUI)
echo 2. Run tty-0.3a.exe to start the terminal interface
echo 3. Run train-0.3a.exe to train new AI models
echo 4. Run route-trainer-0.3a.exe to configure module routing
echo 5. Run webui-0.3a.exe to start the web interface
echo.
echo Note: config.cfg is shared by all applications
echo.
echo TTY Interface Features:
echo - Full terminal/command line interface
echo - Same AI engine and module routing as GUI
echo - Real-time text streaming
echo - All commands: stats, context, reset, models, modules, config, help
echo.
echo New Features in v0.3a:
echo - New search module (replaces DuckDuckGo search)
echo - Enhanced module routing system
echo - Improved text streaming
echo - Better error handling
echo - Custom application icons
echo.
echo System Requirements:
echo - Windows 10 or later
echo - Built with Nuitka for better performance
echo - Internet connection for weather and search modules
) > "%PACKAGE_DIR%\README.txt"

REM ============================================================
REM Clean up build artifacts (keep final dist\package only)
REM ============================================================
echo Cleaning up build artifacts...
if exist "build" rmdir /s /q "build"
if exist "*.build" rmdir /s /q "*.build"
if exist "*.dist" rmdir /s /q "*.dist"
del /q *.spec 2>nul

REM Clean the intermediate dist files but keep the package directory
if exist "dist\*.exe" del /q "dist\*.exe"
if exist "dist\*.pdb" del /q "dist\*.pdb"

REM ============================================================
REM Show completion message and open folder
REM ============================================================
echo.
echo ========================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Final distribution package is in: %PACKAGE_DIR%
echo.
echo Included executables:
dir /b "%PACKAGE_DIR%\*.exe"
echo.
echo Icons have been embedded in executables.
echo Config file is shared by all applications in the package directory.
echo.
echo Note: Built with Nuitka for improved performance and smaller size.
echo.
pause
echo Opening distribution folder...
explorer "%PACKAGE_DIR%"