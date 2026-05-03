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


#include "VulkanApp.hpp"

void ResourceIndex::Create()
{
		m_NumElements =  (uint32_t)indices.size();
		m_BufSize = sizeof(indices[0]) * indices.size();
		m_Buffers.resize(1);
		m_BuffersMemory.resize(1); 
		m_StagingBuffer;
		m_StagingBufferMemory; 

        m_App->CreateBuffer(m_BufSize, 
			VK_BUFFER_USAGE_TRANSFER_SRC_BIT, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, 
			m_StagingBuffer, m_StagingBufferMemory,"Index Staging");

        void* data;
        vkMapMemory(m_App->GetLogicalDevice(), m_StagingBufferMemory, 0, m_BufSize, 0, &data);
        memcpy(data, indices.data(), (size_t) m_BufSize);
        vkUnmapMemory(m_App->GetLogicalDevice(), m_StagingBufferMemory);

        m_App->CreateBuffer(m_BufSize, 
			VK_BUFFER_USAGE_TRANSFER_DST_BIT |
			VK_BUFFER_USAGE_INDEX_BUFFER_BIT, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 
			m_Buffers[0], m_BuffersMemory[0], "IndexBuffer");

       
}
void ResourceIndex::Create(std::vector<glm::vec3>* indices)
{
	m_NumElements = (uint32_t)indices->size();
	m_BufSize = sizeof(indices[0]) * indices->size();
	m_Buffers.resize(1);
	m_BuffersMemory.resize(1);
	m_StagingBuffer;
	m_StagingBufferMemory;

	m_App->CreateBuffer(m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_SRC_BIT, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
		m_StagingBuffer, m_StagingBufferMemory, "Index Staging");

	void* data;
	vkMapMemory(m_App->GetLogicalDevice(), m_StagingBufferMemory, 0, m_BufSize, 0, &data);
	memcpy(data, indices->data(), (size_t)m_BufSize);
	vkUnmapMemory(m_App->GetLogicalDevice(), m_StagingBufferMemory);

	m_App->CreateBuffer(m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_INDEX_BUFFER_BIT, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0], m_BuffersMemory[0], "IndexBuffer");


}
void ResourceIndex::CopyMem()
{
	if (m_StagingBuffer == nullptr)
	{	std::string msg = "Copy Mem in :" + m_Name + " has not been created.";
		throw std::runtime_error(msg.c_str());
	}
	m_CPL->CopyBuffer(m_StagingBuffer, m_Buffers[0], m_BufSize);

    vkDestroyBuffer(m_App->GetLogicalDevice(), m_StagingBuffer, nullptr);
    vkFreeMemory(m_App->GetLogicalDevice(), m_StagingBufferMemory, nullptr);
}

void* ResourceIndex::GetBuffer(uint32_t bufNum, uint32_t ImageIndex, unsigned long& size)
{
	size = static_cast<unsigned long>(m_BufSize);
	return &m_Buffers[ImageIndex];

}