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
void ResourceVertexSphere::Create(ResourceVertexParticle* PartVert)
{
	ConfigObj* cfg = CfgApp;
	//float nside = (float)CfgTst->GetInt("application.boundary_side_length", true);
	m_FileName = CfgApp->GetString("application.sphere_file", true);
	ResourceVertexObj::Create(0, PartVert);

	for (size_t ii = 0; ii < m_vtemp.size(); ii++)
	{
		CartVert tmp = {};
		tmp.pos.x = m_vtemp[ii].x * 2 * PartVert->m_Radius;
		tmp.pos.y = m_vtemp[ii].y * 2 * PartVert->m_Radius; //*m_ParticleVert->m_SideLength;
		tmp.pos.z = m_vtemp[ii].z * 2 * PartVert->m_Radius; //*m_ParticleVert->m_SideLength;
		tmp.pos.w = 0.2f;
		tmp.color = glm::vec4(1.0, 0.0, 0.0, 1.0);
		m_Verts.push_back(tmp);
	}


	//m_Verts = m_Axes;
	ResourceVertexObj::Create(0);


}
