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
%*$Revision: 31 $PhysDevObj
%*
%*
%******************************************************************/

#include "VulkanObj/VulkanApp.hpp"

void PhysDevObj::CreatePhysicalDevice()
{
	vkEnumeratePhysicalDevices(m_App->m_Instance, &m_DeviceCount, nullptr);
	if (m_DeviceCount == 0)
	{
		throw std::runtime_error("vkEnumeratePhysicalDevices number of devices is zero.");
	}
	m_Devices.resize(m_DeviceCount);
	vkEnumeratePhysicalDevices(m_App->m_Instance, &m_DeviceCount, m_Devices.data());
	for (const auto& device : m_Devices)
	{
		vkGetPhysicalDeviceProperties(device, &m_Properties);
		uint32_t ver = VK_VERSION_MAJOR(m_Properties.apiVersion);
		uint32_t ver2 = VK_VERSION_MINOR(m_Properties.apiVersion);;

		mout << "Device Available #:" << m_Properties.deviceID << " is:" << m_Properties.deviceName <<
			" API Version:" << ver << "." << ver2 << ende;
		if (strcmp(m_Properties.deviceName, m_App->m_PhysDevice.c_str()) == 0)
		{
			mout << "Looking for:" << m_App->m_PhysDevice.c_str() << " Finding:" << m_Properties.deviceName << ende;
			IsPhysDevSuitable(device);
			if (m_DeviceSuitable)
			{
				mout << "Device Selected #:" <<
					m_Properties.deviceID << " is:" << m_Properties.deviceName << ende;
				m_App->m_PhysicalDevice = device;

				break;
			}
			else
			{
				mout << "No Match:" << m_App->m_PhysDevice.c_str() << " Finding:" << m_Properties.deviceName << ende;

			}

		}
		else
		{

			mout << "Requested device not found Default Device Selected #:" <<
				m_Properties.deviceID << " is:" << m_Properties.deviceName << ende;
			if (m_DeviceSuitable)
			{
				m_App->m_PhysicalDevice = device;
				break;
			}

		}

	}


	if (m_App->m_PhysicalDevice == VK_NULL_HANDLE)
	{
		throw std::runtime_error("Failed to find a suitable GPU!");
	}

	GetPhysDeviceLimits();
	
	m_App->CreateLogicalDevice();
	m_App->NameStaticObjects();
	VmaAllocatorCreateInfo vmaa = {};
	vmaa.device = m_App->GetLogicalDevice();
	vmaa.physicalDevice = m_App->GetPhysicalDevice();
	vmaa.vulkanApiVersion = VK_API_VERSION_1_3;
	vmaa.flags;
	vmaa.instance = m_App->m_Instance;
	vmaa.pAllocationCallbacks;
	vmaa.pDeviceMemoryCallbacks;
	vmaa.pHeapSizeLimit;
	vmaa.preferredLargeHeapBlockSize;
	vmaa.pTypeExternalMemoryHandleTypes;
	vmaa.pVulkanFunctions;
	vmaa.pTypeExternalMemoryHandleTypes;

	VkResult vkresult = vmaCreateAllocator(&vmaa, &m_App->m_vmaAllocator);
	if (vkresult != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "vmaCreateAllocator Failed. Returns:" << vkresult << std::ends;
		throw std::runtime_error(objtxt.str());
	}

	

}
void PhysDevObj::CheckSubGroupProperties(VkPhysicalDevice PhysDev)
{
	//VkPhysicalDeviceSubgroupProperties vkpdsp{};
	//VkStructureType        sType;
	//void* pNext;
	//uint32_t               subgroupSize;
	//VkShaderStageFlags     supportedStages;
	//VkSubgroupFeatureFlags supportedOperations;
	//VkBool32               quadOperationsInAllStages;
	
	
	m_physDevSampLoc.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLE_LOCATIONS_PROPERTIES_EXT;
	m_physDevSampLoc.pNext = nullptr;
	m_physDevSampLoc.sampleLocationSampleCounts = VK_SAMPLE_COUNT_8_BIT ;

	
	VkPhysicalDeviceSubgroupProperties subgroupProperties;
	subgroupProperties.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES;
	subgroupProperties.pNext = nullptr;
	subgroupProperties.subgroupSize = 8;

	VkPhysicalDeviceProperties2 physicalDeviceProperties;
	physicalDeviceProperties.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
	physicalDeviceProperties.pNext = &subgroupProperties;

	vkGetPhysicalDeviceProperties2(PhysDev, &physicalDeviceProperties);
	bool frag = false;
	std::string FragSupp = "no";
	// Example of checking if supported in fragment shader
	if ((subgroupProperties.supportedStages & VK_SHADER_STAGE_FRAGMENT_BIT) != 0) {
		FragSupp = "yes";
		frag = true;
	}
	bool vert = false;
	std::string VertSupp = "no";
	if ((subgroupProperties.supportedStages & VK_SHADER_STAGE_VERTEX_BIT) != 0) {
		VertSupp = "yes";
		vert = true;
	}
	bool comp = false;
	std::string CompSupp = "no";
	if ((subgroupProperties.supportedStages & VK_SHADER_STAGE_COMPUTE_BIT) != 0) {
		CompSupp = "yes";
		comp = true;
	}
	
	if (frag && comp && vert)
		m_SubGroupSupported = true;

	
	mout << "subgroupSize:" << subgroupProperties.subgroupSize
		<< " FragmnentStageSupport:" << FragSupp
		<< " VertexStageSupport:" << VertSupp
		<< " ComputeStageSupport:" << VertSupp
		<< " supportedOperations:" << subgroupProperties.supportedOperations
		<< " quadOperationsInAllStages:" << subgroupProperties.quadOperationsInAllStages
		<< ende;
		
};

