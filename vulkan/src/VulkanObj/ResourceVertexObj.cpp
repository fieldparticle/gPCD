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



void ResourceVertexObj::MakeAxes(uint32_t sidelen)
{
		
	
	m_CubeIndices =
	{
		0, 2, 1,  2, 0, 3,   // back
		4, 5, 6,  6, 7, 4,   // front

		0, 4, 7,  7, 3, 0,   // left
		1, 2, 6,  6, 5, 1,   // right

		0, 1, 5,  5, 4, 0,   // bottom
		3, 7, 6,  6, 2, 3    // top
	};
	int side = static_cast<int>(sidelen)-1;
	
	m_Axes.push_back({ { 0, 0, 0, 1.0 },{1.0,1.0,1.0,1} });
	m_Axes.push_back({ { side, 0.0, 0.0, 1.0 }, {1.0,1,1.,1} });
	m_Axes.push_back({ { side,  side, 0.0, 1.0 }, {1.,1.,1,1} });
	m_Axes.push_back({ {0.0,  side, 0.0, 1.0 }, {1,1,1.,1} });

	m_Axes.push_back({ {0.0, 0.0,  side, 1.0 }, {1,1.,1,1} });
	m_Axes.push_back({ { side, 0.0,  side, 1.0 }, {1.,1,1,1} });
	m_Axes.push_back({ { side,  side,  side, 1.0 }, {1,1,1,1} });
	m_Axes.push_back({ {0.0,  side,  side, 1.0 }, {1.0,1.0,1.0,1} });
	
	m_Verts = m_Axes;
	/*
	m_Axes.push_back({ {0.0,0.0,0.0,1.0f},{1.0, 0.0, 0.0,1.0} });
	m_Axes.push_back({ {sidelen,0.0,0.0,1.0f}, {1.0, 0.0, 0.0,1.0} });
	//y		
	m_Axes.push_back({ {0.0, 0.0, 0.0,1.0f},{0.0, 1.0, 0.0,1.0} });
	m_Axes.push_back({ {0.0, sidelen, 0.0,1.0f}, {0.0, 1.0, 0.0,1.0} });
	//z		
	m_Axes.push_back({ {0.0, 0.0, 0.0,1.0},{0.0, 0.0, 1.0,1.0} });
	m_Axes.push_back({ {0.0, 0.0, sidelen,1.0},{0.0, 0.0, 1.0,1.0} });

#if 0
	for (size_t ii = 0; ii < sidelen; ii++)
	{
		float length = static_cast<float>(ii + 1);
		// 	xtic
		m_Axes.push_back({ {length,-0.1,0.0,1.0},{1.0,0.0,0.0,1.0} });
		m_Axes.push_back({ {length,0.1,0.0,1.0},{1.0,0.0,0.0,1.0} });
		// y tic
		m_Axes.push_back({ {0.0,length,0.1,1.0},{0.0,1.0,0.0,1.0} });
		m_Axes.push_back({ {0.0,length,-0.1,1.0},{0.0,1.0,0.0,1.0} });
		// z tic
		m_Axes.push_back({ {0.1,0.0,length,1.0},{0.0,0.0,1.0,1.0} });
		m_Axes.push_back({ {-0.1,0.0,length,1.0},{0.0,0.0,1.0,1.0} });
	}
#endif
	m_Axes.push_back({ {0.90,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {0.90,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });

	m_Axes.push_back({ {1.10,-0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });
	m_Axes.push_back({ {1.10,0.5,0.0,1.0},{1.0,0.0,0.0,1.0} });



	//m_Verts = m_Axes;
	*/
}
