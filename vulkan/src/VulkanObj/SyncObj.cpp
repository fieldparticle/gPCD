/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/SyncObj.cpp $
% $Id: SyncObj.cpp 31 2023-06-12 20:17:58Z jb $
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

#include "VulkanObj/VulkanApp.hpp"

void SyncObj::AddFence(std::string Name)
{
	
	fencedef fce{};
	fce.name = Name;
	fce.fencevec.resize(m_thisFramesBuffered);
	
	VkFenceCreateInfo fenceInfo{};
	//Before we can proceed, there is a slight hiccup in 
	// our design.On the first frame we call drawFrame(), 
	// which immediately waits on inFlightFence to be 
	// signaled.inFlightFence is only signaled after a 
	// frame has finished rendering, yet since this is 
	// the first frame, there are no previous frames 
	// in which to signal the fence!Thus vkWaitForFences() 
	// blocks indefinitely, waiting on something which 
	// will never happen. Create the fence in the signaled
	//  state, so that the first call to vkWaitForFences() 
	// returns immediately 
	fenceInfo.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
	fenceInfo.flags = VK_FENCE_CREATE_SIGNALED_BIT;

	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		if(vkCreateFence(m_App->GetLogicalDevice(), 
			&fenceInfo, nullptr, 
			&fce.fencevec[i]) != VK_SUCCESS)
			{
			std::string str = "AddFence() could not add:" + Name;
			throw std::runtime_error(str.c_str());
			}
		
		m_App->NameObject(VK_OBJECT_TYPE_FENCE, (uint64_t)fce.fencevec[i], Name.c_str());
	}
	
	m_Fences.push_back(fce);
}

// Signal Semaphores are not asscociated with pipline statge
void SyncObj::AddSignalSemaphore(std::string Name)
{
	
	semdef sph{};
	sph.name = Name;
	sph.semvec.resize(m_thisFramesBuffered);
	
	VkSemaphoreCreateInfo semaphoreInfo{};
	semaphoreInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		if (vkCreateSemaphore(m_App->GetLogicalDevice(), 
			&semaphoreInfo, nullptr, &sph.semvec[i]) != VK_SUCCESS)
		{
			std::string str = "AddSemaphore() could not add:" + Name;
			throw std::runtime_error(str.c_str());
		}
		m_App->NameObject(VK_OBJECT_TYPE_SEMAPHORE, (uint64_t)sph.semvec[i], Name.c_str());
	}
	
	m_SigSemaphores.push_back(sph);	
	
}

void SyncObj::AddWaitSemaphore(std::string Name, VkPipelineStageFlags PipeStage)
{
	
	semdef sph{};
	sph.name = Name;
	sph.semvec.resize(m_thisFramesBuffered);
	sph.pipeStage.resize(m_thisFramesBuffered);
	VkSemaphoreCreateInfo semaphoreInfo{};
	semaphoreInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
	for (size_t i = 0; i < m_thisFramesBuffered; i++)
	{
		if (vkCreateSemaphore(m_App->GetLogicalDevice(), 
			&semaphoreInfo, nullptr, &sph.semvec[i]) != VK_SUCCESS)
		{
			std::string str = "AddSemaphore() could not add:" + Name;
			throw std::runtime_error(str.c_str());
		}

		m_App->NameObject(VK_OBJECT_TYPE_SEMAPHORE, (uint64_t)sph.semvec[i], Name.c_str());
		sph.pipeStage[i] = PipeStage;
	}
	m_WaitSemaphores.push_back(sph);	
	
}
VkFence* SyncObj::gf(uint32_t Num, uint32_t FrameNum)
{
		return &m_Fences[Num].fencevec[FrameNum];
	
}
VkFence* SyncObj::GetFence(std::string Name, uint32_t FrameNum)
{
	for (size_t ii = 0; ii< m_Fences.size();ii++)
	{
		if(m_Fences[ii].name == Name)
		{
			return &m_Fences[ii].fencevec[FrameNum];
		}
	}
	std::string str = "GetFence() could not find:" + Name;
	throw std::runtime_error(str.c_str());
	
}
VkSemaphore* SyncObj::GetWaitSemaphore(std::string Name, uint32_t FrameNum)
{
	for (size_t ii = 0;ii<m_WaitSemaphores.size();ii++)
	{
		if(m_WaitSemaphores[ii].name == Name)
		{
			return &m_WaitSemaphores[ii].semvec[FrameNum];
		}
	}
	std::string str = "GetWaitSemaphore() could not find:" + Name;
	throw std::runtime_error(str.c_str());
	
}
VkSemaphore* SyncObj::gws(uint32_t Num, uint32_t FrameNum)
{
	return &m_WaitSemaphores[Num].semvec[FrameNum];
}

