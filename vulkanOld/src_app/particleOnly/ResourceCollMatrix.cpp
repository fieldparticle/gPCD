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
// Create the layouts for the decriptors which are esentially descriptor definitions.
// Shader Uniform struct->binding point->UniformBuffersMemory
void ResourceCollMatrix::Create(uint32_t BindPoint, ResourceVertexParticle* particle)
{

    m_thisFramesBuffered = 1;
    m_particle           = particle;
    
    m_MaxCollArray = CfgTst->GetInt("cell_occupancy_list_size", true);

    uint32_t Size = static_cast<uint32_t>(m_particle->m_SideLength);
    m_BindPoint = BindPoint;
    // Sizes are in bytes
    m_MaxLoc = static_cast<uint32_t>((CfgTst->GetUInt("CellAryW", true)) 
                                        * (CfgTst->GetUInt("CellAryH", true)) 
                                        * (CfgTst->GetUInt("CellAryL", true)));


    m_BufSize = (m_MaxLoc*sizeof(uint32_t))*(CfgTst->GetInt("cell_occupancy_list_size", true));
    mout << "MEMALLOC:ResourceCollMatrix V2:" << m_BufSize << ende;    
    
    uint32_t elements = m_BufSize / sizeof(uint32_t);
    uint32_t locations = elements / CfgTst->GetInt("cell_occupancy_list_size", true);
    createLayout();
    createBuffers();
}
void ResourceCollMatrix::createLayout() 
{  
   
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding              = m_BindPoint;
    m_LayoutBinding[0].descriptorCount      = 1;
    m_LayoutBinding[0].descriptorType       = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    m_LayoutBinding[0].pImmutableSamplers   = nullptr;
    m_LayoutBinding[0].stageFlags           = VK_SHADER_STAGE_COMPUTE_BIT| VK_SHADER_STAGE_FRAGMENT_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_GEOMETRY_BIT;
}



void ResourceCollMatrix::createBuffers() 
{
	
    VkDeviceSize bufferSize = m_BufSize;
    m_Buffers.resize(m_thisFramesBuffered);
    m_BuffersMemory.resize(m_thisFramesBuffered);
    m_BuffersMapped.resize(m_thisFramesBuffered);
    m_BufferInfo.resize(m_thisFramesBuffered);
    m_DescriptorWrite.resize(m_thisFramesBuffered);
    m_Allocation.resize(m_thisFramesBuffered);
    std::ostringstream  objtxt;
    for (size_t i = 0; i < m_thisFramesBuffered; i++)
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
        m_DescriptorWrite[i].dstBinding = m_BindPoint;
        m_DescriptorWrite[i].dstArrayElement = 0;
        m_DescriptorWrite[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        m_DescriptorWrite[i].descriptorCount = 1;
        m_DescriptorWrite[i].pBufferInfo = &m_BufferInfo[i];
        objtxt.clear();
    }
}

void ResourceCollMatrix::PushMem(uint32_t currentBuffer)
{
        // Just createing the buffer on the device
}