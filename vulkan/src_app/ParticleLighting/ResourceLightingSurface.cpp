/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#include "VulkanObj/VulkanApp.hpp"


#include <algorithm>
#include <cmath>

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
	MakeRectangleWalls();

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

void ResourceLightingSurface::MakeRectangleWalls()
{
	m_SurfaceVertices.clear();

	uint32_t subdivisionsPerCell = 1;
	if (CfgTst->CheckKey("boundary_light_wall_subdivisions_per_cell"))
		subdivisionsPerCell = CfgTst->GetUInt("boundary_light_wall_subdivisions_per_cell", true);
	if (subdivisionsPerCell == 0)
		throw std::runtime_error("boundary_light_wall_subdivisions_per_cell must be positive");

	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;
	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	uint32_t emittedVertexID = 0u;
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
		glm::vec3 uAxis = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 3)),
			static_cast<float>(config_setting_get_float_elem(segment, 4)),
			static_cast<float>(config_setting_get_float_elem(segment, 5))));
		glm::vec3 vAxis = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 6)),
			static_cast<float>(config_setting_get_float_elem(segment, 7)),
			static_cast<float>(config_setting_get_float_elem(segment, 8))));
		float uLength = static_cast<float>(config_setting_get_float_elem(segment, 9));
		float vLength = static_cast<float>(config_setting_get_float_elem(segment, 10));
		glm::vec3 normal = SafeNormalize(glm::vec3(
			static_cast<float>(config_setting_get_float_elem(segment, 11)),
			static_cast<float>(config_setting_get_float_elem(segment, 12)),
			static_cast<float>(config_setting_get_float_elem(segment, 13))));
		float wallFlag = static_cast<float>(config_setting_get_float_elem(segment, 14));
		float materialID = segmentLength >= 16
			? static_cast<float>(config_setting_get_float_elem(segment, 15))
			: 0.0f;

		auto emitVertex = [&](const glm::vec3& position, float localU, float localV)
		{
			LightingSurfaceVertex vertex{};
			vertex.pos = glm::vec4(position, wallFlag);
			vertex.normal_flag = glm::vec4(normal, materialID);
			vertex.light = glm::vec4(0.0f);
			vertex.meta = glm::vec4(
				localU,
				localV,
				static_cast<float>(emittedVertexID),
				0.0f);
			m_SurfaceVertices.push_back(vertex);
			emittedVertexID++;
		};

		auto emitQuad = [&](float u0, float u1, float v0, float v1)
		{
			glm::vec3 p00 = origin + uAxis * u0 + vAxis * v0;
			glm::vec3 p10 = origin + uAxis * u1 + vAxis * v0;
			glm::vec3 p01 = origin + uAxis * u0 + vAxis * v1;
			glm::vec3 p11 = origin + uAxis * u1 + vAxis * v1;

			emitVertex(p00, u0, v0);
			emitVertex(p10, u1, v0);
			emitVertex(p11, u1, v1);
			emitVertex(p00, u0, v0);
			emitVertex(p11, u1, v1);
			emitVertex(p01, u0, v1);
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
