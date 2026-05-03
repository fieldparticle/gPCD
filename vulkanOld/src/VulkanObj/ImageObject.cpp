/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/RenderPass.cpp $
% $Id: RenderPass.cpp 31 2023-06-12 20:17:58Z jb $
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

void ImageObject::ClearAttachment()
{
	vkDestroyImageView(m_App->GetLogicalDevice(), m_ImageView, nullptr);
	vmaDestroyImage(m_App->m_vmaAllocator, m_Image, nullptr);
	//vkFreeMemory(m_App->GetLogicalDevice(), m_Attachments.attachment.mem, nullptr);
}

// Create a frame buffer attachment
void ImageObject::CreateAttachment(VkFormat format, 
	VkImageUsageFlags usage, VkImageAspectFlags aspectMask)
{

	m_Format = format;
	VkImageCreateInfo imageCreateInfo{};
	imageCreateInfo.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;;
	imageCreateInfo.pNext = VK_NULL_HANDLE;
	imageCreateInfo.imageType = VK_IMAGE_TYPE_2D;
	imageCreateInfo.format = format;
	imageCreateInfo.extent.width = m_SCO->GetSwapWidth();
	imageCreateInfo.extent.height = m_SCO->GetSwapHeight();
	imageCreateInfo.extent.depth = 1;
	imageCreateInfo.mipLevels = 1;
	imageCreateInfo.arrayLayers = 1;
	imageCreateInfo.samples = VK_SAMPLE_COUNT_1_BIT;
	imageCreateInfo.tiling = VK_IMAGE_TILING_OPTIMAL;
	// VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT flag is required for input attachments
	imageCreateInfo.usage = usage | VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT;
	imageCreateInfo.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

#if 0
	if(vkCreateImage(m_App->GetLogicalDevice(), 
		&imageCreateInfo, nullptr,
		&m_Image) != VK_SUCCESS)
	{
		throw std::runtime_error("Failed to create image in ImageObject ImageObject::CreateAttachment.");
	}
#endif
	m_Allocation.resize(1);
	std::ostringstream  objtxt;
	objtxt << m_Name << " Number:" << "0" << std::ends;

	VmaAllocationCreateInfo allocationCreateInfo = {};
	allocationCreateInfo.usage = VMA_MEMORY_USAGE_AUTO;
	allocationCreateInfo.preferredFlags = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;
	allocationCreateInfo.flags = VMA_ALLOCATION_CREATE_DEDICATED_MEMORY_BIT;// VMA_ALLOCATION_CREATE_HOST_ACCESS_SEQUENTIAL_WRITE_BIT;
	uint32_t memoryTypeIndex = 0;
	VkResult vkresult = vmaFindMemoryTypeIndexForImageInfo(m_App->m_vmaAllocator,
		&imageCreateInfo, &allocationCreateInfo, &memoryTypeIndex);

	if (vkresult != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "vmaFindMemoryTypeIndexForImageInfo Failed. Returns:" << vkresult << std::ends;
		throw std::runtime_error(objtxt.str());
	}

	m_App->VMACreateDeviceMemImage(	VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Image, m_Allocation[0], allocationCreateInfo, imageCreateInfo, objtxt.str());

	VkImageViewCreateInfo imageView{};
	imageView.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
	imageView.viewType = VK_IMAGE_VIEW_TYPE_2D;
	imageView.format = format;
	imageView.subresourceRange = {};
	imageView.subresourceRange.aspectMask = aspectMask;
	imageView.subresourceRange.baseMipLevel = 0;
	imageView.subresourceRange.levelCount = 1;
	imageView.subresourceRange.baseArrayLayer = 0;
	imageView.subresourceRange.layerCount = 1;
	imageView.image = m_Image;
	if(vkCreateImageView(m_App->GetLogicalDevice(), &imageView, nullptr, &m_ImageView))
	{
		throw std::runtime_error("Failed to vkCreateImageView in ImageObject::CreateAttachment.");
	}
}
void ImageObject::Cleanup()
{

	vkDestroyImageView(m_App->GetLogicalDevice(), m_ImageView, nullptr);
	vmaDestroyImage(m_App->m_vmaAllocator, m_Image, m_Allocation[0]);

};


VkFormat ImageObject::findFormat() {
	return findSupportedFormat(
		{ VK_FORMAT_D32_SFLOAT, VK_FORMAT_D32_SFLOAT_S8_UINT, VK_FORMAT_D24_UNORM_S8_UINT },
		VK_IMAGE_TILING_OPTIMAL,
		VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT
	);
}

uint32_t ImageObject::findMemoryType(uint32_t typeFilter, VkMemoryPropertyFlags properties)
{
	VkPhysicalDeviceMemoryProperties memProperties;
	vkGetPhysicalDeviceMemoryProperties(m_App->GetPhysicalDevice(), &memProperties);

	for (uint32_t i = 0; i < memProperties.memoryTypeCount; i++)
	{
		if ((typeFilter & (1 << i)) && (
			memProperties.memoryTypes[i].propertyFlags & properties) == properties)
		{
			return i;
		}
	}

	throw std::runtime_error("Failed to find required memory type.");
}

void ImageObject::createImageView(VkImageAspectFlags aspectFlags) 
{
	VkImageViewCreateInfo viewInfo{};
	viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
	viewInfo.image = m_Image;
	viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
	viewInfo.format = m_Format;
	viewInfo.subresourceRange.aspectMask = aspectFlags;
	viewInfo.subresourceRange.baseMipLevel = 0;
	viewInfo.subresourceRange.levelCount = 1;
	viewInfo.subresourceRange.baseArrayLayer = 0;
	viewInfo.subresourceRange.layerCount = 1;
	//viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
	// Stencil aspect should only be set on depth + stencil formats (VK_FORMAT_D16_UNORM_S8_UINT..VK_FORMAT_D32_SFLOAT_S8_UINT
	
	if (m_Format >= VK_FORMAT_D16_UNORM_S8_UINT) {
		viewInfo.subresourceRange.aspectMask |= VK_IMAGE_ASPECT_STENCIL_BIT;
	}
	
	if (vkCreateImageView(m_App->GetLogicalDevice(), 
		&viewInfo, nullptr, &m_ImageView) != VK_SUCCESS) {
		throw std::runtime_error("ImageObject::createImageView failed at vkCreateImageView");
	}

	
}

VkFormat ImageObject::findSupportedFormat(const std::vector<VkFormat>& candidates, 
	VkImageTiling tiling, VkFormatFeatureFlags features) {
	for (VkFormat format : candidates) {
		VkFormatProperties props;
		vkGetPhysicalDeviceFormatProperties(m_App->GetPhysicalDevice(), format, &props);

		if (tiling == VK_IMAGE_TILING_LINEAR && 
				(props.linearTilingFeatures & features) == features) {
			return format;
		}
		else if (tiling == VK_IMAGE_TILING_OPTIMAL && 
				(props.optimalTilingFeatures & features) == features) {
			return format;
		}

	}

	throw std::runtime_error("ImageObject::createImageView failed at findSupportedFormat");
}