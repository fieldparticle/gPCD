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


using namespace std;
// Create the layouts for the decriptors which are esentially descriptor definitions.
// Shader Uniform struct->binding point->UniformBuffersMemory
void ResourceAtomicGraphics::Create(uint32_t BindPoint,PerfObj*	perfObj)
{
	m_PerfObj = perfObj;
	m_ReportGraphFramesLessThan = CfgApp->GetInt("application.reportGraphFramesLessThan", true);
	Resource::CheckBindPoint(BindPoint);
	m_thisFramesBuffered = m_App->m_FramesBuffered;
	createLayout();
	createBuffers();
}
void ResourceAtomicGraphics::createLayout() 
{  
	
    // Step 1: Add layout biding definition.
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding              = m_BindPoint;
    m_LayoutBinding[0].descriptorCount      = 1;
    m_LayoutBinding[0].descriptorType       = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    m_LayoutBinding[0].pImmutableSamplers   = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_FRAGMENT_BIT | VK_SHADER_STAGE_VERTEX_BIT;
}

void ResourceAtomicGraphics::createBuffers()
{
	
	m_BufSize = sizeof(GCollision);
	std::ostringstream  objtxt;
	
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);
	for (size_t i = 0; i < m_thisFramesBuffered;i++)
	{
		
		objtxt << m_Name << " Number:" << i << std::ends;
		m_App->VMACreateDeviceBuffer(m_BufSize,
			VK_BUFFER_USAGE_TRANSFER_DST_BIT |
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
			VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			m_Buffers[i], m_Allocation[i], m_Name);
		m_BufferInfo[i].buffer = m_Buffers[i];
		m_BufferInfo[i].offset = 0;
		m_BufferInfo[i].range = m_BufSize;

		m_DescriptorWrite[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
		// m_descriptorWrite[i].dstSet; Written in ResourceSetObj.
		m_DescriptorWrite[i].dstBinding = m_BindPoint;
		m_DescriptorWrite[i].dstArrayElement = 0;
		m_DescriptorWrite[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
		m_DescriptorWrite[i].descriptorCount = 1;
		m_DescriptorWrite[i].pBufferInfo = &m_BufferInfo[i];
		objtxt.clear();
	}

}
void ResourceAtomicGraphics::PushMem(uint32_t currentBuffer)
{
	return;
	m_collisionStruct.ErrorReturn = 0;
	m_collisionStruct.numParticles = 0;
	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, &m_collisionStruct, m_Allocation[currentBuffer],
		0, sizeof(GCollision));
}

void ResourceAtomicGraphics::PullMem(uint32_t currentBuffer)
{
#ifndef NDEBUG
	if (CfgApp->GetBool("application.enableValidationLayers", true) == false)
		return;

	void* mappedData = {};
	vmaMapMemory(m_App->m_vmaAllocator, m_Allocation[currentBuffer], &mappedData);
	memcpy(&m_collisionStruct, mappedData, sizeof(GCollision));
	vmaUnmapMemory(m_App->m_vmaAllocator, m_Allocation[currentBuffer]);
	
	
		if (m_collisionStruct.ErrorReturn > 0)
		{
			
			std::ostringstream  objtxt;
			if (m_collisionStruct.ErrorReturn == 2)
			{
				m_App->m_quit_event = 2;
				objtxt << m_Name << " ResourceAtomicGraphics::Vertex Kernel Error Max Slots: "
					<< m_collisionStruct.ErrorReturn 
					<< " Failing Slot:"
					<< m_collisionStruct.ExcessSlots << std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			else
			if (m_collisionStruct.ErrorReturn == 3)
			{
				m_App->m_quit_event = 3;
				objtxt << m_Name << " ResourceAtomicGraphics::Vertex Kernel Error Max Location:"
					<< m_collisionStruct.ErrorReturn
					<< " Excess slots:" << m_collisionStruct.ExcessSlots << std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			if (m_collisionStruct.ErrorReturn == 4)
			{
				m_App->m_quit_event = 4;
				objtxt << 
					m_Name << " ResourceAtomicGraphics::Vertex Kernel Error Boundary Error: "
					<< m_collisionStruct.ErrorReturn 
					<<" P(" << m_collisionStruct.ExcessSlots << ")" << std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			if (m_collisionStruct.ErrorReturn == 5)
			{
				m_App->m_quit_event = 5;
				objtxt << m_Name << " ResourceAtomicGraphics::Boundary"
					<< m_collisionStruct.ErrorReturn 
					<< "(" << m_collisionStruct.ExcessSlots << ")" << std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			if (m_collisionStruct.ErrorReturn == 6)
			{
				m_App->m_quit_event = 5;
				objtxt << m_Name << " ResourceAtomicGraphics::Isnan at Frame:"
					<< m_collisionStruct.ErrorReturn 
					<< m_App->m_FrameNumber 
					<< "Particle:" 
					<< m_collisionStruct.particleNumber <<  std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			if (m_collisionStruct.ErrorReturn == 5)
			{
				m_App->m_quit_event = 8;
				objtxt << m_Name << " ResourceAtomicGraphics::Lost Index:"
					<< m_collisionStruct.ErrorReturn 
					<< m_App->m_FrameNumber 
					<< "Particle:" 
					<< m_collisionStruct.particleNumber <<  std::ends;
				mout << objtxt.str().c_str() << ende;
			}
			//throw std::runtime_error(objtxt.str().c_str());

		}

	if (m_App->m_FrameNumber < m_ReportGraphFramesLessThan )
	{
		
		mout << "Vertex F:" << m_App->m_FrameNumber
			<< " Deadlock:" << m_collisionStruct.ErrorReturn
			<< " R/W Conflicts:"	<< m_collisionStruct.ReadWriteConflict
			<< " Blocking:"			<< m_collisionStruct.ExcessSlots
			<< " Num Particles:"	<< m_collisionStruct.numParticles
			<< ende;
		
		
	}
#endif
}
void ResourceAtomicGraphics::AskObject(uint32_t AnyNumber)
{
	m_PerfObj->m_ReportBuffer[AnyNumber].NumParticlesGraphicsCount = m_collisionStruct.numParticles;
}


VkVertexInputBindingDescription* ResourceAtomicGraphics::GetBindingDescription()
{

	m_BindingDescription.binding = 0;
	m_BindingDescription.stride = sizeof(m_BufSize);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;


	return &m_BindingDescription;
}



std::vector<VkVertexInputAttributeDescription>* ResourceAtomicGraphics::GetAttributeDescriptions()
{
#if 0

	VkVertexInputAttributeDescription ad{};
	ad.binding = 0;
	ad.location = 0;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT; // Needs to match attribute length https://vulkan-tutorial.com/Vertex_buffers/Vertex_input_description
	ad.offset = offsetof(PVertex, PosLoc);
	m_AttributeDescriptions.push_back(ad);

	ad.binding = 0;
	ad.location = 1;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(PVertex, RadVel);
	m_AttributeDescriptions.push_back(ad);

	ad.binding = 0;
	ad.location = 2;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(PVertex, FrcAng);
	m_AttributeDescriptions.push_back(ad);
#endif
	return &m_AttributeDescriptions;
}
