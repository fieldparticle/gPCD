/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/CommandPool.hpp $
% $Id: CommandPool.hpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef COMMANDOBJ_HPP
#define COMMANDOBJ_HPP
class CommandPoolObj;
class CommandObj : public BaseObj
{

public:
	uint32_t m_QueryCount					= 0;
	VkQueryPool m_PerfQueryPool				= VK_NULL_HANDLE;
	std::vector<uint64_t> mTimeQueryResults = {};
	double m_ExecutionTime					= 0.0;
	std::vector<PipelineObj*> m_PLO			= {};
	ResourceContainerObj* m_RCO				= {};
	CommandPoolObj* m_CPL					= {};
	SwapChainObj* m_SCO						= {};
	FrameBufferObj* m_FBO					= {};
	RenderPassObj* m_RPO					= {};
	bool	trace_on_flag = false;
	
	std::vector<VkCommandBuffer>    m_CommandBuffers = {};


	virtual void RecordCommands(uint32_t imageIndex,uint32_t CurrentBuffer)=0;
	CommandObj(VulkanObj* App, std::string Name) : BaseObj(Name,0,App){};
	virtual void Create(SwapChainObj* SCO,
		FrameBufferObj* FBO,
		RenderPassObj* RPO,
		ResourceContainerObj* RCO,
		std::vector<PipelineObj*> PLO);
	//void PreRecordCommands();
	void CreateCommandBuffers(CommandPoolObj* CPL);
	void Cleanup();
	void CreateQueryPool();
	void FetchRenderTimeResults(uint32_t CurrentBuffer);
	void SetTimeStamp(uint32_t currentBuffer);
	double GetExecutionTime();

};
#endif