@echo off
setlocal
cd /d "%~dp0"
title EF+ - Plataforma de Educacion Fisica
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)
echo ===========================================
echo EF+ PLATAFORMA DE EDUCACION FISICA
echo ===========================================
echo.
echo Primera configuracion (si ya existe, no se repetira):
%PY% app.py init
if errorlevel 1 (
 echo Ocurrio un error durante la configuracion. Revisa Python.
 pause
 exit /b 1
)
echo.
echo Abre esta direccion en tu navegador:
echo http://127.0.0.1:8000
echo.
echo Para detener el programa presiona Ctrl+C.
%PY% app.py
pause
