@echo off
setlocal
cd /d "%~dp0.."
set "APP_ROOT=%CD%"
if exist "%CD%\node.exe" (
  "%CD%\node.exe" "%CD%\launcher\launch.mjs"
) else (
  node "%CD%\launcher\launch.mjs"
)
endlocal