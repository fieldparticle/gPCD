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

//
//
//
void CommandPoolParticleSub::CreateCommandPool()
{
	
	VkCommandPoolCreateInfo poolInfo{};
	poolInfo.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
	poolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
	poolInfo.queueFamilyIndex = m_QA->m_QFIndices.graphicsFamily.value();

	if (vkCreateCommandPool(m_App->GetLogicalDevice(), &poolInfo,
		nullptr, &m_CommandPool) != VK_SUCCESS)
	{
		throw std::runtime_error("failed to create command pool!");
	}

	m_App->NameObject(VK_OBJECT_TYPE_COMMAND_POOL,
		(uint64_t)m_CommandPool, m_Name.c_str());

	// One time copy of buffers upon creation of command pool.
	// Command pool required a resource container so this is always valid
	PipelineObj* particlePipeline = GetPipelineByName("GraphicsContainerParticle");
	std::vector<Resource*> gdrlst = particlePipeline->m_RCO->GetResourceList();
	for (uint32_t ii = 0; ii < gdrlst.size(); ii++)
	{
		gdrlst[ii]->CopyMem(this, 0, 0);
	}
	
	PipelineObj* boundaryPipline = GetPipelineByName("ResourceContainerBoundary");
	std::vector<Resource*> bdrlst = boundaryPipline->m_RCO->GetResourceList();
	for (uint32_t ii = 0; ii < bdrlst.size(); ii++)
	{
		bdrlst[ii]->CopyMem(this, 0, 0);
	}


	PipelineObj* computePipline = GetPipelineByName("ResourceContainerCompute");
	std::vector<Resource*> cdrlst = computePipline->m_RCO->GetResourceList();
	for (uint32_t ii = 0; ii < cdrlst.size(); ii++)
		{
			cdrlst[ii]->CopyMem(this, 0, 0);
		}
	

}
void CommandPoolParticleSub::CreateCommandBuffers()
{
	// For every pipline (compute or graphics)
	
		CreateGBuffers();
		CreateCBuffers();

}
void CommandPoolParticleSub::CreateCBuffers()
{
	m_CommandCBuffers.resize(m_App->m_FramesInFlight);
	
	VkCommandBufferAllocateInfo allocInfo{};
	allocInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
	allocInfo.commandPool = m_CommandPool;
	allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
	allocInfo.commandBufferCount = static_cast<uint32_t>(m_CommandCBuffers.size());

	if (vkAllocateCommandBuffers(m_App->GetLogicalDevice(), &allocInfo, m_CommandCBuffers.data()) != VK_SUCCESS)
	{
		throw std::runtime_error("failed to allocate command buffers!");
	}
	m_wkstr = m_Name + "Compute";
	m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER, (uint64_t)m_CommandCBuffers[0], m_wkstr.c_str());
	m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER, (uint64_t)m_CommandCBuffers[1], m_wkstr.c_str());
}
//
//
//
//
void CommandPoolParticleSub::CreateGBuffers()
{
	
		// Resize to how many frames in flight 
		// FF are so that cpu can process while gpu is rendering
		m_CommandGBuffers.resize(m_App->m_FramesInFlight);

		VkCommandBufferAllocateInfo allocInfo{};
		allocInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
		allocInfo.commandPool = m_CommandPool;
		allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
		allocInfo.commandBufferCount = static_cast<uint32_t>(m_CommandGBuffers.size());

		if (vkAllocateCommandBuffers(m_App->GetLogicalDevice(),
			&allocInfo, m_CommandGBuffers.data()) != VK_SUCCESS)
		{
			throw std::runtime_error("failed to allocate command buffers!");
		}

		for (size_t i = 0; i < m_App->m_FramesInFlight; i++)
		{
			std::ostringstream  objtxt;
			objtxt << m_Name << "Graphics Buffer:" << i << std::ends;

			m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER,
				(uint64_t)m_CommandGBuffers[i], objtxt.str().c_str());
		}
}


