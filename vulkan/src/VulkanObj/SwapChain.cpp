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
 void SwapChain::CreateSwapChain() 
 {
	SwapChainSupportDetails swapChainSupport = 	QueryPhysDevSwapChainSupport(m_App->GetPhysicalDevice());
	m_SurfaceFormat	= ChooseSwapSurfaceFormat(swapChainSupport.formats);
	VkPresentModeKHR presentMode = 	ChooseSwapPresentMode(swapChainSupport.presentModes);
	VkExtent2D extent = ChooseSwapExtent(swapChainSupport.capabilities);

	m_NumSwapImages = swapChainSupport.capabilities.minImageCount;
	
	if (swapChainSupport.capabilities.maxImageCount > 0 && m_NumSwapImages > swapChainSupport.capabilities.maxImageCount)
	{
		m_NumSwapImages = swapChainSupport.capabilities.maxImageCount;
	}

	
	VkSwapchainCreateInfoKHR createInfo{};
	createInfo.sType 			= VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
	createInfo.surface 			= m_App->GetSurface();
	createInfo.minImageCount 	= m_NumSwapImages;
	createInfo.imageFormat 		= m_SurfaceFormat.format;
	createInfo.imageColorSpace 	= m_SurfaceFormat.colorSpace;
	createInfo.imageExtent 		= extent;
	createInfo.imageArrayLayers = 1;
	
	// VK_IMAGE_USAGE_TRANSFER_SRC_BIT is need to transfer in Media::Save()
	createInfo.imageUsage 		= VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT ;

	uint32_t queueFamilyIndices[] 	= { m_CO->m_QFIndices.graphicsFamily.value(), m_CO->m_QFIndices.presentFamily.value()};

	if (m_CO->m_QFIndices.graphicsFamily != m_CO->m_QFIndices.presentFamily)
	{
		//createInfo.imageSharingMode 		= VK_SHARING_MODE_CONCURRENT;
		createInfo.queueFamilyIndexCount 	= 2;
		createInfo.pQueueFamilyIndices 		= queueFamilyIndices;
	} 
	else 
	{
		createInfo.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
	}

	createInfo.preTransform 	= swapChainSupport.capabilities.currentTransform;
	createInfo.compositeAlpha 	= VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
	createInfo.presentMode 		= presentMode;

	//##JMB
	createInfo.clipped 			= VK_TRUE;

	if (vkCreateSwapchainKHR( m_App->GetLogicalDevice(), &createInfo, nullptr, &m_SwapChain) != VK_SUCCESS) 
	{
		throw std::runtime_error("SwapChain::CreateSwapChain() Failed.");
	}
	
	m_App->NameObject(VK_OBJECT_TYPE_SWAPCHAIN_KHR, (uint64_t)m_SwapChain, m_Name.c_str());
	
	vkGetSwapchainImagesKHR( m_App->GetLogicalDevice(), m_SwapChain, &m_NumSwapImages, nullptr);
	m_SwapChainImages.resize(m_NumSwapImages);
	vkGetSwapchainImagesKHR( m_App->GetLogicalDevice(), m_SwapChain, &m_NumSwapImages, m_SwapChainImages.data());
	
	for (uint32_t ii = 0; ii< m_NumSwapImages;ii++)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << " SwapImage#:" << ii << std::ends;
		m_App->NameObject(VK_OBJECT_TYPE_IMAGE, (uint64_t)m_SwapChainImages[ii], objtxt.str().c_str());
	}
	m_App->SetSwapCount(m_NumSwapImages);
	m_SwapChainImageFormat 	= m_SurfaceFormat.format;
	SetSwapExtent(extent);
	SetSwapHeight(extent.height);
	SetSwapWidth(extent.width) ;
	SetSwapChainImageFormat(m_SwapChainImageFormat);
	//m_SwapChainExtent 		= extent;

}
//	
//	
//
//	
VkExtent2D SwapChain::ChooseSwapExtent(const VkSurfaceCapabilitiesKHR& Capabilities) 
{
	if (Capabilities.currentExtent.width != std::numeric_limits<uint32_t>::max()) 
	{
		return Capabilities.currentExtent;
	} 
	else 
	{
		int width, height;
		glfwGetFramebufferSize(m_App->GetGLFWWindow(), &width, &height);
		VkExtent2D actualExtent = {
			static_cast<uint32_t>(width),
			static_cast<uint32_t>(height)
		};

		actualExtent.width = std::clamp(actualExtent.width, 
										Capabilities.minImageExtent.width, 
										Capabilities.maxImageExtent.width);
		actualExtent.height = std::clamp(actualExtent.height, 
										Capabilities.minImageExtent.height, 
										Capabilities.maxImageExtent.height);

		return actualExtent;
	}
}
//
//
//
//
#if 0
void SwapChain::recreateSwapChain(FrameBuffer* FBO) 
{
	int width = 0, height = 0;
	
	glfwGetFramebufferSize(m_App->window, &width, &height);
	
	while (width == 0 || height == 0) 
	{
		glfwGetFramebufferSize(m_App->window, &width, &height);
		glfwWaitEvents();
	}

	vkDeviceWaitIdle( m_App->GetLogicalDevice());

	Cleanup();
	CreateSwapChain();
	CreateImageViews();
	FBO->CreateFramebuffers();
}
#endif
//
//
//
//
VkImageView SwapChain::CreateSwapImageView(VkImage Image, VkFormat Format) 
{
	
    VkImageViewCreateInfo viewInfo{};
    viewInfo.sType 								= VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    viewInfo.image 								= Image;
    viewInfo.viewType 							= VK_IMAGE_VIEW_TYPE_2D;
    viewInfo.format 							= Format;
    viewInfo.subresourceRange.aspectMask 		= VK_IMAGE_ASPECT_COLOR_BIT;
    viewInfo.subresourceRange.baseMipLevel 		= 0;
    viewInfo.subresourceRange.levelCount 		= 1;
    viewInfo.subresourceRange.baseArrayLayer 	= 0;
    viewInfo.subresourceRange.layerCount 		= 1;
	viewInfo.components = {
			VK_COMPONENT_SWIZZLE_R,
			VK_COMPONENT_SWIZZLE_G,
			VK_COMPONENT_SWIZZLE_B,
			VK_COMPONENT_SWIZZLE_A
	};
	viewInfo.flags = 0;
    VkImageView imageView;
    if (vkCreateImageView(m_App->GetLogicalDevice(), &viewInfo, nullptr, &imageView) != VK_SUCCESS) 
	{
        throw std::runtime_error("SwapChain::CreateSwapImageView Failed");
    }
	

    return imageView;
}
	
