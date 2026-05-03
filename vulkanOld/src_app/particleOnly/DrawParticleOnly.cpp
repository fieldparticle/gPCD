/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************GPO
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/DrawObj.cpp $
% $Id: DrawObj.cpp 31 2023-06-12 20:17:58Z jb $
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
///FIXX THIS
void DrawParticleOnly::Create(CommandPoolObj* CPL,
	SwapChainObj* SCO,
	RenderPassObj* RPO,
	FrameBufferObj* FBO,
	SyncObj* SO)
{
	m_CPL = CPL;
	m_SCO = SCO;
	m_FBO = FBO; 
	m_SO = SO;
	m_ComputeCommandObj		= m_CPL->GetCommandObjByName("CommandParticleCompute");
	m_GraphicsCommandObj	= m_CPL->GetCommandObjByName("CommandObjParticleGraphics");
	m_Graphicslst			= m_GraphicsCommandObj->m_RCO->m_DRList;
	m_Computelst			= m_ComputeCommandObj->m_RCO->m_DRList;
	m_ImageDir				= MpsApp->GetString("imageDir", true);
	m_ImagePrefix			= MpsApp->GetString("imagePrefix", true);
}

void DrawParticleOnly::DrawFrame()
{
	VkResult ret;
	
	//=========================================================
	// Allocate all semaphores
	//=========================================================
	
	//if (CfgApp->m_NoCompute != true)
	{
		//=========================================================
		// Wait for compute fences
		//=========================================================
		if ((ret = vkWaitForFences(m_App->GetLogicalDevice(), 1,
			&m_SO->m_Fences[SyncObjPO::F_CINFLIGHT].fencevec[currentBuffer], VK_TRUE, UINT64_MAX)) != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkWaitForFences failed:" << ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};
		if(Extflg == true)
			return ;
		//=========================================================
		// Update Compute resources
		//=========================================================

		m_Computelst[0]->PushMem(currentBuffer);
		m_Computelst[3]->PushMem(currentBuffer);

		ret = vkResetFences(m_App->GetLogicalDevice(), 1,
			&m_SO->m_Fences[SyncObjPO::F_CINFLIGHT].fencevec[currentBuffer]);
		if (ret != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkResetFences computeInFlightFences failed:" << ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};
		if(Extflg == true)
			return ;


		//=========================================================
		// Reset Compute Command Buffers.
		//=========================================================

		ret = vkResetCommandBuffer(
			m_ComputeCommandObj->m_CommandBuffers[currentBuffer],
			VK_COMMAND_BUFFER_RESET_RELEASE_RESOURCES_BIT);
		if (ret != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkResetCommandBuffer failed:"
				<< ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};

		

		//=========================================================
		// Record Compute commands
		//=========================================================
		m_ComputeCommandObj->RecordCommands(0,currentBuffer);
		if(Extflg == true)
			return ;
		VkSubmitInfo csubmitInfo{};
		csubmitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
		csubmitInfo.commandBufferCount = 1;
		csubmitInfo.pCommandBuffers =
			&m_ComputeCommandObj->m_CommandBuffers[currentBuffer];
		csubmitInfo.signalSemaphoreCount = 1;
		csubmitInfo.pSignalSemaphores =
			&m_SO->m_WaitSemaphores[SyncObjPO::W_COMPUTEFIN].semvec[currentBuffer];
		if(Extflg == true)
			return ;

		//=========================================================
		// Submit Compute commands
		//=========================================================
		ret = vkQueueSubmit(m_App->GetComputeQueue(), 1, &csubmitInfo,
			m_SO->m_Fences[SyncObjPO::F_CINFLIGHT].fencevec[currentBuffer]);
		if (ret != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkQueueSubmit GetComputeQueue failed:"
				<< ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};
		m_ComputeCommandObj->FetchRenderTimeResults(currentBuffer);
#ifndef NDEBUG
		m_Computelst[3]->PullMem(currentBuffer);
#endif
		if(Extflg == true)
			return ;
		//########################################### Graphics ##########################################################
		//=========================================================
		// Wait for graphics fences
		//=========================================================

#if 1
		ret = vkWaitForFences(m_App->GetLogicalDevice(), 1,
			&m_SO->m_Fences[SyncObjPO::F_INFLIGHT].fencevec[currentBuffer], VK_TRUE, UINT64_MAX);
		if (ret != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkWaitForFences inFlightFences failed:" << ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};
#endif
		// Get draw count from compute


		//=========================================================
		// Acquire next completed image from swap-chain. Get the id of swap chain image
	// 
		//=========================================================
		uint32_t imageIndex = 0;
		VkResult result = vkAcquireNextImageKHR(
			m_App->GetLogicalDevice(),
			m_SCO->m_SwapChain,
			UINT64_MAX,
			m_SO->m_WaitSemaphores[SyncObjPO::W_IMAGAVAIL].semvec[currentBuffer],
			VK_NULL_HANDLE,
			&imageIndex);
		if (result == VK_ERROR_OUT_OF_DATE_KHR)
		{
			//m_SCO->RecreateSwapChain(m_FBO);
			return;
		}
		else if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR)
		{
			throw std::runtime_error("Acquire Swap Chain Image Error.");
		}


		//=========================================================
		// Reset all fences unsignald
		//=========================================================
		ret = vkResetFences(m_App->GetLogicalDevice(), 1, &m_SO->m_Fences[SyncObjPO::F_INFLIGHT].fencevec[currentBuffer]);
		if (ret != VK_SUCCESS)
		{

			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkResetFences inFlightFences failed:" << ret << std::ends;

			throw std::runtime_error(objtxt.str().c_str());
		};

		//=========================================================
		// 	// Clear command buffer to rerecord. 
		//  If everything is on the GPU chnage this.
		//=========================================================
		ret = vkResetCommandBuffer(m_GraphicsCommandObj->m_CommandBuffers[currentBuffer],
			VK_COMMAND_BUFFER_RESET_RELEASE_RESOURCES_BIT);
		if (ret != VK_SUCCESS)
		{
			std::ostringstream  objtxt;
			objtxt << "DrawIParticle::DrawFrame() vkResetCommandBuffer m_CommandGBuffers failed:" << ret << std::ends;
			throw std::runtime_error(objtxt.str().c_str());
		};
	
		//Push constants
		m_Graphicslst[1]->PushMem(currentBuffer);
		m_Graphicslst[2]->PushMem(currentBuffer);
		//Atomic graphics
		m_Graphicslst[5]->PushMem(currentBuffer);

		// Record a new command buffer for the current frame and associate with swap chain image.
		m_GraphicsCommandObj->RecordCommands(imageIndex,currentBuffer );
		if(Extflg == true)
			return ;
		VkSemaphore waitSemaphores[] = 
		{ m_SO->m_WaitSemaphores[SyncObjPO::W_COMPUTEFIN].semvec[currentBuffer] ,
			 m_SO->m_WaitSemaphores[SyncObjPO::W_IMAGAVAIL].semvec[currentBuffer] };
		if(Extflg == true)
			return ;
		VkPipelineStageFlags waitStages[] = 
		{ m_SO->m_WaitSemaphores[SyncObjPO::W_COMPUTEFIN].pipeStage[currentBuffer] ,
			 m_SO->m_WaitSemaphores[SyncObjPO::W_IMAGAVAIL].pipeStage[currentBuffer] };
		if(Extflg == true)
			return ;
		// Build submit info
		VkSubmitInfo submitInfo = {};
		submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
		submitInfo.waitSemaphoreCount = 2;
		submitInfo.pWaitSemaphores = waitSemaphores,
		submitInfo.pWaitDstStageMask = waitStages,
		submitInfo.commandBufferCount = 1;
		submitInfo.pCommandBuffers = &m_GraphicsCommandObj->m_CommandBuffers[currentBuffer];
		submitInfo.signalSemaphoreCount = 1;
		submitInfo.pSignalSemaphores = &m_SO->m_SigSemaphores[SyncObjPO::S_RENDERFIN].semvec[currentBuffer];
		if(Extflg == true)
			return ;

		// Submit the command pool to the graphics command queue.
		VkResult subret = vkQueueSubmit(m_App->GetGraphicsQueue(),
			1,
			&submitInfo,
			m_SO->m_Fences[SyncObjPO::F_INFLIGHT].fencevec[currentBuffer]);
		std::ostringstream  objtxt;
		if (subret == VK_ERROR_OUT_OF_HOST_MEMORY)
		{
			objtxt << "Error - DrawObj:" << m_Name
				<< " Returns:VK_ERROR_OUT_OF_HOST_MEMORY " << m_App->m_TotalMemoryBytes << std::ends;
			throw std::runtime_error(objtxt.str());
		}
		else
			if (subret == VK_ERROR_OUT_OF_DEVICE_MEMORY)
			{
				objtxt << "Error - DrawObj:" << m_Name
					<< " Returns:VK_ERROR_OUT_OF_DEVICE_MEMORY " << m_App->m_TotalMemoryBytes << std::ends;
				throw std::runtime_error(objtxt.str());
			}
			else
				if (subret == VK_ERROR_DEVICE_LOST)
				{
					objtxt << "Error - DrawObj:" << m_Name
						<< " Returns:VK_ERROR_DEVICE_LOST" << m_App->m_TotalMemoryBytes << std::ends;
					throw std::runtime_error(objtxt.str());

				}
		m_GraphicsCommandObj->FetchRenderTimeResults(currentBuffer);
#ifndef NDEBUG
		m_Graphicslst[5]->PullMem(currentBuffer);
#endif
		// Wait for complettion of rendering then pick up the completed frame buffer 
		// and send to presentation device.
		VkSwapchainKHR swapChains[] = { m_SCO->m_SwapChain };

		// Build presentation info
		VkPresentInfoKHR presentInfo{};
		presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
		presentInfo.waitSemaphoreCount = 1;
		presentInfo.pWaitSemaphores = &m_SO->m_SigSemaphores[SyncObjPO::S_RENDERFIN].semvec[currentBuffer];
		presentInfo.swapchainCount = 1;
		presentInfo.pSwapchains = swapChains;
		presentInfo.pImageIndices = &imageIndex;

		// Send to presentation device
		result = vkQueuePresentKHR(m_App->GetPresentQueue(), &presentInfo);
		if (result == VK_ERROR_OUT_OF_DATE_KHR ||
			result == VK_SUBOPTIMAL_KHR)
		{
			//	m_App->m_FramebufferResized = false;
			//	m_SCO->RecreateSwapChain(m_FBO);
		}
		else if (result != VK_SUCCESS)
		{
			throw std::runtime_error("vkQueuePresentKHR in DrawFrame Failed.");
		}
		currentBuffer = (currentBuffer + 1) % m_App->m_FramesBuffered;
		m_App->SetCurrentBuffer(currentBuffer);
		
	}

}

void DrawParticleOnly::SaveImage(uint32_t ImgNum)
{
	
	
	bool supportsBlit = true;

	// Check blit support for source and destination
	VkFormatProperties formatProps;

	// Check if the device supports blitting from optimal images (the swapchain images are in optimal format)
	vkGetPhysicalDeviceFormatProperties(m_App->GetPhysicalDevice(), m_SCO->m_SwapChainImageFormat, &formatProps);
	if (!(formatProps.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT)) {
		//std::cerr << "Device does not support blitting from optimal tiled images, using copy instead of blit!" << std::endl;
		supportsBlit = false;
	}

	// Check if the device supports blitting to linear images
	vkGetPhysicalDeviceFormatProperties(m_App->GetPhysicalDevice(), VK_FORMAT_R8G8B8A8_UNORM, &formatProps);
	if (!(formatProps.linearTilingFeatures & VK_FORMAT_FEATURE_BLIT_DST_BIT)) {
		//std::cerr << "Device does not support blitting to linear tiled images, using copy instead of blit!" << std::endl;
		supportsBlit = false;
	}

	// Source for the copy is the last rendered swapchain image
	VkImage srcImage = m_SCO->m_SwapChainImages[currentBuffer];

	// Create the linear tiled destination image to copy to and to read the memory from
	VkImageCreateInfo imageCreateCI;
	imageCreateCI.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
	imageCreateCI.imageType = VK_IMAGE_TYPE_2D;
	// Note that vkCmdBlitImage (if supported) will also do format conversions if the swapchain color format would differ
	imageCreateCI.format = VK_FORMAT_R8G8B8A8_UNORM;
	imageCreateCI.extent.width = m_SCO->GetSwapWidth();
	imageCreateCI.extent.height = m_SCO->GetSwapHeight();
	imageCreateCI.extent.depth = 1;
	imageCreateCI.arrayLayers = 1;
	imageCreateCI.mipLevels = 1;
	imageCreateCI.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
	imageCreateCI.samples = VK_SAMPLE_COUNT_1_BIT;
	imageCreateCI.tiling = VK_IMAGE_TILING_LINEAR;
	imageCreateCI.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
	imageCreateCI.pNext = nullptr;
	imageCreateCI.flags = 0;
	imageCreateCI.pQueueFamilyIndices = 0;
	imageCreateCI.sharingMode = VK_SHARING_MODE_EXCLUSIVE ;
	

	// Create the image
	VkImage dstImage;
	uint32_t ret = vkCreateImage(m_App->GetLogicalDevice(), &imageCreateCI, nullptr, &dstImage);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::SaveImage vkCreateImage failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}

	// Create memory to back up the image
	VkMemoryRequirements memRequirements;

	VkMemoryAllocateInfo memAllocInfo{};
	memAllocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;

	VkDeviceMemory dstImageMemory;

	vkGetImageMemoryRequirements(m_App->GetLogicalDevice(), dstImage, &memRequirements);

	memAllocInfo.allocationSize = memRequirements.size;

	// Memory must be host visible to copy from
	memAllocInfo.memoryTypeIndex = getMemoryType(memRequirements.memoryTypeBits, 
		VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);

	ret = vkAllocateMemory(m_App->GetLogicalDevice(), &memAllocInfo, nullptr, &dstImageMemory);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::SaveImage vkAllocateMemory failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}

	ret = vkBindImageMemory(m_App->GetLogicalDevice(), dstImage, dstImageMemory, 0);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::SaveImage vkBindImageMemory failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}

	// Do the actual blit from the swapchain image to our host visible destination image
	VkCommandBuffer copyCmd = createCommandBuffer(VK_COMMAND_BUFFER_LEVEL_PRIMARY, true);

	// Transition destination image to transfer destination layout
	insertImageMemoryBarrier(
		copyCmd,
		dstImage,
		0,
		VK_ACCESS_TRANSFER_WRITE_BIT,
		VK_IMAGE_LAYOUT_UNDEFINED,
		VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VkImageSubresourceRange{ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 });

	// Transition swapchain image from present to transfer source layout
	insertImageMemoryBarrier(
		copyCmd,
		srcImage,
		VK_ACCESS_MEMORY_READ_BIT,
		VK_ACCESS_TRANSFER_READ_BIT,
		VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
		VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VkImageSubresourceRange{ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 });

	// If source and destination support blit we'll blit as this also does automatic format conversion (e.g. from BGR to RGB)
	if (supportsBlit)
	{
		// Define the region to blit (we will blit the whole swapchain image)
		VkOffset3D blitSize;
		blitSize.x = m_SCO->GetSwapWidth();
		blitSize.y = m_SCO->GetSwapHeight();
		blitSize.z = 1;
		VkImageBlit imageBlitRegion{};
		imageBlitRegion.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
		imageBlitRegion.srcSubresource.layerCount = 1;
		imageBlitRegion.srcOffsets[1] = blitSize;
		imageBlitRegion.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
		imageBlitRegion.dstSubresource.layerCount = 1;
		imageBlitRegion.dstOffsets[1] = blitSize;

		// Issue the blit command
		vkCmdBlitImage(
			copyCmd,
			srcImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
			dstImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
			1,
			&imageBlitRegion,
			VK_FILTER_NEAREST);
	}
	else
	{
		// Otherwise use image copy (requires us to manually flip components)
		VkImageCopy imageCopyRegion{};
		imageCopyRegion.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
		imageCopyRegion.srcSubresource.layerCount = 1;
		imageCopyRegion.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
		imageCopyRegion.dstSubresource.layerCount = 1;
		imageCopyRegion.extent.width = m_SCO->GetSwapWidth();
		imageCopyRegion.extent.height = m_SCO->GetSwapHeight();
		imageCopyRegion.extent.depth = 1;

		// Issue the copy command
		vkCmdCopyImage(
			copyCmd,
			srcImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
			dstImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
			1,
			&imageCopyRegion);
	}

	// Transition destination image to general layout, which is the required layout for mapping the image memory later on
	insertImageMemoryBarrier(
		copyCmd,
		dstImage,
		VK_ACCESS_TRANSFER_WRITE_BIT,
		VK_ACCESS_MEMORY_READ_BIT,
		VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
		VK_IMAGE_LAYOUT_GENERAL,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VkImageSubresourceRange{ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 });

	// Transition back the swap chain image after the blit is done
	insertImageMemoryBarrier(
		copyCmd,
		srcImage,
		VK_ACCESS_TRANSFER_READ_BIT,
		VK_ACCESS_MEMORY_READ_BIT,
		VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
		VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VK_PIPELINE_STAGE_TRANSFER_BIT,
		VkImageSubresourceRange{ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 });

	flushCommandBuffer(copyCmd, m_App->GetPresentQueue(), true);

	// Get layout of the image (including row pitch)
	VkImageSubresource subResource { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
	VkSubresourceLayout subResourceLayout;
	vkGetImageSubresourceLayout(m_App->GetLogicalDevice(), dstImage, &subResource, &subResourceLayout);

	// Map image memory so we can start copying from it
	const char* data;
	vkMapMemory(m_App->GetLogicalDevice(), dstImageMemory, 0, VK_WHOLE_SIZE, 0, (void**)&data);
	data += subResourceLayout.offset;

	std::ostringstream  objtxt;
	objtxt << m_ImageDir << "/" << m_ImagePrefix << std::setfill('0') << std::setw(5) << ImgNum << ".ppm";
	
	std::ofstream file(objtxt.str(), std::ios::out | std::ios::binary);

	// ppm header
	file << "P6\n" << m_SCO->GetSwapWidth() << "\n" << m_SCO->GetSwapHeight() << "\n" << 255 << "\n";

	// If source is BGR (destination is always RGB) and we can't use blit (which does automatic conversion), we'll have to manually swizzle color components
	bool colorSwizzle = false;
	// Check if source is BGR
	// Note: Not complete, only contains most common and basic BGR surface formats for demonstration purposes
	if (!supportsBlit)
	{
		std::vector<VkFormat> formatsBGR = { VK_FORMAT_B8G8R8A8_SRGB, VK_FORMAT_B8G8R8A8_UNORM, VK_FORMAT_B8G8R8A8_SNORM };
		colorSwizzle = (std::find(formatsBGR.begin(), formatsBGR.end(), m_SCO->m_SwapChainImageFormat) != formatsBGR.end());
	}

	// ppm binary pixel data
	for (uint32_t y = 0; y < m_SCO->GetSwapHeight(); y++)
	{
		unsigned int *row = (unsigned int*)data;
		for (uint32_t x = 0; x < m_SCO->GetSwapWidth(); x++)
		{
			if (colorSwizzle)
			{
				file.write((char*)row+2, 1);
				file.write((char*)row+1, 1);
				file.write((char*)row, 1);
			}
			else
			{
				file.write((char*)row, 3);
			}
			row++;
		}
		data += subResourceLayout.rowPitch;
	}
	file.close();

	//std::cout << "Screenshot saved to disk" << std::endl;

	// Clean up resources
	vkUnmapMemory(m_App->GetLogicalDevice(), dstImageMemory);
	vkFreeMemory(m_App->GetLogicalDevice(), dstImageMemory, nullptr);
	vkDestroyImage(m_App->GetLogicalDevice(), dstImage, nullptr);

		
}


