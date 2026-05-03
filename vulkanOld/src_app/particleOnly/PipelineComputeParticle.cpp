/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/GraphicsPipeline.cpp $
% $Id: GraphicsPipeline.cpp 28 2023-05-03 19:30:42Z jb $
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

void PipelineComputeParticle::CreatePipeline()
{


    std::string testtype = CfgApp->GetString("application.testtype", true);
    std::string t_cshader_spv   = "application." + testtype +".comp_kernParticlespv";
    std::string t_cshader_glsl  = "application." + testtype +".comp_kernParticle";
  

    std::string cshader_spv = CfgApp->GetString(t_cshader_spv, true);;
    std::string cshader_glsl = CfgApp->GetString(t_cshader_glsl, true);;

    std::vector<char>  compShaderCode;
    m_SHO->CompileShader(cshader_glsl, cshader_spv, compShaderCode, m_SHO->SH_COMP);
    
    VkShaderModule computeShaderModule = 
        createShaderModule(compShaderCode, cshader_glsl);
       
        VkPipelineShaderStageCreateInfo computeShaderStageInfo{};
        computeShaderStageInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        computeShaderStageInfo.stage = VK_SHADER_STAGE_COMPUTE_BIT;
        computeShaderStageInfo.module = computeShaderModule;
        computeShaderStageInfo.pName = "main";
		
        // Associate decriptor memory and push constant layouts with the pipline then
       // the combination is the pipline layout.
        Resource* pco = (m_RCO->GetResourceName("PushConstants"));
        VkPipelineLayoutCreateInfo pipelineLayoutInfo{};
        pipelineLayoutInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        pipelineLayoutInfo.setLayoutCount = 1;
		pipelineLayoutInfo.pPushConstantRanges = &pco->m_PushConstant;
		pipelineLayoutInfo.pushConstantRangeCount = 1;
        pipelineLayoutInfo.pSetLayouts = m_RCO->GetDescriptorSetLayout();

        if (vkCreatePipelineLayout(m_App->GetLogicalDevice(), 
            &pipelineLayoutInfo, 
            nullptr,
            &m_PipelineLayout) != VK_SUCCESS) {
            throw std::runtime_error("Failed to create Compute Pipeline layout.");
        }

        VkComputePipelineCreateInfo pipelineInfo{};
        pipelineInfo.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        pipelineInfo.layout = m_PipelineLayout;
        pipelineInfo.stage = computeShaderStageInfo;

        if (vkCreateComputePipelines(m_App->GetLogicalDevice(), 
            VK_NULL_HANDLE, 
            1,
            &pipelineInfo, 
            nullptr, 
            &m_Pipeline) != VK_SUCCESS) {
            throw std::runtime_error("Failed to create Compute Pipeline.");
        }
		m_wkstr = m_Name+"Layout";
		m_App->NameObject(VK_OBJECT_TYPE_PIPELINE_LAYOUT, 
            (uint64_t)m_PipelineLayout, m_wkstr.c_str());
		
		m_App->NameObject(VK_OBJECT_TYPE_PIPELINE, (uint64_t)m_Pipeline, m_Name.c_str());

        vkDestroyShaderModule(m_App->GetLogicalDevice(), computeShaderModule, nullptr);
}
