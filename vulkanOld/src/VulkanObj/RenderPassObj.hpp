/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/RenderPassObj.hpp $
% $Id: RenderPassObj.hpp 31 2023-06-12 20:17:58Z jb $
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

#ifndef RENDERPASSOBJ_HPP
#define RENDERPASSOBJ_HPP

class RenderPass;
class  RenderPassObj : public BaseObj
{
    public:
        std::vector<Resource*> m_SubPassList;
        std::vector<VkDescriptorImageInfo> m_DescriptorImageInfo{};

    SwapChainObj*	m_SCO={};	
    VkRenderPass 	m_RenderPass={};
    VkRenderPass GetRenderPass()
    {
        return m_RenderPass;
    }
    std::vector<ImageObject*>      m_IMO;
    RenderPassObj(VulkanObj *App, std::string Name) : 
        BaseObj(Name,0,App){};

    virtual void createRenderPass()=0;
    virtual void Create(SwapChainObj* SCO,std::vector<ImageObject*> IMO );
    virtual void Create(SwapChainObj* SCO, std::vector<ImageObject*> IMO,  std::vector<Resource*> SubPassItem);
    virtual void Create(SwapChainObj* SCO) ;

    void Cleanup();

   

};
#endif