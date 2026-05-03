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
void SubPassBoundary::Create(SwapChainObj* SCO, std::vector<ImageObject*>  IMO, uint32_t StartBindPoint, uint32_t SubPassNum, uint32_t TotSubPass)
{
    
    m_DesWriteCount = 0;
    
    m_SCO = SCO;
    m_IMO = IMO;
    
    m_BindPoint = StartBindPoint;
    m_SubPassNum = SubPassNum;
    m_TotSubPass = TotSubPass;
	
    m_VkType = VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT;
    m_ColorAttachment.format = IMO[0]->m_Format;
    m_ColorAttachment.samples = VK_SAMPLE_COUNT_1_BIT;
    m_ColorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    m_ColorAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    m_ColorAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    m_ColorAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    m_ColorAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    m_ColorAttachment.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
   

    if(m_TotSubPass > 1)
        m_ColorAttachmentRef.attachment = 1;
    else
        m_ColorAttachmentRef.attachment = 0;

    m_ColorAttachmentRef.layout = 
        VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
           
    m_DepthAttachment.format = IMO[1]->m_Format;
    m_DepthAttachment.samples = VK_SAMPLE_COUNT_1_BIT;
    m_DepthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    m_DepthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    m_DepthAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    m_DepthAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    m_DepthAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    m_DepthAttachment.finalLayout = 
        VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    if (m_TotSubPass > 1)
        m_DepthAttachmentRef.attachment = 2;
    else    
        m_DepthAttachmentRef.attachment = 1;

    m_DepthAttachmentRef.layout =
        VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    m_Subpass.resize(1);
   	VkAttachmentReference colorReference02{};
	colorReference02.attachment = 0;
	colorReference02.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

	m_Subpass[0].pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
	m_Subpass[0].colorAttachmentCount = 1;
	m_Subpass[0].pColorAttachments = &colorReference02;


	m_InputReferences[0].attachment = 1;
	m_InputReferences[0].layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;

	m_InputReferences[0].attachment = 2;
	m_InputReferences[0].layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;

	m_Subpass.resize(1);
	m_Subpass[0].inputAttachmentCount = 2;
	m_Subpass[0].pInputAttachments = m_InputReferences;
	
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = 1;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
	

      
	
}

