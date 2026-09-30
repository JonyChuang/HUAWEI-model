@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PYTHONUTF8=1
set "LOG=%~dp0c8_run_log.txt"
set "PYEXE="
echo searching python... > "%LOG%"

rem 1) conda environments list (base env is usually the first line)
if exist "%USERPROFILE%\.conda\environments.txt" (
  for /f "usebackq delims=" %%L in ("%USERPROFILE%\.conda\environments.txt") do (
    if not defined PYEXE if exist "%%L\python.exe" set "PYEXE=%%L\python.exe"
  )
)

rem 2) Windows registry (python.org / anaconda registered installs)
if not defined PYEXE (
  for /f "delims=" %%K in ('reg query HKCU\Software\Python /s /v ExecutablePath 2^>nul ^| find /i "ExecutablePath"') do (
    if not defined PYEXE for /f "tokens=2*" %%A in ("%%K") do if exist "%%B" set "PYEXE=%%B"
  )
)
if not defined PYEXE (
  for /f "delims=" %%K in ('reg query HKLM\Software\Python /s /v ExecutablePath 2^>nul ^| find /i "ExecutablePath"') do (
    if not defined PYEXE for /f "tokens=2*" %%A in ("%%K") do if exist "%%B" set "PYEXE=%%B"
  )
)

rem 3) common locations
for %%R in ("%USERPROFILE%" "%LOCALAPPDATA%" "%LOCALAPPDATA%\Programs" "%ProgramData%" "C:" "D:" "E:" "F:" "C:\Program Files" "D:\Program Files") do (
  if not defined PYEXE for /d %%P in ("%%~R\*") do (
    if not defined PYEXE if exist "%%P\python.exe" (
      echo %%P | find /i "WindowsApps" >nul
      if errorlevel 1 set "PYEXE=%%P\python.exe"
    )
  )
)
if not defined PYEXE for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if not defined PYEXE if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"
if not defined PYEXE for /d %%D in ("%USERPROFILE%\.conda\envs\*") do if not defined PYEXE if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"

rem 4) PATH (skip the Microsoft Store stub)
if not defined PYEXE (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYEXE (
      echo %%P | find /i "WindowsApps" >nul
      if errorlevel 1 set "PYEXE=%%P"
    )
  )
)
if not defined PYEXE (
  where py >nul 2>nul && set "PYEXE=py"
)
if not defined PYEXE (
  echo [ERROR] python.exe not found >> "%LOG%"
  echo [ERROR] python.exe not found
  timeout /t 30
  exit /b 1
)
echo Using python: %PYEXE%
echo Using python: %PYEXE% >> "%LOG%"
"%PYEXE%" "%~dp0aggregate_detailed_results.py" >> "%LOG%" 2>&1
echo EXIT CODE %errorlevel% >> "%LOG%"
type "%LOG%"
echo.
echo DONE. This window closes in 30 s.
timeout /t 30
