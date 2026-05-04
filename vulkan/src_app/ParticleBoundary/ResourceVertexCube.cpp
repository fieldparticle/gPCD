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
void ResourceVertexCube::Create(ResourceVertexParticle* PartVert)
{
#if 0
	ConfigObj* cfg = CfgApp;
	float nside = (float)CfgTst->GetInt("boundary_side_length", true);
	m_FileName = CfgApp->GetString("boundary_file_obj", true);
	ResourceVertexObj::Create(0, PartVert);
	bool boundaryFlag = CfgApp->GetBool("boundary_flag", true);
	if (boundaryFlag != true)
		for (size_t ii = 0; ii < m_vtemp.size(); ii++)
		{
			CartVert tmp = {};
			tmp.pos.x = m_vtemp[ii].x;// *m_ParticleVert->m_SideLength;
			tmp.pos.y = m_vtemp[ii].y; //*m_ParticleVert->m_SideLength;
			tmp.pos.z = m_vtemp[ii].z; //*m_ParticleVert->m_SideLength;
			tmp.pos.w = 1.0;
			tmp.color = glm::vec4(1.0, 0.0, 1.0, 0.1);
			m_Verts.push_back(tmp);
		}

	if(boundaryFlag ==true)
#endif
		MakeAxes(PartVert->m_SideLength);
	
	ResourceVertexObj::Create(0);



}
