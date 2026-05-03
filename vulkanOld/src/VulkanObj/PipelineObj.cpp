/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/GraphicsPipelineObj.cpp $
% $Id: GraphicsPipelineObj.cpp 28 2023-05-03 19:30:42Z jb $
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

#include "VulkanObj/VulkanApp.hpp"
void PipelineObj::Create(ShaderObj* SHO,ResourceContainerObj* RCO)
{
	m_RCO = RCO;
	m_NumPipes = 1;
	m_SHO = SHO;
	CreatePipeline();
};
void PipelineObj::Create(ShaderObj* SHO, SwapChainObj* SCO, ResourceContainerObj* RCO, RenderPassObj* RPO)
{
	m_SCO = SCO;
	m_RPO = RPO;

	m_RPO->m_SubPassList;
	m_RCO = RCO;
	m_SHO = SHO;
	m_NumPipes = 1;
	CreatePipeline();
};

VkShaderModule PipelineObj::createShaderModule(const std::vector<char>& code, std::string Name) 
{
	VkShaderModuleCreateInfo createInfo{};
	createInfo.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
	createInfo.codeSize = code.size();
	createInfo.pCode = reinterpret_cast<const uint32_t*>(code.data());
	
	VkShaderModule shaderModule;
	uint32_t ret = vkCreateShaderModule(m_App->GetLogicalDevice(), &createInfo, nullptr, &shaderModule);
	if( ret != VK_SUCCESS && ret == VK_ERROR_INVALID_SHADER_NV)
	{
		std::ostringstream  objtxt;
		objtxt << "Error in PipelineObj::createShaderModule:" 
			<< m_Name << " Invalid Shader NV" << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	if (ret != VK_SUCCESS && ret == VK_ERROR_OUT_OF_HOST_MEMORY)
	{
		std::ostringstream  objtxt;
		objtxt << "Error in PipelineObj::createShaderModule:"
			<< m_Name << " VK_ERROR_OUT_OF_HOST_MEMORY" << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	if (ret != VK_SUCCESS && ret == VK_ERROR_OUT_OF_DEVICE_MEMORY)
	{
		std::ostringstream  objtxt;
		objtxt << "Error in PipelineObj::createShaderModule:"
			<< m_Name << " VK_ERROR_OUT_OF_DEVICE_MEMORY" << std::ends;
		throw std::runtime_error(objtxt.str());
	}
	m_App->NameObject(VK_OBJECT_TYPE_SHADER_MODULE, (uint64_t)shaderModule, Name.c_str());

	return shaderModule;
}


std::vector<char> PipelineObj::ReadFile(const std::string& filename) 
{
	std::ifstream file(filename, std::ios::ate | std::ios::binary);

	if (!file.is_open()) 
	{
		std::string rpt = "Failed to open file:" + filename;
		throw std::runtime_error(rpt.c_str());
	}

	size_t fileSize = (size_t) file.tellg();
	std::vector<char> buffer(fileSize);

	file.seekg(0);
	file.read(buffer.data(), fileSize);

	file.close();

	return buffer;
}
