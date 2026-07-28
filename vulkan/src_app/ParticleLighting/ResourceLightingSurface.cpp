/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#include "VulkanObj/VulkanApp.hpp"
#include "VulkanObj/ObjLoader.hpp"


#include <algorithm>
#include <cmath>
#include <string>

namespace
{
	glm::vec3 SafeNormalize(glm::vec3 value)
	{
		float length = glm::length(value);
		if (length <= 1.0e-6f)
			return glm::vec3(0.0f);
		return value / length;
	}
}

void ResourceLightingSurface::Create(uint32_t BindPoint, Resource* particle)
{
	std::ostringstream objtxt;

	m_BindPoint = BindPoint;
	m_thisFramesBuffered = 1;
	CreateLayout();
	LoadLightingSurfaceObjects();

	m_NumElements = static_cast<uint64_t>(m_SurfaceVertices.size());
	if (m_SurfaceVertices.empty())
	{
		LightingSurfaceVertex dummy{};
		m_SurfaceVertices.push_back(dummy);
	}

	m_BufSize = static_cast<uint64_t>(sizeof(LightingSurfaceVertex)) *
		static_cast<uint64_t>(m_SurfaceVertices.size());
	m_Buffers.resize(m_thisFramesBuffered);
	m_BuffersMemory.resize(m_thisFramesBuffered);
	m_BuffersMapped.resize(m_thisFramesBuffered);
	m_BufferInfo.resize(m_thisFramesBuffered);
	m_DescriptorWrite.resize(m_thisFramesBuffered);
	m_Allocation.resize(m_thisFramesBuffered);

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

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		m_SurfaceVertices.data(),
		m_Allocation[0],
		0,
		m_BufSize);

	m_SurfaceVertices.clear();
	std::vector<LightingSurfaceVertex> empty;
	m_SurfaceVertices.swap(empty);
}

void ResourceLightingSurface::CreateLayout()
{
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;
}

uint32_t ResourceLightingSurface::SurfaceTypeID(const std::string& surfaceType)
{
	if (surfaceType == "SPHERE")
		return BOUNDARY_LIGHT_SURFACE_SPHERE;
	if (surfaceType == "RECTANGLE_WALL")
		return BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL;
	if (surfaceType == "NONE")
		return BOUNDARY_LIGHT_SURFACE_NONE;

	std::ostringstream errtxt;
	errtxt << "Unknown lighting surface_type: " << surfaceType << std::ends;
	throw std::runtime_error(errtxt.str().c_str());
}

void ResourceLightingSurface::LoadObjSurface(
	const std::string& objFile,
	uint32_t surfaceType,
	uint32_t surfaceID,
	uint32_t materialID,
	uint32_t& emittedVertexID)
{
	std::vector<glm::vec3> positions;
	std::vector<glm::vec2> uvs;
	std::vector<glm::vec3> normals;

	if (!loadOBJ(objFile.c_str(), positions, uvs, normals))
	{
		std::ostringstream errtxt;
		errtxt << "Unable to load lighting surface OBJ: " << objFile << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	if (positions.empty())
	{
		std::ostringstream errtxt;
		errtxt << "Lighting surface OBJ has no vertices: " << objFile << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	for (size_t index = 0; index < positions.size(); ++index)
	{
		glm::vec3 normal(0.0f);
		if (index < normals.size())
			normal = SafeNormalize(normals[index]);

		if (glm::length(normal) <= 1.0e-6f && (index / 3u) * 3u + 2u < positions.size())
		{
			size_t base = (index / 3u) * 3u;
			normal = SafeNormalize(glm::cross(
				positions[base + 1u] - positions[base],
				positions[base + 2u] - positions[base]));
		}

		glm::vec2 uv(0.0f);
		if (index < uvs.size())
			uv = uvs[index];

		LightingSurfaceVertex vertex{};
		vertex.pos = glm::vec4(positions[index], static_cast<float>(surfaceID));
		vertex.normal_flag = glm::vec4(normal, static_cast<float>(materialID));
		vertex.light = glm::vec4(0.0f);
		vertex.meta = glm::vec4(
			uv.x,
			uv.y,
			static_cast<float>(emittedVertexID),
			static_cast<float>(surfaceType));

		m_SurfaceVertices.push_back(vertex);
		emittedVertexID++;
	}
}

void ResourceLightingSurface::LoadLightingSurfaceObjects()
{
	m_SurfaceVertices.clear();

	int objectCount = 0;
	config_setting_t* objectList = nullptr;
	if (CfgTst->CheckKey("lighting_surface_objects"))
		objectList = CfgTst->StartStructure("lighting_surface_objects", objectCount);

	if (objectList == nullptr || objectCount == 0)
		throw std::runtime_error("lighting_surface_objects is required and must not be empty for ParticleLighting");

	uint32_t emittedVertexID = 0u;

	for (uint32_t pass = 0u; pass < 2u; ++pass)
	{
		for (int index = 0; index < objectCount; ++index)
		{
			config_setting_t* object = CfgTst->GetSubStructAddress(objectList, index);
			if (object == nullptr)
				throw std::runtime_error("lighting_surface_objects contains an invalid object");

			const char* source = nullptr;
			const char* objFile = nullptr;
			const char* surfaceTypeText = nullptr;
			int surfaceID = 0;
			int materialID = 0;

			if (config_setting_lookup_string(object, "source", &source) != CONFIG_TRUE ||
				std::string(source) != "obj")
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].source must be \"obj\"" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_string(object, "obj_file", &objFile) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].obj_file is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_string(object, "surface_type", &surfaceTypeText) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].surface_type is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_int(object, "surface_id", &surfaceID) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].surface_id is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_int(object, "material_id", &materialID) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].material_id is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}

			uint32_t surfaceType = SurfaceTypeID(surfaceTypeText);
			bool wallPass = surfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL;
			if ((pass == 0u && !wallPass) || (pass == 1u && wallPass))
				continue;

			LoadObjSurface(
				objFile,
				surfaceType,
				static_cast<uint32_t>(surfaceID),
				static_cast<uint32_t>(materialID),
				emittedVertexID);
		}
	}
}

VkVertexInputBindingDescription* ResourceLightingSurface::GetBindingDescription()
{
	m_BindingDescription.binding = 0;
	m_BindingDescription.stride = sizeof(LightingSurfaceVertex);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	return &m_BindingDescription;
}

std::vector<VkVertexInputAttributeDescription>* ResourceLightingSurface::GetAttributeDescriptions()
{
	m_AttributeDescriptions.clear();

	VkVertexInputAttributeDescription ad{};
	ad.binding = 0;
	ad.location = 0;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(LightingSurfaceVertex, pos);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 1;
	ad.offset = offsetof(LightingSurfaceVertex, normal_flag);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 2;
	ad.offset = offsetof(LightingSurfaceVertex, light);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 3;
	ad.offset = offsetof(LightingSurfaceVertex, meta);
	m_AttributeDescriptions.push_back(ad);

	return &m_AttributeDescriptions;
}
