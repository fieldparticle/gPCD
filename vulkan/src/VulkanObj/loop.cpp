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
#include <cstdint>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>
namespace fs = std::filesystem;
std::unordered_set<uint32_t> ParseCaptureFrames(
	const std::vector<const char*>& entries);
int Loop(PerfObj* perfObj, TCPObj* tcp,TCPObj* tcpsapp, DrawObj* DrawInstance, VulkanObj* VulkanWin, ResourceGraphicsContainer* rgc, ResourceComputeContainer* rcc)
{
	TimerObj* timerstep;
	uint32_t			endFrame		= CfgApp->GetUInt("application.end_frame", true);
	bool				stopondata		= CfgApp->GetBool("application.stopondata", true);
	float				frameDelay		= CfgApp->GetFloat("application.frame_delay", true);
	float				deltaTime		= 0.0f;
	float				lastFrame		= 0.0f;
	uint32_t			quit_event		= 0;
	uint32_t			seriesLength	=  CfgApp->GetInt("application.seriesLength", true);;
	uint32_t			aprCount		= 0;
	double				lastTime		= glfwGetTime();
	double				lastCapTime     = 0;
	int					nbFrames		= 0;
	bool				doAuto			= CfgApp->GetBool("application.doAuto", true);
	bool				captureFrame	= MpsApp->GetBool("captureFrame", true);
	bool				copyFrame		= MpsApp->GetBool("copyFrame", true);
	double				capFrameDelay	= MpsApp->GetFloat("cap_frame_delay", true);	
	bool				doCap			= MpsApp->GetBool("do_cap", true);
	bool				stopOnError		= CfgApp->GetBool("application.stopOnError", true);
	bool				doAutoSingleFile= CfgApp->GetBool("application.doAutoSingleFile", true); 
	uint32_t			imgNum			= 0;
	std::string			oringcap_dir = CfgApp->GetString("application.testfile", true);
	std::string			out_dir = CfgApp->GetString("application.capture_dir", true);
	fs::path p = oringcap_dir;

	std::cout << "Root name      : " << p.root_name() << '\n';
	std::cout << "Root directory : " << p.root_directory() << '\n';
	std::cout << "Root path      : " << p.root_path() << '\n';
	std::cout << "Parent path    : " << p.parent_path() << '\n';
	std::cout << "Filename       : " << p.filename() << '\n';
	std::cout << "Stem           : " << p.stem() << '\n';
	std::cout << "Extension      : " << p.extension() << '\n';
			
	std::ostringstream  cap_prfx;
	cap_prfx << out_dir << "/" << p.stem().string();
	

	bool auto_cap_frames = CfgApp->GetBool("application.auto_cap_frames", true);
	std::vector<const char*> cap_ary = CfgApp->GetArray("application.capture_frames");
	std::unordered_set<uint32_t> cap_frames = ParseCaptureFrames(cap_ary);

	if (CfgTst->CheckKey("DT"))
	{	float cfg_dt = CfgApp->GetFloat("application.dt", true);
		float tst_dt = CfgTst->GetFloat("DT", false);
		VulkanWin->m_dt = CfgTst->GetFloat("DT", false);

		if (tst_dt != cfg_dt)
		{
			mout << "WARNING:Delta Time Mismatch->ConfigFile Val:" << cfg_dt << " *.tst file Val:" << tst_dt << "Using the *.tst val" << ende;
			
		}
	}

	int ret = 0;
	uint32_t partErrC=0;
	uint32_t partErrG=0;
	uint32_t collErr=0;
					

	timerstep = new TimerObj;
	
	if (perfObj->m_SeriesLength != 0)
		seriesLength = perfObj->m_SeriesLength;
	else
		seriesLength = 61;

	perfObj->m_ReportBuffer.resize(seriesLength);

	SetCallBacks(VulkanWin);

	try
	{
		// While window is open.
	
	
		while (!glfwWindowShouldClose(VulkanWin->GetGLFWWindow())
			&& glfwGetKey(VulkanWin->GetGLFWWindow(), GLFW_KEY_ESCAPE) != GLFW_PRESS)
		{
			

			perfObj->m_ReportBuffer[aprCount].SecondPerFrame = timerstep->elapsed();
			timerstep->reset();
			//Esc normal termination
			if (QuitEvent)
			{
				VulkanWin->m_quit_event = 1;
				return VulkanWin->m_quit_event;
			};

			if (VulkanWin->m_quit_event > 1)
			{
				std::ostringstream  objtxt;
				objtxt << "Quit Loop Error number:" << VulkanWin->m_quit_event <<  std::ends;
				throw std::runtime_error(objtxt.str());
			};

			float currentBuffer = static_cast<float>(glfwGetTime());
			deltaTime = currentBuffer - lastFrame;
			lastFrame = currentBuffer;

			// Poll window events.
			glfwPollEvents();

			// Get the current time
			double currentTime = glfwGetTime();

			


			// Draw the frame.
			DrawInstance->DrawFrame();
	

			if(VulkanWin->m_quit_event > 0)
			{
				std::ostringstream out_file;
				out_file << cap_prfx.str() << "_" << VulkanWin->m_FrameNumber-1.0 << ".cap";
				DrawInstance->CaptureFrame(out_file.str());
				return VulkanWin->m_quit_event;
			}


			// is true capture this frame
			if (G_ExportFrame == true && auto_cap_frames == false)
			{
				G_ExportFrame = false;
				std::ostringstream out_file;
				out_file << cap_prfx.str() << "_" << VulkanWin->m_FrameNumber << ".cap";
				DrawInstance->CaptureFrame(out_file.str());
			}
			else if (auto_cap_frames == true)
			{
				if (cap_frames.find(VulkanWin->m_FrameNumber) != cap_frames.end())
				{
					std::ostringstream out_file;
					out_file << cap_prfx.str() << "_" << VulkanWin->m_FrameNumber << ".cap";
					DrawInstance->CaptureFrame(out_file.str());
				}
			}
			
			// Increment frame number to be sent as push element.
			VulkanWin->m_FrameNumber++;

			// Sewt the cap counter first time.
			if(nbFrames == 0)
				lastCapTime = currentTime;

			// Increment frame counter
			nbFrames++;
			double ddt = currentTime - lastCapTime;
			double diff_time = currentTime - lastTime;
			if (currentTime - lastTime >= 1.0 && doAuto != true)
			{ 
				float fps = static_cast<double>(nbFrames) / diff_time;
				float spf = diff_time / nbFrames;
				 
				std::cout << "Seconds:" << aprCount << " FrameNumber:" << VulkanWin->m_FrameNumber 
					<< " FRate:" << 1000.0 / double(nbFrames) << " ms/F, " 
					<< " FPS:" << nbFrames << " F/s." << std::endl;
				nbFrames = 0;
				lastTime += 1.0;
			}
			// Load the perf data if less than series length
			if (currentTime - lastTime >= 1.0 && doAuto == true)
			{
				perfObj->m_ReportBuffer[aprCount].FrameRate = static_cast<float>(nbFrames);
				//Populate the data
				if (aprCount < seriesLength )
				{
					perfObj->m_ReportBuffer[aprCount].Second = diff_time;
					perfObj->m_ReportBuffer[aprCount].FrameRate = static_cast<double>(nbFrames)/diff_time;
					perfObj->m_ReportBuffer[aprCount].SecondPerFrame = diff_time / nbFrames;
					perfObj->m_ReportBuffer[aprCount].ComputeExecutionTime =
						DrawInstance->m_ComputeCommandObj->m_ExecutionTime;
					perfObj->m_ReportBuffer[aprCount].GraphicsExecutionTime =
						DrawInstance->m_GraphicsCommandObj->m_ExecutionTime;

					for (int ii = 0; ii < rgc->m_DRList.size(); ii++)
						rgc->m_DRList[ii]->AskObject(aprCount);

					for (int ii = 0; ii < rcc->m_DRList.size(); ii++)
						rcc->m_DRList[ii]->AskObject(aprCount);

					//Check for particle number errors in compute
					if((VulkanWin->m_Numparticles-1) != perfObj->m_ReportBuffer[aprCount].NumParticlesComputeCount)
					{
						partErrC = 1;
						ret = 1;					
					}
					if((VulkanWin->m_Numparticles-1) != perfObj->m_ReportBuffer[aprCount].NumParticlesGraphicsCount)
					{
						partErrG = 1;
						ret = 1;
					}
					if(perfObj->m_ReportBuffer[aprCount].NumCollisionsComputeCount != perfObj->m_colcount)
					{
						collErr = 1;
						ret = 1;

					}


					std::ostringstream  objtxt;
					objtxt	<< "perfline,"													// 0-Identifier 
					<< perfObj->m_ReportBuffer[aprCount].Second << ","						// 1- time
					<< perfObj->m_ReportBuffer[aprCount].FrameRate << ","					// 2- fps
					<< 1.0f/perfObj->m_ReportBuffer[aprCount].FrameRate << ","				// 3-cpums: cpu time
					<< perfObj->m_ReportBuffer[aprCount].ComputeExecutionTime << ","		// 4-cms: compute ms
					<< perfObj->m_ReportBuffer[aprCount].GraphicsExecutionTime << ","		// 5-gms: graphics ms				
					<< perfObj->m_partcount << ","											// 6-expectedp: frm tst - generated
					<< VulkanWin->m_Numparticles-1 << ","									// 7-loadedp: loaded into rccdApp
					<< perfObj->m_ReportBuffer[aprCount].NumParticlesComputeCount << ","	// 8-shaderp_comp: counted from compute
					<< perfObj->m_ReportBuffer[aprCount].NumParticlesGraphicsCount << ","	// 9-shaderp_grp: counted from graphics
					<< perfObj->m_colcount << ","											// 10-expectedc: expected collisions
					<< perfObj->m_ReportBuffer[aprCount].NumCollisionsComputeCount << ","	// 11-shaderc: compute counted collisions
					<< perfObj->m_ReportBuffer[aprCount].ThreadCountComp << ","				// 12-threadcount: number of threads compute
					<< VulkanWin->m_SideLength << ","										// 13-sidelen
					<< 	partErrC << ","														// 14-error compute particles
					<< 	partErrG << ","														// 15-error graphics particle
					<< 	collErr << ","														// 16-error compute collsions
					<< std::endl;

					aprCount++;
				}

				

				// If it has been 60 second or the amoint set in series length write the perf data
				// and return.
				if (aprCount == seriesLength && seriesLength != 0)
				{
					vkDeviceWaitIdle(VulkanWin->GetLogicalDevice());
					aprCount++;
					if (perfObj->Doperf(DrawInstance, VulkanWin, tcp, aprCount) != 0)
						return 0;

					if(ret == 1 && stopOnError == true)
						return 1;
					
					return 0;
				}
			
				std::cout << "Seconds:" << aprCount << " FrameNumber:" << VulkanWin->m_FrameNumber << " FRate:" << 1000.0 / double(nbFrames) << " ms/F, " << " FPS:" << nbFrames << " F/s." << std::endl;
				//if (nbFrames < 2)
//					return 3;
				nbFrames = 0;
				lastTime += 1.0;
			}
			// Sleep if frame_delay is set
			if(doAuto != true)
				Sleep(frameDelay);
			//vkDeviceWaitIdle(VulkanWin->GetLogicalDevice());
			
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

std::unordered_set<uint32_t> ParseCaptureFrames(
	const std::vector<const char*>& entries)
{
	std::unordered_set<uint32_t> frames;

	for (const char* entryPtr : entries)
	{
		const std::string entry(entryPtr);
		std::vector<uint32_t> values;
		std::stringstream stream(entry);
		std::string token;

		while (std::getline(stream, token, ':'))
		{
			if (token.empty())
				throw std::runtime_error(
					"Empty value in capture_frames entry: " + entry);

			size_t parsed = 0;
			unsigned long value = std::stoul(token, &parsed);

			if (parsed != token.size() || value > UINT32_MAX)
				throw std::runtime_error(
					"Invalid capture_frames entry: " + entry);

			values.push_back(static_cast<uint32_t>(value));
		}

		if (values.size() == 1)
		{
			frames.insert(values[0]);
			continue;
		}

		uint32_t start;
		uint32_t step;
		uint32_t end;

		if (values.size() == 2)
		{
			start = values[0];
			step = 1;
			end = values[1];
		}
		else if (values.size() == 3)
		{
			start = values[0];
			step = values[1];
			end = values[2];
		}
		else
		{
			throw std::runtime_error(
				"Expected frame, start:end, or start:step:end: " + entry);
		}

		if (step == 0)
			throw std::runtime_error(
				"Capture frame step cannot be zero: " + entry);

		if (start > end)
			throw std::runtime_error(
				"Descending capture frame range: " + entry);

		for (uint64_t frame = start; frame <= end; frame += step)
		{
			frames.insert(static_cast<uint32_t>(frame));

			// Prevent overflow when the range approaches UINT32_MAX.
			if (frame + step > UINT32_MAX)
				break;
		}
	}

	return frames;
}