void CommandPoolParticleSub::RecordGCommandBuffer(uint32_t ImageIndex, uint32_t currentFrame)
{
	ConfigObj* cfg = m_App->m_CFG;
	PipelineObj* pipelineParticle = GetPipelineByName("GraphicsContainerParticle");
	PipelineObj* pipelineGraphicsBoundary = GetPipelineByName("GraphicsContainerParticle");

	Resource* collMem = (pipelineParticle->m_RCO->GetResourceName("CollisionImage"));
	Resource* lockMem = (pipelineParticle->m_RCO->GetResourceName("CollisionLockImage"));
	//Resource* counterMem = (m_GraphicsResourceContainer->GetResourceName("Atomic"));
	// Bind vertex buffer to command buffer.
	unsigned long size = 0;
	Resource* dvo = (pipelineParticle->m_RCO->GetResourceName("VertexParticle"));
	
		VkCommandBufferBeginInfo beginInfo{};
		beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;

		// Start recording command buffer.	
		if (vkBeginCommandBuffer(m_CommandGBuffers[currentFrame], &beginInfo) != VK_SUCCESS)
		{
			throw std::runtime_error("failed to begin recording command buffer!");
		}
		// Associate a render pass with command buffer
		VkRenderPassBeginInfo renderPassInfo{};
		renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
		// Associate renderpass with command buffer
		renderPassInfo.renderPass = m_RPO->m_RenderPass;
		// Associate frame buffer with current swap chain image number.
		renderPassInfo.framebuffer = m_FBO->m_SwapChainFramebuffers[ImageIndex];
		renderPassInfo.renderArea.offset = { 0, 0 };
		renderPassInfo.renderArea.extent = m_SCO->GetSwapExtent();

		std::array<VkClearValue, 2> clearValues{};
		clearValues[0].color = { {0.0f, 0.0f, 0.0f, 1.0f} };
		clearValues[1].depthStencil = { 1.0f, 0 };
		VkClearValue clearColor = { {{0.0f, 0.0f, 0.0f, 1.0f}} };
		renderPassInfo.clearValueCount = static_cast<uint32_t>(clearValues.size());
		renderPassInfo.pClearValues = clearValues.data();

		vkCmdFillBuffer(m_CommandGBuffers[currentFrame],
			collMem->m_Buffers[0],
			0,
			collMem->m_BufSize,
			0);

		vkCmdFillBuffer(m_CommandGBuffers[currentFrame],
			lockMem->m_Buffers[0],
			0,
			lockMem->m_BufSize,
			0);

		// Record render pass parameters tell it where to get memory for shaders.
		vkCmdBeginRenderPass(m_CommandGBuffers[currentFrame], &renderPassInfo, VK_SUBPASS_CONTENTS_INLINE);
		RecordSubPassParticle(currentFrame, pipelineParticle);
		

		vkCmdNextSubpass(m_CommandGBuffers[currentFrame], VK_SUBPASS_CONTENTS_INLINE);
		RecordSubPassCube(currentFrame, pipelineGraphicsBoundary);
		


		vkCmdEndRenderPass(m_CommandGBuffers[currentFrame]);

		if (vkEndCommandBuffer(m_CommandGBuffers[currentFrame]) != VK_SUCCESS)
		{
			throw std::runtime_error("failed to record command buffer!");
		}
	
 }

