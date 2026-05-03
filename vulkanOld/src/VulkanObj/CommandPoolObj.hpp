/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/CommandObj.hpp $
% $Id: CommandObj.hpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef COMMANDPOOLOBJ_HPP
#define COMMANDPOOLOBJ_HPP

class SwapChainObj;
class RenderPassObj;
class FrameBufferObj;
class PipelineObj;
class CommandPoolObj : public BaseObj {
public:

	PhysDevObj* m_QA;
	SwapChainObj* m_SCO = nullptr;
	RenderPassObj* m_RPO = nullptr;
	FrameBufferObj* m_FBO = nullptr;

	std::vector<CommandObj*> m_CPO;

	VkCommandPool                   m_CommandPool = {};
	void SetCommandPool(VkCommandPool CommandPool)
	{
		m_CommandPool = CommandPool;
	};

	VkCommandPool                   m_TransferCommandPool = {};
	void SetTransferCommandPool(VkCommandPool CommandPool)
	{
		m_TransferCommandPool = CommandPool;
	};



	CommandPoolObj(VulkanObj* App, std::string Name, uint32_t Type = 0) :
		BaseObj(Name, Type, App) {};

	void Create(PhysDevObj* QA, SwapChainObj* SCO,
		RenderPassObj* RPO,
		FrameBufferObj* FBO,
		std::vector<CommandObj*> CPO);

	virtual void CreateCommandPool();
	virtual void CreateCommandBuffers( );

	void Cleanup();
	CommandObj* GetCommandObjByName(std::string Name)
	{

		for (uint32_t ii = 0; ii < m_CPO.size(); ii++)
		{
			if (m_CPO[ii]->m_Name == Name)
				return m_CPO[ii];
		}
		std::string errtxt = "ResourceContainer::GetResourceName getDescriptorResourceName Failed on :" + Name;
		throw std::runtime_error(errtxt.c_str());
	}
	
};
#endif