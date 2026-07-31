/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#ifndef RESOURCELIGHTINGSURFACE_HPP
#define RESOURCELIGHTINGSURFACE_HPP

#include "ParticleLighting/LightingStructs.hpp"

class ResourceLightingSurface : public Resource
{
public:
	ResourceLightingSurface(VulkanObj* App, std::string Name) :
		Resource(App, Name, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER)
	{
		m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	};

	virtual void AskObject(uint32_t AnyNumber) {};
	virtual void Create(uint32_t BindPoint, Resource* particle);
	void CreateLayout();
	void LoadLightingSurfaceObjects();

	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions();
	VkVertexInputBindingDescription* GetBindingDescription();

	void PullMem(uint32_t currentBuffer) {};
	virtual void PushMem(uint32_t currentBuffer) {};
	void ClearTempMemory() {};
	void Cleanup()
	{
		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}

private:
	uint32_t SurfaceTypeID(const std::string& surfaceType);
	void LoadObjSurface(
		const std::string& objFile,
		const std::string& meshFile,
		uint32_t surfaceType,
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		uint32_t rectangleUSegments,
		uint32_t rectangleVSegments,
		uint32_t sphereLatSegments,
		uint32_t sphereLonSegments,
		uint32_t& emittedVertexID);
	void BuildRectangleSurface(
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		uint32_t rectangleUSegments,
		uint32_t rectangleVSegments,
		uint32_t& emittedVertexID);
	void BuildSphereSurface(
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		uint32_t sphereLatSegments,
		uint32_t sphereLonSegments,
		uint32_t& emittedVertexID);
	void AppendSurfaceVertex(
		const glm::vec3& position,
		const glm::vec3& normal,
		const glm::vec2& uv,
		uint32_t surfaceType,
		uint32_t surfaceID,
		uint32_t materialID,
		const glm::vec4& initialSurfaceColor,
		const glm::vec4& albedo,
		uint32_t& emittedVertexID);

	std::vector<LightingSurfaceVertex> m_SurfaceVertices;
	std::vector<uint32_t> m_SurfaceIndices;
};

#endif
