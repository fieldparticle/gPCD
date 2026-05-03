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

#ifndef IMAGEOBJ_HPP
#define IMAGEOBJ_HPP

class SwapChainObj;
class Resource;
class ImageObject : public Resource
{
public:

///==================== SUPPASSES ============


	struct FrameBufferAttachment {
		VkImage image = VK_NULL_HANDLE;
		VkDeviceMemory mem = VK_NULL_HANDLE;
		VkImageView view = VK_NULL_HANDLE;
		VkFormat format;
	};


// ================= Images ====================
	std::vector < VmaAllocation> m_Allocation = {};
	
	VkImage 		m_Image={};
	VkDeviceMemory 	m_ImageMemory={};
	VkImageView 	m_ImageView={};
	VkFormat 		m_Format={};
	SwapChainObj*	m_SCO={};	
	//FrameBufferAttachment m_Attachment;
	VkImage GetImage(){
		return m_Image;};

	VkDeviceMemory GetImageMemory()
	{
		return m_ImageMemory;
	}
	virtual void AskObject(uint32_t AnyNumber) {};
	VkImageView GetImageView()
	{ return m_ImageView;};
	VkFormat GetImageFormat(){
		return m_Format;}

	void CreateAttachment(VkFormat format,
		VkImageUsageFlags usage,VkImageAspectFlags aspectMask);
	void ClearAttachment();
	ImageObject(VulkanObj* App, std::string Name) : Resource(App,Name,0) {};

	void createImage(uint32_t width, uint32_t height, VkFormat format,
		VkImageTiling tiling, VkImageUsageFlags usage,
		VkMemoryPropertyFlags properties, VkImage& image, VkDeviceMemory& imageMemory);
	VkFormat findSupportedFormat(const std::vector<VkFormat>& candidates,
		VkImageTiling tiling,
		VkFormatFeatureFlags features);
	void copyBufferToImage(VkBuffer buffer, VkImage image, uint32_t width, uint32_t height) {};
	void transitionImageLayout(VkImage image, VkFormat format,
		VkImageLayout oldLayout, VkImageLayout newLayout) {};
	VkFormat findFormat();
	uint32_t findMemoryType(uint32_t typeFilter, VkMemoryPropertyFlags properties);
	void createImageView(VkImageAspectFlags aspectFlags);
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return VK_NULL_HANDLE; };
	VkVertexInputBindingDescription* GetBindingDescription() { return VK_NULL_HANDLE; };



	void PushMem(uint32_t currentBuffer) {};
	void PullMem(uint32_t currentBuffer) {};
	virtual void Cleanup();
	
};
#endif