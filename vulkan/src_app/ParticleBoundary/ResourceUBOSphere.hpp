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
#ifndef RESOURCESPHEREUBO_HPP
#define RESOURCESPHEREUBO_HPP



class ResourceVertexParticle;
class ResourceUBOSphere : public Resource
{

public:

	
	ResourceVertexParticle* m_Particle = {};
	
	VkDeviceSize m_bufferSize=0;
	
	
	bool InitFlag = false;
	ResourceUBOSphere(VulkanObj* App, std::string Name) : 
		Resource(App, Name, VBW_TYPE_UNIFORM_BUFFER)
	{
		m_VkType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
		
	};
	virtual void GetShaderMem() {};
	void Create(uint32_t BindPoint, SwapChainObj* SCO, ResourceVertexParticle* particle);
	void Create(uint32_t BindPoint, SwapChainObj* SCO);
	void createLayout();
	void createBuffers();
	void AskObject(uint32_t AnyNumber) {};
	void Cleanup()
	{
		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* GetBindingDescription() { return {}; };
	void PushMem(uint32_t currentBuffer);
	virtual void PullMem(uint32_t currentBuffer) {};


};


#endif