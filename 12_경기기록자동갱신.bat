@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Endgame - Register match records auto-update

echo.
echo  ==================================================
echo    Auto-update match records (Google Sheet -^> site)
echo  ==================================================
echo.
echo   What this does
echo     - 4 times a day (21:30, 01:30, 05:30, 09:30) it reads
echo       the Google Sheet, and if there are new matches it
echo       rebuilds and deploys the site to pubgin.com/endgame.
echo     - If nothing changed, it uploads nothing (safe).
echo     - If records SHRANK (sheet accident) update.py stops
echo       by itself and deploys nothing.
echo     - Runs hidden, no console window.
echo     - This PC must be ON at those times.
echo.
pause

schtasks /Query /TN "SC Endgame Records Update" >nul 2>nul
if not errorlevel 1 (
  echo  [i] Task already exists. Replacing it...
  schtasks /Delete /TN "SC Endgame Records Update" /F >nul 2>nul
)

echo.
echo  [1/2] Creating task (daily 21:30, repeat every 4 hours for 12 hours)...
echo.

schtasks /Create /TN "SC Endgame Records Update" /SC DAILY /ST 21:30 /RI 240 /DU 0012:00 /F /TR "wscript.exe //B \"%~dp0tools\run-update-hidden.vbs\""

if errorlevel 1 (
  echo.
  echo  [X] Could not create the task.
  echo      Right click this file and pick "Run as administrator",
  echo      then try again.
  echo.
  pause
  exit /b 1
)

echo.
echo  [2/2] Adjusting power settings...
echo.

powershell -NoProfile -Command ^
  "try { $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew; Set-ScheduledTask -TaskName 'SC Endgame Records Update' -Settings $s | Out-Null; Write-Host '      OK' } catch { Write-Host '      skipped (not critical)' }"

echo.
echo  ---- registered task ----
schtasks /Query /TN "SC Endgame Records Update" /FO LIST | findstr /C:"TaskName" /C:"Status" /C:"Next Run"

echo.
echo   Done. Match records will auto-update 4 times a day.
echo   This PC needs to be on at those times.
echo   To run it once right now:  python tools\update.py
echo.
pause
exit /b 0