void SwapChain::CreateImageViews() 
{
	m_SwapChainImageViews.resize(m_SwapChainImages.size());

	for (size_t i = 0; i < m_SwapChainImages.size(); i++) 
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << " SwapView#:" << i << std::ends;
		m_SwapChainImageViews[i] = CreateSwapImageView(m_SwapChainImages[i],
			m_SwapChainImageFormat);

		m_App->NameObject(VK_OBJECT_TYPE_IMAGE_VIEW, 
			(uint64_t)m_SwapChainImageViews[i], objtxt.str().c_str());
	}
}
//
//
//
//	
VkSurfaceFormatKHR SwapChain::ChooseSwapSurfaceFormat(const std::vector<VkSurfaceFormatKHR>& AvailableFormats) 
{
	for (const auto& availableFormat : AvailableFormats) 
	{
		if (availableFormat.format == VK_FORMAT_B8G8R8A8_SRGB 
			&& availableFormat.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) 
		{
			return availableFormat;
		}
	}
	return AvailableFormats[0];
}
//
//
//

VkPresentModeKHR SwapChain::ChooseSwapPresentMode(const std::vector<VkPresentModeKHR>& AvailablePresentModes) 
{
	//VK_PRESENT_MODE_FIFO_KHR
	for (const auto& availablePresentMode : AvailablePresentModes) 
	{
		if (availablePresentMode == VK_PRESENT_MODE_MAILBOX_KHR) 
		//if (availablePresentMode == VK_PRESENT_MODE_FIFO_KHR)
		{
			return availablePresentMode;
		}
	}

    return VK_PRESENT_MODE_FIFO_KHR;
}
void SwapChain::Cleanup()
	{
		for (auto imageView : m_SwapChainImageViews) 
		{
			vkDestroyImageView(m_App->GetLogicalDevice(), imageView, nullptr);
		}

		vkDestroySwapchainKHR(m_App->GetLogicalDevice(), m_SwapChain, nullptr);
    }