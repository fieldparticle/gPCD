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

namespace
{
	config_setting_t* LookupStrict(ConfigObj* config, const char* key)
	{
		config_setting_t* setting = config->CheckKey(key);
		if (setting == nullptr)
			throw std::runtime_error(std::string("Missing required config item: ") + key);
		return setting;
	}

	bool LookupBoolStrict(ConfigObj* config, const char* key, bool defaultValue)
	{
		config_setting_t* setting = config->CheckKey(key);
		if (setting == nullptr)
			return defaultValue;
		if (config_setting_type(setting) != CONFIG_TYPE_BOOL)
			throw std::runtime_error(std::string(key) + " must be a bool");
		return config_setting_get_bool(setting) != CONFIG_FALSE;
	}

	float LookupFloatStrict(ConfigObj* config, const char* key)
	{
		config_setting_t* setting = LookupStrict(config, key);
		if (config_setting_type(setting) != CONFIG_TYPE_FLOAT)
			throw std::runtime_error(std::string(key) + " must be a float");
		return static_cast<float>(config_setting_get_float(setting));
	}

	glm::vec3 LookupVec3Strict(ConfigObj* config, const char* key)
	{
		config_setting_t* setting = LookupStrict(config, key);
		if (config_setting_length(setting) != 3)
			throw std::runtime_error(std::string(key) + " must contain exactly three values");

		glm::vec3 value(0.0f);
		for (int axis = 0; axis < 3; ++axis)
		{
			config_setting_t* element = config_setting_get_elem(setting, axis);
			if (element == nullptr || config_setting_type(element) != CONFIG_TYPE_FLOAT)
				throw std::runtime_error(std::string(key) + " values must be floats");
			value[axis] = static_cast<float>(config_setting_get_float(element));
		}
		return value;
	}

	bool LookupOptionalVec3Strict(ConfigObj* config, const char* key, glm::vec3& value)
	{
		if (config->CheckKey(key) == nullptr)
			return false;
		value = LookupVec3Strict(config, key);
		return true;
	}

	glm::vec3 EyeUpVector(glm::vec3 direction)
	{
		glm::vec3 worldUp(0.0f, 0.0f, 1.0f);
		if (glm::abs(glm::dot(glm::normalize(direction), worldUp)) > 0.98f)
			return glm::vec3(0.0f, 1.0f, 0.0f);
		return worldUp;
	}
}

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

