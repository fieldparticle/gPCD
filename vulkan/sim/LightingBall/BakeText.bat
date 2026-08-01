@echo on
cd /d "%~dp0"

"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" ^
    --background ^
    --python "%~dp0bake_uf_logo.py"

pause