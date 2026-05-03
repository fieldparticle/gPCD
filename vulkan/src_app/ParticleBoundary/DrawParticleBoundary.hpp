/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/DrawObj.hpp $
% $Id: DrawObj.hpp 31 2023-06-12 20:17:58Z jb $
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


#ifndef DRAWPARTICLEBOUNDARY_HPP
#define DRAWPARTICLEBOUNDARY_HPP

class DrawParticleBoundary : public DrawObj
{
    public:
    
	std::vector<Resource*> m_Graphicslst;
	std::vector<Resource*> m_Computelst;
	CommandObj* m_ComputeCommandObj;
	CommandObj* m_GraphicsCommandObj;


    virtual void DrawFrame(); 
	void Create(CommandPoolObj* CPL,
		SwapChainObj* SCO,
		RenderPassObj* RPO,
		FrameBufferObj* FBO,
		SyncObj* SO);


	
	DrawParticleBoundary(VulkanObj* App, std::string Name) : DrawObj(Name,App ){};
	uint32_t currentBuffer = 0;

    void Cleanup(){
       
    };
	
};
#endif