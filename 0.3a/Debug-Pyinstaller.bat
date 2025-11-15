@echo off
set PYINSTALLER=C:\Users\aayde\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe
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
  main.py

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
REM Build visualizer.exe from Rule_Viewer\Visulizer.py for 0.3a
REM ============================================================
echo Building visualizer-0.3a.exe...
"%PYINSTALLER%" --onefile ^
  --distpath "%PACKAGE_DIR%" ^
  --name "visualizer-0.3a" ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --add-data "core;core" ^
  --hidden-import "fuzzywuzzy" ^
  --hidden-import "fuzzywuzzy.process" ^
  --hidden-import "fuzzywuzzy.fuzz" ^
  "Rule_Viewer\Visulizer.py"

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
echo - chat-0.3a.exe      - Main Edgar AI application
echo - train-0.3a.exe     - Training application
echo - route-trainer-0.3a.exe - Routing configuration tool
echo - visualizer-0.3a.exe - Rule visualization tool
echo - config.cfg         - Configuration file
echo - resources\         - Routing configuration and resources
echo - models\           - AI model data
echo.
echo Usage:
echo 1. Run chat-0.3a.exe to start the main AI assistant
echo 2. Run train-0.3a.exe to train new AI models
echo 3. Run route-trainer-0.3a.exe to configure module routing
echo 4. Run visualizer-0.3a.exe to visualize rule structures
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
echo Opening distribution folder...
explorer "%PACKAGE_DIR%"

pause