/**
* Allocate a command buffer from the command pool
*
* @param level Level of the new command buffer (primary or secondary)
* @param pool Command pool from which the command buffer will be allocated
* @param (Optional) begin If true, recording on the new command buffer will be started (vkBeginCommandBuffer) (Defaults to false)
*
* @return A handle to the allocated command buffer
*/
VkCommandBuffer DrawParticleOnly::createCommandBuffer(VkCommandBufferLevel level, VkCommandPool pool, bool begin)
{
	
	VkCommandBufferAllocateInfo commandBufferAllocateInfo {};
			commandBufferAllocateInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
			commandBufferAllocateInfo.commandPool = pool;
			commandBufferAllocateInfo.level = level;
			commandBufferAllocateInfo.commandBufferCount = 1;
	VkCommandBuffer cmdBuffer;
	uint32_t ret = vkAllocateCommandBuffers(m_App->GetLogicalDevice(), &commandBufferAllocateInfo, &cmdBuffer);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::SaveImage vkBindImageMemory failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}
	// If requested, also start recording for the new command buffer
	if (begin)
	{
		VkCommandBufferBeginInfo cmdBufferBeginInfo {};
		cmdBufferBeginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
		ret = vkBeginCommandBuffer(cmdBuffer, &cmdBufferBeginInfo);
		if (ret != VK_SUCCESS)
		{
			std::ostringstream  objtxt;
			objtxt << "DrawParticleHeadless::SaveImage vkBindImageMemory failed:" << ret << std::ends;
			throw std::runtime_error(objtxt.str().c_str());
		}
	}
	return cmdBuffer;
}
VkCommandBuffer DrawParticleOnly::createCommandBuffer(VkCommandBufferLevel level, bool begin)
{
	return createCommandBuffer(level, m_CPL->m_CommandPool, begin);
}

