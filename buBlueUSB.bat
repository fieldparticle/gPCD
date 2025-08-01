cls
echo %1
echo %2
echo off
SET dsk=%1
set /p input=Type any input:
SET "target=J:\FPIBG"
SET "bkdir=E:\FPIBG
echo %bkdir%
set "d=vulkan\make"



SET "dtnm=%DATE:~4,2%-%DATE:~7,2%-%DATE:~12,2%_%time:~1,1%%time:~3,2%"
SET Datefolder=%bkdir%\%dtnm%\%input%
echo %Datefolder%
MD %Datefolder%
REM SET "cmdln= %Datefolder% ^>buRpt%target%.txt"
echo %cmdln%

attrib +A /S /D %target%\*.*
pause
xcopy %target%\*.* %Datefolder% > %Datefolder%\buRpt%dtnm%.txt /S /V /R /F /Y /C /E

start "C:\Program Files (x86)\Notepad++\notepad++.exe" %Datefolder%\buRpt%dtnm%.txt

rem git add --all
rem git commit -am %input%
rem git pull main origin
rem git config --list --show-origin

pause