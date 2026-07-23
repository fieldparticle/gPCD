/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.cpp $
% $Id: ResourceVertex.cpp 28 2023-05-03 19:30:42Z jb $
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
#include "ParticleLighting/LightingStructs.hpp"


void ResourceLighting::Create(uint32_t BindPoint, ResourceVertexParticle* particle)
{
	
	std::ostringstream  objtxt;
	
	m_BindPoint = BindPoint;
	if (particle->m_NumBoundaryParticles == 0)
	{
		std::ostringstream  errtxt;
		errtxt << m_Name << " ResourceLighting::Create no boundary light records." << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}
	std::vector<BoundaryLightRecord> lightRecords(particle->m_NumBoundaryParticles);
	m_BufSize = static_cast<uint64_t>(sizeof(BoundaryLightRecord))*lightRecords.size();
	m_Buffers.resize(1);
	m_BuffersMemory.resize(1);
	m_BuffersMapped.resize(1);
	m_BufferInfo.resize(1);
	m_DescriptorWrite.resize(1);
	m_Allocation.resize(1);
	VkBuffer buf = {};

	objtxt << m_Name << " Number:" << 0 << std::ends;
	VkBufferUsageFlags usage =
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;


	m_App->VMACreateDeviceBuffer(
		m_BufSize,
		usage,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0],
		m_Allocation[0],
		objtxt.str());
	
	m_BufferInfo[0].buffer = m_Buffers[0];
	m_BufferInfo[0].offset = 0;
	m_BufferInfo[0].range = m_BufSize;

	m_DescriptorWrite[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[0].dstBinding = m_BindPoint;
	m_DescriptorWrite[0].dstArrayElement = 0;
	m_DescriptorWrite[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_DescriptorWrite[0].descriptorCount = 1;
	m_DescriptorWrite[0].pBufferInfo = &m_BufferInfo[0];
	objtxt.clear();

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, lightRecords.data(), m_Allocation[0],
		0, m_BufSize);
}


void ResourceLighting::CreateLayout()
{

	// Step 1: Add layout biding definition.
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;
}
VkVertexInputBindingDescription* 
ResourceLighting::GetBindingDescription()
{
	
	m_BindingDescription.binding = m_BindPoint;
	m_BindingDescription.stride = sizeof(BoundaryLightRecord);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	

	return &m_BindingDescription;
}
