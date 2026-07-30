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


void CommandLightingGraphics::Create(SwapChainObj* SCO,
	FrameBufferObj* FBO,
	RenderPassObj* RPO,
	ResourceContainerObj* RCO,
	std::vector<PipelineObj*> PLO)
{
	CommandObj::Create(SCO, FBO, RPO, RCO, PLO);
	for (uint32_t ii = 0; ii < m_PLO.size(); ii++)
	{
		if (!m_PLO[ii]->m_RenderPassName.compare("SubpassCube"))
			m_BoundarySubPass = ii;
	}

	for (uint32_t ii = 0; ii < m_PLO.size(); ii++)
	{
		if (!m_PLO[ii]->m_RenderPassName.compare("SubpassParticle"))
			m_ParticleSubPass = ii;
	}




}
void CommandLightingGraphics::RecordCommands(uint32_t imageindex, uint32_t currentBuffer)
{

	ConfigObj* cfg = CfgApp;
	std::ostringstream  objtxt;
	objtxt << m_Name << "Graphics Command Buffer:" << currentBuffer << std::ends;
	m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER,
		(uint64_t)m_CommandBuffers[currentBuffer], objtxt.str().c_str());

	Resource* collMem = (m_RCO->GetResourceName("CollisionImage"));
	Resource* lockMem = (m_RCO->GetResourceName("CollisionLockImage"));

	VkCommandBufferBeginInfo beginInfo{};
	beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;

		// Start recording command buffer.
		if (vkBeginCommandBuffer(m_CommandBuffers[currentBuffer], &beginInfo) != VK_SUCCESS)
		{
			throw std::runtime_error("CommandParticleGraphicsSub::RecordCommands failed at vkBeginCommandBuffer.");
		}
	// Associate a render pass with command buffer
	VkRenderPassBeginInfo renderPassInfo{};
	renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
	// Associate renderpass with command buffer
	renderPassInfo.renderPass = m_RPO->m_RenderPass;
	// Associate frame buffer with current swap chain image number.
	renderPassInfo.framebuffer = m_FBO->m_SwapChainFramebuffers[imageindex];
	renderPassInfo.renderArea.offset = { 0, 0 };
	renderPassInfo.renderArea.extent = m_SCO->GetSwapExtent();

	std::array<VkClearValue, 2> clearValues{};
	clearValues[0].color				= { {0.3f, 0.3f, 0.3f, 1.0f} };
	clearValues[1].depthStencil			= { 1.0f, 0 };
	//VkClearValue clearColor				= { {{0.0f, 0.0f, 0.0f, 1.0f}} };
	renderPassInfo.clearValueCount		= static_cast<uint32_t>(clearValues.size());
	renderPassInfo.pClearValues			= clearValues.data();

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

	// Record render pass parameters tell it where to get memory for shaders.
	vkCmdBeginRenderPass(m_CommandBuffers[currentBuffer], &renderPassInfo, VK_SUBPASS_CONTENTS_INLINE);
	RecordSubPassParticle(imageindex,currentBuffer);
	vkCmdNextSubpass(m_CommandBuffers[currentBuffer], VK_SUBPASS_CONTENTS_INLINE);
	RecordSubPassCube(imageindex,currentBuffer);
	vkCmdEndRenderPass(m_CommandBuffers[currentBuffer]);

	if (vkEndCommandBuffer(m_CommandBuffers[currentBuffer]) != VK_SUCCESS)
	{
		throw std::runtime_error("CommandParticleGraphicsSub::RecordCommands failed at vkEndCommandBuffer.");
	}

 }

