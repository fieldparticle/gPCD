/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VADebug.cpp $
% $Id: VADebug.cpp 31 2023-06-12 20:17:58Z jb $
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
#define VK_USE_PLATFORM_WIN32_KHR
#include "vulkan\vulkan.hpp"	
bool Extflg = false;

void VulkanObj::NameObject(VkObjectType objectType, uint64_t objectHandle, const char* pObjectName)
{
	#ifndef NDEBUG
	//https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VkObjectType.html
	VkDebugUtilsObjectNameInfoEXT nameobj{};
	nameobj.sType = VK_STRUCTURE_TYPE_DEBUG_UTILS_OBJECT_NAME_INFO_EXT;
	nameobj.pNext = nullptr;
	nameobj.objectType = objectType;
	nameobj.objectHandle = objectHandle;
	nameobj.pObjectName = pObjectName;

	SetDebugUtilsObjectNameEXT(m_LogicalDevice, &nameobj);
#endif


}
#if 1
void VulkanObj::AssignMarkerFunctions()
{
#ifndef NDEBUG
	// Setup the function pointers
	CmdBeginDebugUtilsLabelEXT =
		reinterpret_cast<PFN_vkCmdBeginDebugUtilsLabelEXT>(
			vkGetInstanceProcAddr(
				m_Instance,
				"vkCmdBeginDebugUtilsLabelEXT"));

	
	if (CmdBeginDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdBeginDebugUtilsLabelEXT unassigned.");
	}

	CmdEndDebugUtilsLabelEXT = reinterpret_cast<PFN_vkCmdEndDebugUtilsLabelEXT>(vkGetInstanceProcAddr(
		m_Instance,
		"vkCmdEndDebugUtilsLabelEXT"));
	if (CmdEndDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdEndDebugUtilsLabelEXT unassigned.");
	}

	CmdInsertDebugUtilsLabelEXT = reinterpret_cast<PFN_vkCmdInsertDebugUtilsLabelEXT>(vkGetInstanceProcAddr(
		m_Instance,
		"vkCmdInsertDebugUtilsLabelEXT"));
	if (CmdInsertDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdInsertDebugUtilsLabelEXT unassigned.");
	}

	SetDebugUtilsObjectNameEXT = reinterpret_cast<PFN_vkSetDebugUtilsObjectNameEXT>(vkGetInstanceProcAddr(
		m_Instance,
		"vkSetDebugUtilsObjectNameEXT"));

	if (SetDebugUtilsObjectNameEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions SetDebugUtilsObjectNameEXT unassigned.");
	}

	
#endif
}
#endif

void VulkanObj::NameStaticObjects()
{

	std::string str_tmp;
	
	NameObject(VK_OBJECT_TYPE_PHYSICAL_DEVICE, 
		(uint64_t)m_PhysicalDevice, m_PhysDevice.c_str());
	std::string appnm = m_AppName +"LogicalDevice";
	NameObject(VK_OBJECT_TYPE_DEVICE, (uint64_t)m_LogicalDevice,appnm.c_str());
	//NameObject(VK_OBJECT_TYPE_INSTANCE, (uint64_t)&instance, "FPM Insytance\0");

}

static VKAPI_ATTR VkBool32 VKAPI_CALL ReportCallback(VkDebugReportFlagsEXT flags,
	VkDebugReportObjectTypeEXT objectType,
	uint64_t object,
	size_t location,
	int32_t messageCode,
	const char* pLayerPrefix,
	const char* pMessage,
	void* pUserData)
{
	if (flags & VK_DEBUG_REPORT_INFORMATION_BIT_EXT)
	{
		std::string msg = pMessage;
		size_t last = msg.find_last_of('|');
		size_t endof = msg.size();
		std::string pch = msg.substr(last+1, endof);
		mout << pch.c_str() << ende;
	}

	return false;

}
VkResult VulkanObj::CreateReportUtilsMessengerEXT()
	
