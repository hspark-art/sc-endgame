@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Endgame - Register winners doc auto-import

echo.
echo  ==================================================
echo    Auto-import Google Doc winners -^> winners sheet
echo  ==================================================
echo.
echo   What this does
echo     - Every evening 22:00 to 24:00 (every 30 min)
echo       it reads the Google Doc and adds any NEW
echo       winners to the admin winners sheet.
echo     - Already-listed winners are skipped (safe).
echo     - Runs hidden, no console window.
echo     - This PC must be ON during 22:00-24:00.
echo.
pause

schtasks /Query /TN "SC Endgame Winners Doc" >nul 2>nul
if not errorlevel 1 (
  echo  [i] Task already exists. Replacing it...
  schtasks /Delete /TN "SC Endgame Winners Doc" /F >nul 2>nul
)

echo.
echo  [1/2] Creating task (daily 22:00, repeat every 30 min for 2 hours)...
echo.

schtasks /Create /TN "SC Endgame Winners Doc" /SC DAILY /ST 22:00 /RI 30 /DU 0002:00 /F /TR "wscript.exe //B \"%~dp0tools\run-gdoc-hidden.vbs\""

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
  "try { $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew; Set-ScheduledTask -TaskName 'SC Endgame Winners Doc' -Settings $s | Out-Null; Write-Host '      OK' } catch { Write-Host '      skipped (not critical)' }"

echo.
echo  ---- registered task ----
schtasks /Query /TN "SC Endgame Winners Doc" /FO LIST | findstr /C:"TaskName" /C:"Status" /C:"Next Run"

echo.
echo   Done. The winners sheet will auto-update every evening 22:00-24:00.
echo   This PC needs to be on during that window.
echo   To run it once right now, use  10_winners-doc.bat  (10_당첨자문서반영.bat).
echo.
pause
exit /b 0
