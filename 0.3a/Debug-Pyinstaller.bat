@echo off

set PYINSTALLER=C:\Users\aayde\Documents\GitHub\Edgar_Rule_based_AI\0.3a\.venv\Scripts\pyinstaller.exe
set PACKAGE_DIR=dist\package

REM ============================================================
REM Clean previous builds and create package directory
REM ============================================================
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
del /q *.spec 2>nul
mkdir "%PACKAGE_DIR%"

REM ============================================================
REM Build chat.exe from main.py (GUI app) for 0.3a
REM ============================================================
echo Building chat-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "chat-0.3a" ^
  --add-data "config.cfg;." ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --hidden-import "core.modules.weather" ^
  --hidden-import "core.modules.time" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "ddgs" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  main.py

REM ============================================================
REM Build tty.exe from tty.py (Terminal app) for 0.3a
REM ============================================================
echo Building tty-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "tty-0.3a" ^
  --console ^
  --add-data "config.cfg;." ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --hidden-import "core.modules.weather" ^
  --hidden-import "core.modules.time" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "ddgs" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  tty.py

REM ============================================================
REM Build train.exe from training/train.py (GUI app) for 0.3a
REM ============================================================
echo Building train-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "train-0.3a" ^
  --add-data "config.cfg;." ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --add-data "training;training" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  training\train.py

REM ============================================================
REM Build route-trainer.exe from route trainer.py for 0.3a
REM ============================================================
echo Building route-trainer-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "route-trainer-0.3a" ^
  --add-data "resources;resources" ^
  --add-data "core;core" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  "route trainer.py"

REM ============================================================
REM Build webui.exe from webui.py (Web interface app) for 0.3a
REM ============================================================
echo Building webui-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "webui-0.3a" ^
  --add-data "config.cfg;." ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --add-data "webui;webui" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "ddgs" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  webui.py

REM ============================================================
REM Copy additional resource files to package directory
REM ============================================================
echo Copying resource files...
copy "config.cfg" "%PACKAGE_DIR%\"
xcopy "resources" "%PACKAGE_DIR%\resources\" /E /I /Y
xcopy "models" "%PACKAGE_DIR%\models\" /E /I /Y

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
echo - config.cfg         - Configuration file
echo - resources\         - Routing configuration and resources
echo - models\           - AI model data
echo.
echo Usage:
echo 1. Run chat-0.3a.exe to start the main AI assistant (GUI)
echo 2. Run tty-0.3a.exe to start the terminal interface
echo 3. Run train-0.3a.exe to train new AI models
echo 4. Run route-trainer-0.3a.exe to configure module routing
echo 5. Run webui-0.3a.exe to start the web interface
echo.
echo TTY Interface Features:
echo - Full terminal/command line interface
echo - Same AI engine and module routing as GUI
echo - Real-time text streaming
echo - All commands: stats, context, reset, models, modules, config, help
echo.
echo System Requirements:
echo - Windows 10 or later
echo - Python 3.12 (included in executable)
echo - Internet connection for weather and time modules
) > "%PACKAGE_DIR%\README.txt"

REM ============================================================
REM Clean up build artifacts (keep package directory)
REM ============================================================
echo Cleaning up build artifacts...
rmdir /s /q build
del /q *.spec

REM ============================================================
REM Show completion message and open folder
REM ============================================================
echo.
echo ========================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Executables and resources are in: %PACKAGE_DIR%
echo.
pause
echo Opening distribution folder...
explorer "%PACKAGE_DIR%"