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


	m_CubeIndices =
	{
		0, 2, 1,  2, 0, 3,   // back
		4, 5, 6,  6, 7, 4,   // front

		0, 4, 7,  7, 3, 0,   // left
		1, 2, 6,  6, 5, 1,   // right

		0, 1, 5,  5, 4, 0,   // bottom
		3, 7, 6,  6, 2, 3    // top
	};
	int side = static_cast<int>(sidelen) - 1;

	m_Axes.push_back({ { 0, 0, 0, 1.0 },{1.0,1.0,1.0,1} });
	m_Axes.push_back({ { side, 0.0, 0.0, 1.0 }, {1.0,1,1.,1} });
	m_Axes.push_back({ { side,  side, 0.0, 1.0 }, {1.,1.,1,1} });
	m_Axes.push_back({ {0.0,  side, 0.0, 1.0 }, {1,1,1.,1} });

	m_Axes.push_back({ {0.0, 0.0,  side, 1.0 }, {1,1.,1,1} });
	m_Axes.push_back({ { side, 0.0,  side, 1.0 }, {1.,1,1,1} });
	m_Axes.push_back({ { side,  side,  side, 1.0 }, {1,1,1,1} });
	m_Axes.push_back({ {0.0,  side,  side, 1.0 }, {1.0,1.0,1.0,1} });

	m_Verts = m_Axes;
	/*
	m_Axes.push_back({ {0.0,0.0,0.0,1.0f},{1.0, 0.0, 0.0,1.0} });
	m_Axes.push_back({ {sidelen,0.0,0.0,1.0f}, {1.0, 0.0, 0.0,1.0} });
	//y
	m_Axes.push_back({ {0.0, 0.0, 0.0,1.0f},{0.0, 1.0, 0.0,1.0} });
	m_Axes.push_back({ {0.0, sidelen, 0.0,1.0f}, {0.0, 1.0, 0.0,1.0} });
	//z
	m_Axes.push_back({ {0.0, 0.0, 0.0,1.0},{0.0, 0.0, 1.0,1.0} });
	m_Axes.push_back({ {0.0, 0.0, sidelen,1.0},{0.0, 0.0, 1.0,1.0} });

#if 0
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
#endif
	m_Axes.push_back({ {0.90,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {0.90,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });

	m_Axes.push_back({ {1.10,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {1.10,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });



	//m_Verts = m_Axes;
	*/
}
