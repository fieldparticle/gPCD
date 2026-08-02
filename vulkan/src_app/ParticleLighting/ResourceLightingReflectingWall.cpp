/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#include "VulkanObj/VulkanApp.hpp"
#include "ParticleLighting/ResourceLightingReflectingWall.hpp"

#include <sstream>

namespace
{
	glm::vec3 SafeNormalize(glm::vec3 value)
	{
		float length = glm::length(value);
		if (length <= 1.0e-6f)
			return glm::vec3(0.0f);
		return value / length;
	}

	void AppendSurfaceVertex(
		const glm::vec3& position,
		const glm::vec3& normal,
		const glm::vec2& uv,
		uint32_t surfaceType,
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		const glm::vec4& albedo,
		std::vector<LightingSurfaceVertex>& surfaceVertices,
		uint32_t& emittedVertexID)
	{
		LightingSurfaceVertex vertex{};
		vertex.pos = glm::vec4(position, static_cast<float>(surfaceID));
		vertex.normal_flag = glm::vec4(SafeNormalize(normal), static_cast<float>(materialID));
		vertex.light = initialSurfaceColor;
		vertex.meta = glm::vec4(
			uv.x,
			uv.y,
			static_cast<float>(emittedVertexID),
			static_cast<float>(surfaceType));
		vertex.albedo = albedo;

		surfaceVertices.push_back(vertex);
		emittedVertexID++;
	}
}

void ResourceLightingReflectingWall::Create(uint32_t BindPoint)
{
	bool enabled =
		CfgTst->CheckKey("reflecting_wall_light_map.enabled") &&
		CfgTst->GetBool("reflecting_wall_light_map.enabled", true);

	m_BindPoint = BindPoint;
	m_thisFramesBuffered = 1;
	CreateLayout();

	if (enabled)
	{
		uint32_t surfaceID =
			CfgTst->GetUInt("reflecting_wall_light_map.surface_id", true);
		if (surfaceID != SurfaceID)
		{
			std::ostringstream errtxt;
			errtxt << "reflecting_wall_light_map.surface_id must be "
				<< SurfaceID << std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}

		m_MapWidth = CfgTst->GetUInt("reflecting_wall_light_map.width", true);
		m_MapHeight = CfgTst->GetUInt("reflecting_wall_light_map.height", true);
		if (m_MapWidth == 0u || m_MapHeight == 0u)
			throw std::runtime_error("reflecting_wall_light_map width/height must be positive");
	}
	else
	{
		m_MapWidth = 1u;
		m_MapHeight = 1u;
	}

	uint64_t cellCount =
		static_cast<uint64_t>(m_MapWidth) * static_cast<uint64_t>(m_MapHeight);
	m_NumElements = cellCount;
	m_LightMap.assign(static_cast<size_t>(cellCount), ReflectingWallLightMapCell{});
	m_BufSize =
		static_cast<uint64_t>(sizeof(ReflectingWallLightMapCell)) * cellCount;
	m_SplatCapacity = CfgTst->CheckKey("reflecting_wall_light_map.splat_capacity")
		? CfgTst->GetUInt("reflecting_wall_light_map.splat_capacity", true)
		: CfgTst->GetUInt("num_particles", true) + 1u;
	if (m_SplatCapacity == 0u)
		throw std::runtime_error("reflecting_wall_light_map.splat_capacity must be positive");
	m_SplatCount = m_SplatCapacity;
	m_Splats.assign(
		static_cast<size_t>(m_SplatCapacity),
		ReflectingWallPhotonSplat{});
	m_SplatBufSize =
		static_cast<uint64_t>(sizeof(ReflectingWallPhotonSplat)) *
		static_cast<uint64_t>(m_SplatCapacity);

	m_Buffers.resize(2);
	m_BuffersMemory.resize(2);
	m_BuffersMapped.resize(2);
	m_BufferInfo.resize(2);
	m_DescriptorWrite.resize(2);
	m_Allocation.resize(2);

	std::ostringstream objtxt;
	objtxt << m_Name << " LightMap Number:" << 0 << std::ends;
	m_App->VMACreateDeviceBuffer(
		m_BufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0],
		m_Allocation[0],
		objtxt.str());

	std::ostringstream splatTxt;
	splatTxt << m_Name << " PhotonSplat Number:" << 1 << std::ends;
	m_App->VMACreateDeviceBuffer(
		m_SplatBufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[1],
		m_Allocation[1],
		splatTxt.str());

	m_BufferInfo[0].buffer = m_Buffers[0];
	m_BufferInfo[0].offset = 0;
	m_BufferInfo[0].range = m_BufSize;

	m_BufferInfo[1].buffer = m_Buffers[1];
	m_BufferInfo[1].offset = 0;
	m_BufferInfo[1].range = m_SplatBufSize;

	m_DescriptorWrite[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[0].dstBinding = m_BindPoint;
	m_DescriptorWrite[0].dstArrayElement = 0;
	m_DescriptorWrite[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_DescriptorWrite[0].descriptorCount = 1;
	m_DescriptorWrite[0].pBufferInfo = &m_BufferInfo[0];

	m_DescriptorWrite[1].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[1].dstBinding = m_BindPoint + 1u;
	m_DescriptorWrite[1].dstArrayElement = 0;
	m_DescriptorWrite[1].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_DescriptorWrite[1].descriptorCount = 1;
	m_DescriptorWrite[1].pBufferInfo = &m_BufferInfo[1];

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		m_LightMap.data(),
		m_Allocation[0],
		0,
		m_BufSize);

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		m_Splats.data(),
		m_Allocation[1],
		0,
		m_SplatBufSize);
}

