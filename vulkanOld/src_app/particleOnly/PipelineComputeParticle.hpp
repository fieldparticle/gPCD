/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/GraphicsPipeline.hpp $
% $Id: GraphicsPipeline.hpp 28 2023-05-03 19:30:42Z jb $
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

#ifndef PIPLINECOMPUTEPARTICLE_HPP
#define PIPLINECOMPUTEPARTICLE_HPP
class PipelineComputeParticle : public PipelineObj
{
    public:
		
		PipelineComputeParticle(VulkanObj* App, std::string Name):
			PipelineObj(App,Name, VBW_TYPE_COMPUTEPIPE)
		{
	
		};
		
		void CreatePipeline();
	
};

#endif