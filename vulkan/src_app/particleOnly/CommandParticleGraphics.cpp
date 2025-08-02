/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/CommandPool.cpp $
% $Id: CommandPool.cpp 31 2023-06-12 20:17:58Z jb $
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


void CommandParticleGraphics::RecordCommands( uint32_t imageIndex, uint32_t currentBuffer)
{
			
	Resource* collMem = (m_RCO->GetResourceName("CollisionImage"));
	Resource* lockMem = (m_RCO->GetResourceName("CollisionLockImage"));
	// Bind vertex buffer to command buffer.
	unsigned long size = 0;
	Resource* dvo = (m_RCO->GetResourceName("VertexParticle"));
	VkBuffer* vertexBuffers = static_cast<VkBuffer*>(&dvo->m_Buffers[0]);
	VkDeviceSize offsets[] = { 0 };

	VkCommandBufferBeginInfo beginInfo{};
	beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;

	// Start recording command buffer.	
	if (vkBeginCommandBuffer(m_CommandBuffers[currentBuffer], &beginInfo) != VK_SUCCESS)
	{
		std::ostringstream  objtxt;
		objtxt << m_Name << " Failed at  vkBeginCommandBuffer" << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	//SetTimeStamp(currentBuffer);
#if 1
	vkCmdFillBuffer(m_CommandBuffers[currentBuffer],
		collMem->m_Buffers[0],
		0,
		collMem->m_BufSize,
		0);

	vkCmdFillBuffer(m_CommandBuffers[currentBuffer],
		lockMem->m_Buffers[0],
		0,
		lockMem->m_BufSize,
		0);
#endif

	// Associate a render pass with command buffer
	VkRenderPassBeginInfo renderPassInfo{};
	renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
	// Associate renderpass with command buffer
	renderPassInfo.renderPass = m_RPO->m_RenderPass;

	// Validation Error: [ VUID-VkPresentInfoKHR-pImageIndices-01430 ] 
	// is violated if this is not the same image index.
	// Associate frame buffer with current swap chain image number.
	renderPassInfo.framebuffer = m_FBO->m_SwapChainFramebuffers[imageIndex];
	renderPassInfo.renderArea.offset = { 0, 0 };
	renderPassInfo.renderArea.extent = m_SCO->GetSwapExtent();

	
	VkClearValue clearValues{};
	clearValues.color = { {0.0f, 0.0f, 0.0f, 1.0f} };
	VkClearValue clearColor = { {{0.0f, 0.0f, 0.0f, 1.0f}} };
	renderPassInfo.clearValueCount = 1;
	renderPassInfo.pClearValues = &clearColor;
	if (trace_on_flag == true)
	{
		vkCmdResetQueryPool(m_CommandBuffers[currentBuffer], m_PerfQueryPool,
			0, static_cast<uint32_t>(mTimeQueryResults.size()));
		vkCmdWriteTimestamp(m_CommandBuffers[currentBuffer],
			VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, m_PerfQueryPool, 0);
	}
	
	// Record render pass parameters tell it where to get memory for shaders.
	vkCmdBeginRenderPass(m_CommandBuffers[currentBuffer], &renderPassInfo, VK_SUBPASS_CONTENTS_INLINE);

	// Bind a pipline to this render pass.
	vkCmdBindPipeline(m_CommandBuffers[currentBuffer], VK_PIPELINE_BIND_POINT_GRAPHICS,
		m_PLO[0]->m_Pipeline );


	//--------------------------------------------------------------------------
	// Bind all vertex memory, descriptors for GPU memory (UBO,Push,SSBO,etc)
	// to command buffer.
	//--------------------------------------------------------------------------
		
	// Record the viewpoer to be used
	VkViewport viewport{};
	viewport.x = 0.0f;
	viewport.y = 0.0f;
	viewport.width = static_cast<float>(m_SCO->GetSwapWidth());
	viewport.height = static_cast<float>(m_SCO->GetSwapHeight());

	viewport.minDepth = static_cast<float>(m_SCO->GetSizzorMin());
	viewport.maxDepth = static_cast<float>(m_SCO->GetSizzorMax());
	vkCmdSetViewport(m_CommandBuffers[currentBuffer], 0, 1, &viewport);

	// Record the scissor area.
	VkRect2D scissor{};
	scissor.offset = { 0, 0 };
	scissor.extent = m_SCO->GetSwapExtent();
	vkCmdSetScissor(m_CommandBuffers[currentBuffer], 0, 1, &scissor);
	vkCmdBindVertexBuffers(m_CommandBuffers[currentBuffer], 4, 1, vertexBuffers, offsets);

	//vkCmdSetRasterizationSamplesEXT(m_CommandBuffers[currentBuffer],VK_SAMPLE_COUNT_8_BIT );


	// Bind the descriptor set associated with this record.
	vkCmdBindDescriptorSets(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_GRAPHICS,
		m_PLO[0]->m_PipelineLayout,
		0,
		1,
		m_RCO->GetResourceSets(currentBuffer),
		0,
		nullptr);

	ResourceParticlePush* pco = (ResourceParticlePush*) (m_RCO->GetResourceName("PushConstants"));
	unsigned long pcosize = sizeof(pco->m_ShaderFlags);
	void* sfl = &pco->m_ShaderFlags;
	uint32_t upcosize = static_cast<uint32_t>(pcosize);
	// Bind push constants to command buffer.
	vkCmdPushConstants(m_CommandBuffers[currentBuffer],
		m_PLO[0]->m_PipelineLayout,
		VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);

	
	/*#################################################################
	* Draw comand
	* #################################################################*/
	
	uint32_t vnum = dvo->m_NumElements;

	vkCmdDraw(m_CommandBuffers[currentBuffer], vnum, 1, 0, 0);
	/* The particle, collisions andlock image must be done before
	* contimuing to compute shader.
	* */
	

		
	vkCmdEndRenderPass(m_CommandBuffers[currentBuffer]);
	if (trace_on_flag == true)
	{
		vkCmdWriteTimestamp(m_CommandBuffers[currentBuffer],
			VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, m_PerfQueryPool, 1);
	}
	if (vkEndCommandBuffer(m_CommandBuffers[currentBuffer]) != VK_SUCCESS)
	{
		throw std::runtime_error("CommandParticleGraphics::RecordCommands at vkEndCommandBuffer");
	}
	
 }
