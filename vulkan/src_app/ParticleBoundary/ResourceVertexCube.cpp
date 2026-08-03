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

	bool show_boundary_as_obj = CfgApp->GetBool("application.boundary_as_obj", true);

	if (show_boundary_as_obj == true)
	{
		m_FileName = CfgApp->GetString("application.boundary_file", true);
		ResourceVertexObj::Create(0, PartVert);
		for (size_t ii = 0; ii < m_vtemp.size(); ii++)
		{
			CartVert tmp = {};
			tmp.pos.x = m_vtemp[ii].x;// *m_ParticleVert->m_SideLength;
			tmp.pos.y = m_vtemp[ii].y; //*m_ParticleVert->m_SideLength;
			tmp.pos.z = m_vtemp[ii].z; //*m_ParticleVert->m_SideLength;
			tmp.pos.w = 1.0;
			tmp.color = glm::vec4(1.0, 1.0, 1.0, 1.0);
			tmp.extra = glm::vec4(0.0, 0.0, 0.0, 0.0);
			m_Verts.push_back(tmp);
		}
	}
	else
		{

			MakeAxes(PartVert->m_SideLength);
		}

	ConfigObj* pistonVisualCfg = nullptr;
	std::string pistonVisualPrefix;
	if (CfgTst != nullptr && CfgTst->CheckKey("piston_visual.enabled"))
	{
		pistonVisualCfg = CfgTst;
		pistonVisualPrefix = "piston_visual.";
	}
	else if (CfgApp->CheckKey("application.piston_visual.enabled"))
	{
		pistonVisualCfg = CfgApp;
		pistonVisualPrefix = "application.piston_visual.";
	}

	if (pistonVisualCfg != nullptr &&
		pistonVisualCfg->GetBool(pistonVisualPrefix + "enabled", true))
	{
		float pistonX = 0.0f;
		if (CfgTst != nullptr && CfgTst->CheckKey("piston_x_start"))
			pistonX = CfgTst->GetFloat("piston_x_start", true);
		else if (pistonVisualCfg->CheckKey(pistonVisualPrefix + "x"))
			pistonX = pistonVisualCfg->GetFloat(pistonVisualPrefix + "x", true);

		float yMin = pistonVisualCfg->GetFloat(pistonVisualPrefix + "y_min", true);
		float yMax = pistonVisualCfg->GetFloat(pistonVisualPrefix + "y_max", true);
		float z = pistonVisualCfg->GetFloat(pistonVisualPrefix + "z", true);
		float headLength = pistonVisualCfg->CheckKey(pistonVisualPrefix + "head_length")
			? pistonVisualCfg->GetFloat(pistonVisualPrefix + "head_length", true)
			: pistonVisualCfg->GetFloat(pistonVisualPrefix + "x_thickness", true);
		float rodLength = pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_length", true);
		float rodHeight = pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_height", true);
		float yCenter = 0.5f * (yMin + yMax);
		float rodYMin = yCenter - 0.5f * rodHeight;
		float rodYMax = yCenter + 0.5f * rodHeight;
		glm::vec4 headColor(
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "head_color.red", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "head_color.green", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "head_color.blue", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "head_color.alpha", true));
		glm::vec4 rodColor(
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_color.red", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_color.green", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_color.blue", true),
			pistonVisualCfg->GetFloat(pistonVisualPrefix + "rod_color.alpha", true));

		auto addVertex = [&](float x, float y, float z, const glm::vec4& color)
		{
			CartVert tmp = {};
			tmp.pos = glm::vec4(x, y, z, 1.0f);
			tmp.color = color;
			tmp.extra = glm::vec4(1.0, 0.0, 0.0, 0.0);
			m_Verts.push_back(tmp);
		};

		auto addRect = [&](float xMin, float xMax, float rectYMin, float rectYMax, const glm::vec4& color)
		{
			addVertex(xMin, rectYMin, z, color);
			addVertex(xMax, rectYMin, z, color);
			addVertex(xMax, rectYMax, z, color);
			addVertex(xMin, rectYMin, z, color);
			addVertex(xMax, rectYMax, z, color);
			addVertex(xMin, rectYMax, z, color);
		};

		float headXMin = pistonX - headLength;
		float headXMax = pistonX;
		float rodXMin = headXMin - rodLength;
		float rodXMax = headXMin;
		addRect(headXMin, headXMax, yMin, yMax, headColor);
		addRect(rodXMin, rodXMax, rodYMin, rodYMax, rodColor);
	}
	
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



	if (show_boundary_as_obj == false)
	{
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
	}

	m_Verts.clear();
	std::vector<CartVert> vempty;
	m_Verts.swap(vempty);
	m_CubeIndices.clear();
	std::vector<uint32_t> cempty;
	m_CubeIndices.swap(cempty);



}
void ResourceVertexCube::MakeAxes(uint32_t sidelen)
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
