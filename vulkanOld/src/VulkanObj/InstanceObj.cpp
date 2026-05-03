/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VAPhysicalDevice.cpp $
% $Id: VAPhysicalDevice.cpp 31 2023-06-12 20:17:58Z jb $
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
void InstanceObj::Create() 
{
	
	InitWindow();
	CreateInstance();
	m_App->AssignMarkerFunctions();
	m_App->SetupDebugMessenger();
	m_App->CreateReportUtilsMessengerEXT();
	CreateSurface();
};
void InstanceObj::InitWindow()
{
	
	glfwSetErrorCallback(GLFWError);
	glfwInit();
	glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
	
    const GLFWvidmode * mode = glfwGetVideoMode(glfwGetPrimaryMonitor());

    uint32_t window_width = mode->width;
    uint32_t window_height = mode->height;

	int count;
	GLFWmonitor** monitors = glfwGetMonitors(&count);

	if(MpsApp->GetBool("window.usedefault",true) == true)
		m_App->m_Window = glfwCreateWindow(mode->width,
			mode->height, "Vulkan", nullptr, nullptr);
	else
		m_App->m_Window = glfwCreateWindow(MpsApp->GetInt("window.size.w", true),
			MpsApp->GetInt("window.size.h", true), "Vulkan", nullptr, nullptr);
	 glfwSetWindowPos(m_App->m_Window,
                 0,
                 0); 
	glfwSetWindowUserPointer(m_App->m_Window, this);
	glfwSetFramebufferSizeCallback(m_App->m_Window, m_App->FramebufferResizeCallback);
}
void InstanceObj::CreateInstance()
{
	if (m_App->m_EnableValidationLayers && !CheckValidationLayerSupport())
	{
		throw std::runtime_error("validation layers requested, but not available!");
	}


	VkApplicationInfo appInfo{};
	appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
	appInfo.pApplicationName = "Field Paricle Method";
	appInfo.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
	appInfo.pEngineName = "No Engine";
	appInfo.engineVersion = VK_MAKE_VERSION(1, 0, 0);
	appInfo.apiVersion = VK_API_VERSION_1_3;


	VkInstanceCreateInfo createInfo{};
	createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
	createInfo.pApplicationInfo = &appInfo;



	GetRequiredInstanceExtensions();
	createInfo.enabledExtensionCount = static_cast<uint32_t>(m_App->m_InstanceExtensions.size());
	createInfo.ppEnabledExtensionNames = m_App->m_InstanceExtensions.data();

	VkDebugUtilsMessengerCreateInfoEXT debugCreateInfo{};


	if (m_App->m_EnableValidationLayers)
	{

		mout << "Validation Layers Enabled!" << ende;
		createInfo.enabledLayerCount = static_cast<uint32_t>(m_App->m_ValidationLayers.size());
		createInfo.ppEnabledLayerNames = m_App->m_ValidationLayers.data();
		m_App->PopulateDebugMessengerCreateInfo(debugCreateInfo);
		//createInfo.pNext = (VkDebugUtilsMessengerCreateInfoEXT*)&debugCreateInfo;

		VkValidationFeatureEnableEXT enabled[] = { VK_VALIDATION_FEATURE_ENABLE_DEBUG_PRINTF_EXT };
		VkValidationFeaturesEXT      features{ VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT };
		features.disabledValidationFeatureCount = 0;
		features.enabledValidationFeatureCount = 1;
		features.pDisabledValidationFeatures = nullptr;
		features.pEnabledValidationFeatures = enabled;
		features.pNext = (VkDebugUtilsMessengerCreateInfoEXT*)&debugCreateInfo;
		createInfo.pNext = &features;


	}
	else
	{
		createInfo.enabledLayerCount = 0;
		createInfo.pNext = nullptr;
	}

	if (vkCreateInstance(&createInfo, nullptr, &m_App->m_Instance) != VK_SUCCESS)
	{
		throw std::runtime_error("InstanceObj::CreateInstance failed at vkCreateInstance");
	}

}
bool InstanceObj::CheckValidationLayerSupport()
{
	uint32_t layerCount;

	//https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/vkEnumerateInstanceLayerProperties.html
	vkEnumerateInstanceLayerProperties(&layerCount, nullptr);

	//https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VkLayerProperties.html
	std::vector<VkLayerProperties> availableLayers(layerCount);

	vkEnumerateInstanceLayerProperties(&layerCount, availableLayers.data());

	for (const char* layerName : m_App->m_ValidationLayers)
	{
		bool layerFound = false;


		for (const auto& layerProperties : availableLayers)
		{
			if (strcmp(layerName, layerProperties.layerName) == 0)
			{
				layerFound = true;
				break;
			}
		}

		if (!layerFound)
		{
			return false;
		}
	}

	return true;
}

