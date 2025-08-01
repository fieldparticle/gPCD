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
#ifndef MPSVERIFY_HPP
#define MPSVERIFY_HPP
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
#include <windows.h>
#include <filesystem>
#include <queue>
#include "mout2_0/mout.hpp"
#include "libconfig.h"
extern MsgStream mout;
#include "VerifyConfigObj.hpp"
extern VerifyConfigObj* cfg;
uint32_t ArrayToIndex(uint32_t x, uint32_t y, uint32_t z, uint32_t len);
void IndexToArray(uint32_t index, uint32_t len, uint32_t* ary);
void VerifyArrayIndexing();
void VerifyArrayIndexingV2();
uint32_t CountCollisions(bool);
#endif
