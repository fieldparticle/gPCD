# FPIBG

These are the instruction for downloading and compiling third party dependencies.

## Part I - Download and compile 3rd party applications glm,VMA,glfw.
	
	
3. Download VMA 

Unzip in FPIBG3rdPty as FPIBG3rdPty/VMA (Chnage the full name to VMA)

Get it here as zip: https://github.com/google/shaderc

**It does not need to be compiled.**

1. Download Open G/L Window library (glfw)

Unzip in FPIBG3rdPty
then remove version number so it's just glfw. 

Get it here : https://www.glfw.org/

1.A. Using the cmake gui set "where is the source code" to:
	
	`FPIBG3rdPty/glfw`
    
in "Where to build the libraries" set this to:
	
	`FPIBG3rdPty/glfw/build`

Then press "Configure" until there are no red colored lines 

Then press "Generate"

Then press "Open Project" which should open Visual C++

Or, navigate to 

	`FPIBG3rdPty/glfw/build`
	
and open GLFW.sln.

Select "Debug" Version and build.

elect "Release" Version and build.

NOTE: The application looks for glfw3.lib. If it is a newer version then change 

`VisualC++->Properties->Linker->J:\FPIBG3rdPty\glfw\build\src\Debug\glfw3.lib` 

to the glfw version.

NOTE: If you get undefined errors go to the glfw project and make sure this is set
	
	`VisualC++->Properties->C/C++/Code Generation/Multi-Threaded Debug (/MTd)`


2. Open G/L Math library (glm)

Unzip in FPIBG3rdPty

then remove version umber so it's just glm.

Get it here: https://glm.g-truc.net/0.9.9/index.html

It does not need to be built.


## Part II - Downoad and compile 3rd party application for shaderc.
	

1. Download shaderc
Unzip in FPIBG3rdPty as FPIBG3rdPty/shaderc

Get it here as zip: https://github.com/google/shaderc

2. Download google test and install in: 

	`FPIBG3rdPty/shaderc/third_party`

as 

	`FPIBG3rdPty/shaderc/third_party/googletest`

Get it here as zip: https://github.com/google/googletest


## **IMPORTANT: **
**Go to the directory:**

	FPIBG\vulkan\src\glsl.

**Copy and replace the following files**

	1. file_compiler.cc
	2. file_compiler.h
	3. main.cc

**into**

	FPIBG3rdPty/shaderc/glslc/src

(This provides an command line like interface with glslc)

3. Download SPRIV-Tools 
    
	`PIBG3rdPty/shaderc/third_party/`

    as 

	`FPIBG3rdPty/shaderc/third_party/SPIRV-Tools`

Get it here: https://github.com/KhronosGroup/SPIRV-Tools

4. Download regular expression library re2 and install in 
    
	`PIBG3rdPty/shaderc/third_party/`
as 
    `FPIBG3rdPty/shaderc/third_party/re2`

Get it here: https://github.com/google/re2

5. Download 

    `SPRIV-Headers PIBG3rdPty/shaderc/third_party/`
as
	`FPIBG3rdPty/shaderc/third_party/SPIRV-Headers`

Get it here: https://github.com/KhronosGroup/SPIRV-Headers

6. Download glslang 

	`PIBG3rdPty/shaderc/third_party/`
as 

	`FPIBG3rdPty/shaderc/third_party/glslang`

Get it here: https://github.com/KhronosGroup/glslang


7. Download Effcee to 
    
	`PIBG3rdPty/shaderc/third_party/`
as 
    `FPIBG3rdPty/shaderc/third_party/effcee`

Get it here: https://github.com/google/effcee

8. Download Abseil C++ library 

	`PIBG3rdPty/shaderc/third_party/`
as 
    `FPIBG3rdPty/shaderc/third_party/abseil_cpp`

NOTE: it installs as as abseil-cpp so change the name to abseil_cpp

Get it here: https://github.com/abseil/abseil-cpp

NOTE: There is a good tutorial on Reddit if you experience problems building shaderc:
	https://www.reddit.com/r/vulkan/comments/m6wn5k/shaderc_step_by_step_build_on_visual_studio_2019/


9. Using the cmake gui set "where is the source code" to 
 
        `FPIBG3rdPty/shaderc`

In 	"Where to build the libraries" set this to 

	`FPIBG3rdPty/shaderc/build`

Then press "Configure"

Mark the check boxes beside:

		`SPRIV_SKIP_TESTS`
		and		
		`SHADERC_SKIP_EXAMPLES`
			
Then press "Generate"

	Press "Open Project" which should open the visual C++.
	or navigate to shaderc/build and open shaderc.sln

	In Visual C++ build solution in both release and debug.

