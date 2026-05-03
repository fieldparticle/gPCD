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
void CommandParticleCompute::Create(SwapChainObj* SCO,
		FrameBufferObj* FBO,
		RenderPassObj* RPO,
		ResourceContainerObj* RCO,
		std::vector<PipelineObj*> PLO)
{
	CommandObj::Create(SCO,FBO,RPO,RCO,PLO);

	m_dkx = CfgTst->GetInt("dispatchx", true);
	m_dky = CfgTst->GetInt("dispatchy", true);
	m_dkz = CfgTst->GetInt("dispatchz", true);

}
//
//
//
void CommandParticleCompute::RecordCommands(uint32_t imageIndex, uint32_t currentBuffer)
{
	Resource* dvo = (m_RCO->GetResourceName("VertexParticle"));
	
	VkCommandBufferBeginInfo beginInfo{};
	beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
	
	if (vkBeginCommandBuffer(m_CommandBuffers[currentBuffer], &beginInfo) != VK_SUCCESS) {
		throw std::runtime_error("Failed to vkBeginCommandBuffer Compute Command Buffer.");
	}
	Resource* lockMem = (m_RCO->GetResourceName("CollisionLockImage"));
	vkCmdFillBuffer(m_CommandBuffers[currentBuffer],
		lockMem->m_Buffers[0],
		0,
		lockMem->m_BufSize,
		0);

	//vkResetQueryPool(m_App->GetLogicalDevice(), m_PerfQueryPool, 0, 4);
	vkCmdBindPipeline(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_COMPUTE, m_PLO[0]->m_Pipeline);

	vkCmdBindDescriptorSets(m_CommandBuffers[currentBuffer],
		VK_PIPELINE_BIND_POINT_COMPUTE,
		m_PLO[0]->m_PipelineLayout,
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
		m_PLO[0]->m_PipelineLayout,
		VK_SHADER_STAGE_COMPUTE_BIT | 
		VK_SHADER_STAGE_VERTEX_BIT | 
		VK_SHADER_STAGE_FRAGMENT_BIT,
		0,
		upcosize,
		sfl);

	if (trace_on_flag == true)
	{
		vkCmdResetQueryPool(m_CommandBuffers[currentBuffer], m_PerfQueryPool,
			0, static_cast<uint32_t>(mTimeQueryResults.size()));

		vkCmdWriteTimestamp(m_CommandBuffers[currentBuffer],
			VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, m_PerfQueryPool, 0);
		uint32_t vnum = dvo->m_NumElements;
	}

	vkCmdDispatch(m_CommandBuffers[currentBuffer], m_dkx, m_dky, m_dkz);
	
	if (trace_on_flag == true)
	{
		vkCmdWriteTimestamp(m_CommandBuffers[currentBuffer],
			VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, m_PerfQueryPool, 1);
	}
	
	if (vkEndCommandBuffer(m_CommandBuffers[currentBuffer]) != VK_SUCCESS) {
		throw std::runtime_error("Failed vkEndCommandBuffer Compute Command Buffer.");
	}
}

