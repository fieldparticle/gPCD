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
#ifndef RESOURCEVERTEXPARTICLE_HPP
#define RESOURCEVERTEXPARTICLE_HPP

class ResourceVertexParticle : public ResourceVertexObj
{
    public:
		uint32_t				m_MaxColls = 0;
		float					m_SideLength = 0;
		float					m_Radius = 0.2f;
		uint32_t				BoundaryParticleLimit = 0;
		std::vector<Particle>	m_Particles;
		uint32_t				m_NumParticles = 0;

		ResourceVertexParticle(VulkanObj *App, std::string Name):
					ResourceVertexObj(App, Name)
				{
					m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
				};
		virtual void AskObject(uint32_t AnyNumber) {};
		float CalcSpeedLimit(float max_vel, float radius);
	virtual void Create(uint32_t BindPoint);
	uint32_t CalcSideLength(size_t PartPerCell);
	void CreateLayout();
	
	//============================================================
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions();
	VkVertexInputBindingDescription* GetBindingDescription();
	
	void PullMem(uint32_t currentBuffer) {};
	virtual void PushMem(uint32_t currentBuffer){};
	
	void Cleanup()
	{

		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}
	

};
#endif