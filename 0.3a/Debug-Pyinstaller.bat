@echo off
set PYINSTALLER=C:\Users\aayde\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe

REM ============================================================
REM Build chat.exe from main.py (GUI app)
REM ============================================================
"%PYINSTALLER%" --onefile --name chat-0.3a main.py

REM ============================================================
REM Build train.exe from training/train.py (GUI app)
REM ============================================================
"%PYINSTALLER%" --onefile --name train-0.3a training\train.py

REM ============================================================
REM Clean up build artifacts
REM ============================================================
rmdir /s /q build
del /q *.spec

REM ============================================================
REM Open File Explorer in the dist folder where EXEs are stored
REM ============================================================
explorer dist
pause