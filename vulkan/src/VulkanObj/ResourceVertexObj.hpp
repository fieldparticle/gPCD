/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.hpp $
% $Id: ResourceVertex.hpp 28 2023-05-03 19:30:42Z jb $
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
#ifndef RESOURCE_VERTEXOBJ_HPP
#define RESOURCE_VERTEXOBJ_HPP
struct CartVert {
	glm::vec4 pos;
	glm::vec4 color;
};
class ResourceVertexParticle;
class ResourceVertexObj : public Resource
{
    public:

		std::vector<CartVert> m_Axes;
		std::string m_FileName;
		std::vector<glm::vec3> m_vtemp;
		
		virtual void GetShaderMem() {};
		//vcb::Mesh                                m_Model;
		ResourceVertexParticle* m_ParticleVert{};
		std::vector<CartVert> m_Verts{};
		std::vector<glm::vec2> m_UVS{};
		std::vector<glm::vec3> m_Normals{};
		ResourceVertexObj(VulkanObj *App, std::string Name):
					Resource(App, Name,VBW_TYPE_VERTEX_BUFFER)
				{
			m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
				};
		void MakeAxes(uint32_t sidelen);
	
	virtual void Create(uint32_t BindPoint, ResourceVertexParticle* PartVert);
	virtual void Create(uint32_t BindPoint);
	
	//============================================================
	// Virtual
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions();
	VkVertexInputBindingDescription* GetBindingDescription();

	void PullMem(uint32_t currentBuffer) {};
	virtual void PushMem(uint32_t currentBuffer) {};
	void Cleanup() {


		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[0], m_Allocation[ii]);
	}
	virtual void UpdateMem() {};
	

};
#endif