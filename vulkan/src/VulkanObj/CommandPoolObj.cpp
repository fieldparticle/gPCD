/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/CommandObj.cpp $
% $Id: CommandObj.cpp 31 2023-06-12 20:17:58Z jb $
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



void CommandPoolObj::Create(
    PhysDevObj* QA,
    SwapChainObj* SCO,
    RenderPassObj* RPO,
    FrameBufferObj* FBO,
    std::vector<CommandObj*> CPO)
{
    m_QA = QA;
    m_CPO = CPO;
    m_SCO = SCO;
    m_RPO = RPO;
    m_FBO = FBO;
    
    m_thisFramesBuffered = m_App->m_FramesBuffered;

    
    CreateCommandPool();
    CreateCommandBuffers();
    
}
void CommandPoolObj::CreateCommandPool()
{

    VkCommandPoolCreateInfo poolInfo{};
    poolInfo.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    poolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    poolInfo.queueFamilyIndex = m_QA->m_QFIndices.graphicsFamily.value();

    if (vkCreateCommandPool(m_App->GetLogicalDevice(), &poolInfo,
        nullptr, &m_CommandPool) != VK_SUCCESS)
    {
        std::ostringstream  objtxt;
        objtxt << m_Name << ":CommandPoolObj::CreateCommandPool Failed" << std::ends;
        throw std::runtime_error(objtxt.str());
    }

    m_App->NameObject(VK_OBJECT_TYPE_COMMAND_POOL,
        (uint64_t)m_CommandPool, m_Name.c_str());
    
  }
void CommandPoolObj::CreateCommandBuffers()
{

    for (uint32_t ii = 0; ii < m_CPO.size(); ii++)
    {
        // Resize to how many frames in flight 
        // FF are so that cpu can process while gpu is rendering
        m_CPO[ii]->CreateCommandBuffers(this);
    }
}

void CommandPoolObj::Cleanup()
{
    vkDestroyCommandPool(m_App->GetLogicalDevice(),m_CommandPool, VK_NULL_HANDLE);

}