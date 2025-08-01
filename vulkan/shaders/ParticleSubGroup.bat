echo off
@echo %1%	
SET PATH=%PATH%;%cd%;%~dp0
echo %~dp0
echo %cd%
del %~dp0\*.spv
cd %~dp0\
set src=common\ParticleBoundaryInstance.vert
set dst=vert1.spv
echo Compiling vert shader %src% to %dst%
	glslc.exe  --target-env=vulkan1.3 %src% -o  %dst% >> vert.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo vert shader compile failed
	  goto errexit
	)
	
set src=common\ParticleBoundary.frag
set dst=frag1.spv
echo Compiling frag shader %src% to %dst%
	glslc.exe --target-env=vulkan1.3 %src% -o  %dst% >> frg.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo frag shader compile failed
	  goto errexit
	)
	
set src=Threads\ParticleThreads.vert
set dst=vert2.spv
echo Compiling vert shader %src% to %dst%
	%~dp0\glslc.exe --target-env=vulkan1.3 -g %src% -o %dst% >> vert.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo vert shader compile failed
	  goto errexit
	)
	
	
set src=Threads\ParticleThreads.frag
set dst=frag2.spv
echo Compiling frag shader %src% to %dst%
	%~dp0\glslc.exe --target-env=vulkan1.3 -g %src% -o  %dst% >> frg.log
	IF %ERRORLEVEL% NEQ 0 ( 
	  echo frag shader compile failed
	  goto errexit
	)
	
set src=Threads\ParticleSubgroup.comp
set dst=comp.spv
echo Compiling comp shader %src% to %dst%
	%~dp0\glslc.exe --target-env=vulkan1.3 -g %src% -o  %dst% >> comp.log
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
	
	

