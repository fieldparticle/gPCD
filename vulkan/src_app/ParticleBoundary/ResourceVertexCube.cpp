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
void ResourceVertexCube::Create(ResourceVertexParticle* PartVert)
{
#if 0
	ConfigObj* cfg = CfgApp;
	float nside = (float)CfgTst->GetInt("boundary_side_length", true);
	m_FileName = CfgApp->GetString("boundary_file_obj", true);
	ResourceVertexObj::Create(0, PartVert);
	bool boundaryFlag = CfgApp->GetBool("boundary_flag", true);
	if (boundaryFlag != true)
		for (size_t ii = 0; ii < m_vtemp.size(); ii++)
		{
			CartVert tmp = {};
			tmp.pos.x = m_vtemp[ii].x;// *m_ParticleVert->m_SideLength;
			tmp.pos.y = m_vtemp[ii].y; //*m_ParticleVert->m_SideLength;
			tmp.pos.z = m_vtemp[ii].z; //*m_ParticleVert->m_SideLength;
			tmp.pos.w = 1.0;
			tmp.color = glm::vec4(1.0, 0.0, 1.0, 0.1);
			m_Verts.push_back(tmp);
		}

	if(boundaryFlag ==true)
#endif
		MakeAxes(PartVert->m_SideLength);
	
	
	Resource::CheckBindPoint(0);

	/*for (int ii = 0; ii < m_Model.Data.size() / 3;)
	{
		Vertex ad;
		ad.position.x = m_Model.Data[ii];
		ad.position.y = m_Model.Data[++ii];
		ad.position.z = m_Model.Data[++ii];
		ii++;
		m_Verts.push_back(ad);
	}*/
	m_thisFramesBuffered = 2;
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


	objtxt << m_Name << " Number:" << 0 << std::ends;
	m_App->VMACreateDeviceBuffer(m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0], m_Allocation[0], objtxt.str());

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_Verts.data(), m_Allocation[0],
		0, m_BufSize);

	m_BufSize = sizeof(CartVert) * (uint32_t)m_CubeIndices.size();
	objtxt << m_Name << " Number:" << 0 << std::ends;
	m_App->VMACreateDeviceBuffer(m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_INDEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[1], m_Allocation[1], objtxt.str());

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_CubeIndices.data(), m_Allocation[1],
		0, m_BufSize);


	m_Verts.clear();
	m_CubeIndices.clear();



}
void ResourceVertexCube::MakeAxes(uint32_t sidelen)
{
	m_Axes.clear();
	m_CubeIndices.clear();

	bool basw = CfgApp->GetBool("application.boundary_as_walls", true);

	glm::vec3 minCorner;
	glm::vec3 maxCorner;

	if (basw == false)
	{
		minCorner = glm::vec3(0.0f, 0.0f, 0.0f);

		float side = static_cast<float>(sidelen) - 1.0f;

		maxCorner = glm::vec3(side, side, side);
	}
	else
	{
		minCorner = glm::vec3(
			CfgTst->GetFloat("wallXMIN", true),
			CfgTst->GetFloat("wallYMIN", true),
			CfgTst->GetFloat("wallZMIN", true)
		);

		maxCorner = glm::vec3(
			CfgTst->GetFloat("wallXMAX", true),
			CfgTst->GetFloat("wallYMAX", true),
			CfgTst->GetFloat("wallZMAX", true)
		);
	}

	float xmin = minCorner.x;
	float ymin = minCorner.y;
	float zmin = minCorner.z;

	float xmax = maxCorner.x;
	float ymax = maxCorner.y;
	float zmax = maxCorner.z;

	m_CubeIndices =
	{
		0, 2, 1,  2, 0, 3,   // back
		4, 5, 6,  6, 7, 4,   // front

		0, 4, 7,  7, 3, 0,   // left
		1, 2, 6,  6, 5, 1,   // right

		0, 1, 5,  5, 4, 0,   // bottom
		3, 7, 6,  6, 2, 3    // top
	};

	glm::vec4 color(1.0f, 1.0f, 1.0f, 1.0f);

	m_Axes.push_back({ { xmin, ymin, zmin, 1.0f }, color });
	m_Axes.push_back({ { xmax, ymin, zmin, 1.0f }, color });
	m_Axes.push_back({ { xmax, ymax, zmin, 1.0f }, color });
	m_Axes.push_back({ { xmin, ymax, zmin, 1.0f }, color });

	m_Axes.push_back({ { xmin, ymin, zmax, 1.0f }, color });
	m_Axes.push_back({ { xmax, ymin, zmax, 1.0f }, color });
	m_Axes.push_back({ { xmax, ymax, zmax, 1.0f }, color });
	m_Axes.push_back({ { xmin, ymax, zmax, 1.0f }, color });

	m_Verts = m_Axes;

	// Optional: save these for PushMem/view-centering
	//m_MinCorner = minCorner;
	//m_MaxCorner = maxCorner;
}
