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
void CommandObj::Create(SwapChainObj* SCO,
    FrameBufferObj* FBO,
    RenderPassObj* RPO,
    ResourceContainerObj* RCO,
    std::vector<PipelineObj*> PLO)
{
    m_thisFramesBuffered = m_App->m_FramesBuffered;
    m_PLO = PLO;
    m_RCO = RCO;
    m_SCO = SCO;
    m_FBO = FBO;
    m_RPO = RPO;
   
    m_CommandBuffers.resize(m_thisFramesBuffered);
    

}
void CommandObj::Cleanup()
{
	vkFreeCommandBuffers(m_App->GetLogicalDevice(),
		m_CPL->m_CommandPool, 1, m_CommandBuffers.data());
    if(m_PerfQueryPool != VK_NULL_HANDLE)
        vkDestroyQueryPool(m_App->GetLogicalDevice(), m_PerfQueryPool, VK_NULL_HANDLE);

};
void CommandObj::CreateCommandBuffers(CommandPoolObj* CPL)
{
    m_CPL = CPL;
        // Resize to how many frames in flight 
    // FF are so that cpu can process while gpu is rendering
    m_CommandBuffers.resize(m_thisFramesBuffered);

    VkCommandBufferAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    allocInfo.commandPool = m_CPL->m_CommandPool;
    allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    allocInfo.commandBufferCount = static_cast<uint32_t>(m_CommandBuffers.size());

    // Give all resources pointer to command pool.
  //  for (size_t jj = 0; jj < m_RCO->m_DRList.size(); jj++)
  //  {
  //      m_RCO->m_DRList[jj]->m_CPL = CPL;
  //  }

    if (vkAllocateCommandBuffers(m_App->GetLogicalDevice(),
        &allocInfo, m_CommandBuffers.data()) != VK_SUCCESS)
    {
        throw std::runtime_error("CommandPoolObj::CreateCommandBuffers() vkAllocateCommandBuffers Failed");
    }

    for (size_t i = 0; i < m_thisFramesBuffered; i++)
    {
        std::ostringstream  objtxt;
        objtxt << m_Name << "CommandBuffer:" << i << std::ends;

        m_App->NameObject(VK_OBJECT_TYPE_COMMAND_BUFFER,
            (uint64_t)m_CommandBuffers[i], objtxt.str().c_str());
    }
    CreateQueryPool();
}

void CommandObj::SetTimeStamp(uint32_t currentBuffer)
{
    vkCmdResetQueryPool(m_CommandBuffers[currentBuffer], m_PerfQueryPool, currentBuffer, currentBuffer * 2);
    vkCmdWriteTimestamp(m_CommandBuffers[currentBuffer],
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, m_PerfQueryPool, currentBuffer * 2);
}
void CommandObj::CreateQueryPool()
{
    VkQueryPoolCreateInfo createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
    createInfo.pNext = nullptr; // Optional
    createInfo.flags = 0; // Reserved for future use, must be 0!

    createInfo.queryType = VK_QUERY_TYPE_TIMESTAMP;
    m_QueryCount = (uint32_t)m_CommandBuffers.size() * 2; // REVIEW
    createInfo.queryCount = m_QueryCount;
    mTimeQueryResults.resize(m_QueryCount);
    
    VkResult result = vkCreateQueryPool(m_App->GetLogicalDevice(), &createInfo, nullptr, &m_PerfQueryPool);
    if (result != VK_SUCCESS)
    {
        throw std::runtime_error("CommandObj::CreateQueryPool Error at vkCreateQueryPool.");
    }

    std::ostringstream  objtxt;
    objtxt << m_Name << " QueryPool:" << std::ends;
    m_App->NameObject(VK_OBJECT_TYPE_QUERY_POOL,
        (uint64_t)m_PerfQueryPool, objtxt.str().c_str());
   

}
void CommandObj::FetchRenderTimeResults(uint32_t CurrentBuffer)
{
    uint64_t buffer[2];
#if 1
        VkResult result = vkGetQueryPoolResults(m_App->GetLogicalDevice(), m_PerfQueryPool,
            0, 2, sizeof(uint64_t) * m_QueryCount, buffer, sizeof(uint64_t),
            VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
        if (result == VK_NOT_READY)
        {
            return;
        }
        else if (result == VK_SUCCESS)
        {
            mTimeQueryResults[CurrentBuffer] = (buffer[1] - buffer[0]);
            m_ExecutionTime = static_cast<double>(mTimeQueryResults[CurrentBuffer]
                * m_App->m_DevProp.limits.timestampPeriod) / 1000000000.0;
        }
        else
        {
            throw std::runtime_error("Failed to receive query results!");
        }


        // Queries must be reset after each individual use.
        vkResetQueryPool(m_App->GetLogicalDevice(), m_PerfQueryPool, 0, m_QueryCount);
#endif   
}

double CommandObj::GetExecutionTime()
{
    return m_ExecutionTime;


}