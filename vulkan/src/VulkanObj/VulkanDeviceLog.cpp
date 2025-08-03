/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VALogicalDevice.cpp $
% $Id: VALogicalDevice.cpp 31 2023-06-12 20:17:58Z jb $
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

//
//
//
//
void VulkanObj::CreateLogicalDevice() {
    m_QueueFamiliesIndexes = m_QA->m_QFIndices;// FindPhysDevQueueFamilies(m_PhysicalDevice);

    std::vector<VkDeviceQueueCreateInfo> queueCreateInfos;

        std::set<uint32_t> uniqueQueueFamilies = {
            m_QueueFamiliesIndexes.graphicsFamily.value(),
            m_QueueFamiliesIndexes.presentFamily.value(),
            m_QueueFamiliesIndexes.computeFamily.value()};

        float queuePriority = 1.0f;
        for (uint32_t queueFamily : uniqueQueueFamilies) 
		{
            VkDeviceQueueCreateInfo queueCreateInfo{};
            queueCreateInfo.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
			queueCreateInfo.pNext = nullptr;
            queueCreateInfo.queueFamilyIndex = queueFamily;
            queueCreateInfo.queueCount = 1;
            queueCreateInfo.pQueuePriorities = &queuePriority;
            queueCreateInfos.push_back(queueCreateInfo);
        }
       
        VkPhysicalDeviceHostQueryResetFeatures resetFeatures;
        resetFeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_HOST_QUERY_RESET_FEATURES;
        resetFeatures.pNext = nullptr;
        resetFeatures.hostQueryReset = VK_TRUE;

        
        VkPhysicalDeviceShaderSMBuiltinsFeaturesNV builtins{};
        builtins.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SM_BUILTINS_FEATURES_NV;
        builtins.pNext = &resetFeatures;
        builtins.shaderSMBuiltins = VK_TRUE;
        VkPhysicalDeviceFeatures deviceFeatures{};
        // For textures
        deviceFeatures.samplerAnisotropy = VK_TRUE;
        deviceFeatures.vertexPipelineStoresAndAtomics = VK_TRUE;
		deviceFeatures.fragmentStoresAndAtomics = VK_TRUE;
		deviceFeatures.sampleRateShading = VK_TRUE;
		deviceFeatures.geometryShader = VK_TRUE;
        deviceFeatures.shaderClipDistance = VK_TRUE;
        deviceFeatures.fillModeNonSolid = VK_TRUE;

        VkPhysicalDeviceShadingRateImageFeaturesNV fragFeatures{};
        fragFeatures.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADING_RATE_IMAGE_FEATURES_NV;
        fragFeatures.pNext =&builtins;
        fragFeatures.shadingRateImage = VK_TRUE;

       

        VkPhysicalDeviceShaderAtomicFloatFeaturesEXT supportedatomics{};
        supportedatomics.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT_FEATURES_EXT;
        supportedatomics.pNext = &fragFeatures;
        supportedatomics.shaderBufferFloat32AtomicAdd = VK_TRUE;
        supportedatomics.shaderBufferFloat32Atomics = VK_TRUE;
        supportedatomics.shaderBufferFloat64AtomicAdd = VK_TRUE;
        supportedatomics.shaderBufferFloat64Atomics = VK_TRUE;
        supportedatomics.shaderImageFloat32AtomicAdd = VK_TRUE;
        supportedatomics.shaderImageFloat32Atomics = VK_TRUE;
        supportedatomics.shaderSharedFloat64AtomicAdd = VK_TRUE;
        supportedatomics.shaderSharedFloat64Atomics = VK_TRUE;
        supportedatomics.sparseImageFloat32AtomicAdd = VK_TRUE;
        supportedatomics.sparseImageFloat32Atomics = VK_TRUE;


        VkPhysicalDeviceFragmentShaderInterlockFeaturesEXT interlock{};
        interlock.sType= VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_INTERLOCK_FEATURES_EXT;
        interlock.pNext = &supportedatomics;
        interlock.fragmentShaderSampleInterlock = VK_TRUE;
        interlock.fragmentShaderPixelInterlock = VK_TRUE;
        interlock.fragmentShaderShadingRateInterlock = VK_TRUE;
        
        VkDeviceCreateInfo createInfo{};
        createInfo.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;

        createInfo.queueCreateInfoCount = static_cast<uint32_t>(queueCreateInfos.size());
        createInfo.pQueueCreateInfos = queueCreateInfos.data();
		createInfo.pNext = &interlock;
        createInfo.pEnabledFeatures = &deviceFeatures;

        createInfo.enabledExtensionCount = static_cast<uint32_t>(m_DeviceExtensions.size());
        createInfo.ppEnabledExtensionNames = m_DeviceExtensions.data();

        for (uint32_t i = 0; i < m_DeviceExtensions.size(); i++)
        {
            mout << "DEVICE EXTENSION:" << m_DeviceExtensions[i] << ende;
        }

        if (m_SaveExtensions)
        {
            std::ofstream file("ActiveDeviceExtensions.log", std::ios::out | std::ios::binary);
            for (uint32_t i = 0; i < m_DeviceExtensions.size(); i++)
            {
                file << m_DeviceExtensions[i] << std::endl;
            }
            file.close();
        }

        if (m_EnableValidationLayers) 
		{
            createInfo.enabledLayerCount = static_cast<uint32_t>(m_ValidationLayers.size());
            createInfo.ppEnabledLayerNames = m_ValidationLayers.data();
        } else 
		{
            createInfo.enabledLayerCount = 0;
        }

        if (vkCreateDevice(m_PhysicalDevice, &createInfo, nullptr, &m_LogicalDevice) != VK_SUCCESS) 
		{
            throw std::runtime_error("VulkanObj::CreateLogicalDevice() Create Failed");
        }

        std::string pd = m_AppName + " Physical Device";
        NameObject(VK_OBJECT_TYPE_PHYSICAL_DEVICE, (uint64_t)m_PhysicalDevice, pd.c_str());

		vkGetDeviceQueue(m_LogicalDevice, 
            m_QueueFamiliesIndexes.graphicsFamily.value(),
				0, 
				&m_GraphicsQueue);

		std::string qnm = m_AppName + " GraphicsQueue";
		NameObject(VK_OBJECT_TYPE_QUEUE, (uint64_t)m_GraphicsQueue, qnm.c_str());
		
		vkGetDeviceQueue(m_LogicalDevice, 
            m_QueueFamiliesIndexes.computeFamily.value(),
				0, 
				&m_ComputeQueue);

		qnm = m_AppName + " ComputeQueue";
		NameObject(VK_OBJECT_TYPE_QUEUE, (uint64_t)m_GraphicsQueue, qnm.c_str());

		vkGetDeviceQueue(m_LogicalDevice, 
            m_QueueFamiliesIndexes.presentFamily.value(),
				0, 
				&m_PresentQueue);
		qnm = m_AppName + " PresentQueue";
		NameObject(VK_OBJECT_TYPE_QUEUE, (uint64_t)m_GraphicsQueue, qnm.c_str());
    }
