/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.hpp $
% $Id: ResourceVertex.hpp 28 2023-05-03 19:30:42Z jb $
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
#ifndef RESOURCE_VERTEXSPHERE_HPP
#define RESOURCE_VERTEXSPHERE_HPP
class ResourceVertexParticle;
class ResourceVertexSphere : public ResourceVertexObj
{
    public:
		
		ResourceVertexSphere(VulkanObj* App, std::string Name) :
			ResourceVertexObj(App, Name) {};
		virtual void UpdateMem() {};
		virtual void GetShaderMem() {};
		virtual void CopyMem() {};

		virtual void* GetBuffer(uint32_t bufNum,
			uint32_t ImageIndex, unsigned long& size) {
			return NULL;
		};
		virtual void AskObject(uint32_t AnyNumber) {};
		virtual void Create(ResourceVertexParticle* PartVert);
		
	
	

};
#endif