VkBool32 VulkanObj::IsDepthFormatSupported(VkPhysicalDevice physicalDevice, VkFormat *depthFormat,VkFormatFeatureFlagBits formatFeature)
{
	// Since all depth formats may be optional, we need to find a suitable depth format to use
	// Start with the highest precision packed format
	std::vector<VkFormat> formatList = {
		VK_FORMAT_D32_SFLOAT_S8_UINT,
		VK_FORMAT_D32_SFLOAT,
		VK_FORMAT_D24_UNORM_S8_UINT,
		VK_FORMAT_D16_UNORM_S8_UINT,
		VK_FORMAT_D16_UNORM
	};

	for (auto& format : formatList)
	{
		VkFormatProperties formatProps;
		vkGetPhysicalDeviceFormatProperties(physicalDevice, format, &formatProps);
		if (formatProps.optimalTilingFeatures & formatFeature)
		{
			*depthFormat = format;
			return true;
		}
	}

	return false;
}

void PhysDevObj::CheckPhysDevFeatureSupport(VkPhysicalDevice PhysDev)
{

	
	if (m_ExtensionsSupported)
	{
		m_SwapChainSupport = QueryPhysDevSwapChainSupport(PhysDev);

		m_SwapChainAdequate = !m_SwapChainSupport.formats.empty()
			&& !m_SwapChainSupport.presentModes.empty();
	}

	VkPhysicalDeviceSampleLocationsPropertiesEXT physicalDeviceSampleLocationsPropertiesEXT{};
	physicalDeviceSampleLocationsPropertiesEXT.sampleLocationSampleCounts = 

	// Get atomics features
	m_Supportedatomics.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT_FEATURES_EXT;
	m_Supportedatomics.pNext = nullptr;

	m_Atomicsfeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
	m_Atomicsfeatures.pNext = &m_Supportedatomics;
	vkGetPhysicalDeviceFeatures2(PhysDev, &m_Atomicsfeatures);
	
	//
	m_FragFeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADING_RATE_IMAGE_FEATURES_NV;
	m_FragFeatures.pNext = nullptr;

	m_Otherfeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
	m_Otherfeatures.pNext = &m_FragFeatures;
	vkGetPhysicalDeviceFeatures2(PhysDev, &m_Otherfeatures);

	//Shader builtin features 
	m_Builtins.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SM_BUILTINS_FEATURES_NV;
	m_Builtins.pNext = nullptr;

	m_Otherfeatures = {};
	m_Otherfeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
	m_Otherfeatures.pNext = &m_Builtins;
	vkGetPhysicalDeviceFeatures2(PhysDev, &m_Otherfeatures);
		
	//Shader builtin features 
	m_Timestampf.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_QUERY_RESET_FEATURES_EXT;
	m_Timestampf.pNext = nullptr;
	m_Timestampf.hostQueryReset = VK_TRUE;
	m_Otherfeatures = {};
	m_Otherfeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
	m_Otherfeatures.pNext = &m_Timestampf;
	vkGetPhysicalDeviceFeatures2(PhysDev, &m_Otherfeatures);


	vkGetPhysicalDeviceFeatures(PhysDev, &m_SupportedFeatures);

	
}
//
//
//
//
void PhysDevObj::CheckPhysDevExtensionSupport(VkPhysicalDevice PhysDev)
{

	vkEnumerateDeviceExtensionProperties(PhysDev, nullptr, &m_ExtensionCount, nullptr);
	m_AvailableExtensions.resize(m_ExtensionCount);
	vkEnumerateDeviceExtensionProperties(PhysDev, nullptr, &m_ExtensionCount, m_AvailableExtensions.data());
	if (m_App->m_SaveExtensions)
	{
		std::ofstream file("DeviceExtensions.log", std::ios::out | std::ios::binary);
		for (uint32_t i = 0; i < m_AvailableExtensions.size(); i++)
		{
			file << m_AvailableExtensions[i].extensionName << std::endl;
		}
		file.close();
	}
	
	std::set<std::string> requiredExtensions(m_App->m_DeviceExtensions.begin(),
		m_App->m_DeviceExtensions.end());

	for (const auto& extension : m_AvailableExtensions)
	{
		requiredExtensions.erase(extension.extensionName);
	}

	m_ExtensionsSupported = requiredExtensions.empty();
}
//
//
//
//
SwapChainSupportDetails PhysDevObj::QueryPhysDevSwapChainSupport(VkPhysicalDevice PhysDev)
{
	

	vkGetPhysicalDeviceSurfaceCapabilitiesKHR(PhysDev, m_App->m_Surface, &m_Details.capabilities);

	
	vkGetPhysicalDeviceSurfaceFormatsKHR(PhysDev, m_App->m_Surface, &m_FormatCount, nullptr);

	if (m_FormatCount != 0)
	{
		m_Details.formats.resize(m_FormatCount);

		vkGetPhysicalDeviceSurfaceFormatsKHR(PhysDev, m_App->m_Surface, &m_FormatCount, m_Details.formats.data());
	}

	

	vkGetPhysicalDeviceSurfacePresentModesKHR(PhysDev, m_App->m_Surface, &m_PresentModeCount, nullptr);

	if (m_PresentModeCount != 0)
	{
		m_Details.presentModes.resize(m_PresentModeCount);
		vkGetPhysicalDeviceSurfacePresentModesKHR(PhysDev, m_App->m_Surface, &m_PresentModeCount, m_Details.presentModes.data());
	}

	return m_Details;
}
//
//
//
// 
void PhysDevObj::IsPhysDevSuitable(VkPhysicalDevice PhysDev)
{

	FindPhysDevQueueFamilies(PhysDev);
	CheckPhysDevExtensionSupport(PhysDev);
	CheckPhysDevFeatureSupport(PhysDev);
	CheckSubGroupProperties(PhysDev);
	mout << "Extension Supported:" << m_ExtensionsSupported
		<< " swapChainAdequate:" << m_SwapChainAdequate
		<< " supportedFeatures.samplerAnisotropy:" << m_SupportedFeatures.samplerAnisotropy
		<< " fragmentStoresAndAtomics:" << m_SupportedFeatures.fragmentStoresAndAtomics << ende;

	m_DeviceSuitable = m_QFIndices.isComplete() &&
		m_ExtensionsSupported &&
		m_SwapChainAdequate &&
		m_SupportedFeatures.samplerAnisotropy &&
		m_SupportedFeatures.fragmentStoresAndAtomics &&
		m_SubGroupSupported;
}
//
//
//
//
void PhysDevObj::FindPhysDevQueueFamilies(VkPhysicalDevice PhysDev)
{
	VkQueueFamilyProperties* pQueueFamilyProperties = {};
	vkGetPhysicalDeviceQueueFamilyProperties(PhysDev, &m_QueueFamilyCount, nullptr);

	
	m_QueueFamilies.resize(m_QueueFamilyCount);

	vkGetPhysicalDeviceQueueFamilyProperties(PhysDev, &m_QueueFamilyCount, m_QueueFamilies.data());



	int i = 0;
	for (const auto& queueFamily : m_QueueFamilies)
	{
		mout << "Grapics Family Index" << ende;
		if (queueFamily.queueFlags & VK_QUEUE_GRAPHICS_BIT)
			mout << "->Graphics Family Index :" << i << ende;

		else if (queueFamily.queueFlags & VK_QUEUE_COMPUTE_BIT)
			mout << "->Compute Family Index :" << i << ende;

		else if (queueFamily.queueFlags & VK_QUEUE_TRANSFER_BIT)
			mout << "->Transfer Family Index :" << i << ende;
		else
			mout << "->Unknown Family Index :" << i << ende;

		if (queueFamily.timestampValidBits > 0)
		{
			m_App->m_TimeStampDivisor=queueFamily.timestampValidBits;
		
			mout << "VkQueryPool Perf Counters supported, count is:" << queueFamily.timestampValidBits
				<< ende;
		}
		else
			mout << "VkQueryPool Perf Counters NOT supported:" << queueFamily.timestampValidBits
			<< ende;

		if ((queueFamily.queueFlags & VK_QUEUE_GRAPHICS_BIT))
		{
			m_QFIndices.graphicsFamily = i;
		}

		if ((queueFamily.queueFlags & VK_QUEUE_COMPUTE_BIT))
		{
			m_QFIndices.computeFamily = i;
		}
		VkBool32 presentSupport = false;

		vkGetPhysicalDeviceSurfaceSupportKHR(PhysDev, i, m_App->m_Surface, &presentSupport);

		if (presentSupport && (queueFamily.queueFlags & VK_QUEUE_GRAPHICS_BIT))
		{
			m_QFIndices.presentFamily = i;
		}

		if (m_QFIndices.isComplete())
		{
			break;
		}

		i++;
	}
	
}
void PhysDevObj::GetPhysDeviceLimits()
{
	


	m_App->m_DevProp.limits = m_App->m_DevLimit;
	m_App->m_DevProp.sparseProperties = m_App->m_DevSProp;
	
	vkGetPhysicalDeviceProperties(m_App->m_PhysicalDevice, &m_App->m_DevProp);
	vkGetPhysicalDeviceMemoryProperties(m_App->m_PhysicalDevice, &m_App->m_DeviceMemory);
	
	m_App->m_DevProp.limits.timestampPeriod;

	if (m_App->m_SaveDevLimits)
	{

		std::ofstream file("DeviceLimits.log", std::ios::out | std::ios::binary);
		file << "devLimit.maxComputeWorkGroupSize[0]:" << m_App->m_DevProp.limits.timestampPeriod << std::endl;
		file << "devLimit.maxComputeWorkGroupSize[0]:" << m_App->m_DevProp.limits.maxComputeWorkGroupSize[0] << std::endl;
		file << "devLimit.maxComputeWorkGroupSize[1]:" << m_App->m_DevProp.limits.maxComputeWorkGroupSize[1] << std::endl;
		file << "devLimit.maxComputeWorkGroupSize[2]:" << m_App->m_DevProp.limits.maxComputeWorkGroupSize[2] << std::endl;
		file << "devLimit.maxComputeWorkGroupCount[0]:" << m_App->m_DevProp.limits.maxComputeWorkGroupCount[0] << std::endl;
		file << "devLimit.maxComputeWorkGroupCount[1]:" << m_App->m_DevProp.limits.maxComputeWorkGroupCount[1] << std::endl;
		file << "devLimit.maxComputeWorkGroupCount[2]:" << m_App->m_DevProp.limits.maxComputeWorkGroupCount[2] << std::endl;
		file << "devLimit.maxComputeWorkGroupInvocations:" << m_App->m_DevProp.limits.maxComputeWorkGroupInvocations << std::endl;
		file << "devLimit.maxComputeSharedMemorySize:" << m_App->m_DevProp.limits.maxComputeSharedMemorySize << std::endl;
		file << "devLimit.maxStorageBufferRange:" << m_App->m_DevProp.limits.maxStorageBufferRange << std::endl;
		file << "devLimit.maxMemoryAllocationCount:" << m_App->m_DevProp.limits.maxMemoryAllocationCount << std::endl;
		file << "devLimit.minMemoryMapAlignment:" << m_App->m_DevProp.limits.minMemoryMapAlignment << std::endl;

		file << "Memory ===========================================" << std::endl;
		file << "DeviceMemoryPrperties.memoryTypeCount:" << m_App->m_DeviceMemory.memoryTypeCount << std::endl;
		file << "Memory Types  ===========================================" << std::endl;
		file << "->memoryTypes.memoryTypeCount:" << m_App->m_DeviceMemory.memoryTypeCount << std::endl;
		for (size_t ii = 0; ii < m_App->m_DeviceMemory.memoryTypeCount; ii++)
		{	
			file << "->memoryTypes.heapIndex:" << m_App->m_DeviceMemory.memoryTypes[ii].heapIndex << std::endl;
			PrintMemoryProps(file, m_App->m_DeviceMemory.memoryTypes[ii].propertyFlags);
		}

		file << "DeviceMemoryPrperties.memoryHeapCount:" << m_App->m_DeviceMemory.memoryHeapCount << std::endl;
		for (size_t ii = 0; ii < m_App->m_DeviceMemory.memoryTypeCount; ii++)
		{
			file << "->memoryHeaps.Size:" 
					<< m_App->m_DeviceMemory.memoryHeaps[ii].size/1073741824 
					<< " GB" << std::endl;
			PrintMemoryHeaps(file, m_App->m_DeviceMemory.memoryHeaps[ii].flags);
		}

		file.close();
	}

}

