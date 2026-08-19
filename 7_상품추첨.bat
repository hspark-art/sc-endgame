chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
cd /d "%~dp0"

rem Start prize picker control program (SOOP live chat)
rem Usage: double-click for live, or "7_PrizePicker.bat demo" for practice

if "%1"=="demo" (
  python tools\prizewatch.py --demo
) else (
  python tools\prizewatch.py
)
pause
