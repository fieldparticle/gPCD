@echo off
setlocal
cd /d "%~dp0"

set "BLENDER_DIR=C:\Program Files\Blender Foundation\Blender 5.2"
set "BLENDER_EXE=%BLENDER_DIR%\blender.exe"

if not exist "%BLENDER_EXE%" (
    echo ERROR: blender.exe was not found here:
    echo %BLENDER_EXE%
    echo.
    echo Do not use blender-launcher.exe for this background script.
    pause
    exit /b 1
)

if not exist "%~dp0UFBall.obj" (
    echo ERROR: UFBall.obj is not beside this batch file.
    pause
    exit /b 1
)

if not exist "%~dp0bake_uf_logo_fixed.py" (
    echo ERROR: bake_uf_logo_fixed.py is not beside this batch file.
    pause
    exit /b 1
)

echo Running Blender...
"%BLENDER_EXE%" --background --factory-startup --python "%~dp0bake_uf_logo_fixed.py"
set "RESULT=%ERRORLEVEL%"

echo.
if not "%RESULT%"=="0" (
    echo Bake failed with exit code %RESULT%.
    echo Open this log:
    echo %~dp0bake_uf_logo.log
) else (
    echo Bake completed.
    echo Outputs:
    echo %~dp0UFBall_Baked.obj
    echo %~dp0UFBall_Baked.mtl
    echo %~dp0UFBall_Baked.blend
)

echo.
pause
exit /b %RESULT%
