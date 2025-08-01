/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
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
#include "ParticleStruct.hpp"
const float PI = (float)3.14159265359;

// getname is called in PipelineGraphics::createPipeline()
// ResourceSetObj::createPool() gets layout bindings
// Below in PipelineGraphics::createPipeline()
// 		auto bindingDescription 	= dvo->getBindingDescription();
//		auto attributeDescriptions 	= dvo->getAttributeDescriptions();

void ResourceParticleUBO::Create(uint32_t BindPoint, SwapChainObj* SCO, ResourceVertexParticle* particle)
{
	m_Particle = particle;
	m_NumElements = 0;// m_Particle->m_NumParticles;

	Create(BindPoint, SCO);
}
void ResourceParticleUBO::createLayout()
{
	// Create the layouts for the decriptors which are 
	// esentially descriptor definitions.	
	// This block is called in ResourceSetObj::createPool()
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	// If this memory is an array this is the number of elements.
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT;


}
void ResourceParticleUBO::Create(uint32_t BindPoint, SwapChainObj* SCO)
{
	m_thisFramesBuffered = m_App->m_FramesBuffered;
	m_SCO = SCO;
	m_BindPoint = BindPoint;
	createLayout();
	createBuffers();
}
void ResourceParticleUBO::createBuffers()
{
	m_BufSize = sizeof(UniformBufferObject);

	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		m_BufferInfo.resize(m_thisFramesBuffered);
		m_DescriptorWrite.resize(m_thisFramesBuffered);
		m_Buffers.resize(m_thisFramesBuffered);
		m_BuffersMemory.resize(m_thisFramesBuffered);
		m_BuffersMapped.resize(m_thisFramesBuffered);
		m_Allocation.resize(m_thisFramesBuffered);
		std::string bname = m_Name;


		m_App->VMACreateDeviceBuffer(m_BufSize,
			VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
			VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
			m_Buffers[i], m_Allocation[i], m_Name);


		//=================================================================================
		// This is added to the resource contaier and called ResourceSetObj::createSets()
		m_BufferInfo[i].buffer = m_Buffers[i];
		m_BufferInfo[i].offset = 0;
		m_BufferInfo[i].range = sizeof(UniformBufferObject);

		m_DescriptorWrite[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
		// m_descriptorWrite[i].dstSet; Written in ResourceSetObj.
		m_DescriptorWrite[i].dstBinding = m_BindPoint;
		m_DescriptorWrite[i].dstArrayElement = 0;
		m_DescriptorWrite[i].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
		m_DescriptorWrite[i].descriptorCount = 1;
		m_DescriptorWrite[i].pBufferInfo = &m_BufferInfo[0];
	}
}


void ResourceParticleUBO::PushMem(uint32_t currentBuffer)
{
	
	//if(m_done == true)
	//return;
	float sidelength = m_Particle->m_SideLength;
	m_UBO = {};
	///================================ Subpass 1
	m_UBO.model = glm::rotate(glm::mat4(1.0f), glm::radians(rRotZ), glm::vec3(0.0f, 0.0f, 1.0f));
	m_UBO.model = glm::rotate(m_UBO.model, glm::radians(rRotY), glm::vec3(0.0f, 1.0f, 0.0f));
	m_UBO.model = glm::rotate(m_UBO.model, glm::radians(rRotX), glm::vec3(1.0f, 0.0f, 0.0f));
	m_UBO.model = glm::translate(m_UBO.model,
		glm::vec3(-sidelength / 2.0f, -sidelength / 2.0f, -sidelength / 2.0f));

	m_UBO.model = glm::scale(m_UBO.model,
		glm::vec3(ZoomX, ZoomX, ZoomX));
	
	m_UBO.view = glm::lookAt(glm::vec3(0.0, 0.0f, sidelength * 4.0f),
		glm::vec3(0.0, 0.0, 0.0),
		glm::vec3(0.0f, 1.0f, 0.0f));
	
	m_UBO.proj = glm::ortho(-static_cast<float>(sidelength) /1.5f,
							static_cast<float>(sidelength) / 1.5f,
							-static_cast<float>(sidelength) /1.5f,
							static_cast<float>(sidelength) / 1.5f,G_OrthoMin,G_OrthoMax);
	
	m_UBO.proj[1][1] *= -1.0f;
	void* data = nullptr;
	uint32_t bufsize = sizeof(m_UBO) + m_NumElements * sizeof(uint32_t);

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, &m_UBO, m_Allocation[currentBuffer],
		0, sizeof(m_UBO));
	m_done = true;
}
