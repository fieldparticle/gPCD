/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/ResourcePush.cpp $
% $Id: ResourcePush.cpp 28 2023-05-03 19:30:42Z jb $
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

void ResourceParticlePush::Create(ResourceVertexParticle* vertP)
{
	m_VertP = vertP;
	m_numParts = static_cast<float>(m_VertP->m_NumParticles);
	//setup push constants
	
	//this push constant range starts at the beginning
	m_PushConstant.offset			= 0;
	//this push constant range takes up the size of a MeshPushConstants struct
	m_PushConstant.size			= sizeof(ShaderFlags);
	//this push constant range is accessible only in the vertex shader
	m_PushConstant.stageFlags		= VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT;

}

void ResourceParticlePush::PushMem(uint32_t currentBuffer)
{
	
	//m_ShaderFlags.DrawInstance = 5.0;
	m_ShaderFlags.SideLength = static_cast<float>(m_VertP->m_SideLength);
	m_ShaderFlags.Ptot = static_cast<float>(m_App->m_Numparticles);
	m_ShaderFlags.dt = m_App->m_dt;
	m_ShaderFlags.systemp = 250.0;
	m_ShaderFlags.ColorMap = ColorMap;

	if(G_Stop == true)
	{
		m_ShaderFlags.StopFlg = 1.0;
	}
	else
	{
		m_ShaderFlags.actualFrame++;
		m_ShaderFlags.StopFlg = 0.0;
		if(static_cast<uint32_t>(m_ShaderFlags.actualFrame) % 1000 == 0)
			std::cout << "Actual Frame :" <<  static_cast<uint32_t>(m_ShaderFlags.actualFrame) << std::endl;
	}

	if(G_Boundary == true)
		m_ShaderFlags.Boundary = 1.0;
	else
		m_ShaderFlags.Boundary = 0.0;

	m_ShaderFlags.frameNum = static_cast<float>(m_App->m_FrameNumber);
	//mout << "ResourcePush::UpdateMem frame num:" << m_App->m_FrameNumber << ende;
}
