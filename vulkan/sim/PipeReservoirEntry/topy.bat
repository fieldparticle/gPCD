del *.log
del *.spv

xcopy C:\_DJ\gPCD\vulkan\sim\BoundarySpheresMotion\*.* C:\_DJ\gPCD\DynamicsCPT\glsl\BoundarySpheresMotion\ /i
xcopy C:\_DJ\gPCD\vulkan\sim\common\*.* C:\_DJ\gPCD\DynamicsCPT\glsl\common\ /i

pause