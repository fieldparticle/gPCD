
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
#include "tcpip/TCPSObj.hpp"
#include "tcpip/TCPCObj.hpp"
int CompileShaders();
void LaunchExecutable(std::string path, std::string cmd) ;
int main() try
{
	
	mout.Init("particle.log", "Particle");
	mout << "Starting FPIBG\r\n" << ende;
	MpsApp = new ConfigObj;
	MpsApp->Create("mps.cfg");
	CfgApp = new ConfigObj;
	CfgApp->Create(MpsApp->GetString("studyFile", true));
	std::string app = CfgApp->GetString("application.app",true);
	//std::cout << "Byte Size:" << sizeof(uint32_t) << std::endl;
	//return 0;
	CfgTst = new ConfigObj;
	
	PerfObj* pf = new PerfObj();
	pf->Create();
	
	// Check working directory
	std::filesystem::path cwd = std::filesystem::current_path();
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
			if (pf->DoStudy(nullptr,nullptr,false))
			{
				return 1;
			}

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

int ExecuteShader(std::string CommandLine)
{
	STARTUPINFO startinfo = { 0 };
	PROCESS_INFORMATION processinfo = { 0 };
	BOOL bsuccess = CreateProcess(TEXT(CommandLine.c_str()), NULL, NULL, NULL, FALSE, NULL, NULL,
		NULL, &startinfo, &processinfo);

	if (bsuccess)
	{
		std::cout << "Process Injected" << std::endl
			<< "Process ID:\t" << processinfo.dwProcessId << std::endl;

	}
	else
	{
		std::cout << "Error to start the injected process" << GetLastError() << std::endl;
	}
	//std::cin.get();
	return(0);

}

#if 0
int CompileShaders()
{

		//const std::string begin = "C:\\_DJ\\gPCD\\vulkan\\shaders\\glslc.exe";
		const std::string begin = "..\\..\\shaders\\ParticleVerfPerf.bat";
		const std::string end = " --target-env=vulkan1.3 -fshader-stage=vertex -g";
		const std::string src = "C:\\_DJ\\gPCD\\vulkan\\shaders\\VerfPerf\\ParticleVerfPerf.vert";
		const std::string dst = "-o C:\\_DJ\\gPCD\\vulkan\\shaders\\VerfPerf\\vert2.spv";
		const std::string command = begin; // + end + src + dst;
		mout << "Executing shader compile:" << command.c_str() << ende;
		std::cout << "Compiling file using " << command << '\n';
		size_t ret = 0;
		if ((ret = std::system((const char*)command.c_str())) != 0)
			std::cout << "Failed " << ret << "Compiling file using " << command << '\n';
		else
			return 0;
	
}
#endif