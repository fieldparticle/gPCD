# FPIBG
# Fast parallel index-based GPU-driven particle collision detection
## Particle Collison Detection Verification Reports

PerfApp is located in `FPIBG\vulkan\run\PerfReport\PerfReport.exe`

perfApp will run the debug tests on files with siffix `*.D.csv`

1. It will compare `(expectedp)` the expected number of particles with the number 
of particles loaded by the application before sending the command buffers to the GPU `(loadedp)`

2. It will compare `(expectedp)` the expected number of particles with the number 
of particles loaded by the command pipeline  `(shaderp_comp)`

3. It will compare `(expectedp)` the expected number of particles with the number 
of particles processed by the vertex shader pipeline  `(shaderp_grph)`

4. It will compare `(expectedc)` the expected number of collisions with the number 
of collisions processed by the compute shader `(shaderc)`

Since at this point there are no performance files with suffix `*.R.csv` the program will abort.
It is advisable to run the debug version first to insure that all verification tests complete before runnning
particleApp in release mode so there won't be a waste of time rerunning it if the verification tests fail.


It will not complete if there are errors which will be reported in the log file 
`FPIBG\vulkan\run\PerfReport\PerfReport.log`


