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

const float PI = (float)3.14159265359;

void ResourceUBOSphere::Create(uint32_t BindPoint, SwapChainObj* SCO, ResourceVertexParticle* particle)
{
	m_Particle = particle;
	Create(BindPoint, SCO);
}
void ResourceUBOSphere::createLayout()
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
void ResourceUBOSphere::Create(uint32_t BindPoint, SwapChainObj* SCO)
{
	m_thisFramesBuffered = m_App->m_FramesBuffered;
	m_SCO = SCO;
	m_BindPoint = BindPoint;
	createLayout();
	createBuffers();
}
void ResourceUBOSphere::createBuffers()
{
	m_BufSize = sizeof(UniformBufferObject);

	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);
	std::string bname = m_Name;


	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		

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


void ResourceUBOSphere::PushMem(uint32_t currentBuffer)
{

	
	float s = m_Particle->m_SideLength;
	GeneralViewing(m_Particle->m_SideLength, currentBuffer);
}