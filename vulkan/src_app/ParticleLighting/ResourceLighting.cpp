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
#include "ParticleLighting/LightingStructs.hpp"

#include <cmath>

namespace
{
	struct LightingSphereSurface
	{
		bool enabled = false;
		glm::vec3 center = glm::vec3(0.0f);
		float radius = 0.0f;
		uint32_t wallFlag = 0u;
		uint32_t materialID = 0u;
	};

	struct LightingRectangleWallSurface
	{
		glm::vec3 origin = glm::vec3(0.0f);
		glm::vec3 uAxis = glm::vec3(1.0f, 0.0f, 0.0f);
		glm::vec3 vAxis = glm::vec3(0.0f, 1.0f, 0.0f);
		float uLength = 0.0f;
		float vLength = 0.0f;
		glm::vec3 normal = glm::vec3(0.0f);
		uint32_t wallFlag = 0u;
		uint32_t materialID = 0u;
	};

	uint32_t BoundaryLightCellIndex(uint32_t x, uint32_t y, uint32_t z, uint32_t width, uint32_t height)
	{
		return x + width * (y + height * z);
	}

	glm::vec3 SafeNormalize(glm::vec3 value)
	{
		float length = glm::length(value);
		if (length <= 1.0e-6f)
			return glm::vec3(0.0f);
		return value / length;
	}

	bool CellOwnsSphereSurface(glm::vec3 cellCenter, const LightingSphereSurface& sphere)
	{
		if (!sphere.enabled || sphere.radius <= 0.0f)
			return false;
		float distance = glm::length(cellCenter - sphere.center);
		return std::abs(distance - sphere.radius) <= 0.75f;
	}

	bool CellOwnsRectangleWallSurface(glm::vec3 cellCenter, const LightingRectangleWallSurface& wall)
	{
		glm::vec3 normal = SafeNormalize(wall.normal);
		if (glm::length(normal) <= 1.0e-6f)
			return false;

		glm::vec3 rel = cellCenter - wall.origin;
		float signedDistance = glm::dot(rel, normal);
		if (std::abs(signedDistance) > 0.75f)
			return false;

		glm::vec3 projectedPoint = cellCenter - signedDistance * normal;
		glm::vec3 planeRel = projectedPoint - wall.origin;
		float uCoord = glm::dot(planeRel, wall.uAxis);
		float vCoord = glm::dot(planeRel, wall.vAxis);
		return uCoord >= -0.5f
			&& uCoord <= wall.uLength + 0.5f
			&& vCoord >= -0.5f
			&& vCoord <= wall.vLength + 0.5f;
	}
}

