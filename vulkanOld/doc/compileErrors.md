----------------------------------------------------------------------------------------------------------------------------------------
Error:

1>libconfig.obj : error LNK2019: unresolved external symbol __imp_PathIsRelativeA referenced in function config_default_include_func

Soltution:

#pragma comment (lib,"Shlwapi.lib")

----------------------------------------------------------------------------------------------------------------------------------------