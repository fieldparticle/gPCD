/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/VulkanObject.cpp $
% $Id: VulkanObject.cpp 31 2023-06-12 20:17:58Z jb $
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
void VulkanObj::VMACreateDeviceBuffer(VkDeviceSize size,
	VkBufferUsageFlags usage,
	VkMemoryPropertyFlags properties,
	VkBuffer& buffer,
	VmaAllocation& allocation,
	std::string Name)
{
	//A memory type is chosen that has all the required flags and as many preferred flags set as possible.

	VkBufferCreateInfo bufferInfo = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO };
	bufferInfo.size = size;
	m_TotalMemoryBytes += size;
	
	bufferInfo.usage = usage;
	VmaAllocationCreateInfo stagingAllocInfo = {};
	stagingAllocInfo.usage = VMA_MEMORY_USAGE_AUTO;
	stagingAllocInfo.preferredFlags = properties;
	//stagingAllocInfo.requiredFlags = properties;
	stagingAllocInfo.flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_SEQUENTIAL_WRITE_BIT;


	VkResult vkresult = vmaCreateBuffer(m_vmaAllocator,
		&bufferInfo, &stagingAllocInfo,
		&buffer, &allocation, nullptr);
	if (vkresult != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "VMACreateDeviceBuffer Failed. Returns:" << vkresult << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	VmaAllocationInfo pAllocationInfo = {};
	vmaGetAllocationInfo(m_vmaAllocator, allocation, &pAllocationInfo);
	std::string duname = Name + "DeviceMemory";
	NameObject(VK_OBJECT_TYPE_BUFFER, (uint64_t)buffer, duname.c_str());
}




void VulkanObj::VMACreateDeviceMemImage(VkMemoryPropertyFlags properties,
	VkImage& image,
	VmaAllocation& allocation,
	VmaAllocationCreateInfo& stagingAllocInfo,
	VkImageCreateInfo &imageCreateInfo,
	std::string Name)
{
	//A memory type is chosen that has all the required flags and as many preferred flags set as possible.

	VkResult vkresult = vmaCreateImage(m_vmaAllocator,
		&imageCreateInfo,
		&stagingAllocInfo,
		&image, &allocation, nullptr);
								
	if (vkresult != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "VMACreateDeviceBuffer Failed. Returns:" << vkresult << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	VmaAllocationInfo pAllocationInfo = {};
	vmaGetAllocationInfo(m_vmaAllocator, allocation, &pAllocationInfo);
	std::string duname = Name + " Image";
	NameObject(VK_OBJECT_TYPE_IMAGE, (uint64_t)image, duname.c_str());
}
void VulkanObj::VMAMapMemory(VmaAllocation& allocation,void* data, size_t size)
{
	
	void* mappedData;
	vmaMapMemory(m_vmaAllocator, allocation, &mappedData);
	memcpy(mappedData, &data, size);
	vmaUnmapMemory(m_vmaAllocator, allocation);
}

void VulkanObj::VMACreateStagingBuffer(VkDeviceSize size,
				VkBufferUsageFlags usage,
				VkMemoryPropertyFlags properties,
				VkBuffer& buffer,
				VmaAllocation& allocation,
				std::string Name)
{
	//A memory type is chosen that has all the required flags and as many preferred flags set as possible.

	VkBufferCreateInfo bufferInfo = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO };
	bufferInfo.size = size;
	bufferInfo.usage = usage;

	VmaAllocationCreateInfo stagingAllocInfo = {};
	stagingAllocInfo.usage = VMA_MEMORY_USAGE_AUTO;
	stagingAllocInfo.preferredFlags = properties;
	stagingAllocInfo.requiredFlags = properties;
	stagingAllocInfo.flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_SEQUENTIAL_WRITE_BIT;
	
	
	VkResult vkresult = vmaCreateBuffer(m_vmaAllocator,
		&bufferInfo, &stagingAllocInfo,
		&buffer, &allocation, nullptr);
	if (vkresult != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "vmaCreateBuffer Failed. Returns:" << vkresult << std::ends;
		throw std::runtime_error(objtxt.str());
	}

	std::string buname = Name + "DeviceBuffer";
	NameObject(VK_OBJECT_TYPE_BUFFER, (uint64_t)buffer, buname.c_str());
	VkMemoryRequirements memRequirements;
	vkGetBufferMemoryRequirements(m_LogicalDevice, buffer, &memRequirements);
	VmaBudget vmabudget = {};
	vmaGetHeapBudgets(m_vmaAllocator, &vmabudget);

}
