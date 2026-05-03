/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VulkanObj.hpp $
% $Id: VulkanObj.hpp 31 2023-06-12 20:17:58Z jb $
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
#include "VulkanObj/TimerObj.hpp"
#include <winsock2.h>
#include "VulkanObj/Core.hpp"
#include "VulkanObj/VulkanDefines.hpp"
#include "VulkanObj/ConfigObj.hpp"
extern ConfigObj* CfgTst;
extern ConfigObj* CfgApp;
extern ConfigObj* MpsApp;
#include "VulkanObj/BaseObj.hpp"
#include "VulkanObj/VulkanObj.hpp"
#include "VulkanObj/SyncObj.hpp" // Needs obj
#include "VulkanObj/SwapChainObj.hpp"
#include "VulkanObj/Resource.hpp"
#include "VulkanObj/ImageObject.hpp"
#include "VulkanObj/RenderPassObj.hpp" // Needs obj
#include "VulkanObj/FrameBufferObj.hpp"// Needs obj
#include "VulkanObj/ContainerObj.hpp" 
#include "VulkanObj/PipelineObj.hpp"
#include "VulkanObj/CommandObj.hpp"
#include "VulkanObj/CommandPoolObj.hpp"
#include "VulkanObj/DrawObj.hpp"
#include "VulkanObj/Input.hpp"
#include "VulkanObj/PhysDevObj.hpp"
#include "VulkanObj/InstanceObj.hpp"
#include "VulkanObj/ResourceVertexObj.hpp"
#include "TCPIP/TCPSObj.hpp"
#include "TCPIP/TCPCObj.hpp"
#include "particleOnly/ParticleOnly.hpp"



void MemStats(VulkanObj* vulkanObj);

#include <glm/glm.hpp>
//#include "objloader.hpp"
#if 0
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_vulkan.h"
//#include "LoadWavefrontFile.hpp"
#endif


extern bool Extflg;
std::vector<std::string> ReadFileByBlocks(const char* filename, TCPObj* tcps);
int Loop(PerfObj* pf, TCPObj* tcp, TCPObj* tcpapp,DrawObj* DrawInstance, VulkanObj* VulkanWin, ResourceGraphicsContainer* rgc, ResourceComputeContainer* rcc);
int NoPerfLoop(PerfObj* perfObj, TCPObj* tcp, TCPObj* tcpsapp,DrawObj* DrawInstance, VulkanObj* VulkanWin, ResourceGraphicsContainer* rgc, ResourceComputeContainer* rcc);
int Capture(uint32_t ImgNum);
int SetupCapture();
int ParticleOnly(PerfObj* perObj, TCPObj* tcp, TCPObj* tcpapp,bool rmtFlag);
int ParticleBoundary(ConfigObj* configVCube);
int ParticleBoundaryV2(ConfigObj* configVCube);
int glsl(std::vector<std::string>& InputArgs, std::vector<char>& OutPutSPV);
int ParticleOnlyGraphics(ConfigObj* configVCube);
void GLFWError(int err, const char* err_str);
void LaunchExecutable(std::string path, std::string cmd) ;