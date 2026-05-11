/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourceVertex.cpp $
% $Id: ResourceVertex.cpp 28 2023-05-03 19:30:42Z jb $
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
#include "VulkanObj/VulkanApp.hpp"

#include <iostream>


void ResourceVertexObj::Create(uint32_t BindPoint, ResourceVertexParticle* PartVert)
{
	
	m_ParticleVert = PartVert;
	bool res = loadOBJ(m_FileName.c_str(), m_vtemp, m_UVS, m_Normals);
	if (!res)
	{
		std::ostringstream  objtxt;
		objtxt << "ResourceVertexObj::Create Failed File:" << m_FileName << ende;
		
		throw std::runtime_error(objtxt.str());
	}

}
void ResourceVertexObj::Create(uint32_t BindPoint)
{
	
	
	

}

VkVertexInputBindingDescription* 
	ResourceVertexObj::GetBindingDescription()
{
	m_BindingDescription.binding = m_BindPoint;
	m_BindingDescription.stride = sizeof(CartVert);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	

	return &m_BindingDescription;
}
std::vector<VkVertexInputAttributeDescription>* ResourceVertexObj::GetAttributeDescriptions()
{

		VkVertexInputAttributeDescription ad{};
		ad.binding = 0;
		ad.location = 0;
		ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
		ad.offset = offsetof(CartVert, pos);;
		m_AttributeDescriptions.push_back(ad);
		
		ad.binding = 0;
		ad.location = 1;
		ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
		ad.offset = offsetof(CartVert, color);;
		m_AttributeDescriptions.push_back(ad);
		
		
	
	return &m_AttributeDescriptions;
}



