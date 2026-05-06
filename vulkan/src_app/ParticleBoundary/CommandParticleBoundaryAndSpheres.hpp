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
#ifndef COMMANDPARTICLEGRAPHICSSUB_HPP
#define COMMANDPARTICLEBOUNDARYANDSPHERES_HPP

class CommandParticleBoundaryAndSpheres : public CommandObj
{
public:
	virtual void Create(SwapChainObj* SCO,
		FrameBufferObj* FBO,
		RenderPassObj* RPO,
		ResourceContainerObj* RCO,
		std::vector<PipelineObj*> PLO);
	uint32_t m_BoundarySubPass = 0;
	uint32_t m_ParticleSubPass = 0;
	virtual void RecordCommands(uint32_t currentBuffer,uint32_t imageIndex);
	
	CommandParticleBoundaryAndSpheres(VulkanObj* App, std::string Name) : CommandObj(App, Name){};
	void RecordSubPassCube(uint32_t imageindex, uint32_t currentBuffer);
	void RecordSubPassParticle(uint32_t imageindex, uint32_t currentBuffer);
};
#endif