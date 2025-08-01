
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


@head3 		Description. |
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/
struct lstr {
	uint pindex;
	uint ploc;
	uint fill;
};
struct bcoll {
	uint clflg;
};
struct ccoll {
	uint pindex;
	uint clflg;
};
// The particle structure.
struct Particle {
	vec4  PosLoc; 				// Position - x,y,z, and w stores the particle radius.
	vec4  VelRad;				// Velocity - mapped to vertex input
	vec4  FrcAng;				// Not implimented yet.
    vec4  prvvel;				// Previous velocity (delete)
	vec4  parms;				// x containes the sequens, y kills the particle
	lstr  zlink[8];	// Link list
	bcoll bcs[4];				// boundary collisions
	ccoll ccs[12];		// boundary collisions
	uint  sltnum;					// dupcate collisions slot
	uint  ColFlg;				// Not implimented yet.
	float MolarMatter;
	float temp_vel;
};
struct boundStruct
{
	bool inBX;
	bool inBY;
	bool inBZ;
};
// Layout for the particle Array - this is dynamic right now -
// chnage to static so the GPU can preallocate memory.
layout(scalar, binding = 4) buffer ParticleSSBOOut 
{
   Particle P[NUMPARTS];
};



