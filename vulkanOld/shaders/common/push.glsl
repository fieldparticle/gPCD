/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
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


@head3 		Description. 
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/

// Layout for push constants addressed in all shaders.
layout( push_constant ) uniform constants
{
	float DrawInstance;	// Not used yet.
	float SideLength;	// Side length as a check.
	float Ptot;			// Total number of particles for check.
	float dt;			// Time step.
	float systemp;		// Not implimented
	float ColorMap;		// 0.0 = Color Collision 
						// 1.0 = Color velocity angle.
	float Boundary;		// Not implimented	
	float StopFlg;
	float frameNum;		// Current frame number
	float actualFrame;  // actual frame for flow
	
} ShaderFlags;