
# Fast parallel index-based GPU-driven particle collision detection
## Generating bench-marking data sets

### Run mmrr triangle
The first application run in this setup is 

`J:\FPIBG\vulkan\run\mmrrTriangle\mmrrTriangleR.exe`

This application records the minimum machine render rate, **mmrr**.

**mmrr** is based on the time it takes the GPU graphics pipeline on any hardware to render a 
single triangle where vertices are embedded in the kernel. 
A test is run for one minute which records the graphics processing time 
every second and then takes the minimum render time of the 60 timings. 

The steps for recording **mmrr** are as follows:

1. Navigate to `J:\FPIBG\vulkan\run\mmrrTriangle\shaders` and run the shader compiler batch file 
`CompileShaders.bat`. Insure that `vert.spv` and `frag.spv` are successfully generated.
2. Compile mmrrTrangleR.exe in release mode.
3. Run mmrrTrangleR.exe. It will run for one minute and at the end of the process it will write
`FPIBGDATA/mmrr.csv`


### Generate benchmarking files

`J:\FPIBG\vulkan\run\GenBenchData\GenDataSets.exe` application generates the following data.

## Particle Quantity Benchmark (PQB)

1. Number of particles:variable
2. Particle cell density:fixed
3. Number of collisions:fixed

## Collision Fraction Benchmark (CFB)

1. Number of particles:variable
2. Particle cell density:variable
3. Number of collisions:fixed

## Particle Cell Density Benchmark (PCD)

1. Number of particles:fixed
2. Particle cell density:fixed
3. Number of collisions:variable

This is an exact collision detection method and it therefore requires verification and performance testing. Each step of this process is documented here with publicly available code and data. The overall process entails :


1. generating data, 
2. verifying that data, 
3. verifying the application against that data, 
4. performance testing against the data,
5. generating plots and tables,
6. vetting data and code.

There are situations where particle-cell density varies greatly over the modeled space. For instance, a group of cells may be have a high density of particles while other particles are spread in cells far away, and/or where some cells do not contain any particles. 

The **particle quantity benchmark** (PQB) tests the processing time for an 
increasing number of particles while collision and particle-cell density are held constant.

The **collision fraction benchmark** (CFB) tests a varying number of collisions while holding the number of particles and the particle-cell density constant.

The **particle cell density benchmark** (PCB) measures the execution times for a decreasing number of cells while increasing 
the particle destiny in those cells while maintaining particle quantity.

## Generating Data

Run 

	`FPIBG\vulkan\run\GenBenchData\GenDataSets.exe`

It will populate the following directoies:

	
	FPIBGData+-|
		   +--- perfdataCFB 
		   +--- perfdataPCD 
		   +--- perfdataPQB 

And will generate the folling file types:

*.bin -> Contains the binary particle data for particle.exe

*.tst -> Provides confiuration data for each *.bin file for particle.exe


If there are errors the error will be reported in the log file

`FPIBG\vulkan\run\GenBenchData\GenDataSets.log`
