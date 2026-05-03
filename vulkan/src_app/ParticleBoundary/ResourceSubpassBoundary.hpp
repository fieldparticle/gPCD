/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/RenderPass.cpp $
% $Id: RenderPass.cpp 31 2023-06-12 20:17:58Z jb $
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

#ifndef SUBPASSBOUNDARY_HPP
#define SUBPASSBOUNDARY_HPP
class RenderPass;
class SubPassBoundary: public Resource
{

public:
	VkAttachmentReference m_InputReferences[2]{};
	virtual void GetShaderMem() {};
	SubPassBoundary(VulkanObj* App, std::string Name, uint32_t Type = VBW_TYPE_SUBPASS) :
		Resource(App, Name, Type) {};


	void* getBuffer(uint32_t bufNum, uint32_t ImageIndex, unsigned long& size)
	{
		size = static_cast<unsigned long>(m_BufSize);
		return &m_Buffers[ImageIndex];

	}
	virtual void AskObject(uint32_t AnyNumber) {};
	std::vector<VkVertexInputAttributeDescription>* GetAttributeDescriptions() { return {}; };
	VkVertexInputBindingDescription* GetBindingDescription() { return {}; };
	void* GetBuffer(uint32_t bufNum, uint32_t ImageIndex, unsigned long& size) { return nullptr; };

	void CopyMem() {};
	
	void PushMem(uint32_t currentBuffer) {};
	void PullMem(uint32_t currentBuffer) {};
	void Create(SwapChainObj* SCO, std::vector<ImageObject*>  IMO, uint32_t BindPoint, uint32_t SubPassNum, uint32_t TotSubPass);
private:

};


#endif