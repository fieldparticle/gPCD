/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/RenderPass.cpp $
% $Id: RenderPass.cpp 31 2023-06-12 20:17:58Z jb $
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
 void RenderPassSubs::createRenderPass()
 {
    
     VkSubpassDependency dependency{};
     VkRenderPassCreateInfo renderPassInfo{};
     
     std::array<VkAttachmentDescription, 2> attachments = {};
     // Color attachment
     attachments[0].format = m_IMO[0]->m_Format;
     attachments[0].samples = VK_SAMPLE_COUNT_1_BIT;
     attachments[0].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
     attachments[0].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
     attachments[0].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
     attachments[0].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
     attachments[0].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
     attachments[0].finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;

     // Depth attachment
     attachments[1].format = m_IMO[1]->m_Format;
     attachments[1].samples = VK_SAMPLE_COUNT_1_BIT;
     attachments[1].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
     attachments[1].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
     attachments[1].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
     attachments[1].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
     attachments[1].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
     attachments[1].finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;
     
    
     
     VkAttachmentReference colorReferences = {};
     colorReferences.attachment = 0;
     colorReferences.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

     VkAttachmentReference depthReference = {};
     depthReference.attachment = 1;
     depthReference.layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    
     std::array<VkSubpassDescription, 2 > subpassDescriptions{};
     subpassDescriptions[0].pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
     subpassDescriptions[0].colorAttachmentCount = 1;
     subpassDescriptions[0].pColorAttachments = &colorReferences;
     subpassDescriptions[0].pDepthStencilAttachment = &depthReference;
     
     VkAttachmentReference inputReferences[3];
     inputReferences[0] = { 1, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL };
     inputReferences[1] = { 2, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL };


     subpassDescriptions[1].pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
     subpassDescriptions[1].colorAttachmentCount = 1;
     subpassDescriptions[1].pColorAttachments = &colorReferences;
     subpassDescriptions[1].pDepthStencilAttachment = &depthReference;

     // Use the color attachments filled in the first pass as input attachments
     subpassDescriptions[1].inputAttachmentCount = 1;
     subpassDescriptions[1].pInputAttachments = inputReferences;

     // Subpass dependencies for layout transitions
     std::array<VkSubpassDependency, 2> dependencies;

     // This makes sure that writes to the depth image are done before we try to write to it again
     dependencies[0].srcSubpass = VK_SUBPASS_EXTERNAL;
     dependencies[0].dstSubpass = 0;
     dependencies[0].srcStageMask = VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT;
     dependencies[0].dstStageMask = VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT;
     dependencies[0].srcAccessMask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT;
     dependencies[0].dstAccessMask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT;
     dependencies[0].dependencyFlags = VK_DEPENDENCY_BY_REGION_BIT;

     // This dependency transitions the input attachment from color attachment to input attachment read
     dependencies[1].srcSubpass = 0;
     dependencies[1].dstSubpass = 1;
     dependencies[1].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
     dependencies[1].dstStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
     dependencies[1].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
     dependencies[1].dstAccessMask = VK_ACCESS_INPUT_ATTACHMENT_READ_BIT;
     dependencies[1].dependencyFlags = VK_DEPENDENCY_BY_REGION_BIT;


    
    renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    renderPassInfo.attachmentCount = static_cast<uint32_t>(attachments.size());
    renderPassInfo.pAttachments = attachments.data();
    renderPassInfo.subpassCount = static_cast<uint32_t>(subpassDescriptions.size());
    renderPassInfo.pSubpasses = subpassDescriptions.data();
    renderPassInfo.dependencyCount = static_cast<uint32_t>(dependencies.size());;
    renderPassInfo.pDependencies = dependencies.data();


        if (vkCreateRenderPass(m_App->GetLogicalDevice(),
            &renderPassInfo, nullptr, &m_RenderPass) != VK_SUCCESS) 
        {
            throw std::runtime_error("Failed to vkCreateRenderPass in RenderPass::createRenderPass() !");
        }

        m_App->NameObject(VK_OBJECT_TYPE_RENDER_PASS,
            (uint64_t)m_RenderPass, m_Name.c_str());
        
        /// MIght have problem with these since there are multiple swap 
        // image view but only one depth view
        std::array<VkImageView, 2> image_attachments = {
               m_SCO->m_SwapChainImageViews[0],
               m_IMO[0]->m_ImageView
        };
        
}
