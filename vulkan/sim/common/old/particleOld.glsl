
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
	uint pindex; 				// Index of cell the corner occupies
	uint ploc;					// TBD
	uint fill;					// fill
};
struct bcoll {
	uint clflg;					// TBD
};
struct ccoll {
	uint pindex;				// TBD
	uint clflg;					// TBD
};
// The particle structure.
struct Particle {
	vec4  PosLocA; 				// First position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	vec4  PosLocB;				// Second position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	vec4  VelRad;				// Velocity, vx,vy,vz, velocity angle.
    vec4  Data;					// Particle Data x=particle radius, y=inverse_square_softening, z=momentum_per_area, w not used
	vec4  parms;				// x = mass, y = particle type, z = live/dead flag, w unused.
	lstr  CornerList[8];		// Particle Corner List (see lstr)
	bcoll bcs[4];				// Wall contact flags: 1=left, 2=right, 3=bottom, 4=top.
	ccoll ccs[12];				// TBD
	uint  sltnum;				// Use to store contact count.
	uint  colFlg;				// 1 if in collision, 0 if not.
	float MolarMatter;			// To be used later
	float material_id;			// material/species id
};
struct boundStruct
{
	bool inBX;
	bool inBY;
	bool inBZ;
};
// Layout for the particle Array - this is dynamic right now -
// chnage to static so the GPU can preallocate memory.
layout(binding = 4) buffer ParticleSSBOOut 
{
   Particle P[NUMPARTS];
};