VkSemaphore* SyncObj::GetSignalSemaphore(std::string Name, uint32_t FrameNum)
{
	for (size_t ii = 0;ii<m_SigSemaphores.size();ii++)
	{
		if(m_SigSemaphores[ii].name == Name)
		{
			return &m_SigSemaphores[ii].semvec[FrameNum];
		}
	}
	std::string str = "GetSignalSemaphore() could not find:" + Name;
	throw std::runtime_error(str.c_str());
	
}
VkSemaphore* SyncObj::gsn(uint32_t Num, uint32_t FrameNum)
{
	return &m_SigSemaphores[Num].semvec[FrameNum];
	
}
std::vector < VkSemaphore> SyncObj::GetWaitSemaphores(uint32_t FrameNum)
{
	m_ary_waitSem.clear();
	for (size_t ii = 0;ii<m_WaitSemaphores.size();ii++)
	{
		m_ary_waitSem.push_back(m_WaitSemaphores[ii].semvec[FrameNum]);
	}
	return m_ary_waitSem;
}


std::vector < VkPipelineStageFlags> SyncObj::GetWaitPipeStages(uint32_t FrameNum)
{
	
	m_ary_waitPSF.clear();
	for (size_t ii = 0;ii<m_WaitSemaphores.size(); ii++)
	{
		m_ary_waitPSF.push_back(m_WaitSemaphores[ii].pipeStage[FrameNum]);
	}
	return m_ary_waitPSF;
	
}

std::vector < VkSemaphore> SyncObj::GetSignalSemaphores(uint32_t FrameNum)
{
	m_ary_signalSem.clear();
	for (size_t ii = 0;ii<m_SigSemaphores.size(); ii++)
	{
		m_ary_signalSem.push_back(m_SigSemaphores[ii].semvec[FrameNum]);
	}
	return m_ary_signalSem;
	
}
std::vector < VkFence> SyncObj::GetFences(uint32_t FrameNum)
{
	m_ary_fences.clear();
	for (size_t ii = 0;ii<m_Fences.size(); ii++)
	{
		m_ary_fences.push_back(m_Fences[ii].fencevec[FrameNum]);
	}
	return m_ary_fences;
	
}

void SyncObj::Cleanup()
{
	for (size_t ii = 0;ii<m_WaitSemaphores.size(); ii++)
	{
		for (size_t n = 0; n < m_thisFramesBuffered; n++) 
		{
			vkDestroySemaphore(m_App->GetLogicalDevice(), m_WaitSemaphores[ii].semvec[n], nullptr);
		}
	}
	
	for (size_t ii = 0;ii<m_SigSemaphores.size();ii++)
	{
		for (size_t n = 0; n < m_thisFramesBuffered; n++)
		{
			vkDestroySemaphore(m_App->GetLogicalDevice(), m_SigSemaphores[ii].semvec[n], nullptr);
		}
	}
	for (size_t ii = 0;ii<m_Fences.size();ii++)
	{
		for (size_t n = 0; n < m_thisFramesBuffered; n++)
		{
			vkDestroyFence(m_App->GetLogicalDevice(), m_Fences[ii].fencevec[n], nullptr);
		}
	}	
}