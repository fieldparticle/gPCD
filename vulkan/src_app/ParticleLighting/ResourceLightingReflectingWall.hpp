/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#ifndef RESOURCELIGHTINGREFLECTINGWALL_HPP
#define RESOURCELIGHTINGREFLECTINGWALL_HPP

#include "ParticleLighting/LightingStructs.hpp"

#include <cstdint>
#include <string>
#include <vector>

class ResourceLightingReflectingWall : public Resource
{
public:
	static constexpr uint32_t SurfaceID = 3000u;

	ResourceLightingReflectingWall(VulkanObj* App, std::string Name) :
		Resource(App, Name, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER)
	{
		m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	};

	virtual void AskObject(uint32_t AnyNumber) {};
	void Create(uint32_t BindPoint);
	void CreateLayout();
	void InitializeLightMap(const glm::vec4& initialSurfaceColor);
	void AppendSurface(
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		uint32_t rectangleUSegments,
		uint32_t rectangleVSegments,
		std::vector<LightingSurfaceVertex>& surfaceVertices,
		std::vector<uint32_t>& surfaceIndices,
		uint32_t& emittedVertexID);

	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions();
	VkVertexInputBindingDescription* GetBindingDescription();
	uint32_t GetSplatCount() const
	{
		// Draw the fixed capacity; unused records carry zero alpha and discard.
		return m_SplatCount;
	}
	uint32_t GetSplatBufferIndex() const
	{
		return 1u;
	}
	void PullMem(uint32_t currentBuffer) {};
	virtual void PushMem(uint32_t currentBuffer) {};
	void ClearTempMemory()
	{
		m_LightMap.clear();
		std::vector<ReflectingWallLightMapCell> empty;
		m_LightMap.swap(empty);
		m_Splats.clear();
		std::vector<ReflectingWallPhotonSplat> emptySplats;
		m_Splats.swap(emptySplats);
	};
	void Cleanup()
	{
		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}

	uint32_t m_MapWidth = 1u;
	uint32_t m_MapHeight = 1u;
	uint32_t m_SplatCapacity = 0u;
	uint32_t m_SplatCount = 0u;
	uint64_t m_SplatBufSize = 0u;
	std::vector<ReflectingWallLightMapCell> m_LightMap;
	std::vector<ReflectingWallPhotonSplat> m_Splats;
};

#endif
