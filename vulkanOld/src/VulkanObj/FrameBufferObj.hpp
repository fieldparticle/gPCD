/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/FrameBuffer.hpp $
% $Id: FrameBuffer.hpp 31 2023-06-12 20:17:58Z jb $
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

#ifndef FRAMEBUFFFEROBJ_HPP
#define FRAMEBUFFFEROBJ_HPP

class VulkanApp;
class FrameBufferObj : public BaseObj{
    public:
    
    std::vector<VkFramebuffer> 	m_SwapChainFramebuffers;
    RenderPassObj*                 m_RPO;
    SwapChainObj*                  m_SCO;
    ImageObject*                m_IMO;

    FrameBufferObj(VulkanObj *App, std::string Name) : 
        BaseObj(Name, 0, App) {};


    virtual void Create(RenderPassObj* RPO,SwapChainObj* SCO) 
    {
        m_RPO = RPO;
        m_SCO = SCO;
        
        createFramebuffers();
	};
    virtual void Cleanup(){
       for (auto framebuffer : m_SwapChainFramebuffers) {
            vkDestroyFramebuffer(m_App->GetLogicalDevice(), framebuffer, nullptr);
       }
    };
 virtual void createFramebuffers()=0;
   


 //FrameBufferObj() = default;
};
#endif