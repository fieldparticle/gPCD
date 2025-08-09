
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

#include "VulkanObj/VulkanApp.hpp"
#include "windows.h"

MsgStream			mout;
ConfigObj*			CfgTst;
ConfigObj*			MpsApp;
ConfigObj*			CfgApp;
#include "windows.h"
int ParseCommandLine(int argc, const char* argv[], ConfigObj* cfg_file);
#include "tcpip/TCPSObj.hpp"
#include "tcpip/TCPCObj.hpp"

void LaunchExecutable(std::string path, std::string cmd) ;
int main(int argc, const char* argv[]) try
{
	std::filesystem::path cwd = std::filesystem::current_path();
	mout.Init("particle.log", "Particle");
	mout << "Starting gPCD\r\n" << ende;
	MpsApp = new ConfigObj;
	MpsApp->Create("mps.cfg");
	CfgApp = new ConfigObj;
	CfgApp->Create(MpsApp->GetString("studyFile", true));
	// If the are command line options replace items ithe config file
	bool test = true;
	if (argc > 1)
	{
		
		if (ParseCommandLine(argc, argv, CfgApp) > 0)
		{
			mout << "Parse command line failed." << ende;
			return 1;
		}
	}
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	//std::string app = CfgApp->GetString("application.app",true);
	CfgTst = new ConfigObj;
		
	PerfObj* pf = new PerfObj();
	pf->Create();
	
	// Check working directory
	
	mout << "Working Directory :" << cwd.string().c_str() << ende;

	// Get test type
	std::string testtype = CfgApp->GetString("application.testtype", true);
	TCPObj* tcps = nullptr;

	if(testtype.compare("VerfPerf") == 0)
	{
		// Need to go to settings->System->Display->Graphics
		//Down to GPU Prefernce Set to High performance
		SetPriorityClass(GetCurrentProcess(), REALTIME_PRIORITY_CLASS);
		if (CfgApp->GetBool("application.doAuto", true) == true)
		{
			mout << "Do study :" << ende;
			int ret = pf->DoStudy(nullptr, nullptr, false);
			if (ret == 3 || ret == 0)
			{
				return 0;
			}
			else
				return ret;

		}
		else
		{
			std::string testfile = "application." + testtype + ".testfile";
			CfgTst->Create(CfgApp->GetString(testfile, true));	
			if (ParticleOnly(pf,nullptr,nullptr,false))
			{
				return 1;
			}
		}
		return 0;
	}
	if(testtype.compare("cdn") == 0)
	{

		mout << "Performing CD Nozzle Simulation :" << ende;
		std::string testfile = "application." + testtype + ".testfile";
		CfgTst->Create(CfgApp->GetString(testfile, true));	
		if (ParticleOnly(pf,nullptr,nullptr,false))
		{
			return 1;
		}

		return 0;
	}
}
#if 1
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;
	
	exit(1);
}
#endif
int ParseCommandLine(int argc, const char* argv[], ConfigObj* cfg_file)
{
	config_setting_t* setting;
	int count = 0;
	int key_type = 0;
	int ret = 1;
	mout << "Size of argc:" << argc << ende;
#if 1
	for (size_t ii = 1; ii < argc; ii++)
	{
		mout << "arg:" << ii << " is :" << argv[ii] << ende;

	}
#endif
	for (size_t ii = 1; ii < argc; )
	{
		std::string key = argv[ii];
		key.erase(0, 1);
		ii++;
		std::string value = argv[ii];
		mout << "Processed key:" << key.c_str() << " at " << ii << ende;
		
		if ((setting = config_lookup(&(cfg_file->m_cfg), key.c_str())) != NULL)
		{
			count = config_setting_length(setting);
			key_type = config_setting_type(setting);
		}
		else
		{
			mout << "Could not find setting for :" << key.c_str() << ende;
			return 1;
		}
		float fval = 0.0;
		bool bval = true;
		int new_int = 0;
		switch (key_type)
		{
			case CONFIG_TYPE_INT:
				new_int = std::stoi(value,nullptr);
				ret = config_setting_set_int(setting, new_int);
				break;
			case CONFIG_TYPE_FLOAT:
				fval = std::stof(value);
				ret = config_setting_set_float(setting, fval);
				break;
			case CONFIG_TYPE_STRING:
				ret = config_setting_set_string(setting, value.c_str());
				break;
			case CONFIG_TYPE_BOOL:
				if (!value.compare("true"))
					bval = true;
				else if (!value.compare("false"))
					bval = false;
				else
				{
					mout << "Could not find bool type for :" << key.c_str() << ende;
					ret = 4;
					break;
				}
				ret = config_setting_set_bool(setting, bval);
				break;
			default:
			{
				mout << "Could not find key type for :" << key.c_str() << ende;
				return 1;
			}
		};
	if (ret == 0)
		return 3;
	
	ii++;

	}

	return 0;
}