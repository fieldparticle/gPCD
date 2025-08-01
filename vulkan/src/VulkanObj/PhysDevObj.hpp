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

#ifndef PhysDevObj_HPP
#define PhysDevObj_HPP

class PhysDevObj : public BaseObj
{
public:
	
	ConfigObj* m_CO;
	uint32_t m_DeviceCount = 0;
	std::vector<VkPhysicalDevice> m_Devices;
	VkPhysicalDeviceProperties m_Properties{};
	uint32_t m_ExtensionCount;
	std::vector<VkExtensionProperties> m_AvailableExtensions;
	std::set<std::string> m_RequiredExtensions;
	SwapChainSupportDetails m_Details;
	uint32_t m_PresentModeCount = 0;
	uint32_t m_FormatCount=0;
	bool m_SwapChainAdequate = false;
	bool m_ExtensionsSupported = false;
	bool m_DeviceSuitable = false;
	bool m_SubGroupSupported = false;
	QueueFamilyIndices m_QFIndices;
	VkPhysicalDeviceFeatures m_DevFeat{};
	VkPhysicalDeviceShaderAtomicFloatFeaturesEXT m_Supportedatomics{};
	VkPhysicalDeviceSampleLocationsPropertiesEXT  m_physDevSampLoc{};
	VkPhysicalDeviceFeatures2 m_Atomicsfeatures;
	VkPhysicalDeviceShaderSMBuiltinsFeaturesNV m_Builtins{};
	VkPhysicalDeviceFeatures m_SupportedFeatures{};
	SwapChainSupportDetails m_SwapChainSupport;
	uint32_t m_QueueFamilyCount = 0;
	std::vector<VkQueueFamilyProperties> m_QueueFamilies{};
	VmaAllocator m_VMAInstance = {};
	void CheckSubGroupProperties(VkPhysicalDevice PhysDev);
	
	//Transfer stuff
	VkPhysicalDevice 	m_PhysicalDevice = VK_NULL_HANDLE;
	VkPhysicalDeviceHostQueryResetFeatures m_Timestampf = {};
	VkPhysicalDeviceShadingRateImageFeaturesNV m_FragFeatures;
	VkPhysicalDeviceFeatures2 m_Otherfeatures{};
	void PrintMemoryProps(std::ofstream &file, VkMemoryPropertyFlags propertyFlags);
	void PrintMemoryHeaps(std::ofstream& file, VkMemoryPropertyFlags propertyFlags);
	void CreatePhysicalDevice();
	void CheckPhysDevFeatureSupport(VkPhysicalDevice PhysDev);
	void CheckPhysDevExtensionSupport(VkPhysicalDevice PhysDev);
	SwapChainSupportDetails QueryPhysDevSwapChainSupport(VkPhysicalDevice PhysDev);
	void IsPhysDevSuitable(VkPhysicalDevice PhysDev);
	void FindPhysDevQueueFamilies(VkPhysicalDevice PhysDev);
	void GetPhysDeviceFeatures();
	void GetPhysDeviceLimits();
	PhysDevObj(VulkanObj* App, std::string Name) : BaseObj(Name, 0, App) {};
	void Create(ConfigObj* CO) {
		m_CO = CO;
		CreatePhysicalDevice();
	};
	virtual void Cleanup() 
	{
		
	};

};

#endif
