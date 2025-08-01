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
#include <filesystem>

namespace fs = std::filesystem;

int NoPerfLoop(PerfObj* perfObj, TCPObj* tcp, TCPObj* tcpsapp,DrawObj* DrawInstance, VulkanObj* VulkanWin, ResourceGraphicsContainer* rgc, ResourceComputeContainer* rcc)
{
	TimerObj* timerstep;
	uint32_t			endFrame		= CfgApp->GetUInt("application.end_frame", true);
	bool				stopondata		= CfgApp->GetBool("application.stopondata", true);
	uint32_t			frameDelay		= CfgApp->GetInt("application.frame_delay", true);
	float				deltaTime		= 0.0f;
	float				lastFrame		= 0.0f;
	uint32_t			quit_event		= 0;
	uint32_t			AutoWait		=  CfgApp->GetInt("application.seriesLength", true);;
	size_t				aprCount		= 0;
	double				lastTime		= glfwGetTime();
	double				lastCapTime     = 0;
	int					nbFrames		= 0;
	int					ndFrames		= 0;
	bool				doAuto			= CfgApp->GetBool("application.doAuto", true);
	bool				captureFrame	= MpsApp->GetBool("captureFrame", true);
	bool				copyFrame		= MpsApp->GetBool("copyFrame", true);
	double				capFrameDelay	= MpsApp->GetFloat("cap_frame_delay", true);	
	bool				doCap			= MpsApp->GetBool("do_cap", true);
	uint32_t			imgNum			= 0;		
	double				currentTime		=0.0;
	uint32_t			numParts			= CfgTst->GetUInt("pcount",true);
	bool ImageCapRunning = false;
	bool inCapture = false;

	timerstep = new TimerObj;
	
	if (perfObj->m_SeriesLength != 0)
		AutoWait = perfObj->m_SeriesLength;
	else
		AutoWait = 61;

	perfObj->m_ReportBuffer.resize(AutoWait);

	SetCallBacks(VulkanWin);

	try
	{
		// While window is open.
	
		
		while (!glfwWindowShouldClose(VulkanWin->GetGLFWWindow())
			&& glfwGetKey(VulkanWin->GetGLFWWindow(), GLFW_KEY_ESCAPE) != GLFW_PRESS)
		{
			
			timerstep->reset();
			float currentBuffer = static_cast<float>(glfwGetTime());
			deltaTime = currentBuffer - lastFrame;
			lastFrame = currentBuffer;
			
			// Get the current time
			double currentTime = glfwGetTime();

			//Esc normal termination
			if (QuitEvent)
			{
				VulkanWin->m_quit_event = 1;
				QuitEvent = false;
				return 0;
			};

			if (VulkanWin->m_quit_event > 1)
			{
				std::ostringstream  objtxt;
				objtxt << "Quit Loop Error number:" << VulkanWin->m_quit_event <<  std::ends;
				throw std::runtime_error(objtxt.str());
			};

			
			// Poll window events.
			glfwPollEvents();

			// Increment frame counter
			nbFrames++;
			
			// Check to see if caputre delay has been met then capture this frame
			

			// Test for frame number end.
			if (endFrame != 0)
			{
				if (VulkanWin->m_FrameNumber >= endFrame)
					break;

			};
	
			// Sent the cap counter first time.
			if(nbFrames == 0)
				lastCapTime = currentTime;

			DrawInstance->DrawFrame();
			
			// Get the current time
			currentTime = glfwGetTime();
			

			double ddt = currentTime - lastCapTime;
			if (ddt >= capFrameDelay && tcpsapp != nullptr && ImageCapRunning == true)
			{
				mout << "ddt:" << ddt << " capFrameDelay:" << capFrameDelay << ende;;
				tcpsapp->WritePort("next");
				tcpsapp->ReadPort();

				lastCapTime = currentTime;
			}

			if(Extflg == true)
				throw std::runtime_error("External Flag Exit.");

			VulkanWin->m_FrameNumber++;
			
			nbFrames++;
			if (currentTime - lastTime >= 1.0)
			{
				std::ostringstream  objtxt;
				objtxt	<< "perfline"								// 0-Identifier 
						<< "," << VulkanWin->m_FrameNumber			// 1-Total frames
						<< "," << ddt / double(nbFrames)			// 2-FPS
						<< "," << double(nbFrames) /ddt				// 3-SPF
						<< "," << numParts							// 4-Number of particles
						<< std::endl;
				tcp->WritePort(objtxt.str().c_str());
				tcp->ReadPort();
				std::cout << tcp->m_SRecvBuf << std::endl;
					
				if(tcp->m_SRecvBuf.compare("stopcap")==0)
				{
					tcpsapp->WritePort("stopcap");
					tcpsapp->Close();
					delete tcpsapp;
					tcpsapp = nullptr;
				}
				if(tcp->m_SRecvBuf.compare("startcap")==0)
				{
					// If capture image is true and capture to image locally is false 
					// then set up the tcpip server to send command to the capture app.
					if(doCap == true)
					{
		
						// Create a client to exchnage commands with the capture app.
						tcpsapp = new TCPObj;
						tcpsapp->SetServerPort(MpsApp->GetString("capture_cmd_port",true));
						tcpsapp->SetBufSize(MpsApp->GetInt("buffer_size",true));
		
						tcpsapp->Create();
						LaunchExecutable("CaptureApp.exe", "none") ;
						mout << "Connecting to capture thread." << ende;
						std::cout << "Listening for CaptureApp" << std::endl;
						tcpsapp->Connect();
						mout << "Connected to capture thread." << ende;
						std::string cmd = "start";
						tcpsapp->WritePort(cmd);
						ImageCapRunning = true;
					}
				}
				if(tcp->m_SRecvBuf.compare("stop")==0)
				{
					vkDeviceWaitIdle(VulkanWin->GetLogicalDevice());
					return 0;
				}
				if(tcp->m_SRecvBuf.compare("tgrun")==0)
				{
					if(G_Stop == true)
						G_Stop = false;
					else
						G_Stop = true;
				}
				if(tcp->m_SRecvBuf.compare("colorc")==0)
				{
					ColorMap = 0.0;
				}
				if(tcp->m_SRecvBuf.compare("colorang")==0)
				{
					ColorMap = 1.0;
				}
				tcp->m_SRecvBuf = "";

				aprCount++;
				std::cout << "Seconds:" << aprCount << " FrameNumber:" << VulkanWin->m_FrameNumber << " FRate:" << 1000.0 / double(nbFrames) << " ms/F, " << " FPS:" << nbFrames << " F/s." << std::endl;
				nbFrames = 0;
				lastTime += 1.0;
			}

			Sleep(frameDelay);
			vkDeviceWaitIdle(VulkanWin->GetLogicalDevice());
		}

		vkDeviceWaitIdle(VulkanWin->GetLogicalDevice());
		
	}
	catch (const std::exception& e)
	{
		mout << "STANDARD ERROR:" << e.what() << ende;
		mout << "End at frame:" << VulkanWin->m_FrameNumber << ende;
		return EXIT_FAILURE;
	}

	mout << "End at frame:" << VulkanWin->m_FrameNumber << ende;
	
	return 0;
};
