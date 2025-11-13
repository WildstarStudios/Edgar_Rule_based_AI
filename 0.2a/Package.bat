@echo off
echo Building Edgar AI Applications with Nuitka...

echo Cleaning previous builds...
if exist build rmdir /s /q build

echo Building AI Engine GUI (main.py)...
python -m nuitka --standalone --onefile --windows-console-mode=disable --output-dir=build --output-filename=Edgar_AI_GUI.exe --include-package=core --enable-plugin=tk-inter --mingw64 main.py

echo Building Training GUI (train.py)...
python -m nuitka --standalone --onefile --windows-console-mode=disable --output-dir=build --output-filename=Edgar_Training.exe --enable-plugin=tk-inter --include-package=training --mingw64 training/train.py

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo Executables are in the 'build' folder:
echo   - Edgar_AI_GUI.exe
echo   - Edgar_Training.exe
echo Note: These use MinGW64 and don't require VC++ Redistributable
echo ========================================
pause