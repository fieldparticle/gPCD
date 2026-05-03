/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/RenderPassObj.hpp $
% $Id: RenderPassObj.hpp 31 2023-06-12 20:17:58Z jb $
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
void RenderPassObj::Create(SwapChainObj* SCO,
    std::vector<ImageObject*> IMO, 
    std::vector<Resource*> SubPassList)
{

    m_IMO = IMO;
    m_SCO = SCO;
    m_SubPassList = SubPassList;
    
    createRenderPass();
};
void RenderPassObj::Create(SwapChainObj* SCO,
    std::vector<ImageObject*> IMO )
{

    m_IMO = IMO;
    m_SCO = SCO;
    createRenderPass();
};
void RenderPassObj::Create(SwapChainObj* SCO )
{
    m_SCO = SCO;
    
    createRenderPass();
};

void RenderPassObj::RenderPassObj::Cleanup()
{
    vkDestroyRenderPass(m_App->GetLogicalDevice(),
        m_RenderPass, nullptr);
};
