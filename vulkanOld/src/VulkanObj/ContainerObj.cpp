/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSet.cpp $
% $Id: DescriptorSet.cpp 28 2023-05-03 19:30:42Z jb $
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

#include "VulkanObj/VulkanApp.hpp"


void ResourceContainerObj::CreateSetLayoutBindings()
{
    VkDescriptorSetLayoutCreateInfo SetLayout{};

    for (uint32_t ii = 0; ii < m_DRList.size(); ii++)
    {
       // if (m_DRList[ii]->m_DescriptorSet == true)
        if (m_DRList[ii]->m_DescriptorWrite.size() > 0)
        {
            for (uint32_t ll = 0;
                ll < m_DRList[ii]->m_LayoutBinding.size(); ll++)
            {
                m_Bindings.push_back(m_DRList[ii]->m_LayoutBinding[ll]);
            }
        }

    }
    // Create layoutinfor for all layout bindings
    SetLayout.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;


    SetLayout.bindingCount = static_cast<uint32_t>(m_Bindings.size());
    SetLayout.pBindings = m_Bindings.data();

    if (vkCreateDescriptorSetLayout(m_App->GetLogicalDevice(),
        &SetLayout,
        nullptr,
        &m_ResourceSetLayout) != VK_SUCCESS)
    {
        throw std::runtime_error("ResourceContainerParticle::CreateDescriptorSetLayout failed to create Resource Set Layout.");
    }

    m_wkstr = m_Name + " Descriptor Layout ";
    m_App->NameObject(VK_OBJECT_TYPE_DESCRIPTOR_SET_LAYOUT, (uint64_t)m_ResourceSetLayout, m_wkstr.c_str());
};
// Create a descriptor pool from a VkDescriptorPoolCreateInfo.
// Each VkDescriptorPoolCreateInfo containes one or more
// VkDescriptorPoolSize assocaiated with only one type
// of descriptor type.
// 
//      typedef struct VkDescriptorPoolSize 
//      {
//          VkDescriptorType    type;
//              Type of descriptor uniform, image etc
//          uint32_t            descriptorCount;
//              How many of this type.
//      } VkDescriptorPoolSize;
// 
// VkDescriptorPoolCreateInfo 
// VkDescriptorPoolCreateFlags      flags;
// uint32_t                         poolSizeCount;
// VkDescriptorPoolSize*            pPoolSizes;
//      This is the number of pool sizes. Multiple poolsizes
//      Describe the types of descriptor set than can be allocated
// uint32_t                         maxSets;
//      This determines the maximum number of sets that can be allocated
// Rule: For multiple frames in flight use multiple sets with one type descriptor.
void ResourceContainerObj::CreateDescriptorPool()
{


    for (uint32_t ii = 0; ii < m_DRList.size(); ii++)
    {
        //if (m_DRList[ii]->m_DescriptorSet == true)
        for( uint32_t jj=0;jj<m_DRList[ii]->m_DescriptorWrite.size();jj++)
        {
            VkDescriptorPoolSize psz{};
            psz.type = m_DRList[ii]->m_VkType;
            psz.descriptorCount = m_App->m_FramesBuffered 
                * static_cast<uint32_t>(m_DRList[ii]->m_thisFramesBuffered);
            m_PoolSizes.push_back(psz);

        }
    }


    m_PoolInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    m_PoolInfo.poolSizeCount = static_cast<uint32_t>(m_PoolSizes.size());
    m_PoolInfo.pPoolSizes = m_PoolSizes.data();

    //Aside from the maximum number of individual descriptors that are available, 
    // we also need to specify the maximum number of descriptor sets that may 
    // be allocated.
    m_PoolInfo.maxSets = m_App->m_FramesBuffered;

    if (vkCreateDescriptorPool(m_App->GetLogicalDevice(),
        &m_PoolInfo, nullptr, &m_ResourcePool) != VK_SUCCESS)
    {
        throw std::runtime_error("ResourceContainer::CreateDescriptorPool failed to create descriptor pool.");
    }
    m_wkstr = m_Name + " Pool";
    m_App->NameObject(VK_OBJECT_TYPE_DESCRIPTOR_POOL, (uint64_t)m_ResourcePool,
        m_wkstr.c_str());

}
void ResourceContainerObj::AllocateDescriptorSets()
{

    // Allocate numswap VkDescriptorSetLayout
    std::vector<VkDescriptorSetLayout> layouts(m_App->m_FramesBuffered,
        m_ResourceSetLayout);
    // 
    VkDescriptorSetAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    allocInfo.descriptorPool = m_ResourcePool;
    // This is the number of sets that will be allocated 
    // - one per swap image in flight.
    allocInfo.descriptorSetCount = m_App->m_FramesBuffered;
    allocInfo.pSetLayouts = layouts.data();

    // std::vector<VkDescriptorSet>
    m_ResourceDescriptorSets.resize(m_App->m_FramesBuffered);


    if (vkAllocateDescriptorSets(m_App->GetLogicalDevice(),
        &allocInfo,
        m_ResourceDescriptorSets.data()) != VK_SUCCESS)
    {
        throw std::runtime_error("ResourceContainer::DescriptorSets() failed to allocate Descriptor Sets.");
    }

    //objtxt << m_DRList[ii]->m_Name.c_str() << " Subpass Descpt. "
        //<< nd << " of " << ii << std::ends;
    //m_App->NameObject(VK_OBJECT_TYPE_DESCRIPTOR_SET,
      //  (uint64_t)m_ResourceDescriptorSets[ii],
//        objtxt.str().c_str());

}
void ResourceContainerObj::UpdateDescriptorSets()
{
    // After allocating a spot in the
    std::vector<VkWriteDescriptorSet> descriptorWrites{};
    for (uint32_t j = 0; j < m_App->m_FramesBuffered; j++)
    {
        for (uint32_t ii = 0; ii < m_DRList.size(); ii++)
        {
            if (m_DRList[ii]->m_DescriptorWrite.size() != 0)
            {
                m_DRList[ii]->m_DescriptorWrite[0].dstSet= 
                    m_ResourceDescriptorSets[j];;
                descriptorWrites.push_back(m_DRList[ii]->m_DescriptorWrite[0]);
            }

        }

        if (descriptorWrites.size() > 0)
        {
            vkUpdateDescriptorSets(m_App->GetLogicalDevice(),
                static_cast<uint32_t>(descriptorWrites.size()),
                descriptorWrites.data(),
                0,
                nullptr);
        }
    }

}



Resource* ResourceContainerObj::GetResourceType(uint32_t Type)
{

    for (uint32_t ii = 0; ii < m_DRList.size(); ii++)
    {
        if (m_DRList[ii]->m_Type == Type)
            return m_DRList[ii];
    }
    std::string errtxt = "getDescriptorResourceType Failed on :";
    throw std::runtime_error(errtxt.c_str());
}
Resource* ResourceContainerObj::GetResourceName(std::string Name)
{

    for (uint32_t ii = 0; ii < m_DRList.size(); ii++)
    {
        if (m_DRList[ii]->m_Name == Name)
            return m_DRList[ii];
    }
    std::string errtxt = "ResourceContainer::GetResourceName getDescriptorResourceName Failed on :" + Name;
    throw std::runtime_error(errtxt.c_str());
}
