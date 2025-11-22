@echo off

set PYINSTALLER=C:\Users\aayde\Documents\GitHub\Edgar_Rule_based_AI\0.3a\.venv\Scripts\pyinstaller.exe
set PACKAGE_DIR=dist\package
set ICON_DIR=icon

REM ============================================================
REM Clean previous builds and create package directory
REM ============================================================
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
del /q *.spec 2>nul
mkdir "%PACKAGE_DIR%"

REM ============================================================
REM Shared BS4 hidden imports (added to all apps using web queries)
REM ============================================================
set BS4_IMPORTS=^
  --hidden-import "beautifulsoup4" ^
  --hidden-import "bs4" ^
  --hidden-import "bs4.element" ^
  --hidden-import "bs4.builder" ^
  --hidden-import "bs4.builder._htmlparser"

REM ============================================================
REM Build chat.exe from main.py (GUI app) for 0.3a
REM ============================================================
echo Building chat-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "chat-0.3a" ^
  --icon "%ICON_DIR%\chat.ico" ^
  --hidden-import "configparser" ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --hidden-import "core.modules.weather" ^
  --hidden-import "core.modules.time" ^
  --hidden-import "core.modules.search" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  %BS4_IMPORTS% ^
  ui\main.py

REM ============================================================
REM Build tty.exe from tty.py (Terminal app) for 0.3a
REM ============================================================
echo Building tty-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "tty-0.3a" ^
  --icon "%ICON_DIR%\tty.ico" ^
  --console ^
  --hidden-import "configparser" ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --hidden-import "core.modules.weather" ^
  --hidden-import "core.modules.time" ^
  --hidden-import "core.modules.search" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  %BS4_IMPORTS% ^
  ui\tty.py

REM ============================================================
REM Build train.exe from training/train.py (GUI app) for 0.3a
REM ============================================================
echo Building train-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "train-0.3a" ^
  --icon "%ICON_DIR%\train.ico" ^
  --hidden-import "configparser" ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --add-data "training;training" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  %BS4_IMPORTS% ^
  training\train.py

REM ============================================================
REM Build route-trainer.exe from route trainer.py for 0.3a
REM ============================================================
echo Building route-trainer-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "route-trainer-0.3a" ^
  --icon "%ICON_DIR%\route-trainer.ico" ^
  --add-data "resources;resources" ^
  --add-data "core;core" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  %BS4_IMPORTS% ^
  "route trainer.py"

REM ============================================================
REM Build webui.exe from webui.py (Web interface app) for 0.3a
REM ============================================================
echo Building webui-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "webui-0.3a" ^
  --icon "%ICON_DIR%\webui.ico" ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --add-data "webui;webui" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  --hidden-import "pytz" ^
  --hidden-import "requests" ^
  --hidden-import "Levenshtein" ^
  --hidden-import "Levenshtein.levenshtein_cpp" ^
  %BS4_IMPORTS% ^
  ui\webui.py

REM ============================================================
REM Copy additional resource files to package directory
REM ============================================================
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
echo - Python 3.12 (included in executable)
echo - Internet connection for weather and search modules
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
echo Icons have been embedded in executables and copied to icon folder.
echo Config file is shared by all applications in the package directory.
echo.
pause
echo Opening distribution folder...
explorer "%PACKAGE_DIR%"