echo off
@echo %1%	
SET PATH=%PATH%;%cd%;%~dp0
echo %~dp0
echo %cd%
del %~dp0\*.spv
cd %~dp0\

set src=C:\_DJ\gPCD\vulkan\sim\VerfPerf\VerfPerfNoLoopDiag.vert
set dst=vert.spv
echo Compiling vert shader %src% to %dst%
	C:\_DJ\gPCD\vulkan\shaders\glslc.exe --target-env=vulkan1.3 -g %src% -o %dst% >> vert.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo vert shader compile failed
	  goto errexit
	)
	
	
set src=C:\_DJ\gPCD\vulkan\sim\VerfPerf\VerfPerf.frag
set dst=frag.spv
echo Compiling frag shader %src% to %dst%
	C:\_DJ\gPCD\vulkan\shaders\glslc.exe --target-env=vulkan1.3 -g %src% -o  %dst% >> frg.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo frag shader compile failed
	  goto errexit
	)
	
set src=C:\_DJ\gPCD\vulkan\sim\VerfPerf\VerfPerf.comp
set dst=comp.spv
echo Compiling comp shader %src% to %dst%
	C:\_DJ\gPCD\vulkan\shaders\glslc.exe --target-env=vulkan1.3 -g %src% -o  %dst% >> comp.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo frag shader compile failed
	  goto errexit
	)

exit /B 0
	
:errexit
	echo failed
	pause
	exit /B 1
:sucexit
	echo success
	pause
	
	exit /B 0
	
	