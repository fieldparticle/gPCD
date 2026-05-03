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

#ifndef RESOURCEINDEX_HPP
#define RESOURCEINDEX_HPP

const std::vector<uint16_t> indices = {
	0, 1, 3, 3, 1, 2,
	1, 5, 2, 2, 5, 6,
	5, 4, 6, 6, 4, 7,
	4, 0, 7, 7, 0, 3,
	3, 2, 7, 7, 2, 6,
	4, 5, 0, 0, 5, 1
};
class ResourceIndex : public Resource
{
    public:
   
	
		virtual void GetShaderMem() {};
	ResourceIndex(VulkanObj *App, std::string Name): 
		Resource(App, Name,VBW_TYPE_INDEX_BUFFER)
	{
    
        m_DescriptorSet = false;
        
    };
	virtual void Create();
	void Create(uint32_t BindPoint)
	{
		
	};
	void Create(std::vector<glm::vec3>* indices);
	
	void* GetBuffer(uint32_t bufNum, uint32_t ImageIndex, unsigned long& size);
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* GetBindingDescription() { return {}; };
	
	void CopyMem();
	virtual void UpdateMem() {};
    void Cleanup()
	{
       for (size_t i = 0; i < m_Buffers.size(); i++)
		{
			vkDestroyBuffer(m_App->GetLogicalDevice(),
				m_Buffers[i],
				nullptr);
			vkFreeMemory(m_App->GetLogicalDevice(),
				m_BuffersMemory[i],
				nullptr);

		}
        
    };

};

#endif