void ResourceLightingReflectingWall::CreateLayout()
{
	m_LayoutBinding.resize(2);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;

	m_LayoutBinding[1].binding = m_BindPoint + 1u;
	m_LayoutBinding[1].descriptorCount = 1;
	m_LayoutBinding[1].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[1].pImmutableSamplers = nullptr;
	m_LayoutBinding[1].stageFlags = VK_SHADER_STAGE_ALL;
}

void ResourceLightingReflectingWall::InitializeLightMap(
	const glm::vec4& initialSurfaceColor)
{
	for (ReflectingWallLightMapCell& cell : m_LightMap)
	{
		cell.light = initialSurfaceColor;
	}

	if (!m_Allocation.empty() && m_BufSize > 0u)
	{
		vmaCopyMemoryToAllocation(
			m_App->m_vmaAllocator,
			m_LightMap.data(),
			m_Allocation[0],
			0,
			m_BufSize);
	}
}

void ResourceLightingReflectingWall::AppendSurface(
	uint32_t surfaceID,
	uint32_t materialID,
	const glm::vec4& initialSurfaceColor,
	uint32_t rectangleUSegments,
	uint32_t rectangleVSegments,
	std::vector<LightingSurfaceVertex>& surfaceVertices,
	std::vector<uint32_t>& surfaceIndices,
	uint32_t& emittedVertexID)
{
	InitializeLightMap(initialSurfaceColor);

	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;
	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	config_setting_t* segment = nullptr;
	for (int index = 0; segmentList != nullptr && index < segmentCount; ++index)
	{
		config_setting_t* candidate = CfgTst->GetSubStructAddress(segmentList, index);
		if (candidate == nullptr || config_setting_length(candidate) < 15)
			continue;
		uint32_t wallFlag =
			static_cast<uint32_t>(config_setting_get_float_elem(candidate, 14));
		if (wallFlag == surfaceID)
		{
			segment = candidate;
			break;
		}
	}

	if (segment == nullptr)
	{
		std::ostringstream errtxt;
		errtxt << "No rectangle_wall_segments entry for reflecting wall lighting surface "
			<< surfaceID << std::ends;
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

	uint32_t baseVertex = static_cast<uint32_t>(surfaceVertices.size());
	for (uint32_t uIndex = 0u; uIndex <= rectangleUSegments; ++uIndex)
	{
		float uCoord = uLength * static_cast<float>(uIndex) /
			static_cast<float>(rectangleUSegments);
		for (uint32_t vIndex = 0u; vIndex <= rectangleVSegments; ++vIndex)
		{
			float vCoord = vLength * static_cast<float>(vIndex) /
				static_cast<float>(rectangleVSegments);
			glm::vec3 position = origin + uAxis * uCoord + vAxis * vCoord;
			glm::vec2 uv(
				uLength <= 0.0f ? 0.0f : uCoord / uLength,
				vLength <= 0.0f ? 0.0f : vCoord / vLength);
			AppendSurfaceVertex(
				position,
				normal,
				uv,
				BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
				surfaceID,
				materialID,
				initialSurfaceColor,
				glm::vec4(1.0f),
				surfaceVertices,
				emittedVertexID);
		}
	}

	uint32_t rowStride = rectangleVSegments + 1u;
	for (uint32_t uIndex = 0u; uIndex < rectangleUSegments; ++uIndex)
	{
		for (uint32_t vIndex = 0u; vIndex < rectangleVSegments; ++vIndex)
		{
			uint32_t p00 = baseVertex + uIndex * rowStride + vIndex;
			uint32_t p10 = baseVertex + (uIndex + 1u) * rowStride + vIndex;
			uint32_t p11 = baseVertex + (uIndex + 1u) * rowStride + vIndex + 1u;
			uint32_t p01 = baseVertex + uIndex * rowStride + vIndex + 1u;

			surfaceIndices.push_back(p00);
			surfaceIndices.push_back(p10);
			surfaceIndices.push_back(p11);
			surfaceIndices.push_back(p00);
			surfaceIndices.push_back(p11);
			surfaceIndices.push_back(p01);
		}
	}
}

VkVertexInputBindingDescription* ResourceLightingReflectingWall::GetBindingDescription()
{
	m_BindingDescription.binding = 0;
	m_BindingDescription.stride = sizeof(ReflectingWallPhotonSplat);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	return &m_BindingDescription;
}

std::vector<VkVertexInputAttributeDescription>*
ResourceLightingReflectingWall::GetAttributeDescriptions()
{
	m_AttributeDescriptions.clear();

	VkVertexInputAttributeDescription ad{};
	ad.binding = 0;
	ad.location = 0;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(ReflectingWallPhotonSplat, pos_radius);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 1;
	ad.offset = offsetof(ReflectingWallPhotonSplat, color);
	m_AttributeDescriptions.push_back(ad);

	return &m_AttributeDescriptions;
}
