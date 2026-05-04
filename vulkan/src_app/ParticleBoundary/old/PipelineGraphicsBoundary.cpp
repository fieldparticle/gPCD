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

void PipelineGraphicsBoundary::CreatePipeline()
{
    ConfigObj* cfg = m_App->m_CFG;

    std::string fshader_spv = "shaders/" + m_App->m_CFG->m_fragSPVBoundary;
    std::string fshader_glsl = "shaders/" + m_App->m_CFG->m_fragShaderBoundary;

    std::string vshader_spv = "shaders/" + m_App->m_CFG->m_vertSPVBoundary;
    std::string vshader_glsl = "shaders/" + m_App->m_CFG->m_vertShaderBoundary;

    std::vector<char>  fragShaderCode;
    m_SHO->CompileShader(fshader_glsl, fshader_spv, fragShaderCode, m_SHO->SH_FRAG);
    VkShaderModule fragShaderModule = createShaderModule(fragShaderCode,
        fshader_glsl);

    
    std::vector<char>  vertShaderCode;
    m_SHO->CompileShader(vshader_glsl, vshader_spv, vertShaderCode, m_SHO->SH_VERT);
    VkShaderModule vertShaderModule = createShaderModule(vertShaderCode,
        vshader_glsl);

    Resource* dvo = (m_RCO->GetResourceName("VertexCube"));
    VkVertexInputBindingDescription* bindingDescription = dvo->GetBindingDescription();
    std::vector<VkVertexInputAttributeDescription>* attributeDescriptions = dvo->GetAttributeDescriptions();

    

    VkPipelineShaderStageCreateInfo vertShaderStageInfo{};
    vertShaderStageInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    vertShaderStageInfo.stage = VK_SHADER_STAGE_VERTEX_BIT;
    vertShaderStageInfo.module = vertShaderModule;
    vertShaderStageInfo.pName = "main";

    VkPipelineShaderStageCreateInfo fragShaderStageInfo{};
    fragShaderStageInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    fragShaderStageInfo.stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    fragShaderStageInfo.module = fragShaderModule;
    fragShaderStageInfo.pName = "main";


    VkPipelineShaderStageCreateInfo shaderStages[] = { vertShaderStageInfo,fragShaderStageInfo };


    // Tell the pipline the binding points for verticies and attributes. 

    VkPipelineVertexInputStateCreateInfo vertexInputInfo{};
    vertexInputInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertexInputInfo.vertexBindingDescriptionCount = 1;
    vertexInputInfo.vertexAttributeDescriptionCount = static_cast<uint32_t>(attributeDescriptions->size());
    vertexInputInfo.pVertexBindingDescriptions = bindingDescription;
    vertexInputInfo.pVertexAttributeDescriptions = attributeDescriptions->data();


    // cfg->wireframeB
    VkPipelineInputAssemblyStateCreateInfo inputAssembly{};
    if (cfg->m_WireFlag == false)
    {
        inputAssembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        inputAssembly.primitiveRestartEnable = VK_FALSE;
    }
    else
    {
        inputAssembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_LINE_LIST;
        //inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_LINE_STRIP;
        inputAssembly.primitiveRestartEnable = VK_FALSE;
    }

    std::vector<VkDynamicState> dynamicStates = {
       VK_DYNAMIC_STATE_VIEWPORT,
       VK_DYNAMIC_STATE_SCISSOR
    };


    
    m_DynamicState.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    m_DynamicState.dynamicStateCount = static_cast<uint32_t>(dynamicStates.size());
    m_DynamicState.pDynamicStates = dynamicStates.data();

    // Associate decriptor memory and push constant layouts with the pipline then
        // the combination is the pipline layout.
    Resource* pco = (m_RCO->GetResourceName("PushConstants"));


    VkPipelineLayoutCreateInfo pipelineLayoutInfo{};
    pipelineLayoutInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pipelineLayoutInfo.setLayoutCount = 1;
    pipelineLayoutInfo.pSetLayouts = m_RCO->GetDescriptorSetLayout();
    pipelineLayoutInfo.pushConstantRangeCount = 1;
    pipelineLayoutInfo.pPushConstantRanges = &pco->m_PushConstant;


    if (vkCreatePipelineLayout(m_App->GetLogicalDevice(),
        &pipelineLayoutInfo, nullptr,
        &m_PipelineLayout) != VK_SUCCESS)
    {
        throw std::runtime_error("failed to create pipeline layout!");
    }

    m_wkstr = m_Name + " Layout";
    m_App->NameObject(VK_OBJECT_TYPE_PIPELINE_LAYOUT,
        (uint64_t)m_PipelineLayout, m_wkstr.c_str());

    //https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VkGraphicsPipelineCreateInfo.html
    VkGraphicsPipelineCreateInfo pipelineInfo{};
    pipelineInfo.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    pipelineInfo.stageCount = 2;
    pipelineInfo.pStages = shaderStages;
    pipelineInfo.pVertexInputState = &vertexInputInfo;
    pipelineInfo.pInputAssemblyState = &inputAssembly;
    pipelineInfo.pViewportState = &m_ViewportState;
    pipelineInfo.pRasterizationState = &m_Rasterizer;
    pipelineInfo.pMultisampleState = &m_Multisampling;
    pipelineInfo.pColorBlendState = &m_ColorBlending;
    pipelineInfo.pDepthStencilState = &m_DepthStencil;
    pipelineInfo.pDynamicState = &m_DynamicState;
    pipelineInfo.layout = m_PipelineLayout;
    pipelineInfo.renderPass = m_RPO->GetRenderPass();
    pipelineInfo.subpass = 1; // 0


    pipelineInfo.basePipelineHandle = VK_NULL_HANDLE;

    if (vkCreateGraphicsPipelines(m_App->GetLogicalDevice(),
        VK_NULL_HANDLE,
        1,
        &pipelineInfo,
        nullptr,
        &m_Pipeline) != VK_SUCCESS)
    {
        throw std::runtime_error("failed to create graphics pipeline!");
    }


    m_App->NameObject(VK_OBJECT_TYPE_PIPELINE,
        (uint64_t)m_Pipeline, m_Name.c_str());

    vkDestroyShaderModule(m_App->GetLogicalDevice(),
        fragShaderModule, nullptr);
    vkDestroyShaderModule(m_App->GetLogicalDevice(),
        vertShaderModule, nullptr);
}

