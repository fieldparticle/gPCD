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
		uint32_t surfaceType,
		uint32_t surfaceID,
		uint32_t materialID,
		uint32_t& emittedVertexID);

	std::vector<LightingSurfaceVertex> m_SurfaceVertices;
};

#endif
