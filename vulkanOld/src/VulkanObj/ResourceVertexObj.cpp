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

#include <iostream>


void ResourceVertexObj::Create(uint32_t BindPoint, ResourceVertexParticle* PartVert)
{
	
	m_ParticleVert = PartVert;
	bool res = loadOBJ(m_FileName.c_str(), m_vtemp, m_UVS, m_Normals);
	if (!res)
	{
		std::ostringstream  objtxt;
		objtxt << "ResourceVertexObj::Create Failed File:" << m_FileName << ende;
		
		throw std::runtime_error(objtxt.str());
	}

}
void ResourceVertexObj::Create(uint32_t BindPoint)
{
	
	
	Resource::CheckBindPoint(BindPoint);

	/*for (int ii = 0; ii < m_Model.Data.size() / 3;)
	{
		Vertex ad;
		ad.position.x = m_Model.Data[ii];
		ad.position.y = m_Model.Data[++ii];
		ad.position.z = m_Model.Data[++ii];
		ii++;
		m_Verts.push_back(ad);
	}*/
	m_thisFramesBuffered = 1;
	std::ostringstream  objtxt;
	m_BufSize = sizeof(CartVert) * (uint32_t)m_Verts.size();
	mout << "MEMALLOC:ResourceVertexObj:" << m_BufSize << ende;
	m_NumElements = (uint32_t)m_Verts.size();
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);
	VkBuffer buf = {};
	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{

		objtxt << m_Name << " Number:" << i << std::ends;
		m_App->VMACreateDeviceBuffer(m_BufSize,
			VK_BUFFER_USAGE_TRANSFER_DST_BIT |
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
			VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			m_Buffers[i], m_Allocation[i], objtxt.str());
	}

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_Verts.data(), m_Allocation[0],
		0, m_BufSize);
	m_Verts.clear();
    
}

VkVertexInputBindingDescription* 
	ResourceVertexObj::GetBindingDescription()
{
	m_BindingDescription.binding = m_BindPoint;
	m_BindingDescription.stride = sizeof(CartVert);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	

	return &m_BindingDescription;
}
std::vector<VkVertexInputAttributeDescription>* ResourceVertexObj::GetAttributeDescriptions()
{

		VkVertexInputAttributeDescription ad{};
		ad.binding = 0;
		ad.location = 0;
		ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
		ad.offset = offsetof(CartVert, pos);;
		m_AttributeDescriptions.push_back(ad);
		
		ad.binding = 0;
		ad.location = 1;
		ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
		ad.offset = offsetof(CartVert, color);;
		m_AttributeDescriptions.push_back(ad);
		
		
	
	return &m_AttributeDescriptions;
}



void ResourceVertexObj::MakeAxes(uint32_t sidelen)
{
		

		//{ {1.0, 0.0, 1.0,1.0},{1.0, 0.0, 1.0} },
		//{ {0.0, 0.0, 1.0,1.0},{1.0, 0.0, 1.0} },

#if 1
	//x			
	m_Axes.push_back({ {0.0,0.0,0.0,1.0f},{1.0, 0.0, 0.0,1.0} });
	m_Axes.push_back({ {sidelen,0.0,0.0,1.0f}, {1.0, 0.0, 0.0,1.0} });
	//y		
	m_Axes.push_back({{0.0, 0.0, 0.0,1.0f},{0.0, 1.0, 0.0,1.0}});
	m_Axes.push_back({{0.0, sidelen, 0.0,1.0f}, {0.0, 1.0, 0.0,1.0}});
	//z		
	m_Axes.push_back({{0.0, 0.0, 0.0,1.0},{0.0, 0.0, 1.0,1.0}});
	m_Axes.push_back({{0.0, 0.0, sidelen,1.0},{0.0, 0.0, 1.0,1.0}});
	

	for (size_t ii = 0; ii < sidelen; ii++)
	{
		float length = static_cast<float>(ii + 1);
		// 	xtic
		m_Axes.push_back({ {length,-0.1,0.0,1.0},{1.0,0.0,0.0,1.0} });
		m_Axes.push_back({ {length,0.1,0.0,1.0},{1.0,0.0,0.0,1.0} });
		// y tic
		m_Axes.push_back({ {0.0,length,0.1,1.0},{0.0,1.0,0.0,1.0} });
		m_Axes.push_back({ {0.0,length,-0.1,1.0},{0.0,1.0,0.0,1.0} });
		// z tic
		m_Axes.push_back({ {0.1,0.0,length,1.0},{0.0,0.0,1.0,1.0} });
		m_Axes.push_back({ {-0.1,0.0,length,1.0},{0.0,0.0,1.0,1.0} });
	}
	
	m_Axes.push_back({ {0.90,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {0.90,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });

	m_Axes.push_back({ {1.10,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {1.10,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	


	m_Verts = m_Axes;
#else

		glm::mat4 myMatrix = glm::translate(glm::mat4(1.0f), glm::vec3(0.5f,0.5f, 0.55f));
		for (size_t ii = 0; ii < m_Verts.size(); ii++)
		{
			glm::vec4 transformedVector = myMatrix * m_Verts[ii].pos; // guess the result
			m_Verts[ii].pos = transformedVector;
		}
#endif
}
