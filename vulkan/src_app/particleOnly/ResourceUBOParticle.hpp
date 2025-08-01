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
#ifndef RESOURCEPARTICLEUBO_HPP
#define RESOURCEPARTICLEUBO_HPP

class ResourceVertexParticle;
class ResourceParticleUBO : public Resource
{

public:
	ResourceVertexParticle* m_Particle;
	
	UniformBufferObject m_UBO={};
	bool m_done = false;
	float m_RotX = 0.0;
	float m_RotY = 0.0;
	float m_rRotX = 0.0;
	float m_rRotY = 0.0;
	float m_TranslateX=10.0;
	float m_TranslateY=10.0;
	float m_TranslateZ=0.0;
	float width = 800.0;
	float height = 800.0;

	bool InitFlag = false;
	ResourceParticleUBO(VulkanObj* App, std::string Name) : 
		Resource(App, Name, VBW_TYPE_UNIFORM_BUFFER)
	{
		m_VkType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
	};
	virtual void AskObject(uint32_t AnyNumber) {};
	
	void Create(uint32_t BindPoint, SwapChainObj* SCO, ResourceVertexParticle* particle);
	void Create(uint32_t BindPoint, SwapChainObj* SCO);
	void createLayout();
	void createBuffers();
	void PushMem(uint32_t currentBuffer);
	virtual void PullMem(uint32_t currentBuffer){};
	void Cleanup()
	{
		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* GetBindingDescription() { return {}; };
	void* GetBuffer(uint32_t bufNum, uint32_t ImageIndex, unsigned long& size);

};


#endif