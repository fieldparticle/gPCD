
/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VAInstance.cpp $
% $Id: VAInstance.cpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef VULKANDEFINES
#define VULKANDEFINES

#define VK_FLAGS_NONE 0
#define DEFAULT_FENCE_TIMEOUT 100000000000

const enum DesType
{
	VBW_TYPE_PUSH_CONSTANT,
	VBW_TYPE_STORAGE_BUFFER,
	VBW_TYPE_UNIFORM_BUFFER,
	VBW_TYPE_COMBINED_IMAGE_SAMPLER,
	VBW_TYPE_VERTEX_BUFFER,
	VBW_TYPE_INDEX_BUFFER,
	VBW_TYPE_SUBPASS,
	VBW_TYPE_COMPUTEPIPE,
	VBW_TYPE_GRAPHPIPE,
	VBW_TYPE_GRAPHPIPE01,
	VBW_TYPE_RESOURCECONTAINER,
	VBW_TYPE_PARTICLE_VERTEX,
	VBW_DESCRIPTOR_TYPE_STORAGE_BUFFER,
	VBW_DESCRIPTOR_TYPE_PUSH_CONSTANT,
	VBW_DESCRIPTOR_TYPE_COLLMATRIX,
	VBW_DESCRIPTOR_TYPE_PARTICLE,
	VBW_TYPE_ATOMIC
	};

struct SwapChainSupportDetails 
{
	VkSurfaceCapabilitiesKHR capabilities{};
	std::vector<VkSurfaceFormatKHR> formats{};
	std::vector<VkPresentModeKHR> presentModes{};
};
struct QueueFamilyIndices 
{
    std::optional<uint32_t> graphicsFamily;
    std::optional<uint32_t> presentFamily;
	std::optional<uint32_t> computeFamily;

    bool isComplete() 
	{
        return graphicsFamily.has_value() && presentFamily.has_value() && computeFamily.has_value();
    }
};
struct ObjName {
	VkObjectType ObjNum;
	const char* ObjName;
	glm::vec4	Color;
};
extern bool debugVerbose;
static  PFN_vkSubmitDebugUtilsMessageEXT SubmitDebugUtilsMessageEXT;
static 	PFN_vkCmdBeginDebugUtilsLabelEXT CmdBeginDebugUtilsLabelEXT;
static 	PFN_vkCmdEndDebugUtilsLabelEXT CmdEndDebugUtilsLabelEXT;
static 	PFN_vkCmdInsertDebugUtilsLabelEXT CmdInsertDebugUtilsLabelEXT;
static 	PFN_vkSetDebugUtilsObjectNameEXT SetDebugUtilsObjectNameEXT;
const char* DebugAnnotObjectToString(VkObjectType ObjNum);	
static VKAPI_ATTR VkBool32 VKAPI_CALL DebugCallback(VkDebugUtilsMessageSeverityFlagBitsEXT messageSeverity,
	VkDebugUtilsMessageTypeFlagsEXT messageType,
	const VkDebugUtilsMessengerCallbackDataEXT* pCallbackData,
	void* pUserData);
VkResult CreateDebugUtilsMessengerEXT(VkInstance instance,
    const VkDebugUtilsMessengerCreateInfoEXT* pCreateInfo,
    const VkAllocationCallbacks* pAllocator,
    VkDebugUtilsMessengerEXT* pDebugMessenger);

void DestroyDebugUtilsMessengerEXT(VkInstance instance,
    VkDebugUtilsMessengerEXT debugMessenger,
    const VkAllocationCallbacks* pAllocator);

#endif