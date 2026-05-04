/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/GraphicsPipeline.hpp $
% $Id: GraphicsPipeline.hpp 28 2023-05-03 19:30:42Z jb $
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
%*$Revision: 28 $
%*
%*
%******************************************************************/

#ifndef PIPELINEBOUNDARY_HPP
#define PIPELINEBOUNDARY_HPP
class PipelineObj;
class PipelineGraphicsBoundary : public PipelineObj
{
    public:
	bool m_WireFlag = false;
	size_t m_NumPipes = 0;
	std::vector<VkDynamicState> m_DynamicStates = {};
	VkPipelineViewportStateCreateInfo m_ViewportState = {};
	VkPipelineRasterizationStateCreateInfo m_Rasterizer={};
	VkPipelineMultisampleStateCreateInfo m_Multisampling={};
	VkPipelineColorBlendStateCreateInfo m_ColorBlending={};
	VkPipelineDepthStencilStateCreateInfo m_DepthStencil={};
	VkPipelineDynamicStateCreateInfo m_DynamicState={};
	VkViewport m_Viewport = {};
	VkPipelineColorBlendAttachmentState m_ColorBlendAttachment={};
	VkRect2D m_Scissor = {};
	virtual void CreatePipeline();
	void AddBoundaryPipe();
	//void Create(SwapChainObj* SCO, ResourceContainerObj* RCO, RenderPassObj* RPO);
	PipelineGraphicsBoundary(VulkanObj *App, std::string Name): PipelineObj(App, Name, VBW_TYPE_GRAPHPIPE)
	{
		
	};
	
	void createPipeline();
	
};
#endif