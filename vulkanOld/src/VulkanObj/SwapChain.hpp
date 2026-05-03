/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/SwapChain.hpp $
% $Id: SwapChain.hpp 31 2023-06-12 20:17:58Z jb $
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
#ifndef SWAPCHAIN_HPP
#define SWAPCHAIN_HPP
class PhysDevObj;
class SwapChain : public SwapChainObj
{
    public:
    
		

	
    SwapChain(VulkanObj *App, std::string Name) :
		SwapChainObj(App,Name){};
    VkImageView CreateSwapImageView(VkImage Image, VkFormat Format);
	VkExtent2D ChooseSwapExtent(const VkSurfaceCapabilitiesKHR& Capabilities) ;
    VkSurfaceFormatKHR ChooseSwapSurfaceFormat(
		const std::vector<VkSurfaceFormatKHR>& AvailableFormats);
	VkPresentModeKHR ChooseSwapPresentMode(
		const std::vector<VkPresentModeKHR>& AvailablePresentModes) ;
    void CreateImageViews();
    //void RecreateSwapChain(FrameBuffer* FBO);
	void CreateSwapChain(); 
	//void SaveImage(uint32_t ImageNumber);
    virtual void Cleanup();
	
};
#endif