void CommandLightingGraphics::RecordSubPassCube(uint32_t imageindex, uint32_t currentBuffer)
{
	bool use_lighting = CfgApp->GetBool("application.use_lighting", true);

	if (use_lighting == false)
	{
		return;
	}

	// Bind a pipline to this render pass.
	vkCmdBindPipeline(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_GRAPHICS, m_PLO[m_BoundarySubPass]->m_Pipeline);

	// Record the viewpoer to be used
	VkViewport viewport{};
	viewport.x = 0.0f;
	viewport.y = 0.0f;
	viewport.width = static_cast<float>(m_CPL->m_SCO->GetSwapWidth());
	viewport.height = static_cast<float>(m_CPL->m_SCO->GetSwapHeight());
	viewport.minDepth = static_cast<float>(m_CPL->m_SCO->GetSizzorMin());
	viewport.maxDepth = static_cast<float>(m_CPL->m_SCO->GetSizzorMax());
	vkCmdSetViewport(m_CommandBuffers[currentBuffer], 0, 1, &viewport);

	// Record the scissor area.
	VkRect2D scissor{};
	scissor.offset = { 0, 0 };
	scissor.extent = m_CPL->m_SCO->GetSwapExtent();
	vkCmdSetScissor(m_CommandBuffers[currentBuffer], 0, 1, &scissor);

	//############################ 1St Draw ###################################
	//############################ 1St Draw ###################################
	//############################ 1St Draw ###################################
	//--------------------------------------------------------------------------
	// Bind all vertex memory, descriptors for GPU memory (UBO,Push,SSBO,etc)
	// to command buffer.
	//--------------------------------------------------------------------------
	// Bind vertex buffer to command buffer.
	//PipelineObj* pipelineGraphicsBoundary = GetPipelineByName("ResourceContainerBoundary");

	// Bind the descriptor set associated with this record.
	vkCmdBindDescriptorSets(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_GRAPHICS,
		m_PLO[m_BoundarySubPass]->m_PipelineLayout,
		0,
		1,
		m_PLO[m_BoundarySubPass]->m_RCO->GetResourceSets(currentBuffer),
		0,
		nullptr);

	ResourceParticlePush* pco		= (ResourceParticlePush*)(m_RCO->GetResourceName("PushConstants"));
	unsigned long pcosize			= sizeof(pco->m_ShaderFlags);
	void* sfl						= &pco->m_ShaderFlags;
	uint32_t upcosize				= static_cast<uint32_t>(pcosize);

	VkDeviceSize offsets[] = { 0 };
	pco->m_ShaderFlags.DrawInstance = 2.0;
	vkCmdPushConstants(m_CommandBuffers[currentBuffer],
		m_PLO[m_BoundarySubPass]->m_PipelineLayout,
		VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);

	Resource* wallSurface = (m_RCO->GetResourceName("LightingSurfaces"));
	if (wallSurface->m_NumElements > 0)
	{
		VkBuffer* wallVertexBuffers = static_cast<VkBuffer*>(&wallSurface->m_Buffers[0]);
		vkCmdBindVertexBuffers(m_CommandBuffers[currentBuffer], 0, 1, wallVertexBuffers, offsets);

		uint32_t wallVertexCount = wallSurface->m_NumElements;
		vkCmdDraw(m_CommandBuffers[currentBuffer], wallVertexCount, 1, 0, 0);
	}
}
void CommandLightingGraphics::RecordSubPassParticle(uint32_t imageindex, uint32_t currentBuffer)
{

	//PipelineObj* graphicsParticlePipline = (m_RCO->GetResourceName("GraphicsContainerParticle"));
	// Bind a pipline to this render pass.
	vkCmdBindPipeline(m_CommandBuffers[currentBuffer], VK_PIPELINE_BIND_POINT_GRAPHICS,
		m_PLO[m_ParticleSubPass]->m_Pipeline);

#if 0
	Resource* collMem = (m_GraphicsResourceContainer[0]->GetResourceName("CollisionImage"));
	vkCmdFillBuffer(m_CommandGBuffers[currentBuffer],
		collMem->m_Buffers[currentBuffer],
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

	vkCmdSetViewport(m_CommandBuffers[currentBuffer], 0, 1, &viewport);

	// Record the scissor area.
	VkRect2D scissor{};
	scissor.offset = { 0, 0 };
	scissor.extent = m_SCO->GetSwapExtent();
	vkCmdSetScissor(m_CommandBuffers[currentBuffer], 0, 1, &scissor);


	//--------------------------------------------------------------------------
	// Bind all vertex memory, descriptors for GPU memory (UBO,Push,SSBO,etc)
	// to command buffer.
	//--------------------------------------------------------------------------
	// Bind vertex buffer to command buffer.
	unsigned long size = 0;
	Resource* dvo = (m_RCO->GetResourceName("VertexParticle"));
	VkBuffer* vertexBuffers = static_cast<VkBuffer*>(&dvo->m_Buffers[0]);
	VkDeviceSize offsets[] = { 0 };
	vkCmdBindVertexBuffers(m_CommandBuffers[currentBuffer], 4, 1, vertexBuffers, offsets);



	// Bind the descriptor set associated with this record.
	vkCmdBindDescriptorSets(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_GRAPHICS,
		m_PLO[m_ParticleSubPass]->m_PipelineLayout,
		0,
		1,
		m_RCO->GetResourceSets(currentBuffer),
		0,
		nullptr);

	ResourceParticlePush* pco = (ResourceParticlePush*)(m_RCO->GetResourceName("PushConstants"));
	unsigned long pcosize = sizeof(pco->m_ShaderFlags);
	void* sfl = &pco->m_ShaderFlags;
	uint32_t upcosize = static_cast<uint32_t>(pcosize);
	// Bind push constants to command buffer.
	vkCmdPushConstants(m_CommandBuffers[currentBuffer],
		m_PLO[m_ParticleSubPass]->m_PipelineLayout,
		VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);


	uint32_t vnum = dvo->m_NumElements;
	vkCmdDraw(m_CommandBuffers[currentBuffer], vnum, 1, 0, 0);

}
