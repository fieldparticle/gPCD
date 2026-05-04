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
#ifndef COMMANDPOOLPARTICLESUB_HPP
#define COMMANDPOOLPARTICLESUB_HPP

class CommandPoolParticleSub : public CommandObj
{
public:

	const int PLO_PARTICLE = 0;
	const int PLO_BOUNDARY = 1;
	void RecordSubPassCube(uint32_t i, PipelineObj* pipeline);
	void RecordSubPassParticle(uint32_t i, PipelineObj* Pipeline);
	void CreateCBuffers();
	void CreateGBuffers();
	void RecordCCommandBuffer(uint32_t imageIndex);
	virtual void CreatePipeline()=0;
	virtual void CreateCommandPool();
	virtual void CreateCommandBuffers();

	CommandPoolParticleSub(VulkanObj* App, std::string Name) : CommandObj(App, Name){};

	void RecordGCommandBuffer(uint32_t ImageIndex, uint32_t currentFrame);
	



};
#endif