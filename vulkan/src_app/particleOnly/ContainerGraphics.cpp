/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSet.cpp $
% $Id: DescriptorSet.cpp 28 2023-05-03 19:30:42Z jb $
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

#include "VulkanObj/VulkanApp.hpp"


// Assemble all individual VkDescriptorSetLayoutBindings into an array 
// container of VkDescriptorSetLayoutBinding using a 
// VkDescriptorSetLayoutCreateInfo structure. Different types of 
// VkDescriptorSetLayoutBindings can be assembles in one 
// VkDescriptorSetLayoutBinding. Then call vkCreateDescriptorSetLayout
// to assign the VkDescriptorSetLayout pointer to this layout.

//typedef struct VkDescriptorSetLayoutCreateInfo {
//    VkStructureType                        sType;
//    const void*                            pNext;
//    VkDescriptorSetLayoutCreateFlags       flags; 
//          Don't know
//    uint32_t                               bindingCount; 
//          Number of VkDescriptorSetLayoutBindings
//    const VkDescriptorSetLayoutBinding* pBindings;
//          Array of bindings
//} VkDescriptorSetLayoutCreateInfo;
