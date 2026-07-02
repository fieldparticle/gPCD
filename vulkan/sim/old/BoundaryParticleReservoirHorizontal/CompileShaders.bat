@echo off
setlocal

set "SIM=BoundaryParticleReservoirHorizontal"
set "DIR=C:\_DJ\gPCD\vulkan\sim\%SIM%"
set "GLSLC=C:\_DJ\gPCD\vulkan\shaders\glslc.exe"

"%GLSLC%" --target-env=vulkan1.3 -g "%DIR%\%SIM%.vert"  -o "%DIR%\vertb.spv" || exit /b 1
"%GLSLC%" --target-env=vulkan1.3 -g "%DIR%\%SIM%.frag"  -o "%DIR%\fragb.spv" || exit /b 1
"%GLSLC%" --target-env=vulkan1.3 -g "%DIR%\%SIM%P.vert" -o "%DIR%\vert.spv"  || exit /b 1
"%GLSLC%" --target-env=vulkan1.3 -g "%DIR%\%SIM%P.frag" -o "%DIR%\frag.spv"  || exit /b 1
"%GLSLC%" --target-env=vulkan1.3 -g "%DIR%\%SIM%P.comp" -o "%DIR%\comp.spv" || exit /b 1

echo Shader compilation succeeded.
exit /b 0