void  DrawParticleOnly::insertImageMemoryBarrier(
	VkCommandBuffer cmdbuffer,
	VkImage image,
	VkAccessFlags srcAccessMask,
	VkAccessFlags dstAccessMask,
	VkImageLayout oldImageLayout,
	VkImageLayout newImageLayout,
	VkPipelineStageFlags srcStageMask,
	VkPipelineStageFlags dstStageMask,
	VkImageSubresourceRange subresourceRange)
{
	
	VkImageMemoryBarrier imageMemoryBarrier {};
	imageMemoryBarrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
	imageMemoryBarrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
	imageMemoryBarrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
	imageMemoryBarrier.srcAccessMask = srcAccessMask;
	imageMemoryBarrier.dstAccessMask = dstAccessMask;
	imageMemoryBarrier.oldLayout = oldImageLayout;
	imageMemoryBarrier.newLayout = newImageLayout;
	imageMemoryBarrier.image = image;
	imageMemoryBarrier.subresourceRange = subresourceRange;

	vkCmdPipelineBarrier(
		cmdbuffer,
		srcStageMask,
		dstStageMask,
		0,
		0, nullptr,
		0, nullptr,
		1, &imageMemoryBarrier);
}

/**
* Finish command buffer recording and submit it to a queue
*
* @param commandBuffer Command buffer to flush
* @param queue Queue to submit the command buffer to
* @param pool Command pool on which the command buffer has been created
* @param free (Optional) Free the command buffer once it has been submitted (Defaults to true)
*
* @note The queue that the command buffer is submitted to must be from the same family index as the pool it was allocated from
* @note Uses a fence to ensure command buffer has finished executing
*/
void DrawParticleOnly::flushCommandBuffer(VkCommandBuffer commandBuffer, VkQueue queue, VkCommandPool pool, bool free)
{
	if (commandBuffer == VK_NULL_HANDLE)
	{
		return;
	}

	uint32_t ret = vkEndCommandBuffer(commandBuffer);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::flushCommandBuffer vkEndCommandBuffer failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}

	VkSubmitInfo submitInfo {};
	submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
	submitInfo.commandBufferCount = 1;
	submitInfo.pCommandBuffers = &commandBuffer;
	// Create fence to ensure that the command buffer has finished executing
	
	VkFenceCreateInfo fenceCreateInfo {};
	fenceCreateInfo.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
	fenceCreateInfo.flags = VK_FLAGS_NONE;

	VkFence fence;
	ret = vkCreateFence(m_App->GetLogicalDevice(), &fenceCreateInfo, nullptr, &fence);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::flushCommandBuffer vkCreateFence failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}
	// Submit to the queue
	ret = vkQueueSubmit(queue, 1, &submitInfo, fence);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::flushCommandBuffer vkQueueSubmit failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}
	// Wait for the fence to signal that command buffer has finished executing
	ret = vkWaitForFences(m_App->GetLogicalDevice(), 1, &fence, VK_TRUE, DEFAULT_FENCE_TIMEOUT);
	if (ret != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << "DrawParticleHeadless::flushCommandBuffer vkWaitForFences failed:" << ret << std::ends;
		throw std::runtime_error(objtxt.str().c_str());

	}
	vkDestroyFence(m_App->GetLogicalDevice(), fence, nullptr);
	if (free)
	{
		vkFreeCommandBuffers(m_App->GetLogicalDevice(), pool, 1, &commandBuffer);
	}
}

void DrawParticleOnly::flushCommandBuffer(VkCommandBuffer commandBuffer, VkQueue queue, bool free)
{
	return flushCommandBuffer(commandBuffer, queue, m_CPL->m_CommandPool, free);
}
uint32_t DrawParticleOnly::getMemoryType(uint32_t typeBits, VkMemoryPropertyFlags properties, VkBool32 *memTypeFound)
{

	VkPhysicalDeviceMemoryProperties memoryProperties{};
	vkGetPhysicalDeviceMemoryProperties(m_App->m_PhysicalDevice, &memoryProperties);

	for (uint32_t i = 0; i < memoryProperties.memoryTypeCount; i++)
	{
		if ((typeBits & 1) == 1)
		{
			if ((memoryProperties.memoryTypes[i].propertyFlags & properties) == properties)
			{
				if (memTypeFound)
				{
					*memTypeFound = true;
				}
				return i;
			}
		}
		typeBits >>= 1;
	}

	if (memTypeFound)
	{
		*memTypeFound = false;
		return 0;
	}
	else
	{
		throw std::runtime_error("Could not find a matching memory type");
	}
}