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
void SubPassParticle::Create(SwapChainObj* SCO,
	std::vector<ImageObject*>  IMO,
	uint32_t StartBindPoint, uint32_t SubPassNum, uint32_t TotSubPass)
{
	
	m_SCO = SCO;
	m_IMO = IMO;
	m_thisFramesBuffered = 1;
	m_VkType = VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT;
	m_TotSubPass = TotSubPass;
	m_SubPassNum = SubPassNum;
	
	///=================SUBPASS 1 ========================
	VkAttachmentReference colorReference01{};
	colorReference01.attachment = 1;
	colorReference01.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

	VkAttachmentReference depthReference{};
	depthReference.attachment = 2;
	depthReference.layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

	m_Subpass.resize(1);
	m_Subpass[0].pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
	m_Subpass[0].colorAttachmentCount = 1;
	m_Subpass[0].pColorAttachments = &colorReference01;
	m_Subpass[0].pDepthStencilAttachment = &depthReference;
	
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = 0;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT ;
	
	
	m_ImageInfos.resize(2);
	m_ImageInfos[0].imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
	m_ImageInfos[0].imageView = m_IMO[0]->m_ImageView;
	m_ImageInfos[0].sampler = VK_NULL_HANDLE;
	
	m_ImageInfos[1].imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
	m_ImageInfos[1].imageView = m_IMO[1]->m_ImageView;
	m_ImageInfos[1].sampler = VK_NULL_HANDLE;

	m_DescriptorWrite.resize(1);
	m_DescriptorWrite[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[0].descriptorType = VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT;
	m_DescriptorWrite[0].descriptorCount = 1;
	m_DescriptorWrite[0].dstBinding = 0;
	m_DescriptorWrite[0].pImageInfo = m_ImageInfos.data();
		
	

}