void CommandPoolParticleSub::RecordSubPassCube(uint32_t currentFrame, PipelineObj* Pipeline)
{

	// Bind a pipline to this render pass.
	vkCmdBindPipeline(m_CommandGBuffers[currentFrame], VK_PIPELINE_BIND_POINT_GRAPHICS, Pipeline->m_Pipeline[0]);

	// Record the viewpoer to be used
	VkViewport viewport{};
	viewport.x = 0.0f;
	viewport.y = 0.0f;
	viewport.width = static_cast<float>(m_SCO->GetSwapWidth());
	viewport.height = static_cast<float>(m_SCO->GetSwapHeight());
	viewport.minDepth = static_cast<float>(m_SCO->GetSizzorMin());
	viewport.maxDepth = static_cast<float>(m_SCO->GetSizzorMax());
	vkCmdSetViewport(m_CommandGBuffers[currentFrame], 0, 1, &viewport);

	// Record the scissor area.
	VkRect2D scissor{};
	scissor.offset = { 0, 0 };
	scissor.extent = m_SCO->GetSwapExtent();
	vkCmdSetScissor(m_CommandGBuffers[currentFrame], 0, 1, &scissor);


	//--------------------------------------------------------------------------
	// Bind all vertex memory, descriptors for GPU memory (UBO,Push,SSBO,etc)
	// to command buffer.
	//--------------------------------------------------------------------------
	// Bind vertex buffer to command buffer.
	PipelineObj* pipelineParticle = GetPipelineByName("GraphicsContainerParticle");
	PipelineObj* pipelineGraphicsBoundary = GetPipelineByName("ResourceContainerBoundary");
	unsigned long size = 0;
	Resource* dvo = (pipelineGraphicsBoundary->m_RCO->GetResourceName("VertexCube"));
	
	VkBuffer* vertexBuffers = static_cast<VkBuffer*>(dvo->GetBuffer(1, 0, size));
	VkDeviceSize offsets[] = { 0 };
	vkCmdBindVertexBuffers(m_CommandGBuffers[currentFrame], 0, 1, vertexBuffers, offsets);
#if 0
	unsigned long isize = 0;
	Resource* dio = (m_GraphicsResourceContainer->GetResourceName("Index"));
	VkBuffer* indexBuffers = static_cast<VkBuffer*>(dio->GetBuffer(1, 0, isize));
	isize = isize / 2;
	vkCmdBindIndexBuffer(m_CommandGBuffers[currentFrame], *indexBuffers, 0, VK_INDEX_TYPE_UINT16);
	uint16_t inum = dio->m_NumElements;
#else
	uint16_t inum = 0;
#endif
	// Bind the descriptor set associated with this record.
	vkCmdBindDescriptorSets(m_CommandGBuffers[currentFrame],
		VK_PIPELINE_BIND_POINT_GRAPHICS,
		pipelineGraphicsBoundary->m_PipelineLayout[0],
		0,
		1,
		pipelineGraphicsBoundary->m_RCO->GetResourceSets(currentFrame),
		0,
		nullptr);

	Resource* pco = (pipelineGraphicsBoundary->m_RCO->GetResourceName("PushConstants"));
	unsigned long pcosize = 0;
	void* sfl = pco->GetBuffer(0, 0, pcosize);
	uint32_t upcosize = static_cast<uint32_t>(pcosize);
	// Bind push constants to command buffer.
	vkCmdPushConstants(m_CommandGBuffers[currentFrame],
		pipelineGraphicsBoundary->m_PipelineLayout[0],
		VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);

	std::ostringstream  objtxt;
	objtxt << m_Name << "Graphics Command Buffer:" << currentFrame << std::ends;
	m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER,
		(uint64_t)m_CommandGBuffers[currentFrame], objtxt.str().c_str());

	uint16_t vnum = dvo->m_NumElements;
	

	// Record a draw index command.
   //vkCmdDrawIndexed(m_CommandGBuffers[m_App->GetCurrentFrame()], static_cast<uint32_t>(isize), 1.0, 0, 0, 0);
	//vkCmdDrawIndexed(m_CommandGBuffers[currentFrame], inum, 1, 0, 0, 0);
	vkCmdDraw(m_CommandGBuffers[currentFrame], vnum, 1, 0, 0);




}
void CommandPoolParticleSub::RecordSubPassParticle(uint32_t currentFrame, PipelineObj* Pipeline)
{
	PipelineObj* graphicsParticlePipline = GetPipelineByName("GraphicsContainerParticle");
	// Bind a pipline to this render pass.
	vkCmdBindPipeline(m_CommandGBuffers[currentFrame], VK_PIPELINE_BIND_POINT_GRAPHICS, Pipeline->m_Pipeline[0]);

#if 0
	Resource* collMem = (m_GraphicsResourceContainer[0]->GetResourceName("CollisionImage"));
	vkCmdFillBuffer(m_CommandGBuffers[currentFrame],
		collMem->m_Buffers[currentFrame],
		0,
		collMem->m_BufSize,
		0);
#endif

	// Record the viewpoer to be used
	VkViewport viewport{};
	viewport.x = 0.0f;
	viewport.y = 0.0f;
	viewport.width = static_cast<float>(m_SCO->GetSwapWidth());
	viewport.height = static_cast<float>(m_SCO->GetSwapHeight());

	viewport.minDepth = static_cast<float>(m_SCO->GetSizzorMin());
	viewport.maxDepth = static_cast<float>(m_SCO->GetSizzorMax());
	vkCmdSetViewport(m_CommandGBuffers[currentFrame], 0, 1, &viewport);

	// Record the scissor area.
	VkRect2D scissor{};
	scissor.offset = { 0, 0 };
	scissor.extent = m_SCO->GetSwapExtent();
	vkCmdSetScissor(m_CommandGBuffers[currentFrame], 0, 1, &scissor);


	//--------------------------------------------------------------------------
	// Bind all vertex memory, descriptors for GPU memory (UBO,Push,SSBO,etc)
	// to command buffer.
	//--------------------------------------------------------------------------
	// Bind vertex buffer to command buffer.
	unsigned long size = 0;
	Resource* dvo = (graphicsParticlePipline->m_RCO->GetResourceName("VertexParticle"));
	VkBuffer* vertexBuffers = static_cast<VkBuffer*>(dvo->GetBuffer(1, 0, size));
	VkDeviceSize offsets[] = { 0 };
	vkCmdBindVertexBuffers(m_CommandGBuffers[currentFrame], 4, 1, vertexBuffers, offsets);



	// Bind the descriptor set associated with this record.
	vkCmdBindDescriptorSets(m_CommandGBuffers[currentFrame],
		VK_PIPELINE_BIND_POINT_GRAPHICS,
		graphicsParticlePipline->m_PipelineLayout[0],
		0,
		1,
		graphicsParticlePipline->m_RCO->GetResourceSets(currentFrame),
		0,
		nullptr);

	Resource* pco = (graphicsParticlePipline->m_RCO->GetResourceName("PushConstants"));
	unsigned long pcosize = 0;
	void* sfl = pco->GetBuffer(0, 0, pcosize);
	uint32_t upcosize = static_cast<uint32_t>(pcosize);
	// Bind push constants to command buffer.
	vkCmdPushConstants(m_CommandGBuffers[currentFrame],
		graphicsParticlePipline->m_PipelineLayout[0],
		VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);


	uint16_t vnum = dvo->m_NumElements;
	vkCmdDraw(m_CommandGBuffers[currentFrame], vnum, 1, 0, 0);
}

