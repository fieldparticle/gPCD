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
#ifndef SWAPCHAINOBJ_HPP
#define SWAPCHAINOBJ_HPP

class VulkanObj;
class SwapChainObj : public BaseObj
{
public:

	uint32_t					m_NumSwapImages = 0;
	VkSwapchainKHR 				m_SwapChain = {};
	std::vector<VkImage> 		m_SwapChainImages = {};
	VkFormat 					m_SwapChainImageFormat = {};
	VkExtent2D 					m_SwapChainExtent = {};
	std::vector<VkImageView> 	m_SwapChainImageViews = {};
	VkSurfaceFormatKHR			m_SurfaceFormat = {};

	uint32_t					m_SwapWidth = 0;
	uint32_t					m_SwapHeight = 0;
	uint32_t					m_SwapX = 0;
	uint32_t					m_SwapY = 0;

	PhysDevObj*					m_CO = {};



	SwapChainObj(VulkanObj* App, std::string Name) : BaseObj(Name, 0, App) {};
	void Create(PhysDevObj* CO)
	{
		m_CO = CO;
		CreateSwapChain();
		CreateImageViews();
		
	};

	VkFormat GetSwapChainImageFormat()
	{
		return m_SwapChainImageFormat;
	}
	void SetSwapChainImageFormat(VkFormat SwapChainImageFormat)
	{
		m_SwapChainImageFormat = SwapChainImageFormat;
	}
	VkExtent2D GetSwapExtent()
	{
		return m_SwapChainExtent;
	}
	void SetSwapExtent(VkExtent2D extent)
	{
		m_SwapChainExtent = extent;
	}
	void SetSwapHeight(uint32_t height)
	{
		m_SwapHeight = height;
	}

	uint32_t GetSwapHeight()
	{
		return m_SwapHeight;
	}
	void SetSwapWidth(uint32_t width)
	{
		m_SwapWidth = width;
	}

	uint32_t GetSwapX()
	{
		return m_SwapX;
	}
	uint32_t GetSwapY()
	{
		return m_SwapY;
	}
	uint32_t GetSwapWidth()
	{
		return m_SwapWidth;
	}
	VkSwapchainKHR GetSwapChain()
	{
		return m_SwapChain;
	}
	VkSurfaceFormatKHR GetSwapChainFormat()
	{
		return m_SurfaceFormat;
	}
	void SetSwapChainFormat(VkSurfaceFormatKHR SurfFormat)
	{
		m_SurfaceFormat = SurfFormat;
	}
	std::vector<VkImageView> GetImageViews()
	{
		return m_SwapChainImageViews;
	}

	uint32_t					m_SizzorMin = 0;
	void SetSizzorMin(uint32_t	SizzorMin)
	{
		m_SizzorMin = SizzorMin;
	}
	uint32_t GetSizzorMin()
	{
		return m_SizzorMin;
	}
	uint32_t					m_SizzorMax = 0;
	void SetSizzorMax(uint32_t	SizzorMax)
	{
		m_SizzorMax = SizzorMax;
	}
	uint32_t GetSizzorMax()
	{
		return m_SizzorMax;
	}
	SwapChainSupportDetails QueryPhysDevSwapChainSupport(VkPhysicalDevice PhysDev);
    virtual VkImageView CreateSwapImageView(VkImage image, VkFormat format)=0; 
    virtual VkExtent2D ChooseSwapExtent(
		const VkSurfaceCapabilitiesKHR& Capabilities)=0 ;
    virtual VkSurfaceFormatKHR ChooseSwapSurfaceFormat(
		const std::vector<VkSurfaceFormatKHR>& AvailableFormats)=0;
	virtual VkPresentModeKHR ChooseSwapPresentMode(
		const std::vector<VkPresentModeKHR>& AvailablePresentModes)=0 ;
	
	
    virtual void CreateImageViews()=0;
    //virtual void RecreateSwapChain(FrameBuffer* FBO)=0;
	virtual void CreateSwapChain()=0; 
	//virtual void SaveImage(uint32_t ImageNumber);
    virtual void Cleanup()=0;
	
};
#endif