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
#ifndef RESOURCEATOMICCOMPUTE_HPP
#define RESOURCEATOMICCOMPUTE_HPP
struct Collision
{
	uint32_t CollisionCount;
	uint32_t numParticles;
	uint32_t vnumParticles;
	uint32_t holdPidx;
};
class ResourceAtomicCompute : public Resource
{

public:
	Collision				m_collisionStruct = {};
	float					m_PositionInc = 0.0;
	std::vector<Particle>	m_Particles;
	uint32_t				m_NumParticles = 0;
	bool					m_isInit = false;
	uint32_t				m_ReportCompFramesLessThan=0;
	PerfObj*				m_PerfObj;

	bool InitFlag = false;
	ResourceAtomicCompute(VulkanObj* App, std::string Name) :
		Resource(App, Name, VBW_TYPE_ATOMIC)
	{
		
		m_VkType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	};
		
	void createBuffers();
	void Create(uint32_t BindPoint, PerfObj* perfObj);


	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions();
	VkVertexInputBindingDescription* GetBindingDescription();
	
	

	virtual void PushMem(uint32_t currentBuffer);
	virtual void PullMem(uint32_t currentBuffer);
	

	
	void createLayout();
	void Cleanup()
	{
		for (size_t ii = 0; ii < m_Allocation.size(); ii++)
			vmaDestroyBuffer(m_App->m_vmaAllocator, m_Buffers[ii], m_Allocation[ii]);
	}

	virtual void AskObject(uint32_t AnyNumber);

};


#endif