void CommandPoolParticleSub::RecordCCommandBuffer(uint32_t currentFrame)
{
	PipelineObj* computePipline = GetPipelineByName("ResourceContainerCompute");

	VkCommandBufferBeginInfo beginInfo{};
	beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;

	if (vkBeginCommandBuffer(m_CommandCBuffers[currentFrame], &beginInfo) != VK_SUCCESS) {
		throw std::runtime_error("Failed to vkBeginCommandBuffer Compute Command Buffer.");
	}

	vkCmdBindPipeline(m_CommandCBuffers[currentFrame],
		VK_PIPELINE_BIND_POINT_COMPUTE, computePipline->m_Pipeline[0]);



	vkCmdBindDescriptorSets(m_CommandCBuffers[currentFrame],
		VK_PIPELINE_BIND_POINT_COMPUTE,
		computePipline->m_PipelineLayout[0],
		0,
		1,
		computePipline->m_RCO->GetResourceSets(currentFrame),
		0, 
		nullptr);




#if 0
	Resource* counterMem = (m_ComputeResourceContainer->GetResourceName("Atomic"));

	vkCmdFillBuffer(m_CommandCBuffers[currentFrame], counterMem->m_Buffers[currentFrame],
		0, counterMem->m_BufSize, 0);
#endif
	Resource* pco = computePipline->m_RCO->GetResourceName("PushConstants");
	unsigned long pcosize = 0;
	void* sfl = pco->GetBuffer(0, 0, pcosize);
	uint32_t upcosize = static_cast<uint32_t>(pcosize);
	// Bind push constants to command buffer.
	vkCmdPushConstants(m_CommandCBuffers[currentFrame],
		computePipline->m_PipelineLayout[0],
		VK_SHADER_STAGE_COMPUTE_BIT | 
		VK_SHADER_STAGE_VERTEX_BIT | 
		VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);

	Resource* dvo = (computePipline->m_RCO->GetResourceName("VertexParticle"));
	uint16_t vnum = dvo->m_NumElements;

	vkCmdDispatch(m_CommandCBuffers[currentFrame], vnum, 1, 1);

	if (vkEndCommandBuffer(m_CommandCBuffers[currentFrame]) != VK_SUCCESS) {
		throw std::runtime_error("Failed vkEndCommandBuffer Compute Command Buffer.");
	}
}