{
	
		VkDebugReportCallbackCreateInfoEXT drcb{};
	drcb.sType = VK_STRUCTURE_TYPE_DEBUG_REPORT_CALLBACK_CREATE_INFO_EXT;
	drcb.pNext = nullptr;
	drcb.flags = VK_DEBUG_REPORT_INFORMATION_BIT_EXT |
		VK_DEBUG_REPORT_WARNING_BIT_EXT |
		VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT |
		VK_DEBUG_REPORT_ERROR_BIT_EXT |
		VK_DEBUG_REPORT_DEBUG_BIT_EXT;
	drcb.pfnCallback = ReportCallback;
	

	drcb.pUserData = nullptr;
	auto func = (PFN_vkCreateDebugReportCallbackEXT)vkGetInstanceProcAddr(
		m_Instance, "vkCreateDebugReportCallbackEXT");
	if (func != nullptr) 
	{
		return func(m_Instance, &drcb, nullptr, &m_ReportMessenger);
	}
	else
	{
		return VK_ERROR_EXTENSION_NOT_PRESENT;
	}
	
}
//
//
//
//
void DestroyDebugUtilsMessengerEXT(VkInstance instance, VkDebugUtilsMessengerEXT debugMessenger, const VkAllocationCallbacks* pAllocator) {
    auto func = (PFN_vkDestroyDebugUtilsMessengerEXT) vkGetInstanceProcAddr(instance, "vkDestroyDebugUtilsMessengerEXT");
    if (func != nullptr) {
        func(instance, debugMessenger, pAllocator);
    }

}
void VulkanObj::DestroyReportUtilsMessengerEXT()
{
	
	auto vkDestroyDebugReportCallbackEXT = 
		PFN_vkDestroyDebugReportCallbackEXT( vkGetInstanceProcAddr( m_Instance, "vkDestroyDebugReportCallbackEXT" ) );
	if (vkDestroyDebugReportCallbackEXT != nullptr) {
		vkDestroyDebugReportCallbackEXT(m_Instance, m_ReportMessenger, nullptr);}

}

bool debugVerbose = false;
static VKAPI_ATTR VkBool32 VKAPI_CALL debugCallback(VkDebugUtilsMessageSeverityFlagBitsEXT messageSeverity,
	VkDebugUtilsMessageTypeFlagsEXT messageType,
	const VkDebugUtilsMessengerCallbackDataEXT* pCallbackData,
	void* pUserData) {
	
	const char validation[] = "Validation\0";
	const char performance[] = "Performance";
	const char error[] = "ERROR";
	const char warning[] = "WARNING";
	const char unknownType[] = "UNKNOWN_TYPE";
	const char unknownSeverity[] = "UNKNOWN_SEVERITY";
	const char* typeString = unknownType;
	const char* severityString = unknownSeverity;
	const char* messageIdName = pCallbackData->pMessageIdName;
	int32_t messageIdNumber = pCallbackData->messageIdNumber;
	const char* message = pCallbackData->pMessage;

	std::string msgstr;

	if (messageSeverity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT)
	{
		msgstr = "Process Error: ";
		Extflg = true;
	}
	else if (messageSeverity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT)
	{
		msgstr = "Process Warning: ";
		Extflg = true;
	}
	else if (messageSeverity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT)
	{

		msgstr = "Process Verbose: ";
		//if (!debugVerbose)
			//return VK_FALSE;
	}
	else if (messageSeverity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT)
	{

		msgstr = "Process Info: ";
		Extflg = true;

	}
	else if (messageSeverity & VK_DEBUG_REPORT_ERROR_BIT_EXT)
	{

		mout << pCallbackData->pMessage << ende;
		
	}


	// Append Message Type
	if (messageType & VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT)
	{
		msgstr += " :General:";
	}
	else if (messageType & VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT)
	{
		msgstr += " :Validation:";
		//validation_error = 1;
	}
	else if (messageType & VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT)
	{
		msgstr += " :Performance:";
	}

	std::ostringstream  objtxt;
	
	size_t len = strlen(pCallbackData->pMessage)+4096;
	
	char* tmp_message = new char[len];
	memset(tmp_message, 0, sizeof(len));
	//if (strstr(pCallbackData->pMessage, "VkDebugReportCallbackEXT"))
	//	return VK_FALSE;
	sprintf(tmp_message, "%s - Message ID Number: %u,Message ID Name: %s Message ID String :\n%s",
		msgstr.c_str(),
		pCallbackData->messageIdNumber,
		pCallbackData->pMessageIdName,
		pCallbackData->pMessage);
	
	
	objtxt << tmp_message;
	memset(tmp_message, 0, sizeof(tmp_message));
			
	if (pCallbackData->objectCount > 0)
	{
		sprintf(tmp_message, "\n Objects - %d\n", pCallbackData->objectCount);
		objtxt << tmp_message;
		memset(tmp_message, 0, sizeof(tmp_message));
		for (uint32_t object = 0; object < pCallbackData->objectCount; ++object)
		{

			sprintf(tmp_message, " Object[%d] - Type %s, Value %p, Name \"%s\"\n",
				object,
				DebugAnnotObjectToString(pCallbackData->pObjects[object].objectType),
				(void*)(pCallbackData->pObjects[object].objectHandle),
				pCallbackData->pObjects[object].pObjectName);
			objtxt.seekp(0, std::ios_base::end);
			objtxt << tmp_message;
			memset(tmp_message, 0, sizeof(tmp_message));

		}
	}

	if (pCallbackData->cmdBufLabelCount > 0)
	{

		sprintf(tmp_message, "\n Command Buffer Labels - %d\n", pCallbackData->cmdBufLabelCount);
		objtxt.seekp(0, std::ios_base::end);
		objtxt << tmp_message;
		memset(tmp_message, 0, sizeof(tmp_message));

		for (uint32_t label = 0; label < pCallbackData->cmdBufLabelCount; ++label)
		{
			sprintf(tmp_message,
				" Label[%d] - %s { %f, %f, %f, %f}\n",
				label,
				pCallbackData->pCmdBufLabels[label].pLabelName,
				pCallbackData->pCmdBufLabels[label].color[0],
				pCallbackData->pCmdBufLabels[label].color[1],
				pCallbackData->pCmdBufLabels[label].color[2],
				pCallbackData->pCmdBufLabels[label].color[3]);
			objtxt.seekp(0, std::ios_base::end);
			objtxt << tmp_message;
			memset(tmp_message, 0, sizeof(tmp_message));
		}
	}
	
	//throw std::runtime_error(objtxt.str().c_str());
	if(Extflg == true)
		mout << objtxt.str().c_str() << ende;
	else
		mout << objtxt.str().c_str() << ende;

	return VK_FALSE;
}


