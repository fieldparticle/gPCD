/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/GraphicsPipelineObj.hpp $
% $Id: GraphicsPipelineObj.hpp 28 2023-05-03 19:30:42Z jb $
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


#ifndef PIPELINEOBJ_HPP
#define PIPELINEOBJ_HPP
class ShaderObj;
class PipelineObj : public BaseObj
{
    public:
    
	size_t m_NumPipes = 0;
	VkPipelineLayout 		m_PipelineLayout={};
	VkPipeline				m_Pipeline={};
	RenderPassObj*			m_RPO={};
	ResourceContainerObj*	m_RCO={};
	SwapChainObj*			m_SCO={};
	ShaderObj*				m_SHO = {};
	std::string				m_RenderPassName = {};
	
		
	void Create(ShaderObj* SHO, SwapChainObj* SCO, ResourceContainerObj* RCO, RenderPassObj* RPO);
	void Create(ShaderObj* SHO,ResourceContainerObj* RCO);
	PipelineObj(VulkanObj *App, std::string Name, uint32_t Type) : BaseObj(Name, Type,App) {};
	virtual void CreatePipeline()=0;
	VkShaderModule createShaderModule(const std::vector<char>& code,std::string Name);
	//virtual void Create(SwapChainObj* SCO, ResourceContainerObj* RCO, RenderPassObj* RPO) {};

	std::vector<char> ReadFile(const std::string& filename) ;
    void Cleanup()
	{
		vkDestroyPipeline(m_App->GetLogicalDevice(), m_Pipeline, nullptr);
		vkDestroyPipelineLayout(m_App->GetLogicalDevice(), m_PipelineLayout, nullptr);
		
		
    };
};
#endif