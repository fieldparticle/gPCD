
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

	// Get current path 
	std::filesystem::path cwd = std::filesystem::current_path();
	// Initialize mout
	mout.Init("particle.log", "Particle");

	mout << "Starting...\r\n" << ende;
		
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	for (unsigned int ii = 0; ii++; argc)
		mout << "MPS Command Line:" << ii << " is :" << argv[ii] << ende;

	// If the are command line options replace items ithe config file
	bool test = true;

	// allocate and create the main config file
	MpsApp = new ConfigObj;
	MpsApp->Create("mps.cfg");

	// Parse command line.
	// The config items in command line are modified or added to MpsApp
	// so to open the run code confgiuration file CfgApp
	if (argc > 1)
	{
		if (ParseCommandLine(argc, argv, MpsApp) > 0)
		{
			mout << "No Command Line for MpsApp." << ende;

		}
	}
	mout << "Opening study file:" << MpsApp->GetString("studyFile", true) << ende;

	// Create CfgApp based on the studyfile 
	CfgApp = new ConfigObj;
	CfgApp->Create(MpsApp->GetString("studyFile", true));

	//Create the config that will hold the data from *.tst files
	CfgTst = new ConfigObj;
		
	// Create a new performance object
	PerfObj* pf = new PerfObj();
	pf->Create();
	
	// Check working directory
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	TCPObj* tcps = nullptr;

	// Need to go to settings->System->Display->Graphics
	// Down to GPU Prefernce Set to High performance
	SetPriorityClass(GetCurrentProcess(), REALTIME_PRIORITY_CLASS);

	// If the auto flag is set this will be a verf-perf run
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
	// This is a single simulation file
	else
	{
		// Get the name of the simulation file *.tst that was created by the generation software
		std::string testfile = "application.testfile";
		CfgTst->Create(CfgApp->GetString(testfile, true));

		bool show_cell_boundary_cube = CfgApp->GetBool("application.show_cell_boundary_cube", true);
		bool show_wall_as_boundary_cube = CfgApp->GetBool("application.show_wall_as_boundary_cube", true);
		bool particle_as_spheres = CfgApp->GetBool("application.particle_as_spheres", true);
		bool show_boundary_as_obj = CfgApp->GetBool("application.boundary_as_obj", true);


		// If this has both a boundary and spheres.
		if (particle_as_spheres == true && (show_cell_boundary_cube == true || show_wall_as_boundary_cube ==true))
		{
			
			if (ParticleBoundaryandSphere(pf, nullptr, nullptr, false))
			{
				return 1;
			}
		}
		// If this has a boundary and no spheres.
		else if ((show_cell_boundary_cube == true || show_wall_as_boundary_cube == true || show_boundary_as_obj == true) 
			&& particle_as_spheres == false)
		{
			if (ParticleBoundaryOnly(pf, nullptr, nullptr, false))
			{
				return 1;
			}

		}
		// No boudary and no spheres
		else
		{
			if (ParticleOnly(pf, nullptr, nullptr, false))
			{
				return 1;
			}
		}
	}
	return 0;
}
	

// Gloabl catch
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;
	
	exit(1);
}


// Parse the command line and add or modify the configuration items on the 
// passed configuration file.
int ParseCommandLine(int argc, const char* argv[], ConfigObj* cfg_file)
{
	config_setting_t* setting;
	int count = 0;
	int key_type = 0;
	int ret = 1;
	mout << "Size of argc:" << argc << ende;
#if 1
	for (size_t ii = 0; ii < argc; ii++)
	{
		mout << "arg:" << ii << " is :" << argv[ii] << ende;

	}
#endif
	if (argc <= 1)
	{
		mout << "Not enough command line paramerters" << ende;
		return 1;

	}
	for (size_t ii = 1; ii < argc; )
	{
		std::string key = argv[ii];
		//key.erase(0, 1);
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