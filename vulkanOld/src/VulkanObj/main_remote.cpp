
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
#define WIN32_LEAN_AND_MEAN
#include <iostream>
#include <thread>

#include "VulkanObj/VulkanApp.hpp"
#include "windows.h"
#include "TCPSObj.hpp"
#include "TCPCObj.hpp"
MsgStream			mout;
ConfigObj*			CfgTst;
ConfigObj*			MpsApp;
ConfigObj*			CfgApp;

int main() try
{
	// Open mout log and report working directory
	std::cout << "Starting" << std::endl;
	mout.Init("particle.log", "Particle");
	std::filesystem::path cwd = std::filesystem::current_path();
	std::cout << "Working Directory :" << cwd.string().c_str() << std::endl;
	mout << "Working Directory :" << cwd.string().c_str() << ende;
	
	// Read the configuration file from mps.cfg
	mout << "Create mps" << ende;
	MpsApp = new ConfigObj;
	MpsApp->Create("mps.cfg");
	mout << "Open mps" << ende;

	//Open the cfg. file for this applcation
	CfgApp = new ConfigObj;
	
	mout << "Study File Config" << ende;

	// Create the global test file object to hold particlars about these tests
	CfgTst = new ConfigObj;

	// Create and open the server port for the FPIBGUtility application.
	TCPObj* tcps = new TCPObj;
	tcps->SetServerPort(MpsApp->GetString("server_port",true));
	std::cout << "FPIBG Server Listening on port:" << tcps->GetServerPort() << std::endl;
	tcps->SetBufSize(MpsApp->GetInt("buffer_size",true));


	TCPObj* tcpsapp = nullptr;

	bool doCap = MpsApp->GetBool("do_cap", true);
	bool capture_image_local = MpsApp->GetBool("capture_image_local", true);
	

	// Create a perf object to perform performance and verification.
	PerfObj* pf = new PerfObj();
	

	
	// Set the server port to listen - will block here.
	

    int ret = 0;
    while (ret == 0)
    {
		tcps->Create();
		std::cout << "Listening for Python Client" << std::endl;
		tcps->Connect();
		// read the command from the FPIBGUtility app.
        ret = tcps->ReadPort();
		std::vector<std::string> msg = tcps->GetSplitBuffer();
		if(ret == 1)
		{
			tcps->Create();
			tcps->Connect();
			ret = 0;
		}

        if(msg[0].compare("quit")==0)
        {
			ret = 1;
			break;
		}
		if(msg[0].compare("runsim")==0)
		{
			std::cout << "Recieved runsim" << std::endl;
			CfgApp->Create(msg[1]);
			pf->Create();
			CfgTst->Create(CfgApp->GetString("application.cdn.testfile", true));	
			ret=ParticleOnly(pf,tcps,tcpsapp,true);
			tcps->WritePort("simdone");
			tcps->Close();
			ret = 0;
        }

		// Run series 
		if(msg[0].compare("runseries")==0)
        {
			CfgApp->Create(msg[1]);
			pf->Create();
			// Find out if we are doing a series or a single test
			bool autoFlag = CfgApp->GetBool("application.doAuto", true);

			std::cout << "Recieved runseries" << std::endl;
			tcps->m_SRecvBuf = "";
			// If capture is enabled launch the app
			ret = pf->DoStudy(tcps,nullptr,true);
			// If stop command
			if(ret == 2)
				ret = 0;
			tcps->WritePort("perfdone,tcp");
        }
		if(msg[0].compare("sndcsv")==0)
		{
			tcps->m_SRecvBuf = "";
			tcps->SendPerfFile("Particle.cfg",1);
		}
		if(msg[0].compare("rcvcsv")==0)
		{
			tcps->m_SRecvBuf = "";
			tcps->SendPerfFile("Particle.cfg",1);
		}
		if(msg[0].compare("test")==0)
		{
			std::cout << "Recieved Test" << std::endl;
			std::string outbuf = "Recieved Test : OK";
			tcps->WritePort(outbuf);
			outbuf.clear();
		}
		

    }
	tcps->Close();
	return ret;
}

#if 1
catch (const std::exception& e)
{

	mout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << ende;
	std::cout << "EXITING| TYPE:" << typeid(e).name() << " MSG:" << e.what() << std::endl;
	exit(1);
}
#endif
