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


#ifndef DRAWOBJ_HPP
#define DRAWOBJ_HPP

class DrawObj : public BaseObj
{
    public:
		std::vector<Resource*> m_Graphicslst;
		std::vector<Resource*> m_Computelst;
		CommandObj* m_ComputeCommandObj;
		CommandObj* m_GraphicsCommandObj;
		CommandPoolObj* m_CPL= {};
	SwapChainObj* 						m_SCO{};
	std::vector<ResourceContainerObj*>	m_RCO{};
	std::vector<PipelineObj*>			m_GPO{};
	RenderPassObj*						m_RPO{};
	FrameBufferObj*						m_FBO = {};
	SyncObj* m_SO = {};
	


	virtual void SaveImage(uint32_t ImgNum){};
    virtual void DrawFrame()=0; 
	void Create(CommandPoolObj* CPL,
		SwapChainObj* SCO,
		RenderPassObj* RPO,
		FrameBufferObj* FBO,
		SyncObj* SO);
	
	DrawObj(std::string Name,VulkanObj* App ) : BaseObj(Name,0,App ){};
	
								

    void Cleanup(){
       
    };
	
};
#endif