VkResult CreateDebugUtilsMessengerEXT(VkInstance instance,
    const VkDebugUtilsMessengerCreateInfoEXT* pCreateInfo, 
    const VkAllocationCallbacks* pAllocator, 
    VkDebugUtilsMessengerEXT* pDebugMessenger) 
{

	

    auto func = (PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance, "vkCreateDebugUtilsMessengerEXT");
    if (func != nullptr) {
        return func(instance, pCreateInfo, pAllocator, pDebugMessenger);
    }
    else {
        return VK_ERROR_EXTENSION_NOT_PRESENT;
    }
	
	//if (m_DDRCE == VK_NULL_HANDLE)
	//{
//		throw std::runtime_error("VulkanObj::AssignMarkerFunctions vkDestroyDebugReportCallbackEXT unassigned.");
//	}

}
//
//
//
//
#if 0
void DestroyDebugUtilsMessengerEXT(VkInstance instance,
    VkDebugUtilsMessengerEXT debugMessenger,
    const VkAllocationCallbacks* pAllocator) 
{
    auto func = (PFN_vkDestroyDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance, "vkDestroyDebugUtilsMessengerEXT");
    if (func != nullptr) {
        func(instance, debugMessenger, pAllocator);
    }
}
#endif
//
// 
//
//
//
void VulkanObj::PopulateDebugMessengerCreateInfo(VkDebugUtilsMessengerCreateInfoEXT& createInfo) {
        createInfo = {};
        createInfo.sType = VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT;
        createInfo.messageSeverity =    VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT |
                                        VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT  | 
                                        VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;

        createInfo.messageType =    VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT | 
									VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT | 
                                    VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT;
        createInfo.pfnUserCallback = debugCallback;
    }
//
//
//
//

void VulkanObj::SetupDebugMessenger()
{
	if (!m_EnableValidationLayers) return;

	VkDebugUtilsMessengerCreateInfoEXT createInfo;
	PopulateDebugMessengerCreateInfo(createInfo);

	if (CreateDebugUtilsMessengerEXT(
		m_Instance, &createInfo, nullptr, &m_DebugMessenger) != VK_SUCCESS)
	{
		throw std::runtime_error("failed to set up debug messenger!");
	}
}

//
//
//
//



