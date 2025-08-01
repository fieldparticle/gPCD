/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VABufferMemory.cpp $
% $Id: VABufferMemory.cpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef CORE_HPP
#define CORE_HPP
//#define GLFW_INCLUDE_VULKAN
#define GLFW_EXPOSE_NATIVE_WIN32
#define VK_USE_PLATFORM_WIN32_KHR 
#include <GLFW/glfw3.h>
#include <GLFW/glfw3native.h>
//#include "stb_image.h"
#define GLM_FORCE_RADIANS
#define GLM_FORCE_DEPTH_ZERO_TO_ONE
#include <glm/vec4.hpp>
#include <glm/mat4x4.hpp>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <stdexcept>
#include <algorithm>
#include <optional>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <sstream >
#include <strstream>
#include <set>
#include <limits>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <array>
#include <chrono>
#include <ws2tcpip.h>
#include <windows.h>
#include <filesystem>
#include <queue>
#include "mout2_0/mout.hpp"
#include "libconfig.h"
#include "vk_mem_alloc.h"
#include <stack>
extern MsgStream mout;



#define ASSERT_VK(res) if (vk_res != VK_SUCCESS){return EXIT_FAILURE;}
#define ASSERT(res) if (result != EXIT_SUCCESS){ return EXIT_FAILURE;}
static VkResult vk_res = VK_SUCCESS;

#define APP_NAME "Vulkan Cube";

struct HWND_INFO
{
	HINSTANCE hInstance;
	HWND hWnd;
};
#endif
