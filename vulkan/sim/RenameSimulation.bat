@echo off

set oldPrefix=FreeStream
set newPrefix=FreeStreamHetero



set old_dir=%~dp0%oldPrefix%
set new_dir=%~dp0%newPrefix%

echo Old: "%old_dir%"
echo New: "%new_dir%"

set backup_dir=%~dp0backup\%oldPrefix%
md backup_dir
md backup_dir\%oldPrefix%
copy "%old_dir%\*.*"  backup_dir\%oldPrefix%

IF EXIST "%new_dir%\" (
    ECHO [ERROR] "%new_dir%" already exists.
) ELSE (
    REN "%old_dir%" "%newPrefix%"
    ECHO [SUCCESS] Renamed directory.
)

IF EXIST "%new_dir%\%newPrefix%P.comp" (
    ECHO [ERROR] "%new_dir%\%newPrefix%P.comp" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%P.comp" (
        REN "%new_dir%\%oldPrefix%P.comp" "%newPrefix%P.comp"
        ECHO [SUCCESS] Renamed "%oldPrefix%P.comp" to "%newPrefix%P.comp"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%P.comp" does not exist.
    )
)

IF EXIST "%new_dir%\%newPrefix%P.vert" (
    ECHO [ERROR] "%new_dir%\%newPrefix%P.vert" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%P.vert" (
        REN "%new_dir%\%oldPrefix%P.vert" "%newPrefix%P.vert"
        ECHO [SUCCESS] Renamed "%oldPrefix%P.vert" to "%newPrefix%P.vert"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%P.vert" does not exist.
    )
)
IF EXIST "%new_dir%\%newPrefix%P.frag" (
    ECHO [ERROR] "%new_dir%\%newPrefix%P.frag" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%P.frag" (
        REN "%new_dir%\%oldPrefix%P.frag" "%newPrefix%P.frag"
        ECHO [SUCCESS] Renamed "%oldPrefix%P.frag" to "%newPrefix%P.frag"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%P.frag" does not exist.
    )
)
rem =============== Boundary 
IF EXIST "%new_dir%\%newPrefix%.comp" (
    ECHO [ERROR] "%new_dir%\%newPrefix%.comp" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%.comp" (
        REN "%new_dir%\%oldPrefix%.comp" "%newPrefix%.comp"
        ECHO [SUCCESS] Renamed "%oldPrefix%.comp" to "%newPrefix%.comp"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%.comp" does not exist.
    )
)

IF EXIST "%new_dir%\%newPrefix%.vert" (
    ECHO [ERROR] "%new_dir%\%newPrefix%.vert" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%.vert" (
        REN "%new_dir%\%oldPrefix%.vert" "%newPrefix%.vert"
        ECHO [SUCCESS] Renamed "%oldPrefix%.vert" to "%newPrefix%.vert"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%.vert" does not exist.
    )
)
IF EXIST "%new_dir%\%newPrefix%.frag" (
    ECHO [ERROR] "%new_dir%\%newPrefix%.frag" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%.frag" (
        REN "%new_dir%\%oldPrefix%.frag" "%newPrefix%.frag"
        ECHO [SUCCESS] Renamed "%oldPrefix%.frag" to "%newPrefix%.frag"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%.frag" does not exist.
    )
)

IF EXIST "%new_dir%\%newPrefix%.bat" (
    ECHO [ERROR] "%new_dir%\%newPrefix%.bat" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%.bat" (
        REN "%new_dir%\%oldPrefix%.bat" "%newPrefix%.bat"
        ECHO [SUCCESS] Renamed "%oldPrefix%.bat" to "%newPrefix%.bat"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%.bat" does not exist.
    )
)

IF EXIST "%new_dir%\%newPrefix%.cfg" (
    ECHO [ERROR] "%new_dir%\%newPrefix%.cfg" already exists.
) ELSE (
    IF EXIST "%new_dir%\%oldPrefix%.cfg" (
        REN "%new_dir%\%oldPrefix%.cfg" "%newPrefix%.cfg"
        ECHO [SUCCESS] Renamed "%oldPrefix%.cfg" to "%newPrefix%.cfg"
    ) ELSE (
        ECHO [ERROR] "%new_dir%\%oldPrefix%.cfg" does not exist.
    )
)

echo studyFile "%new_dir%\%newPrefix%.cfg" > "%new_dir%\%newPrefix%CMD.txt" 

echo echo off > "%new_dir%\%newPrefix%.bat" 
echo CompileShaders %newPrefix% >> "%new_dir%\%newPrefix%.bat" 

echo cd "C:\_DJ\gPCD\vulkan\run\particleOnly" > "%new_dir%\run.bat" 
echo particleD studyFile "%new_dir%\%newPrefix%.cfg" >> "%new_dir%\run.bat" 
pause