


#include "DoPerf.hpp"
void Doperf(size_t aprCount)
{

//#ifndef PARTICLE_GRAPHICS_PIPE_ONLY 
//	#ifndef PARTICLE_GRAPHICS_AND_COMPUTE_ONLY 
//		return;
//	#endif
//#endif

	
	std::string filename = "J:/RCCDData/perfdata/mmrr.csv";
	
	filename = filename + ".csv";
	{
		float totFps = 0.0;
		float totTime = 0.0;
		std::ofstream ostrm(filename);
		//
		ostrm << "time,fps,spf,expectedp,loadedp,shaderp_comp,shaderp_grp, expectedc,shaderc,threadcount, sidelen,density,PERR,CERR" << std::endl;
		for (size_t ii = 0; ii < aprCount; ii++)
		{
			
			totFps += apr[ii].frameRate;
			totTime += apr[ii].frameTime;
			uint32_t partErr = 0;
			uint32_t colErr = 0;
			

			ostrm << apr[ii].second << ","				// second of record
				<< apr[ii].frameRate << ","				// frame rate
				<< apr[ii].frameTime << ","				//spf
				<< "0" << ","				//expectedp frm tst
				<< "0" << ","	// loadedp from rccdApp
				<< "0" << ","		// shaderp from compute
				<< "0" << ","		// shaderp from vertex
				<< "0" << ","					//expectedc
				<< "0" << ","		// shaderc comp
				<< "0" << ","				//threadcount
				<< "0" << ","			//sidelen
				<< "0" << ","				// density
				<< partErr << ","
				<< colErr << ","
				<< std::endl;
		}
		ostrm << "Total,"
			<< totFps / 60.0 << ","
			<< totTime / 60.0 << ", , , , , ," << std::endl;
		ostrm << "time, is in seconds" << std::endl;
		ostrm << "fps,frames per seconds recorded by rccdApp" << std::endl;
		ostrm << "spf,seconds per frame recorded by rccdApp" << std::endl;
		ostrm << "expectedp,expected number of particles read from *.tst file - tst file is from genApp." << std::endl;
		ostrm << "loadedp,number of particles loaded from *.bin by rccdApp - bin file is from genApp (always loads onw more than expected)." << std::endl;
		ostrm << "shaderp_comp,number of particles processed by the compute shader." << std::endl;
		ostrm << "shaderp_grph,number of particles processed by the vertex shader." << std::endl;
		ostrm << "expectedp,expected number of collisions read from *.tst file - tst file is from genApp." << std::endl;
		ostrm << "shaderc,number of collisions processed by the shader." << std::endl;
		ostrm << "threadcount,number of threads launced by the compute shader." << std::endl;
		ostrm << "sidelen,expected side length - read from *.tst file. " << std::endl;
		ostrm << "density,expected collision density - read from *.tst file " << std::endl;
		ostrm.flush();
		ostrm.close();
		
	}
	

	std::cout << "\n\n\n\n================= Done Perf ======================= \n\n\n\n" << std::endl;
}