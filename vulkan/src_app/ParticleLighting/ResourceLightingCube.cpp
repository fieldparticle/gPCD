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
void ResourceLightingCube::Create(Resource* PartVert)
{
	MakeRectangleWalls();
	
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
	m_thisFramesBuffered = 1;
	std::ostringstream  objtxt;
	uint32_t drawableElementCount = static_cast<uint32_t>(m_Verts.size());
	if (m_Verts.empty())
	{
		CartVert dummy = {};
		m_Verts.push_back(dummy);
	}
	m_BufSize = sizeof(CartVert) * (uint32_t)m_Verts.size();
	mout << "MEMALLOC:ResourceVertexObj:" << m_BufSize << ende;
	m_NumElements = drawableElementCount;
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

	m_Verts.clear();
	std::vector<CartVert> vempty;
	m_Verts.swap(vempty);
	m_CubeIndices.clear();
	std::vector<uint32_t> cempty;
	m_CubeIndices.swap(cempty);



}

void ResourceLightingCube::MakeRectangleWalls()
{
	m_Verts.clear();

	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;
	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	for (int index = 0; segmentList != nullptr && index < segmentCount; ++index)
	{
		config_setting_t* segment = CfgTst->GetSubStructAddress(segmentList, index);
		int segmentLength = segment == nullptr ? 0 : config_setting_length(segment);
		if (segment == nullptr || (segmentLength != 15 && segmentLength != 16))
		{
			std::ostringstream errtxt;
			errtxt << "rectangle_wall_segments[" << index << "] must contain fifteen or sixteen values" << std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}

		glm::vec3 origin(
			static_cast<float>(config_setting_get_float_elem(segment, 0)),
			static_cast<float>(config_setting_get_float_elem(segment, 1)),
			static_cast<float>(config_setting_get_float_elem(segment, 2)));
		glm::vec3 uAxis(
			static_cast<float>(config_setting_get_float_elem(segment, 3)),
			static_cast<float>(config_setting_get_float_elem(segment, 4)),
			static_cast<float>(config_setting_get_float_elem(segment, 5)));
		glm::vec3 vAxis(
			static_cast<float>(config_setting_get_float_elem(segment, 6)),
			static_cast<float>(config_setting_get_float_elem(segment, 7)),
			static_cast<float>(config_setting_get_float_elem(segment, 8)));
		float uLength = static_cast<float>(config_setting_get_float_elem(segment, 9));
		float vLength = static_cast<float>(config_setting_get_float_elem(segment, 10));
		glm::vec3 normal(
			static_cast<float>(config_setting_get_float_elem(segment, 11)),
			static_cast<float>(config_setting_get_float_elem(segment, 12)),
			static_cast<float>(config_setting_get_float_elem(segment, 13)));
		float wallFlag = static_cast<float>(config_setting_get_float_elem(segment, 14));

		glm::vec3 p00 = origin;
		glm::vec3 p10 = origin + uAxis * uLength;
		glm::vec3 p01 = origin + vAxis * vLength;
		glm::vec3 p11 = origin + uAxis * uLength + vAxis * vLength;
		glm::vec4 wallInfo(normal, wallFlag);

		CartVert v0 = { { p00.x, p00.y, p00.z, 1.0f }, wallInfo };
		CartVert v1 = { { p10.x, p10.y, p10.z, 1.0f }, wallInfo };
		CartVert v2 = { { p11.x, p11.y, p11.z, 1.0f }, wallInfo };
		CartVert v3 = { { p00.x, p00.y, p00.z, 1.0f }, wallInfo };
		CartVert v4 = { { p11.x, p11.y, p11.z, 1.0f }, wallInfo };
		CartVert v5 = { { p01.x, p01.y, p01.z, 1.0f }, wallInfo };

		m_Verts.push_back(v0);
		m_Verts.push_back(v1);
		m_Verts.push_back(v2);
		m_Verts.push_back(v3);
		m_Verts.push_back(v4);
		m_Verts.push_back(v5);
	}
}

void ResourceLightingCube::MakeAxes(uint32_t sidelen)
{
	m_Axes.clear();
	m_CubeIndices.clear();

	bool show_wall_as_boundary_cube = CfgApp->GetBool("application.show_wall_as_boundary_cube", true);
	bool show_cell_boundary_cube = CfgApp->GetBool("application.show_cell_boundary_cube", true);

	glm::vec3 minCorner;
	glm::vec3 maxCorner;
#if 0
	if (show_wall_as_boundary_cube ==true)
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
#endif	

	if (show_cell_boundary_cube == true)
	{
		m_CellW = CfgTst->GetUInt("CellAryW", true);
		m_CellL = CfgTst->GetUInt("CellAryL", true);
		m_CellH = CfgTst->GetUInt("CellAryH", true);
		minCorner = glm::vec3(0.5f, 0.5f, 0.5f);
		maxCorner = glm::vec3(
			static_cast<float>(m_CellW) - 0.5f,
			static_cast<float>(m_CellH) - 0.5f,
			static_cast<float>(m_CellL) - 0.5f
		);

	}

	if (show_cell_boundary_cube == true || show_wall_as_boundary_cube == true)
	{
		float xmin = minCorner.x;
		float ymin = minCorner.y;
		float zmin = minCorner.z;

		float xmax = maxCorner.x;
		float ymax = maxCorner.y;
		float zmax = maxCorner.z;
		m_CubeIndices =
		{
			// back face zmin
			0, 1,
			1, 2,
			2, 3,
			3, 0,

			// front face zmax
			4, 5,
			5, 6,
			6, 7,
			7, 4,

			// connecting edges
			0, 4,
			1, 5,
			2, 6,
			3, 7
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
	}
}