void PipelineGraphicsBoundary::createPipeline()
{
        ConfigObj* cfg = m_App->m_CFG;
        // Viewport State
	    //
	  

        m_Viewport.x = 0.0f;
        m_Viewport.y = 0.0f;
        m_Viewport.width = 500.0f;
        m_Viewport.height = 500.0f;
        m_Viewport.minDepth = 0.0f;
        m_Viewport.maxDepth = 1.0f;
#if 0
	    m_Viewport.x = 0.0f;
	    m_Viewport.y = 0.0f;
	    m_Viewport.width = static_cast<float>(m_SCO->GetSwapWidth());
	    m_Viewport.height = static_cast<float>(m_SCO->GetSwapHeight());
        m_Viewport.minDepth = static_cast<float>(m_SCO->GetSizzorMin());
        m_Viewport.maxDepth = static_cast<float>(m_SCO->GetSizzorMax());
#endif
	  
	    m_Scissor.offset = {0, 0};
	    m_Scissor.extent =  m_SCO->GetSwapExtent();

       
        m_ViewportState.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        m_ViewportState.pNext = nullptr;
        m_ViewportState.viewportCount = 1;
        m_ViewportState.pViewports = &m_Viewport;
        m_ViewportState.scissorCount = 1;
        m_ViewportState.pScissors = &m_Scissor;

	
        
        m_Rasterizer.sType 					= VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        m_Rasterizer.depthClampEnable 		= VK_FALSE;
        m_Rasterizer.rasterizerDiscardEnable 	= VK_FALSE;
        m_Rasterizer.polygonMode 				= VK_POLYGON_MODE_FILL;
        m_Rasterizer.lineWidth 				= 1.0f;
        m_Rasterizer.cullMode 				= VK_CULL_MODE_BACK_BIT;
        m_Rasterizer.frontFace 				= VK_FRONT_FACE_COUNTER_CLOCKWISE;
        m_Rasterizer.depthBiasEnable 			= VK_FALSE;
        m_Rasterizer.depthBiasConstantFactor  = 0.0f;
        m_Rasterizer.depthBiasClamp           = 0.0f;
        m_Rasterizer.depthBiasSlopeFactor     = 0.0f;
        

        
        m_Multisampling.sType 				= VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        m_Multisampling.sampleShadingEnable 	= VK_FALSE;
        m_Multisampling.rasterizationSamples 	= VK_SAMPLE_COUNT_1_BIT;

	
        
        m_ColorBlendAttachment.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
        m_ColorBlendAttachment.blendEnable 	= VK_TRUE;
        //m_ColorBlendAttachment.blendEnable 	= VK_FALSE;
		m_ColorBlendAttachment.colorBlendOp = VK_BLEND_OP_ADD;
		m_ColorBlendAttachment.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_COLOR;
		m_ColorBlendAttachment.dstColorBlendFactor = VK_BLEND_FACTOR_SRC_COLOR;
		m_ColorBlendAttachment.alphaBlendOp = VK_BLEND_OP_ADD;
		m_ColorBlendAttachment.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
		m_ColorBlendAttachment.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE;

        
        m_ColorBlending.sType 			= VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        m_ColorBlending.logicOpEnable 	= VK_FALSE;
        //colorBlending.logicOp 			= VK_LOGIC_OP_COPY;
        m_ColorBlending.attachmentCount 	= 1;
        m_ColorBlending.pAttachments 		= &m_ColorBlendAttachment;
        m_ColorBlending.blendConstants[0] = 0.0f;
        m_ColorBlending.blendConstants[1] = 0.0f;
        m_ColorBlending.blendConstants[2] = 0.0f;
        m_ColorBlending.blendConstants[3] = 0.0f;


        
        m_DepthStencil.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
        m_DepthStencil.depthTestEnable = VK_TRUE;
        m_DepthStencil.depthWriteEnable = VK_TRUE;
        m_DepthStencil.depthCompareOp = VK_COMPARE_OP_LESS;
        m_DepthStencil.depthBoundsTestEnable = VK_FALSE;
        m_DepthStencil.minDepthBounds = 0.0f; // Optional
        m_DepthStencil.maxDepthBounds = 1.0f; // Optional
        m_DepthStencil.stencilTestEnable = VK_FALSE;
        m_DepthStencil.front = {}; // Optional
        m_DepthStencil.back = {}; // Optional
	
     
	
        m_DynamicStates = {
            VK_DYNAMIC_STATE_VIEWPORT,
            VK_DYNAMIC_STATE_SCISSOR
        };
		
	
       
        m_DynamicState.sType 				= VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
        m_DynamicState.dynamicStateCount 	= static_cast<uint32_t>(m_DynamicStates.size());
        m_DynamicState.pDynamicStates 	= m_DynamicStates.data();
		
		
		
		
    }
