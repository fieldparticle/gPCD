/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/FrameBuffer.cpp $
% $Id: FrameBuffer.cpp 31 2023-06-12 20:17:58Z jb $
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

class RenderPass;
 void FrameBufferSubPass::createFramebuffers() 
 {
		

        m_SwapChainFramebuffers.resize(m_App->GetSwapCount());
        

        for (size_t i = 0; i < m_App->GetSwapCount(); i++) 
		{
            //VkImageView attachments[] = {m_SCO->m_swapChainImageViews[i]};

            std::array<VkImageView, 2> attachments = {
                m_SCO->m_SwapChainImageViews[i],
                m_RPO->m_SubPassList[0]->m_IMO[1]->m_ImageView
            };
          
            VkFramebufferCreateInfo framebufferInfo{};
            framebufferInfo.sType 			= VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
            framebufferInfo.renderPass 		= m_RPO->m_RenderPass;
            framebufferInfo.attachmentCount = static_cast<uint32_t>(attachments.size());;
            framebufferInfo.pAttachments 	= attachments.data();
            framebufferInfo.width 			= m_SCO->m_SwapChainExtent.width;
            framebufferInfo.height 			= m_SCO->m_SwapChainExtent.height;
            framebufferInfo.layers 			= 1;

            if (vkCreateFramebuffer( m_App->GetLogicalDevice(), 
                &framebufferInfo, nullptr, 
                &m_SwapChainFramebuffers[i]) != VK_SUCCESS) 
			{
                throw std::runtime_error("failed to create framebuffer!");
            }
			
            
            std::ostringstream  objtxt;
			objtxt << m_Name << "#:" << i << std::ends;
			m_App->NameObject(VK_OBJECT_TYPE_FRAMEBUFFER, 
                (uint64_t)m_SwapChainFramebuffers[i], objtxt.str().c_str());
			

        }
    }
	