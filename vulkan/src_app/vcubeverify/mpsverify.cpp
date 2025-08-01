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

//#include "VulkanObj/VulkanApp.hpp"
#include "mpsVerify.hpp"
void CountParticlesMain();
uint32_t Count(bool CountCollisions);
void GetParticleSettings();
MsgStream			mout;
VerifyConfigObj* cfg = nullptr;


int  main()  try
{
	
	mout.Init("mpsverify.log", "MPSVerify");
	cfg = new VerifyConfigObj;
	std::filesystem::path cwd = std::filesystem::current_path();
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	cfg->Create("mpsverify.cfg");

	uint32_t testnum = cfg->GetInt("application.testtype", true);
	cfg->m_partcount = cfg->GetInt("application.pcount", true);
	cfg->m_TestName = cfg->GetString("application.testfile", true);
	cfg->m_TestDir = cfg->GetString("application.testdir", true);
#if 1
	if(testnum == 1)
		CountCollisions(true);
	if (testnum == 3)
		CountParticlesMain();
	if (testnum == 2)
		VerifyArrayIndexingV2();

#endif

}
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;

	exit(1);
}

#include <iostream>
#include <filesystem>
void CountParticlesMain()
{

	namespace fs = std::filesystem;



	std::string path = cfg->m_TestDir;
	std::set<fs::path> sorted_by_name;
	std::vector<std::string> filename;

	for (auto& entry : fs::directory_iterator(path))
	{
		sorted_by_name.insert(entry.path());
		filename.push_back(entry.path().string());
	}
#if 0
	for (const auto& entry : sorted_by_name)
	{
		if ((entry.string().find("tst")) != std::string::npos)
			filename.push_back(entry.string());
	}
#endif
	uint32_t count = 0;

	//for (size_t ii = 0; ii < 4; ii++)
	for (size_t ii = 0; ii < filename.size(); ii++)
	{
		++count;
		std::string::size_type pos = filename[ii].find("tst");
		size_t pt = 0;
		std::string pathtest{};
		pathtest = filename[ii];

		if ((pt = pathtest.find("tst")) != std::string::npos)
		{
			std::cout << "======================="
				<< filename[ii]
				<< "=======================" << std::endl;
			std::cout << filename[ii] << std::endl;
			cfg->m_TestName.clear();
			cfg->m_TestName = filename[ii];
			GetParticleSettings();
			std::string hold = filename[ii].substr(0, pt);
			//config->m_AprFile = hold;
			cfg->m_DataFile = hold + "bin";
			mout << "Auto DataFile : " << cfg->m_DataFile << ende;
			//if(Count(false)!=0)
			//	return;
			

		}
	}

}


void GetParticleSettings()
{
	config_init(&cfg->m_cfg);
	cfg->ReadConfigFile(cfg->m_TestName);
	cfg->m_AprFile = cfg->GetString("aprFile", true);
	cfg->m_DataFile = cfg->GetString("dataFile", true);
	cfg->m_CfgSidelen = cfg->GetUInt("Sidelen", true);
	cfg->m_PartPerCell = cfg->GetUInt("PartPerCell", true);
	cfg->m_wky = cfg->GetInt("workGroupsy", true);
	cfg->m_wkx = cfg->GetInt("workGroupsx", true);
	cfg->m_wkz = cfg->GetInt("workGroupsz", true);
	cfg->m_dkx = cfg->GetInt("dispatchx", true);
	cfg->m_dky = cfg->GetInt("dispatchy", true);
	cfg->m_dkz = cfg->GetInt("dispatchz", true);
	cfg->m_colcount = cfg->GetInt("colcount", true);
	cfg->m_radius = cfg->GetFloat("radius", true);
	cfg->m_density = cfg->GetFloat("density", true);
	cfg->m_partcount = cfg->GetInt("pcount", true);
	cfg->m_MaxCollArray = cfg->GetInt("ColArySize", true);
};

