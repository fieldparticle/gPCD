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
void ResourceVertexSphere::Create(ResourceVertexParticle* PartVert)
{
	ConfigObj* cfg = CfgApp;
	//float nside = (float)CfgTst->GetInt("application.boundary_side_length", true);
	m_FileName = CfgApp->GetString("application.sphere_file", true);
	ResourceVertexObj::Create(0, PartVert);

	for (size_t ii = 0; ii < m_vtemp.size(); ii++)
	{
		CartVert tmp = {};
		tmp.pos.x = m_vtemp[ii].x * 0.5 * PartVert->m_Radius;
		tmp.pos.y = m_vtemp[ii].y * 0.5 * PartVert->m_Radius; //*m_ParticleVert->m_SideLength;
		tmp.pos.z = m_vtemp[ii].z * 0.5 * PartVert->m_Radius; //*m_ParticleVert->m_SideLength;
		tmp.pos.w = 0.2f;
		tmp.color = glm::vec4(1.0, 0.0, 0.0, 1.0);
		m_Verts.push_back(tmp);
	}


	
	ResourceVertexObj::Create(0);
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


	objtxt << m_Name << " Number:" << 0 << std::ends;
	m_App->VMACreateDeviceBuffer(m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0], m_Allocation[0], objtxt.str());

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, m_Verts.data(), m_Allocation[0],
		0, m_BufSize);


}
