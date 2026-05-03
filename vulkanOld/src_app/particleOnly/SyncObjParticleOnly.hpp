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
#ifndef SYNCOBJPARTICLEONLY_HPP
#define SYNCOBJPARTICLEONLY_HPP
class SyncObjPO : public SyncObj
{
public:
	
	static const uint32_t W_IMAGAVAIL = 0;
	static const uint32_t W_COMPUTEFIN = 1;
	static const uint32_t S_RENDERFIN = 0;
	static const uint32_t F_INFLIGHT = 0;
	static const uint32_t F_CINFLIGHT = 1;

	

	SyncObjPO(VulkanObj* App, std::string Name) : SyncObj(App,Name){};
	
	
	
	
};
#endif