std::vector <ObjName> NameAry =
{
	{VK_OBJECT_TYPE_UNKNOWN,"VK_OBJECT_TYPE_UNKNOWN",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_INSTANCE,"VK_OBJECT_TYPE_INSTANCE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PHYSICAL_DEVICE,"VK_OBJECT_TYPE_PHYSICAL_DEVICE",{1.0,0.0,0.0,1.0} },
	{VK_OBJECT_TYPE_DEVICE, "VK_OBJECT_TYPE_DEVICE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_QUEUE, "VK_OBJECT_TYPE_QUEUE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SEMAPHORE, "VK_OBJECT_TYPE_SEMAPHORE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_COMMAND_BUFFER, "VK_OBJECT_TYPE_COMMAND_BUFFER",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_FENCE, "VK_OBJECT_TYPE_FENCE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DEVICE_MEMORY, "VK_OBJECT_TYPE_DEVICE_MEMORY",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_BUFFER, "VK_OBJECT_TYPE_BUFFER",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_IMAGE, "VK_OBJECT_TYPE_IMAGE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_EVENT, "VK_OBJECT_TYPE_EVENT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_QUERY_POOL, "VK_OBJECT_TYPE_QUERY_POOL",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_BUFFER_VIEW, "VK_OBJECT_TYPE_BUFFER_VIEW",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_IMAGE_VIEW, "VK_OBJECT_TYPE_IMAGE_VIEW",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SHADER_MODULE, "VK_OBJECT_TYPE_SHADER_MODULE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PIPELINE_CACHE, "VK_OBJECT_TYPE_PIPELINE_CACHE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PIPELINE_LAYOUT, "VK_OBJECT_TYPE_PIPELINE_LAYOUT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_RENDER_PASS, "VK_OBJECT_TYPE_RENDER_PASS",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PIPELINE, "VK_OBJECT_TYPE_PIPELINE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DESCRIPTOR_SET_LAYOUT, "VK_OBJECT_TYPE_DESCRIPTOR_SET_LAYOUT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SAMPLER, "VK_OBJECT_TYPE_SAMPLER",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DESCRIPTOR_POOL, "VK_OBJECT_TYPE_DESCRIPTOR_POOL",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DESCRIPTOR_SET, "VK_OBJECT_TYPE_DESCRIPTOR_SET",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_FRAMEBUFFER, "VK_OBJECT_TYPE_FRAMEBUFFER",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_COMMAND_POOL, "VK_OBJECT_TYPE_COMMAND_POOL",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SAMPLER_YCBCR_CONVERSION, "VK_OBJECT_TYPE_SAMPLER_YCBCR_CONVERSION",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DESCRIPTOR_UPDATE_TEMPLATE, "VK_OBJECT_TYPE_DESCRIPTOR_UPDATE_TEMPLATE",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PRIVATE_DATA_SLOT, "VK_OBJECT_TYPE_PRIVATE_DATA_SLOT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SURFACE_KHR, "VK_OBJECT_TYPE_SURFACE_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SWAPCHAIN_KHR, "VK_OBJECT_TYPE_SWAPCHAIN_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DISPLAY_KHR, "VK_OBJECT_TYPE_DISPLAY_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DISPLAY_MODE_KHR, "VK_OBJECT_TYPE_DISPLAY_MODE_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DEBUG_REPORT_CALLBACK_EXT, "VK_OBJECT_TYPE_DEBUG_REPORT_CALLBACK_EXT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_VIDEO_SESSION_KHR, "VK_OBJECT_TYPE_VIDEO_SESSION_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_VIDEO_SESSION_PARAMETERS_KHR, "VK_OBJECT_TYPE_VIDEO_SESSION_PARAMETERS_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_CU_MODULE_NVX, "VK_OBJECT_TYPE_CU_MODULE_NVX",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_CU_FUNCTION_NVX, "VK_OBJECT_TYPE_CU_FUNCTION_NVX",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DEBUG_UTILS_MESSENGER_EXT, "VK_OBJECT_TYPE_DEBUG_UTILS_MESSENGER_EXT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_ACCELERATION_STRUCTURE_KHR, "VK_OBJECT_TYPE_ACCELERATION_STRUCTURE_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_VALIDATION_CACHE_EXT, "VK_OBJECT_TYPE_VALIDATION_CACHE_EXT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_ACCELERATION_STRUCTURE_NV, "VK_OBJECT_TYPE_ACCELERATION_STRUCTURE_NV",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PERFORMANCE_CONFIGURATION_INTEL, "VK_OBJECT_TYPE_PERFORMANCE_CONFIGURATION_INTEL",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DEFERRED_OPERATION_KHR, "VK_OBJECT_TYPE_DEFERRED_OPERATION_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_INDIRECT_COMMANDS_LAYOUT_NV, "VK_OBJECT_TYPE_INDIRECT_COMMANDS_LAYOUT_NV",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_BUFFER_COLLECTION_FUCHSIA, "VK_OBJECT_TYPE_BUFFER_COLLECTION_FUCHSIA",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_MICROMAP_EXT, "VK_OBJECT_TYPE_MICROMAP_EXT",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_OPTICAL_FLOW_SESSION_NV, "VK_OBJECT_TYPE_OPTICAL_FLOW_SESSION_NV",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_DESCRIPTOR_UPDATE_TEMPLATE_KHR, "VK_OBJECT_TYPE_DESCRIPTOR_UPDATE_TEMPLATE_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_SAMPLER_YCBCR_CONVERSION_KHR, "VK_OBJECT_TYPE_SAMPLER_YCBCR_CONVERSION_KHR",{1.0,0.0,0.0,1.0}},
	{VK_OBJECT_TYPE_PRIVATE_DATA_SLOT_EXT, "VK_OBJECT_TYPE_PRIVATE_DATA_SLOT_EXT",{1.0,0.0,0.0,1.0}},
};


const char* DebugAnnotObjectToString(VkObjectType ObjNum)
{

	for (uint32_t ii = 0; ii < NameAry.size(); ii++)
	{

		if (NameAry[ii].ObjNum == ObjNum)
			return NameAry[ii].ObjName;
	}
	return nullptr;
}

