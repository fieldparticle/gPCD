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

void Resource::CheckBindPoint( uint32_t BindPoint)
{
	if (m_Type == VBW_TYPE_UNIFORM_BUFFER)
	{
		return;
	}

	if( m_Type == VBW_TYPE_INDEX_BUFFER ||  
		m_Type == VBW_TYPE_PUSH_CONSTANT )
	{	std::string msg = "Resource type:" + m_Name + " does not require binding point.";
		throw std::runtime_error(msg.c_str());
	}
		m_BindPoint=BindPoint;
   
    
}
void Resource::GeneralViewing(uint32_t SideLength, uint32_t CurrentBuffer)
{
	float s = SideLength;

	glm::vec3 center(
		s * 0.5f,
		s * 0.5f,
		s * 0.5f
	);

	m_UBO = {};

	// ============================================================
	// Model matrix
	// Cube corner stays at (0,0,0), cube extends positive.
	// Rotation is performed about cube center.
	// ============================================================

	m_UBO.model = glm::mat4(1.0f);

	m_UBO.model = glm::translate(m_UBO.model, center);

	m_UBO.model = glm::rotate(
		m_UBO.model,
		glm::radians(rRotZ),
		glm::vec3(0.0f, 0.0f, 1.0f)
	);

	m_UBO.model = glm::rotate(
		m_UBO.model,
		glm::radians(rRotY),
		glm::vec3(0.0f, 1.0f, 0.0f)
	);

	m_UBO.model = glm::rotate(
		m_UBO.model,
		glm::radians(rRotX),
		glm::vec3(1.0f, 0.0f, 0.0f)
	);

	m_UBO.model = glm::translate(m_UBO.model, -center);

	// ============================================================
	// View matrix
	// Camera looks at cube center.
	// ============================================================
	glm::vec3 eye;
	glm::vec3 up;

	if (rCoordView == VIEW_XY)
	{
		// Look along +Z toward XY plane
		eye = glm::vec3(center.x, center.y, center.z + s * 4.0f);
		up = glm::vec3(0.0f, 1.0f, 0.0f);
	}
	else if (rCoordView == VIEW_ZY)
	{
		// Look along +X toward ZY plane
		eye = glm::vec3(center.x + s * 4.0f, center.y, center.z);
		up = glm::vec3(0.0f, 1.0f, 0.0f);
	}
	else if (rCoordView == VIEW_XZ)
	{
		// Look along +Y toward XZ plane
		eye = glm::vec3(center.x, center.y + s * 4.0f, center.z);
		up = glm::vec3(0.0f, 0.0f, -1.0f);
	}
	else
	{
		// fallback
		eye = glm::vec3(center.x, center.y, center.z + s * 4.0f);
		up = glm::vec3(0.0f, 1.0f, 0.0f);
	}

	m_UBO.view = glm::lookAt(
		eye,
		center,
		up
	);

	// ============================================================
	// Projection matrix
	// Orthographic zoom is handled here, not by scaling the model.
	// Bounding sphere radius keeps rotated cube visible.
	// ============================================================

	float aspect =
		static_cast<float>(m_SCO->m_SwapChainExtent.width) /
		static_cast<float>(m_SCO->m_SwapChainExtent.height);

	float radius = 0.5f * sqrt(3.0f) * s;
	if (ZoomX == 0.0)
	{
		mout << "Particle UBO Zoom is zero" << ende;

	}
	// Larger ZoomX = zoom in
	float half = radius / ZoomX;

	m_UBO.proj = glm::ortho(
		-half * aspect,
		half * aspect,
		-half,
		half,
		0.1f,
		s * 10.0f
	);

	// Vulkan clip-space correction
	m_UBO.proj[1][1] *= -1.0f;

	// ============================================================
	// Upload UBO
	// ============================================================

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		&m_UBO,
		m_Allocation[CurrentBuffer],
		0,
		sizeof(m_UBO)
	);
}