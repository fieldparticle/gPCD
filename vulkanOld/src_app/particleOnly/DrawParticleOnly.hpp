/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/DrawObj.hpp $
% $Id: DrawObj.hpp 31 2023-06-12 20:17:58Z jb $
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


#ifndef DRAWPARTICLEONLY_HPP
#define DRAWPARTICLEONLY_HPP

class DrawParticleOnly : public DrawObj
{
    public:
		std::string m_ImageDir;
		std::string m_ImagePrefix;
	void flushCommandBuffer(VkCommandBuffer commandBuffer, VkQueue queue, VkCommandPool pool, bool free);
	void flushCommandBuffer(VkCommandBuffer commandBuffer, VkQueue queue, bool free);

	void insertImageMemoryBarrier(
	VkCommandBuffer cmdbuffer,
	VkImage image,
	VkAccessFlags srcAccessMask,
	VkAccessFlags dstAccessMask,
	VkImageLayout oldImageLayout,
	VkImageLayout newImageLayout,
	VkPipelineStageFlags srcStageMask,
	VkPipelineStageFlags dstStageMask,
	VkImageSubresourceRange subresourceRange);
	VkCommandBuffer createCommandBuffer(VkCommandBufferLevel level, VkCommandPool pool, bool begin=false);
	VkCommandPool createCommandPool(uint32_t queueFamilyIndex, VkCommandPoolCreateFlags createFlags);
	uint32_t getMemoryType(uint32_t typeBits, VkMemoryPropertyFlags properties, VkBool32 *memTypeFound = nullptr);
	VkCommandBuffer createCommandBuffer(VkCommandBufferLevel level, bool begin);
	void SaveImage(uint32_t ImgNum);

    virtual void DrawFrame(); 
	void Create(CommandPoolObj* CPL,
		SwapChainObj* SCO,
		RenderPassObj* RPO,
		FrameBufferObj* FBO,
		SyncObj* SO);


	
	DrawParticleOnly(VulkanObj* App, std::string Name) : DrawObj(Name,App ){};
	uint32_t currentBuffer = 0;

    void Cleanup(){
       
    };
	
};
#endif