void ResourceLighting::Create(uint32_t BindPoint, Resource* particle)
{
	
	std::ostringstream  objtxt;
	
	m_BindPoint = BindPoint;
	m_thisFramesBuffered = 1;
	CreateLayout();

	const uint32_t cellCount = m_CellW * m_CellH * m_CellL;
	if (cellCount == 0u)
	{
		std::ostringstream  errtxt;
		errtxt << m_Name << " ResourceLighting::Create no boundary-space cells." << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	LightingSphereSurface sphereSurface{};
	if (CfgTst->CheckKey("Lighting_ball"))
	{
		sphereSurface.enabled = true;
		sphereSurface.center = glm::vec3(
			CfgTst->GetFloat("Lighting_ball.x", true),
			CfgTst->GetFloat("Lighting_ball.y", true),
			CfgTst->GetFloat("Lighting_ball.z", true));
		sphereSurface.radius = CfgTst->GetFloat("Lighting_ball.radius", true);
		if (CfgTst->CheckKey("Lighting_ball.wall_flag"))
			sphereSurface.wallFlag = static_cast<uint32_t>(CfgTst->GetInt("Lighting_ball.wall_flag", false));
		if (CfgTst->CheckKey("Lighting_ball.material_id"))
			sphereSurface.materialID = static_cast<uint32_t>(CfgTst->GetInt("Lighting_ball.material_id", false));
	}

	std::vector<LightingRectangleWallSurface> rectangleWalls;
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

		LightingRectangleWallSurface wall{};
		wall.origin = glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 0)),
			static_cast<float>(config_setting_get_float_elem(segment, 1)),
			static_cast<float>(config_setting_get_float_elem(segment, 2)));
		wall.uAxis = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 3)),
			static_cast<float>(config_setting_get_float_elem(segment, 4)),
			static_cast<float>(config_setting_get_float_elem(segment, 5))));
		wall.vAxis = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 6)),
			static_cast<float>(config_setting_get_float_elem(segment, 7)),
			static_cast<float>(config_setting_get_float_elem(segment, 8))));
		wall.uLength = static_cast<float>(config_setting_get_float_elem(segment, 9));
		wall.vLength = static_cast<float>(config_setting_get_float_elem(segment, 10));
		wall.normal = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 11)),
			static_cast<float>(config_setting_get_float_elem(segment, 12)),
			static_cast<float>(config_setting_get_float_elem(segment, 13))));
		wall.wallFlag = static_cast<uint32_t>(config_setting_get_float_elem(segment, 14));
		if (segmentLength >= 16)
			wall.materialID = static_cast<uint32_t>(config_setting_get_float_elem(segment, 15));
		rectangleWalls.push_back(wall);
	}

	std::vector<BoundaryLightRecord> lightRecords;
	lightRecords.reserve(cellCount);
	for (uint32_t z = 0u; z < m_CellL; z++)
	{
		for (uint32_t y = 0u; y < m_CellH; y++)
		{
			for (uint32_t x = 0u; x < m_CellW; x++)
			{
				uint32_t cellID = BoundaryLightCellIndex(x, y, z, m_CellW, m_CellH);
				glm::vec3 cellCenter = glm::vec3(
					static_cast<float>(x) + 0.5f,
					static_cast<float>(y) + 0.5f,
					static_cast<float>(z) + 0.5f);

				BoundaryLightRecord record{};
				record.rgb_valid = glm::vec4(0.0f, 0.0f, 0.0f, 0.0f);
				record.normal_material = glm::vec4(0.0f);
				record.ids = glm::uvec4(
					cellID,
					BOUNDARY_LIGHT_SURFACE_NONE,
					0u,
					0u);

				if (CellOwnsSphereSurface(cellCenter, sphereSurface))
				{
					glm::vec3 normal = SafeNormalize(cellCenter - sphereSurface.center);
					record.normal_material = glm::vec4(normal, static_cast<float>(sphereSurface.materialID));
					record.ids = glm::uvec4(
						cellID,
						BOUNDARY_LIGHT_SURFACE_SPHERE,
						sphereSurface.wallFlag,
						0u);
				}

				for (const LightingRectangleWallSurface& wall : rectangleWalls)
				{
					if (!CellOwnsRectangleWallSurface(cellCenter, wall))
						continue;
					record.normal_material = glm::vec4(wall.normal, static_cast<float>(wall.materialID));
					record.ids = glm::uvec4(
						cellID,
						BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
						wall.wallFlag,
						0u);
					break;
				}

				lightRecords.push_back(record);
			}
		}
	}
	m_BufSize = static_cast<uint64_t>(sizeof(BoundaryLightRecord))*lightRecords.size();
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);
	VkBuffer buf = {};

	objtxt << m_Name << " Number:" << 0 << std::ends;
	VkBufferUsageFlags usage =
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;


	m_App->VMACreateDeviceBuffer(
		m_BufSize,
		usage,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0],
		m_Allocation[0],
		objtxt.str());
	
	m_BufferInfo[0].buffer = m_Buffers[0];
	m_BufferInfo[0].offset = 0;
	m_BufferInfo[0].range = m_BufSize;

	m_DescriptorWrite[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[0].dstBinding = m_BindPoint;
	m_DescriptorWrite[0].dstArrayElement = 0;
	m_DescriptorWrite[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_DescriptorWrite[0].descriptorCount = 1;
	m_DescriptorWrite[0].pBufferInfo = &m_BufferInfo[0];
	objtxt.clear();

	vmaCopyMemoryToAllocation(m_App->m_vmaAllocator, lightRecords.data(), m_Allocation[0],
		0, m_BufSize);
}


void ResourceLighting::CreateLayout()
{

	// Step 1: Add layout biding definition.
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;
}
VkVertexInputBindingDescription* 
ResourceLighting::GetBindingDescription()
{
	
	m_BindingDescription.binding = m_BindPoint;
	m_BindingDescription.stride = sizeof(BoundaryLightRecord);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	

	return &m_BindingDescription;
}
