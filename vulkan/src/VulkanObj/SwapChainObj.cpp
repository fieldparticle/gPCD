/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/SwapChain.cpp $
% $Id: SwapChain.cpp 31 2023-06-12 20:17:58Z jb $
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

SwapChainSupportDetails SwapChainObj::
    QueryPhysDevSwapChainSupport(VkPhysicalDevice PhysDev)
{
    SwapChainSupportDetails details;

    vkGetPhysicalDeviceSurfaceCapabilitiesKHR(PhysDev, m_App->GetSurface(), &details.capabilities);

    uint32_t formatCount;
    vkGetPhysicalDeviceSurfaceFormatsKHR(PhysDev, m_App->GetSurface(), &formatCount, nullptr);

    if (formatCount != 0) 
	{
        details.formats.resize(formatCount);
		
        vkGetPhysicalDeviceSurfaceFormatsKHR(PhysDev, m_App->GetSurface(), &formatCount, details.formats.data());
    }

    uint32_t presentModeCount;
	
    vkGetPhysicalDeviceSurfacePresentModesKHR(PhysDev, m_App->GetSurface(), &presentModeCount, nullptr);

    if (presentModeCount != 0) 
	{
        details.presentModes.resize(presentModeCount);
        vkGetPhysicalDeviceSurfacePresentModesKHR(PhysDev, m_App->GetSurface(), &presentModeCount, details.presentModes.data());
    }

    return details;
}
