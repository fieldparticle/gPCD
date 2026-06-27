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
   
    
}void Resource::GeneralViewing(uint32_t SideLength, uint32_t CurrentBuffer)
{
    float s = static_cast<float>(SideLength);
    float cellCenter = 0.5f * s;

    glm::vec3 center(
        cellCenter,
        cellCenter,
        cellCenter
    );

    m_UBO = {};

    // ============================================================
    // Model
    // The rendered cell-array extent spans 0..SideLength.
    // Rotate about the extent center so the cell array remains
    // centered in the view.
    // ============================================================

    m_UBO.model = glm::mat4(1.0f);

    m_UBO.model = glm::translate(m_UBO.model, center);
    
    m_UBO.model = glm::rotate(
        m_UBO.model,
        glm::radians((rRotZ)),
        glm::vec3(0.0f, 0.0f, 1.0f)
    );

    m_UBO.model = glm::rotate(
        m_UBO.model,
        glm::radians((rRotY)),
        glm::vec3(0.0f, 1.0f, 0.0f)
    );

    m_UBO.model = glm::rotate(
        m_UBO.model,
        glm::radians(rRotX),
        glm::vec3(1.0f, 0.0f, 0.0f)
    );
    
    m_UBO.model = glm::translate(m_UBO.model, -center);

    // ============================================================
    // View convention:
    //
    // Screen +X = right
    // Screen +Y = up
    // Screen +Z = out of the screen
    //
    // Therefore:
    // VIEW_XY: look along -Z
    // VIEW_ZY: look along -X
    // VIEW_XZ: look along -Y
    // ============================================================

    glm::vec3 eye;
    glm::vec3 up;
    glm::vec3 screenRight;

    float dist = s * 4.0f;

    if (rCoordView == VIEW_XY)
    {
        // screen right = +X
        // screen up    = +Y
        // screen out   = +Z
        eye = center + glm::vec3(0.0f, 0.0f, dist);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
    }
    else if (rCoordView == VIEW_ZY)
    {
        // screen right = +Z
        // screen up    = +Y
        // screen out   = +X
        eye = center + glm::vec3(dist, 0.0f, 0.0f);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(0.0f, 0.0f, 1.0f);
    }
    else if (rCoordView == VIEW_XZ)
    {
        // screen right = +X
        // screen up    = +Z
        // screen out   = +Y
        eye = center + glm::vec3(0.0f, dist, 0.0f);
        up = glm::vec3(0.0f, 0.0f, 1.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
    }
    else
    {
        eye = center + glm::vec3(0.0f, 0.0f, dist);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
    }

    glm::vec3 pan = (PanX * screenRight) + (PanY * up);
    eye += pan;
    center += pan;

    m_UBO.view = glm::lookAt(
        eye,
        center,
        up
    );

    // ============================================================
    // Projection
    // Ortho is centered in view space.
    // ============================================================

    float viewWidth = static_cast<float>(m_SCO->m_SwapChainExtent.width);
    float viewHeight = static_cast<float>(m_SCO->m_SwapChainExtent.height);
    float aspect = viewWidth / viewHeight;

    if (ZoomX == 0.0f)
    {
        mout << "GeneralViewing ZoomX is zero" << ende;
        ZoomX = 1.0f;
    }

    float pixelMargin = 100.0f;
    float usableWidth = viewWidth - (2.0f * pixelMargin);
    float usableHeight = viewHeight - (2.0f * pixelMargin);

    if (usableWidth <= 1.0f || usableHeight <= 1.0f)
    {
        usableWidth = viewWidth;
        usableHeight = viewHeight;
    }

    float fitPixels = (usableWidth < usableHeight) ? usableWidth : usableHeight;
    float pixelsPerWorldUnit = fitPixels / s;
    float half = (0.5f * viewHeight / pixelsPerWorldUnit) / ZoomX;
    //float half = 100.0f;

    m_UBO.proj = glm::ortho(
        -half * aspect,
        half * aspect,
        -half,
        half,
        0.1f,
        s * 10.0f
    );

    //mout << "rRotZ:" << rRotZ << "," << "rRotY:" << rRotY << "," << "rRotX:" << rRotX << "," "zoom:" << ZoomX << ende;
    // Vulkan clip-space correction
    m_UBO.proj[1][1] *= -1.0f;

    vmaCopyMemoryToAllocation(
        m_App->m_vmaAllocator,
        &m_UBO,
        m_Allocation[CurrentBuffer],
        0,
        sizeof(m_UBO)
    );

   
}
