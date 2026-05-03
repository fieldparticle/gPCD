
/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mps/main.cpp $
% $Id: main.cpp 31 2023-06-12 20:17:58Z jb $
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
%*$Revision: 31 $
%*
%*
%******************************************************************/

#include "VulkanApp.hpp"

MsgStream			mout;
uint32_t DoStudy(ConfigObj* configVCube);
int main() try
{
	mout.Init("mps.log", "MPS");
	ConfigObj* config = new ConfigObj;
	std::filesystem::path cwd = std::filesystem::current_path();
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	config->Create("mps.cfg");
	
	
	
#if 1
	if (config->m_StudyName.compare("Particle.cfg") == 0)
	{
		
		if (config->m_DoAuto == true)
			DoStudy(config);
		else
			particleOnly(config);
	}
	else
	{
		
		std::string err = "Unable to open Configuration File from mps.cfg :" + config->m_StudyName;
		throw std::runtime_error(err.c_str());
	}
	
#endif
}
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;

	exit(1);
}
#include <iostream>
#include <filesystem>
uint32_t DoStudy(ConfigObj* config)
{
	
	namespace fs = std::filesystem;



	std::string path = config->m_TestDir;
	std::set<fs::path> sorted_by_name;

	for (auto& entry : fs::directory_iterator(path))
		sorted_by_name.insert(entry.path());

	for (const auto& filename : sorted_by_name)
	{
		std::string::size_type pos = filename.string().find("tst");
		size_t pt = 0;
		std::string pathtest{};
		pathtest = filename.string();
	


		if ((pt= pathtest.find("tst")) != std::string::npos)
		{
			std::cout << filename << std::endl;
			config->m_TestName.clear();
			config->m_TestName = filename.string();
			config->GetParticleSettings();
			std::string hold = filename.string().substr(0, pt);
			config->m_AprFile = hold + "csv";
			config->m_DataFile = hold + "bin";
			mout << "Auto DataFile : " << config->m_DataFile << ende;
			particleOnly(config);
			//return 0;
			

		}
		if (GetAsyncKeyState(VK_ESCAPE))
		{
			return 1;
		}
	}
	

	return 0;
}