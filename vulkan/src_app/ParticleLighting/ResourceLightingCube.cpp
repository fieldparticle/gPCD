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
uint32_t LightingWallCellAddress(const glm::vec3& worldPosition, uint32_t width, uint32_t height, uint32_t depth)
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

	uint32_t subdivisionsPerCell = 1;
	if (CfgTst->CheckKey("boundary_light_wall_subdivisions_per_cell"))
		subdivisionsPerCell = CfgTst->GetUInt("boundary_light_wall_subdivisions_per_cell", true);
	if (subdivisionsPerCell == 0)
		throw std::runtime_error("boundary_light_wall_subdivisions_per_cell must be positive");
	uint32_t cellWidth = CfgTst->GetUInt("CellAryW", true);
	uint32_t cellHeight = CfgTst->GetUInt("CellAryH", true);
	uint32_t cellDepth = CfgTst->GetUInt("CellAryL", true);

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

		glm::vec4 wallInfo(normal, wallFlag);

		auto emitQuad = [&](float u0, float u1, float v0, float v1)
		{
			glm::vec3 p00 = origin + uAxis * u0 + vAxis * v0;
			glm::vec3 p10 = origin + uAxis * u1 + vAxis * v0;
			glm::vec3 p01 = origin + uAxis * u0 + vAxis * v1;
			glm::vec3 p11 = origin + uAxis * u1 + vAxis * v1;

			CartVert cv0 = { { p00.x, p00.y, p00.z, 1.0f }, wallInfo };
			CartVert cv1 = { { p10.x, p10.y, p10.z, 1.0f }, wallInfo };
			CartVert cv2 = { { p11.x, p11.y, p11.z, 1.0f }, wallInfo };
			CartVert cv3 = { { p00.x, p00.y, p00.z, 1.0f }, wallInfo };
			CartVert cv4 = { { p11.x, p11.y, p11.z, 1.0f }, wallInfo };
			CartVert cv5 = { { p01.x, p01.y, p01.z, 1.0f }, wallInfo };

			cv0.extra = glm::vec4(static_cast<float>(LightingWallCellAddress(p00, cellWidth, cellHeight, cellDepth)), 0.0f, 0.0f, 0.0f);
			cv1.extra = glm::vec4(static_cast<float>(LightingWallCellAddress(p10, cellWidth, cellHeight, cellDepth)), 0.0f, 0.0f, 0.0f);
			cv2.extra = glm::vec4(static_cast<float>(LightingWallCellAddress(p11, cellWidth, cellHeight, cellDepth)), 0.0f, 0.0f, 0.0f);
			cv3.extra = cv0.extra;
			cv4.extra = cv2.extra;
			cv5.extra = glm::vec4(static_cast<float>(LightingWallCellAddress(p01, cellWidth, cellHeight, cellDepth)), 0.0f, 0.0f, 0.0f);

			m_Verts.push_back(cv0);
			m_Verts.push_back(cv1);
			m_Verts.push_back(cv2);
			m_Verts.push_back(cv3);
			m_Verts.push_back(cv4);
			m_Verts.push_back(cv5);
		};

		uint32_t uCellCount = static_cast<uint32_t>(std::max(1.0f, std::ceil(uLength)));
		uint32_t vCellCount = static_cast<uint32_t>(std::max(1.0f, std::ceil(vLength)));
		uint32_t uStepCount = uCellCount * subdivisionsPerCell;
		uint32_t vStepCount = vCellCount * subdivisionsPerCell;

		for (uint32_t uIndex = 0; uIndex < uStepCount; ++uIndex)
		{
			float u0 = uLength * static_cast<float>(uIndex) / static_cast<float>(uStepCount);
			float u1 = uLength * static_cast<float>(uIndex + 1) / static_cast<float>(uStepCount);
			for (uint32_t vIndex = 0; vIndex < vStepCount; ++vIndex)
			{
				float v0 = vLength * static_cast<float>(vIndex) / static_cast<float>(vStepCount);
				float v1 = vLength * static_cast<float>(vIndex + 1) / static_cast<float>(vStepCount);
				emitQuad(u0, u1, v0, v1);
			}
		}
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
