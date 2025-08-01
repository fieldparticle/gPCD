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


void PipelineGraphicsParticleOnly::CreatePipeline()
{
    std::string testtype = CfgApp->GetString("application.testtype", true);
    std::string t_fshader_spv   = "application." + testtype +".frag_kernParticlespv";
    std::string t_fshader_glsl  = "application." + testtype +".frag_kernParticle";
    std::string t_vshader_spv     = "application." + testtype +".vert_kernParticlespv";
    std::string t_vshader_glsl    = "application." + testtype +".vert_kernParticle";

    m_RenderPassName = "SubpassParticle";
    std::string fshader_spv = CfgApp->GetString(t_fshader_spv, true);
    std::string fshader_glsl = CfgApp->GetString(t_fshader_glsl, true);

    std::string vshader_spv = CfgApp->GetString(t_vshader_spv, true);
    std::string vshader_glsl = CfgApp->GetString(t_vshader_glsl, true);

    std::vector<char>  fragShaderCode;
    m_SHO->CompileShader(fshader_glsl, fshader_spv, fragShaderCode, m_SHO->SH_FRAG);
    VkShaderModule fragShaderModule = createShaderModule(fragShaderCode,
        fshader_glsl);
   
    
    std::vector<char>  vertShaderCode;
    m_SHO->CompileShader(vshader_glsl, vshader_spv, vertShaderCode, m_SHO->SH_VERT);
    VkShaderModule vertShaderModule = createShaderModule(vertShaderCode,
        vshader_glsl);
   

    VkPipelineShaderStageCreateInfo vertShaderStageInfo{};
    vertShaderStageInfo.sType 	= VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    vertShaderStageInfo.stage 	= VK_SHADER_STAGE_VERTEX_BIT;
    vertShaderStageInfo.module	= vertShaderModule;
    vertShaderStageInfo.pName 	= "main";

    VkPipelineShaderStageCreateInfo fragShaderStageInfo{};
    fragShaderStageInfo.sType 	= VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    fragShaderStageInfo.stage 	= VK_SHADER_STAGE_FRAGMENT_BIT;
    fragShaderStageInfo.module 	= fragShaderModule;
    fragShaderStageInfo.pName 	= "main";

#ifdef GEOSHAD

    VkPipelineShaderStageCreateInfo shaderStages[] = {vertShaderStageInfo, fragShaderStageInfo,geomShaderStageInfo };
#else
    VkPipelineShaderStageCreateInfo shaderStages[] = { vertShaderStageInfo, fragShaderStageInfo };
#endif
	// Get binding and attribute descriptions for vertices. 
    Resource* dvo = (m_RCO->GetResourceName("VertexParticle"));
    VkVertexInputBindingDescription* bindingDescription = dvo->GetBindingDescription();
    std::vector<VkVertexInputAttributeDescription>* attributeDescriptions 	= dvo->GetAttributeDescriptions();
		
        
		
	// Tell the pipline the binding points for verticies and attributes. 
#if 1
    VkPipelineVertexInputStateCreateInfo vertexInputInfo{};
	vertexInputInfo.sType 							= VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertexInputInfo.vertexBindingDescriptionCount 	= 1;
    vertexInputInfo.vertexAttributeDescriptionCount = static_cast<uint32_t>(attributeDescriptions->size());
    vertexInputInfo.pVertexBindingDescriptions 		= bindingDescription;
    vertexInputInfo.pVertexAttributeDescriptions    = attributeDescriptions->data();
#else
    VkPipelineVertexInputStateCreateInfo vertexInputInfo{};
    vertexInputInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertexInputInfo.vertexBindingDescriptionCount = 0;
    vertexInputInfo.vertexAttributeDescriptionCount = 0;
    vertexInputInfo.pVertexBindingDescriptions = nullptr;
    vertexInputInfo.pVertexAttributeDescriptions = nullptr;

#endif

   
    VkPipelineInputAssemblyStateCreateInfo inputAssembly{};
   
    inputAssembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST;
    inputAssembly.primitiveRestartEnable = VK_FALSE;
   
	// Viewport State
	//
	VkViewport viewport = {};
	viewport.x = static_cast<float>(m_SCO->GetSwapX());
	viewport.y = static_cast<float>(m_SCO->GetSwapY());
	viewport.width = static_cast<float>(m_SCO->GetSwapWidth());
	viewport.height = static_cast<float>(m_SCO->GetSwapHeight());
    viewport.minDepth = static_cast<float>(m_SCO->GetSizzorMin());
    viewport.maxDepth = static_cast<float>(m_SCO->GetSizzorMax());
	VkRect2D scissor = {};
	scissor.offset = {0, 0};
	scissor.extent =  m_SCO->GetSwapExtent();

    VkPipelineViewportStateCreateInfo viewportState = {};
	viewportState.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
	viewportState.pNext = nullptr;
	viewportState.viewportCount = 1;
	viewportState.pViewports = &viewport;
	viewportState.scissorCount = 1;
	viewportState.pScissors = &scissor;

	//does not work
    //VkPipelineRasterizationStateRasterizationOrderAMD rasterOrder{};
    
    

    

    VkPipelineRasterizationStateCreateInfo rasterizer{};
    rasterizer.pNext                    = nullptr;
    rasterizer.sType 					= VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rasterizer.depthClampEnable 		= VK_FALSE;
    rasterizer.rasterizerDiscardEnable 	= VK_FALSE;
    // No chnage from VK_POLYGON_MODE_POINT
    //rasterizer.polygonMode 				= VK_POLYGON_MODE_FILL_RECTANGLE_NV;
   // rasterizer.polygonMode 				= VK_POLYGON_MODE_FILL;
    rasterizer.polygonMode = VK_POLYGON_MODE_POINT;
    rasterizer.lineWidth 				= 1.0f;
    //rasterizer.cullMode 				= VK_CULL_MODE_BACK_BIT;
    rasterizer.cullMode = VK_CULL_MODE_NONE;
    //rasterizer.frontFace 				= VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rasterizer.frontFace = VK_FRONT_FACE_CLOCKWISE;
    //rasterizer.depthBiasEnable 			= VK_FALSE;
    rasterizer.depthBiasEnable = VK_FALSE;

#if 0
        //VkSampleLocationEXT
    VkSampleLocationEXT sampleLocation[8];
    sampleLocation[0].x = 0.1f;
    sampleLocation[0].y = 0.1f;
    
    sampleLocation[0].x = 0.2f;
    sampleLocation[0].y = 0.2f;
    
    sampleLocation[0].x = 0.3f;
    sampleLocation[0].y = 0.3f;
    
    sampleLocation[0].x = 0.4f;
    sampleLocation[0].y = 0.4f;
    
    sampleLocation[0].x = 0.5f;
    sampleLocation[0].y = 0.5f;
    
    sampleLocation[0].x = 0.6f;
    sampleLocation[0].y = 0.6f;
    
    sampleLocation[0].x = 0.7f;
    sampleLocation[0].y = 0.7f;
    
    sampleLocation[0].x = 0.8f;
    sampleLocation[0].y = 0.8f;
    
    
    
    VkExtent2D gridext{};
    gridext.height = 1;
    gridext.width = 1;
    VkSampleLocationsInfoEXT sampleLocationsInfo{};
    sampleLocationsInfo.sType = VK_STRUCTURE_TYPE_SAMPLE_LOCATIONS_INFO_EXT;
    sampleLocationsInfo.sampleLocationsPerPixel = VK_SAMPLE_COUNT_1_BIT;
    sampleLocationsInfo.sampleLocationGridSize = gridext;
    sampleLocationsInfo.sampleLocationsCount = 1;
    sampleLocationsInfo.pSampleLocations = sampleLocation;
    
    VkPipelineSampleLocationsStateCreateInfoEXT shadrate{};
    shadrate.sType = VK_STRUCTURE_TYPE_PIPELINE_SAMPLE_LOCATIONS_STATE_CREATE_INFO_EXT;
    shadrate.sampleLocationsEnable = VK_TRUE ;
    shadrate.sampleLocationsInfo = sampleLocationsInfo;
#endif
    VkPipelineMultisampleStateCreateInfo multisampling{};
    multisampling.pNext = nullptr;
    multisampling.sType 				= VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    multisampling.sampleShadingEnable 	= VK_FALSE;
    //multisampling.sampleShadingEnable 	= VK_FALSE;
    multisampling.rasterizationSamples 	= VK_SAMPLE_COUNT_1_BIT;
    multisampling.minSampleShading      = 0.5;
       //multisampling.pSampleMask
    //multisampling.alphaToCoverageEnable
    //multisampling.
	
    VkPipelineColorBlendAttachmentState colorBlendAttachment{};
    colorBlendAttachment.colorWriteMask = VK_COLOR_COMPONENT_R_BIT |
        VK_COLOR_COMPONENT_G_BIT | 
        VK_COLOR_COMPONENT_B_BIT | 
        VK_COLOR_COMPONENT_A_BIT;
    colorBlendAttachment.blendEnable 	= VK_TRUE;
    //colorBlendAttachment.blendEnable 	= VK_FALSE;
	colorBlendAttachment.colorBlendOp = VK_BLEND_OP_ADD;
    colorBlendAttachment.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
	colorBlendAttachment.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
	colorBlendAttachment.alphaBlendOp = VK_BLEND_OP_ADD;
	colorBlendAttachment.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
	colorBlendAttachment.dstAlphaBlendFactor = VK_BLEND_FACTOR_ZERO;

    VkPipelineColorBlendStateCreateInfo colorBlending{};
    colorBlending.sType 			= VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    colorBlending.logicOpEnable 	= VK_FALSE;
    colorBlending.logicOp 			= VK_LOGIC_OP_COPY;
    colorBlending.attachmentCount 	= 1;
    colorBlending.pAttachments 		= &colorBlendAttachment;
    colorBlending.blendConstants[0] = 0.0f;
    colorBlending.blendConstants[1] = 0.0f;
    colorBlending.blendConstants[2] = 0.0f;
    colorBlending.blendConstants[3] = 0.0f;

#if 1
    VkPipelineDepthStencilStateCreateInfo depthStencil{};
    depthStencil.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    //depthStencil.depthTestEnable = VK_TRUE;
    depthStencil.depthTestEnable = VK_FALSE;

    //depthStencil.depthWriteEnable = VK_TRUE;
    depthStencil.depthTestEnable = VK_FALSE;
    //depthStencil.depthCompareOp = VK_COMPARE_OP_LESS;
    depthStencil.depthCompareOp = VK_COMPARE_OP_NEVER;
    depthStencil.depthBoundsTestEnable = VK_FALSE;
    depthStencil.minDepthBounds = 0.0f; // Optional
    depthStencil.maxDepthBounds = 1.0f; // Optional
    depthStencil.stencilTestEnable = VK_FALSE;
    depthStencil.front = {}; // Optional
    depthStencil.back = {}; // Optional
	
#endif    
	
    std::vector<VkDynamicState> dynamicStates = {
        VK_DYNAMIC_STATE_VIEWPORT,
        VK_DYNAMIC_STATE_SCISSOR
    };
		
	
    VkPipelineDynamicStateCreateInfo dynamicState{};
    dynamicState.sType 				= VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dynamicState.dynamicStateCount 	= static_cast<uint32_t>(dynamicStates.size());
    dynamicState.pDynamicStates 	= dynamicStates.data();
		
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
        throw std::runtime_error("PipelineGraphicsParticleOnly::CreatePipeline failed at vkCreatePipelineLayout");
    }

    m_wkstr = m_Name + " Layout";
    m_App->NameObject(VK_OBJECT_TYPE_PIPELINE_LAYOUT,
        (uint64_t)m_PipelineLayout, m_wkstr.c_str());
    VkPipelineRepresentativeFragmentTestStateCreateInfoNV  prftc{};
    prftc.sType = VK_STRUCTURE_TYPE_PIPELINE_REPRESENTATIVE_FRAGMENT_TEST_STATE_CREATE_INFO_NV;
    prftc.representativeFragmentTestEnable = VK_TRUE;

	//https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VkGraphicsPipelineCreateInfo.html
    VkGraphicsPipelineCreateInfo pipelineInfo{};
    pipelineInfo.sType 					= VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    pipelineInfo.pNext                  = nullptr;
    pipelineInfo.stageCount 			= 2;
    pipelineInfo.pStages 				= shaderStages;
    pipelineInfo.pVertexInputState 		= &vertexInputInfo;
    pipelineInfo.pInputAssemblyState 	= &inputAssembly;
    pipelineInfo.pViewportState 		= &viewportState;
    pipelineInfo.pRasterizationState 	= &rasterizer;
    pipelineInfo.pMultisampleState 		= &multisampling;
    pipelineInfo.pColorBlendState 		= &colorBlending;
    pipelineInfo.pDepthStencilState = &depthStencil;
    pipelineInfo.pDynamicState 			= &dynamicState;        
    pipelineInfo.layout 				= m_PipelineLayout;
    pipelineInfo.renderPass 			= m_RPO->GetRenderPass();
    pipelineInfo.subpass = 0;// 1;
    pipelineInfo.basePipelineHandle 	= VK_NULL_HANDLE;
		
    if (vkCreateGraphicsPipelines(m_App->GetLogicalDevice(), 
									VK_NULL_HANDLE, 
									1, 
									&pipelineInfo, 
									nullptr, 
									&m_Pipeline) != VK_SUCCESS) 
	{
        throw std::runtime_error("PipelineGraphicsParticleOnly::CreatePipeline failed at vkCreateGraphicsPipelines");
    }


	m_App->NameObject(VK_OBJECT_TYPE_PIPELINE, 
        (uint64_t)m_Pipeline, m_Name.c_str());

#if 1
    vkDestroyShaderModule(m_App->GetLogicalDevice(), 
        fragShaderModule, nullptr);
    vkDestroyShaderModule(m_App->GetLogicalDevice(), 
        vertShaderModule, nullptr);
#endif
    }