void Resource::GeneralViewing(uint32_t CurrentBuffer)
{
	if (LookupBoolStrict(CfgTst, "align_with_eye", false))
	{
		GeneralViewingEye(CurrentBuffer);
		return;
	}

    glm::vec3 center(
        0.5f * static_cast<float>(m_CellW),
        0.5f * static_cast<float>(m_CellH),
        0.5f * static_cast<float>(m_CellL)
    );

	LookupOptionalVec3Strict(CfgTst, "view_center", center);

    float cellWidth = static_cast<float>(m_CellW);
    float cellHeight = static_cast<float>(m_CellH);
    float cellDepth = static_cast<float>(m_CellL);
    float maxExtent = glm::max(cellWidth, glm::max(cellHeight, cellDepth));

    m_UBO = {};

    // ============================================================
    // Model
    // Rotate around the configured view center, or the cell-array center when
    // no explicit view center is supplied.
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

    float dist = maxExtent * 4.0f;
    float worldWidth = cellWidth;
    float worldHeight = cellHeight;

    if (rCoordView == VIEW_XY)
    {
        // screen right = +X
        // screen up    = +Y
        // screen out   = +Z
        eye = center + glm::vec3(0.0f, 0.0f, dist);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
        worldWidth = cellWidth;
        worldHeight = cellHeight;
    }
    else if (rCoordView == VIEW_ZY)
    {
        // screen right = +Z
        // screen up    = +Y
        // screen out   = +X
        eye = center + glm::vec3(dist, 0.0f, 0.0f);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(0.0f, 0.0f, 1.0f);
        worldWidth = cellDepth;
        worldHeight = cellHeight;
    }
    else if (rCoordView == VIEW_XZ)
    {
        // screen right = +X
        // screen up    = +Z
        // screen out   = +Y
        eye = center + glm::vec3(0.0f, dist, 0.0f);
        up = glm::vec3(0.0f, 0.0f, 1.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
        worldWidth = cellWidth;
        worldHeight = cellDepth;
    }
    else
    {
        eye = center + glm::vec3(0.0f, 0.0f, dist);
        up = glm::vec3(0.0f, 1.0f, 0.0f);
        screenRight = glm::vec3(1.0f, 0.0f, 0.0f);
        worldWidth = cellWidth;
        worldHeight = cellHeight;
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

    float pixelsPerWorldUnit = glm::min(
        usableWidth / worldWidth,
        usableHeight / worldHeight
    );
    float halfWidth = (0.5f * viewWidth / pixelsPerWorldUnit) / ZoomX;
    float halfHeight = (0.5f * viewHeight / pixelsPerWorldUnit) / ZoomX;

    m_UBO.proj = glm::ortho(
        -halfWidth,
        halfWidth,
        -halfHeight,
        halfHeight,
        0.1f,
        maxExtent * 10.0f
    );

    //mout << "rRotZ:" << rRotZ << "," << "rRotY:" << rRotY << "," << "rRotX:" << rRotX << "," "zoom:" << ZoomX << ende;
    // Vulkan clip-space correction. Command recorders should use a positive
    // viewport height; this matrix owns the single Y-axis conversion.
    m_UBO.proj[1][1] *= -1.0f;

    vmaCopyMemoryToAllocation(
        m_App->m_vmaAllocator,
        &m_UBO,
        m_Allocation[CurrentBuffer],
        0,
        sizeof(m_UBO)
    );

   
}

void Resource::GeneralViewingEye(uint32_t CurrentBuffer)
{
	glm::vec3 center(
		0.5f * static_cast<float>(m_CellW),
		0.5f * static_cast<float>(m_CellH),
		0.5f * static_cast<float>(m_CellL)
	);
	LookupOptionalVec3Strict(CfgTst, "view_center", center);

	float cellWidth = static_cast<float>(m_CellW);
	float cellHeight = static_cast<float>(m_CellH);
	float cellDepth = static_cast<float>(m_CellL);
	float maxExtent = glm::max(cellWidth, glm::max(cellHeight, cellDepth));

	glm::vec3 lightingEye = LookupVec3Strict(CfgTst, "lighting_eye_position");
	glm::vec3 direction = LookupVec3Strict(CfgTst, "lighting_eye_direction");
	float directionLength = glm::length(direction);
	if (directionLength <= 1.0e-6f)
		throw std::runtime_error("lighting_eye_direction must not be zero length");
	direction /= directionLength;

	float eyeViewDistance = LookupFloatStrict(CfgTst, "eye_view_distance");
	if (eyeViewDistance <= 0.0f)
		throw std::runtime_error("eye_view_distance must be greater than zero");

	float fovDegrees = LookupFloatStrict(CfgTst, "lighting_eye_fov_degrees");
	if (fovDegrees <= 0.0f || fovDegrees >= 179.0f)
		throw std::runtime_error("lighting_eye_fov_degrees must be greater than 0 and less than 179");

	float viewWidth = static_cast<float>(m_SCO->m_SwapChainExtent.width);
	float viewHeight = static_cast<float>(m_SCO->m_SwapChainExtent.height);
	if (viewWidth <= 0.0f || viewHeight <= 0.0f)
		throw std::runtime_error("swap chain extent must be positive for eye-aligned viewing");

	glm::vec3 eye = lightingEye - direction * eyeViewDistance;
	glm::vec3 target = lightingEye;
	glm::vec3 up = EyeUpVector(direction);
	float farPlane = glm::max(maxExtent * 100.0f, glm::length(eye - center) + maxExtent * 10.0f);

	m_UBO = {};
	m_UBO.model = glm::mat4(1.0f);
	m_UBO.view = glm::lookAt(eye, target, up);
	m_UBO.proj = glm::perspective(
		glm::radians(fovDegrees),
		viewWidth / viewHeight,
		0.1f,
		farPlane
	);
	m_UBO.proj[1][1] *= -1.0f;

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		&m_UBO,
		m_Allocation[CurrentBuffer],
		0,
		sizeof(m_UBO)
	);
}
