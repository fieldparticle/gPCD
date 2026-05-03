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
void ResourceLockMatrix::Create(uint32_t BindPoint, ResourceVertexParticle* particle)
{

    
    m_particle = particle;
    m_particle->m_SideLength;
    
    m_thisFramesBuffered = 1;
    uint32_t Size = static_cast<uint32_t>(m_particle->m_SideLength);
    m_BindPoint = BindPoint;
 
    // Remember the size is goes from 0 to length thats why the +1
    m_MaxLoc = static_cast<uint32_t>((CfgTst->GetUInt("CellAryW", true)) 
                                    * (CfgTst->GetUInt("CellAryH", true)) 
                                    * (CfgTst->GetUInt("CellAryL", true)));
    m_BufSize = m_MaxLoc*sizeof(uint32_t);
    mout << "MEMALLOC:ResourceLockMatrix V2:" << m_BufSize << ende;    
    createLayout();
    std::vector<uint32_t> idxloc;
   
#if 0
    for (size_t ii = 0; ii < m_RptVec.size(); ii++)
    {
        if (m_RptVec[ii].LocationArry.x == 0 || m_RptVec[ii].LocationArry.y == 0 || m_RptVec[ii].LocationArry.z == 0)
        {
            idxloc.push_back(npos);
        }
        if (m_RptVec[ii].LocationArry.x >= Size || m_RptVec[ii].LocationArry.y == Size || m_RptVec[ii].LocationArry.z == Size)
        {
            idxloc.push_back(npos);
        }

    }
#endif
    
    CreateBuffers();
}
void ResourceLockMatrix::createLayout() 
{  
    m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding              = m_BindPoint;
    m_LayoutBinding[0].descriptorCount      = 1;
    m_LayoutBinding[0].descriptorType       = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    m_LayoutBinding[0].pImmutableSamplers   = nullptr;
    m_LayoutBinding[0].stageFlags           = VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_FRAGMENT_BIT |  VK_SHADER_STAGE_VERTEX_BIT;
}


void  ResourceLockMatrix::WriteShaderHeader()
{

   
}

void ResourceLockMatrix::CreateBuffers()
{
#if 0
    VkDeviceSize bufferSize = m_BufSize;
    size_t csize = m_RptVec.size() * sizeof(uint32_t);
    if (m_BufSize != m_RptVec.size() * sizeof(uint32_t))
    {
        std::ostringstream  objtxt = {};
        objtxt << m_Name << "Lock Array size mismatch: Calculated:"
            << m_BufSize << " Loaded:" << m_RptVec.size() * sizeof(uint32_t) << std::ends;
        throw std::runtime_error(objtxt.str().c_str());
    }
#endif
    m_Buffers.resize(m_thisFramesBuffered);
    m_BuffersMemory.resize(m_thisFramesBuffered);
    m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
    m_Allocation.resize(m_thisFramesBuffered);
    

    for (size_t i = 0; i < m_thisFramesBuffered; i++)
    {
        std::ostringstream  objtxt = {};
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
   // vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_RptVec.data(), m_Allocation[0],
    //    0, m_BufSize);
    m_RptVec.clear();
}



void ResourceLockMatrix::PushMem(uint32_t currentBuffer)
{
 // Just creating memeory on the device
}