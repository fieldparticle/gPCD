/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/Resource.hpp $
% $Id: Resource.hpp 31 2023-06-12 20:17:58Z jb $
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
%*$Revision: 31 $
%*
%*
%******************************************************************/

#ifndef RESOURCE_HPP
#define RESOURCE_HPP


const enum DesType;
class BaseObj;
class CommandObj;
class CommandPoolObj;
class ImageObject;
typedef struct uniformBufferObject {
	alignas(16) glm::mat4 model;
	alignas(16) glm::mat4 view;
	alignas(16) glm::mat4 proj;
} UniformBufferObject;

class Resource : public BaseObj
{

public:

	
	//============================================================
	//VK_TYPE_SUBPASS
	VkAttachmentDescription m_ColorAttachment{};
	VkAttachmentReference m_ColorAttachmentRef{};
	VkAttachmentDescription m_DepthAttachment{};
	VkAttachmentReference m_DepthAttachmentRef{};
	VkVertexInputBindingDescription m_BindingDescription{};
	std::vector<VkVertexInputAttributeDescription> m_AttributeDescriptions{};
	uint32_t m_BindingCount = 0;
	uint32_t m_DesWriteCount = 0;
	uint32_t m_SubPassNum = 0;
	uint32_t m_TotSubPass = 0;
	uint32_t m_MaxSets = 0;
	CommandObj* m_CPO = {};
	CommandPoolObj* m_CPL = {};
	bool m_InitFlag = false;
	std::vector<VkSubpassDescription> m_Subpass{};
	SwapChainObj* m_SCO = {};
	std::vector<ImageObject*> m_IMO = {};
	

	//============================================================
	// Variables
	uint32_t 							m_BindPoint = 0;
	std::vector<void*>					m_MappedData = {};
	std::vector<VkBuffer>           	m_Buffers={};
	std::vector<VkDeviceMemory>     	m_BuffersMemory={};
	VkBuffer							m_StagingBuffer = nullptr;
	VkDeviceMemory						m_StagingBufferMemory = nullptr;
	std::vector < VmaAllocationInfo> m_AllocationInfo = {};
	std::vector < VmaAllocation> m_Allocation = {};
	std::vector <VkDescriptorSetLayoutBinding>	m_LayoutBinding = {};
	std::vector <VkDescriptorSetLayoutBinding> LayoutBinding()
	{
		return m_LayoutBinding;
	}
	//============================================================
	// Member Functions
	Resource(VulkanObj* App, std::string Name, uint32_t Type) 
		: BaseObj(Name, Type, App){ };
	Resource() {};
	
	//============================================================
	// Virtual
	
	//============================================================
	// Pure Virtual
	
	virtual std::vector<VkVertexInputAttributeDescription>*
		GetAttributeDescriptions() = 0;


	virtual VkVertexInputBindingDescription*
		GetBindingDescription() = 0;
	// Update mem gets memory from the device
	virtual void PushMem(uint32_t currentBuffer) = 0;
	// Copy meme copies memory to the device
	virtual void PullMem(uint32_t currentBuffer) = 0;

	//============================================================
		
   
	std::vector<void*>              	m_BuffersMapped={};
	uint32_t							m_BufSize=0;
	void*								m_data=nullptr;
	uint32_t							m_NumElements=0;
	VkDescriptorType					m_VkType = {};
	std::string							m_PiplineName = {};
	VkPushConstantRange						m_PushConstant{};
	std::vector<VkWriteDescriptorSet>		m_DescriptorWrite = {};
	std::vector<VkDescriptorBufferInfo>		m_BufferInfo = {};
	std::vector< VkDescriptorImageInfo>		m_ImageInfos{};

	void CheckBindPoint(uint32_t BindPoint);
	std::vector <VkWriteDescriptorSet> GetWriteDescriptorSet()
	{
		return m_DescriptorWrite;
			
	}
	VkDescriptorSetLayoutBinding* GetLayoutBinding(uint32_t Index)
	{

		return &m_LayoutBinding[Index];
	}
	virtual void Cleanup() {};
	virtual void AskObject(uint32_t AnyNumber) = 0;
	
};

#endif