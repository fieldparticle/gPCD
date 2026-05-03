/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/SyncObj.hpp $
% $Id: SyncObj.hpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef SYNCOBJ_HPP
#define SYNCOBJ_HPP


typedef struct Semdef 
{
		std::string name;
		std::vector<VkSemaphore> semvec;	
		std::vector<VkPipelineStageFlags> pipeStage;
} semdef;	

typedef struct Fencedef 
{
		std::string name;
		std::vector<VkFence> fencevec;
	
}fencedef;	
class SwapChainObj;
class SyncObj : public BaseObj
{
public:
	std::vector<semdef>					m_WaitSemaphores;
	std::vector<semdef>					m_SigSemaphores;
	std::vector<fencedef>				m_Fences;
	
	std::vector<VkSemaphore>			m_ary_waitSem;
	std::vector<VkPipelineStageFlags> 	m_ary_waitPSF;
	std::vector<VkSemaphore>			m_ary_signalSem;
	std::vector<VkFence>				m_ary_fences;

	
	void AddSignalSemaphore(std::string Name);
	void AddWaitSemaphore(std::string Name, VkPipelineStageFlags PipeStage);
	void AddFence(std::string Name);

	void Create(uint32_t BindPoint) {}
	void Create()
	{
		m_thisFramesBuffered = m_App->m_FramesBuffered;
	};


	std::vector <VkSemaphore> 			GetWaitSemaphores(uint32_t FrameNum);
	std::vector <VkPipelineStageFlags> 	GetWaitPipeStages(uint32_t FrameNum);
	std::vector <VkSemaphore>			GetSignalSemaphores(uint32_t FrameNum);
	std::vector <VkFence>				GetFences(uint32_t FrameNum);
	VkFence* gf(uint32_t Num, uint32_t FrameNum);
	VkSemaphore* gws(uint32_t Num, uint32_t FrameNum);
	VkSemaphore* gsn(uint32_t Num, uint32_t FrameNum);

	VkSemaphore* GetWaitSemaphore(std::string Name, uint32_t FrameNum);
	VkFence* GetFence(std::string Name, uint32_t FrameNum);
	VkSemaphore* GetSignalSemaphore(std::string Name, uint32_t FrameNum);

	SyncObj(VulkanObj* App, std::string Name) : BaseObj(Name,0,App){};
	
	
	void Cleanup();
	
};
#endif