void PhysDevObj::PrintMemoryProps(std::ofstream &file, VkMemoryPropertyFlags propertyFlags)
{

	if(propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)
		file << "--->VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT" << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)
		file << "--->VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)
		file << "--->VK_MEMORY_PROPERTY_HOST_COHERENT_BIT " << std::endl; 
	if (propertyFlags & VK_MEMORY_PROPERTY_HOST_CACHED_BIT)
		file << "--->VK_MEMORY_PROPERTY_HOST_CACHED_BIT  " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_LAZILY_ALLOCATED_BIT)
		file << "--->VK_MEMORY_PROPERTY_LAZILY_ALLOCATED_BIT  " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_PROTECTED_BIT)
		file << "--->VK_MEMORY_PROPERTY_PROTECTED_BIT " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_DEVICE_COHERENT_BIT_AMD)
		file << "--->VK_MEMORY_PROPERTY_DEVICE_COHERENT_BIT_AMD  " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_DEVICE_UNCACHED_BIT_AMD)
		file << "--->VK_MEMORY_PROPERTY_DEVICE_UNCACHED_BIT_AMD  " << std::endl;
	if (propertyFlags & VK_MEMORY_PROPERTY_RDMA_CAPABLE_BIT_NV)
		file << "--->VK_MEMORY_PROPERTY_RDMA_CAPABLE_BIT_NV  " << std::endl;




}
void PhysDevObj::PrintMemoryHeaps(std::ofstream& file, VkMemoryPropertyFlags propertyFlags)
{

	if (propertyFlags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT)
		file << "--->VK_MEMORY_HEAP_DEVICE_LOCAL_BIT" << std::endl;
	if (propertyFlags & VK_MEMORY_HEAP_MULTI_INSTANCE_BIT)
		file << "--->VK_MEMORY_HEAP_MULTI_INSTANCE_BIT  " << std::endl;
}
void PhysDevObj::GetPhysDeviceFeatures()
{
	
	m_DevFeat.fragmentStoresAndAtomics = true;
	m_DevFeat.fillModeNonSolid = true;
	vkGetPhysicalDeviceFeatures(m_App->m_PhysicalDevice, &m_DevFeat);
	/*
	if (m_SaveExtensions)
	{


		std::ofstream file("PhysicalFeaturess.log", std::ios::out | std::ios::binary);
	file << "robustBufferAccess:" <<  robustBufferAccess <<  std::endl;
	file << "fullDrawIndexUint32:" <<  fullDrawIndexUint32 <<  std::endl;
	file << "imageCubeArray:" <<  imageCubeArray <<  std::endl;
	file << "independentBlend:" <<  independentBlend <<  std::endl;
	file << "geometryShader:" <<  geometryShader <<  std::endl;
	file << "tessellationShader:" <<  tessellationShader <<  std::endl;
	file << "sampleRateShading:" <<  sampleRateShading <<  std::endl;
	file << "dualSrcBlend:" <<  dualSrcBlend <<  std::endl;
	file << "logicOp:" <<  logicOp <<  std::endl;
	file << "multiDrawIndirect:" <<  multiDrawIndirect <<  std::endl;
	file << "drawIndirectFirstInstance:" <<  drawIndirectFirstInstance <<  std::endl;
	file << "depthClamp:" <<  depthClamp <<  std::endl;
	file << "depthBiasClamp:" <<  depthBiasClamp <<  std::endl;
	file << "fillModeNonSolid:" <<  fillModeNonSolid <<  std::endl;
	file << "depthBounds:" <<  depthBounds <<  std::endl;
	file << "wideLines:" <<  wideLines <<  std::endl;
	file << "largePoints:" <<  largePoints <<  std::endl;
	file << "alphaToOne:" <<  alphaToOne <<  std::endl;
	file << "multiViewport:" <<  multiViewport <<  std::endl;
	file << "samplerAnisotropy:" <<  samplerAnisotropy <<  std::endl;
	file << "textureCompressionETC2:" <<  textureCompressionETC2 <<  std::endl;
	file << "textureCompressionASTC_LDR:" <<  textureCompressionASTC_LDR <<  std::endl;
	file << "textureCompressionBC:" <<  textureCompressionBC <<  std::endl;
	file << "occlusionQueryPrecise:" <<  occlusionQueryPrecise <<  std::endl;
	file << "pipelineStatisticsQuery:" <<  pipelineStatisticsQuery <<  std::endl;
	file << "vertexPipelineStoresAndAtomics:" <<  vertexPipelineStoresAndAtomics <<  std::endl;
	file << "fragmentStoresAndAtomics:" <<  fragmentStoresAndAtomics <<  std::endl;
	file << "shaderTessellationAndGeometryPointSize:" <<  shaderTessellationAndGeometryPointSize <<  std::endl;
	file << "shaderImageGatherExtended:" <<  shaderImageGatherExtended <<  std::endl;
	file << "shaderStorageImageExtendedFormats:" <<  shaderStorageImageExtendedFormats <<  std::endl;
	file << "shaderStorageImageMultisample:" <<  shaderStorageImageMultisample <<  std::endl;
	file << "shaderStorageImageReadWithoutFormat:" <<  shaderStorageImageReadWithoutFormat <<  std::endl;
	file << "shaderStorageImageWriteWithoutFormat:" <<  shaderStorageImageWriteWithoutFormat <<  std::endl;
	file << "shaderUniformBufferArrayDynamicIndexing:" <<  shaderUniformBufferArrayDynamicIndexing <<  std::endl;
	file << "shaderSampledImageArrayDynamicIndexing:" <<  shaderSampledImageArrayDynamicIndexing <<  std::endl;
	file << "shaderStorageBufferArrayDynamicIndexing:" <<  shaderStorageBufferArrayDynamicIndexing <<  std::endl;
	file << "shaderStorageImageArrayDynamicIndexing:" <<  shaderStorageImageArrayDynamicIndexing <<  std::endl;
	file << "shaderClipDistance:" <<  shaderClipDistance <<  std::endl;
	file << "shaderCullDistance:" <<  shaderCullDistance <<  std::endl;
	file << "shaderFloat64:" <<  shaderFloat64 <<  std::endl;
	file << "shaderInt64:" <<  shaderInt64 <<  std::endl;
	file << "shaderInt16:" <<  shaderInt16 <<  std::endl;
	file << "shaderResourceResidency:" <<  shaderResourceResidency <<  std::endl;
	file << "shaderResourceMinLod:" <<  shaderResourceMinLod <<  std::endl;
	file << "sparseBinding:" <<  sparseBinding <<  std::endl;
	file << "sparseResidencyBuffer:" <<  sparseResidencyBuffer <<  std::endl;
	file << "sparseResidencyImage2D:" <<  sparseResidencyImage2D <<  std::endl;
	file << "sparseResidencyImage3D:" <<  sparseResidencyImage3D <<  std::endl;
	file << "sparseResidency2Samples:" <<  sparseResidency2Samples <<  std::endl;
	file << "sparseResidency4Samples:" <<  sparseResidency4Samples <<  std::endl;
	file << "sparseResidency8Samples:" <<  sparseResidency8Samples <<  std::endl;
	file << "sparseResidency16Samples:" <<  sparseResidency16Samples <<  std::endl;
	file << "sparseResidencyAliased:" <<  sparseResidencyAliased <<  std::endl;
	file << "variableMultisampleRate:" <<  variableMultisampleRate <<  std::endl;
	file << "inheritedQueries:" <<  inheritedQueries <<  std::endl;

*/

}