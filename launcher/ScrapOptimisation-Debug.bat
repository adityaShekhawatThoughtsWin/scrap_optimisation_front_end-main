@echo off
setlocal
cd /d "%~dp0.."
set "APP_ROOT=%CD%"
set "LAUNCHER_VERBOSE=1"
echo ScrapOptimisation launcher (debug)
echo Install folder: %APP_ROOT%
echo Log files: %APP_ROOT%\config\launcher.log
echo            %APP_ROOT%\config\solver.log
echo            %APP_ROOT%\config\backend.log
echo.
if exist "%CD%\node.exe" (
  "%CD%\node.exe" "%CD%\launcher\launch.mjs"
) else (
  node "%CD%\launcher\launch.mjs"
)
echo.
echo Exit code: %ERRORLEVEL%
pause
endlocal