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

#ifndef RESOURCELOCKMATRIX_HPP
#define RESOURCELOCKMATRIX_HPP

class ResourceLockMatrix : public Resource
{

public:
	const uint32_t npos = 4294967294;
	struct lckBuf {
		uint32_t loc;
	};
	struct rptvec {
		uint32_t LocationIndex;
		glm::uvec3 LocationArry;
	};

	ResourceVertexParticle* m_particle = {};
	uint32_t cc=800;
	uint32_t rr=800;
	uint32_t m_MaxLoc=0;

	std::vector<rptvec> m_RptVec = {};
	void WriteShaderHeader();
	
	std::vector<VkVertexInputAttributeDescription>*
		GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription*
		GetBindingDescription() { return {}; };
	virtual void AskObject(uint32_t AnyNumber) {};
	uint32_t ArrayToIndex(uint32_t x, uint32_t y, uint32_t z, uint32_t len);
	void IndexToArray(uint32_t index, uint32_t len, uint32_t* ary);
	void IndexLockArray();

	static bool sortByLoc(rptvec lhs, rptvec rhs);

	virtual void PushMem(uint32_t currentBuffer);
	ResourceLockMatrix(VulkanObj* App, std::string Name) : 
		Resource(App,Name, VBW_DESCRIPTOR_TYPE_COLLMATRIX)
	{
		m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	};
	
	void Create(uint32_t BindPoint, ResourceVertexParticle* particle);
	void PullMem(uint32_t currentBuffer){};
	void createLayout();
	void Cleanup()
	{

		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}
	void CreateBuffers();
	std::vector<VkVertexInputAttributeDescription>* getAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* getBindingDescription() { return {}; };

};


#endif