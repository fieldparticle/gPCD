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
#pragma once
struct pdata
{
	double pnum;		// Particle numebr
	double rx;			// x pos
	double ry;			// y pos
	double rz;			// z pos
	double radius;		// radius
	double vx;			// x vel
	double vy;			// y vel
	double vz;			// zvel
	double ptype;		// boundary or particle		
	double state_flg;	// 1 live or 0 dead
	double molar_mass;
	double material_id;	// material/species id; independent of ptype boundary role
	double collision_stiffness_q;

} ;
