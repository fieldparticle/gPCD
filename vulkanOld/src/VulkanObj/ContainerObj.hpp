/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSet.hpp $
% $Id: DescriptorSet.hpp 28 2023-05-03 19:30:42Z jb $
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
#ifndef RESOURCECONTOBJ_HPP
#define RESOURCECONTOBJ_HPP

class Resource;
class VulkanObj;
class ResourceContainerObj : public BaseObj
{

public:
	uint32_t m_UBOSetCount = 0;
	uint32_t m_ATTSetCount = 0;

    
    //========================NEW ======================
	std::vector<VkDescriptorSetLayoutBinding> m_Bindings={};
	VkDescriptorSetLayout           m_ResourceSetLayout = {};
	std::vector<VkDescriptorSet> m_ResourceDescriptorSets;
	//========================NEW ======================

	virtual void AllocateDescriptorSets();
	virtual void CreateSetLayoutBindings();
	virtual void CreateDescriptorPool();
	virtual void UpdateDescriptorSets();
	void Create(std::vector<Resource*> DRList)
	{
		m_DRList = DRList;
		CreateSetLayoutBindings();
		CreateDescriptorPool();
		AllocateDescriptorSets();
		UpdateDescriptorSets();

	}
	VkDescriptorSetLayout* GetDescriptorSetLayout()
	{
		return &m_ResourceSetLayout;
	};


	std::vector<VkDescriptorPoolSize>			m_PoolSizes={};
	VkDescriptorPoolCreateInfo					m_PoolInfo={};
	VkDescriptorPool							m_ResourcePool = {};
    
	uint32_t	m_DescriptorCount=0;

	std::vector<VkDescriptorSet> GetResourceDescriptorSets()
	{
		return m_ResourceDescriptorSets;
	}
	std::vector<Resource*>			m_DRList;
    
	ResourceContainerObj(VulkanObj* App, std::string Name, 
		uint32_t Type= VBW_TYPE_GRAPHPIPE)
		: BaseObj(Name,Type, App){};

	std::vector<Resource*> GetResourceList()
	{
		return m_DRList;
	}

	VkDescriptorSet* GetResourceSets(uint32_t currentBuffer)
	{

		return &m_ResourceDescriptorSets[currentBuffer];

	}
	Resource* GetResourceName(std::string Name);
    Resource* GetResourceType(uint32_t m_VTType);
	void Cleanup() 
	{
        vkDestroyDescriptorPool(m_App->GetLogicalDevice(), m_ResourcePool, nullptr);
        vkDestroyDescriptorSetLayout(m_App->GetLogicalDevice(), m_ResourceSetLayout, nullptr);
    };

    
};
#endif