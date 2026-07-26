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
#include <algorithm>
#include <cmath>

namespace
{
uint32_t LightingCellAddress(const glm::vec3& worldPosition, uint32_t width, uint32_t height, uint32_t depth)
{
	const int cellX = std::clamp(
		static_cast<int>(std::floor(worldPosition.x)),
		0,
		static_cast<int>(width) - 1);
	const int cellY = std::clamp(
		static_cast<int>(std::floor(worldPosition.y)),
		0,
		static_cast<int>(height) - 1);
	const int cellZ = std::clamp(
		static_cast<int>(std::floor(worldPosition.z)),
		0,
		static_cast<int>(depth) - 1);

	return static_cast<uint32_t>(
		cellX + (cellY * static_cast<int>(width)) +
		(cellZ * static_cast<int>(width) * static_cast<int>(height)));
}
}

void ResourceLightingSphere::Create(Resource* PartVert)
{
	ConfigObj* cfg = CfgApp;
	//float nside = (float)CfgTst->GetInt("application.boundary_side_length", true);
	m_FileName = CfgApp->GetString("application.sphere_file", true);
	ResourceVertexObj::Create(0, PartVert);

	const glm::vec3 lightingBallCenter(
		CfgTst->GetFloat("Lighting_ball.x", true),
		CfgTst->GetFloat("Lighting_ball.y", true),
		CfgTst->GetFloat("Lighting_ball.z", true));
	const float lightingBallRadius = CfgTst->GetFloat("Lighting_ball.radius", true);

	for (size_t ii = 0; ii < m_vtemp.size(); ii++)
	{
		CartVert tmp = {};
		// The OBJ sphere has radius 0.5.  Store a unit-radius mesh here;
		// the vertex shader scales each instance by P[instance].Data.x.
		tmp.pos.x = m_vtemp[ii].x * 2.0f;
		tmp.pos.y = m_vtemp[ii].y * 2.0f;
		tmp.pos.z = m_vtemp[ii].z * 2.0f;
		tmp.pos.w = 0.2f;
		const glm::vec3 sphereNormal = glm::normalize(glm::vec3(tmp.pos));
		const glm::vec3 worldPosition = lightingBallCenter + sphereNormal * lightingBallRadius;
		const uint32_t cellAddress = LightingCellAddress(worldPosition, m_CellW, m_CellH, m_CellL);
		tmp.color = glm::vec4(1.0, 0.0, 0.0, 1.0);
		tmp.color.w = static_cast<float>(cellAddress);
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
