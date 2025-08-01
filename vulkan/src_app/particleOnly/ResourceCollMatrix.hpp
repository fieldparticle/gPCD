/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.hpp $
% $Id: DescriptorSSBO.hpp 28 2023-05-03 19:30:42Z jb $
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
#include "ParticleStruct.hpp"
#ifndef RESOURCECOLMATRIX_HPP
#define RESOURCECOLMATRIX_HPP
struct ColMatrix
{
	uint32_t *IndexArray;
} ;
class ResourceCollMatrix : public Resource
{

public:
	ColMatrix m_ColMat = {};
	uint32_t m_MaxCollArray = 0;
	uint32_t m_MaxLoc = 0;
	uint32_t m_CellArrayMax=0;
	ResourceVertexParticle* m_particle = {};
	
	
	
	std::vector<VkVertexInputAttributeDescription>*
		GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription*
		GetBindingDescription() { return {}; };
	
	
	virtual void PushMem(uint32_t currentBuffer);

	ResourceCollMatrix(VulkanObj* App, std::string Name) : 
		Resource(App,Name, VBW_DESCRIPTOR_TYPE_COLLMATRIX)
	{
		
		m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	};
	virtual void AskObject(uint32_t AnyNumber) {};
	void Create(uint32_t BindPoint, ResourceVertexParticle* particle);
	void PullMem(uint32_t currentBuffer){};
	void createLayout();
	void createBuffers();
	void Cleanup()
	{

		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}
	std::vector<VkVertexInputAttributeDescription>* getAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* getBindingDescription() { return {}; };

};
#endif