#if 0
void InstanceObj::AssignMarkerFunctions()
{
	// Setup the function pointers
	CmdBeginDebugUtilsLabelEXT =
		reinterpret_cast<PFN_vkCmdBeginDebugUtilsLabelEXT>(
			vkGetInstanceProcAddr(
				m_App->m_Instance,
				"vkCmdBeginDebugUtilsLabelEXT"));

	if (CmdBeginDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdBeginDebugUtilsLabelEXT unassigned.");
	}

	CmdEndDebugUtilsLabelEXT = reinterpret_cast<PFN_vkCmdEndDebugUtilsLabelEXT>(vkGetInstanceProcAddr(
		m_App->m_Instance,
		"vkCmdEndDebugUtilsLabelEXT"));
	if (CmdEndDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdEndDebugUtilsLabelEXT unassigned.");
	}

	CmdInsertDebugUtilsLabelEXT = reinterpret_cast<PFN_vkCmdInsertDebugUtilsLabelEXT>(vkGetInstanceProcAddr(
		m_App->m_Instance,
		"vkCmdInsertDebugUtilsLabelEXT"));
	if (CmdInsertDebugUtilsLabelEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions CmdInsertDebugUtilsLabelEXT unassigned.");
	}

	SetDebugUtilsObjectNameEXT = reinterpret_cast<PFN_vkSetDebugUtilsObjectNameEXT>(vkGetInstanceProcAddr(
		m_App->m_Instance,
		"vkSetDebugUtilsObjectNameEXT"));

	if (SetDebugUtilsObjectNameEXT == VK_NULL_HANDLE)
	{
		throw std::runtime_error("VulkanObj::AssignMarkerFunctions SetDebugUtilsObjectNameEXT unassigned.");
	}
}

#endif
void InstanceObj::CreateSurface()
{
	if (glfwCreateWindowSurface(m_App->m_Instance, m_App->m_Window, nullptr, &m_App->m_Surface)
		!= VK_SUCCESS)
	{
		throw std::runtime_error("Failed to create window surface!");
	}
}
std::vector<const char*> InstanceObj::GetRequiredInstanceExtensions()
{

	uint32_t instanceExtensionCount = 0;
	vkEnumerateInstanceExtensionProperties(nullptr, &instanceExtensionCount, nullptr);

	std::vector<VkExtensionProperties> availableExtensions(instanceExtensionCount);
	vkEnumerateInstanceExtensionProperties(nullptr,
		&instanceExtensionCount, availableExtensions.data());

	if (m_App->m_SaveExtensions)
	{
		std::ofstream file("InstanceExtensions.log", std::ios::out | std::ios::binary);
		for (uint32_t i = 0; i < availableExtensions.size(); i++)
		{
			file << availableExtensions[i].extensionName << std::endl;
		}
		file.close();
	}

	uint32_t glfwExtensionCount = 0;
	const char** glfwExtensions;

	//https://pub.dev/documentation/glfw/latest/glfw/glfwGetRequiredInstanceExtensions.html
	glfwExtensions = glfwGetRequiredInstanceExtensions(&glfwExtensionCount);

	std::vector<const char*> extensions(glfwExtensions, glfwExtensions + glfwExtensionCount);

	m_App->m_InstanceExtensions.insert(m_App->m_InstanceExtensions.end(), extensions.begin(), extensions.end());
	if (m_App->m_SaveExtensions)
	{
		std::ofstream file("ActiveInstanceExtensions.log", std::ios::out | std::ios::binary);
		for (uint32_t i = 0; i < m_App->m_InstanceExtensions.size(); i++)
		{
			file << m_App->m_InstanceExtensions[i] << std::endl;
		}
		file.close();
	}

	return extensions;
}

