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
#ifndef RESOURCEGRAPHCONT_HPP
#define RESOURCEGRAPHCONT_HPP

class Resource;
class VulkanObj;
class ResourceGraphicsContainer : public ResourceContainerObj
{

public:
	//=====================NEW =========================
	
	

	//=====================NEW =========================

	ResourceGraphicsContainer(VulkanObj* App, std::string Name,
		uint32_t Type = VBW_TYPE_GRAPHPIPE)
		: ResourceContainerObj(App ,Name, Type ) {};
	 
	
	


    
};
#endif