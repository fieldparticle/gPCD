/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
%*******************************************************************
%***                         DESCRIPTION                         ***
%*******************************************************************
@doc
@module
			@author: Jackie Michael Bell<nl>
			COPYRIGHT <cp> Jackie Michael Bell<nl>
			Property of Jackie Michael Bell<rtm>. All Rights Reserved.<nl>
			This source code file contains proprietary<nl>
			and confidential information.<nl>


@head3 		Description. |
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/

#include <iostream>
#include <filesystem>
#include "VulkanObj/VulkanApp.hpp"

void PerfObj::Create()
{
	m_SeriesLength = CfgApp->GetUInt("application.seriesLength", true);
	m_TestCFG = CfgApp->GetString("application.perfTest", true);
	m_testPQBRDir= CfgApp->GetString("application.testdirPQBRandom", true);
	m_testPQBSDir= CfgApp->GetString("application.testdirPQBScale", true);
	m_testPQBDir= CfgApp->GetString("application.testdirPQB", true);
	m_testCFBDir= CfgApp->GetString("application.testdirCFB", true);
	m_testPCDDir= CfgApp->GetString("application.testdirPCD", true);
	m_testDUPDir= CfgApp->GetString("application.testdirDUP", true);
	m_SingleFileTest= CfgApp->GetBool("application.doAutoSingleFile", true);
	if(!m_TestCFG.compare("testdirPQBRandom"))
	{
		m_TestDir = m_testPQBRDir;
	}
	if(!m_TestCFG.compare("testdirPQBScale"))
	{
		m_TestDir = m_testPQBSDir;
	}
	if(!m_TestCFG.compare("testdirPQB"))
	{
		m_TestDir = m_testPQBDir;
	}
	if(!m_TestCFG.compare("testdirCFB"))
	{
		m_TestDir = m_testCFBDir;
		
	}
	if(!m_TestCFG.compare("testdirPCD"))
	{
		m_TestDir = m_testPCDDir;
	}
	if(!m_TestCFG.compare("testdirDUP"))
	{
		m_TestDir = m_testDUPDir;
	}

}
uint32_t PerfObj::DoStudy(TCPObj* tcps,TCPObj* tcpcapp, bool rmtFlag)
{
	
	namespace fs = std::filesystem;
	std::set<fs::path> sorted_by_name;
	std::vector<std::string> filename;

	if(m_SingleFileTest == false)
	{
		
		std::string path = m_TestDir;
		for (auto& entry : fs::directory_iterator(path))
		{
			sorted_by_name.insert(entry.path());
			//filename.push_back(entry.path().string());
		}

	#if 1
		for (const auto& entry : sorted_by_name)
		{
			if ((entry.string().find("tst")) != std::string::npos)
				filename.push_back(entry.string());
		}
	#endif
	}
	else
	{

		filename.push_back(CfgApp->GetString("application.VerfPerf.testfile", true));


	}

	uint32_t count = 0;

	//for (size_t ii = 0; ii < 4; ii++)
	for(size_t ii = 0; ii< filename.size();ii++)
	{
		++count;
		std::string::size_type pos = filename[ii].find("tst");
		size_t pt = 0;
		std::string pathtest{};
		pathtest = filename[ii];

		std::filesystem::path cwd = std::filesystem::current_path();
		
		if ((pt= pathtest.find("tst")) != std::string::npos)
		{
			std::cout	<< "=======================" 
						<< filename[ii] 
						<< "=======================" << std::endl;
			std::cout << filename[ii] << std::endl;
			m_TestName.clear();
			m_TestName = filename[ii];
			CfgTst->Create(filename[ii]);
			m_colcount = CfgTst->GetInt("num_particle_colliding", true);
			m_density = CfgTst->GetFloat("collsion_density", true);
			m_partcount = CfgTst->GetInt("num_particles", true);

			std::string hold = filename[ii].substr(0, pt);
			//config->m_AprFile = hold;
			m_DataFile = hold + "bin";
			m_AprFile =  CfgTst->GetString("report_file", true);
			m_DataFile = CfgTst->GetString("particle_data_bin_file", true);
			mout << "Auto DataFile : " << m_DataFile << ende;

			uint32_t ret = ParticleOnly(this,tcps,tcpcapp,false);
			//Fail
			if (ret == 1)
			{
				mout << "Auto - ParticleOnly failed" << ende;
				return 1;
			}
			//Stop command
			if (ret == 2)
			{
				mout << "Auto - ParticleOnly failed" << ende;
				return 2;
			}
			
			if (QuitEvent == 1)
				return 0;
			
			

		}
		if (GetAsyncKeyState(VK_ESCAPE))
		{
			return 0;
		}
	}
	return 0;
}
 

int PerfObj::Doperf(DrawObj* DrawInstance, VulkanObj* VulkanWin, TCPObj* tcp, size_t aprCount)
{
	int ret = 0;
	std::string filename =m_AprFile;
	
#ifndef NDEBUG
	filename = filename + "D.csv";
#else
	filename = filename + "R.csv";
#endif

	

		float totFps = 0.0;
		float totTime = 0.0;
		std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open report file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		
		//
		ostrm << "time,fps,cpums,cms,gms,expectedp,loadedp,shaderp_comp,shaderp_grph,expectedc,shaderc,threadcount,sidelen,density,PERR,CERR" << std::endl;
		for (size_t ii = 0; ii < aprCount-1; ii++)
		{
			
			totFps += m_ReportBuffer[ii].FrameRate;
			totTime +=m_ReportBuffer[ii].Second;
			uint32_t partErr = 0;
			uint32_t colErr = 0;

		
			ostrm	<< m_ReportBuffer[ii].Second << ","				// time
					<< m_ReportBuffer[ii].FrameRate << ","			// fps
					<< 1.0f/m_ReportBuffer[ii].FrameRate << ","		 // cpums: cpu time
					<< m_ReportBuffer[ii].ComputeExecutionTime << ","	// cms: compute ms
					<< m_ReportBuffer[ii].GraphicsExecutionTime << ","	// gms: graphics ms				
					<< m_partcount << ","										// expectedp: frm tst - generated
					<< VulkanWin->m_Numparticles-1 << ","							// loadedp: loaded into rccdApp
					<< m_ReportBuffer[ii].NumParticlesComputeCount << ","// shaderp_comp: counted from compute
					<< m_ReportBuffer[ii].NumParticlesGraphicsCount << ","			// shaderp_grp: counted from graphics
					<< m_colcount << ","										// expectedc: expected collisions
					<< m_ReportBuffer[ii].NumCollisionsComputeCount << ","							// shaderc: compute counted collisions
					<< m_ReportBuffer[ii].ThreadCountComp << ","									// threadcount: number of threads compute
					<< VulkanWin->m_SideLength << ","								// sidelen
					<< m_density << ","										// density
					<< partErr << ","
					<< colErr 
					<< std::endl;

			



		}
		
		ostrm.flush();
		ostrm.close();
		if(tcp != nullptr)
		{
			tcp->WritePort("csvfile");
			tcp->SendPerfFile(filename.c_str(),1);
		}
		
	std::cout << "\n\n\n\n================= Done Perf ======================= \n\n\n\n" << std::endl;
	return ret;

}