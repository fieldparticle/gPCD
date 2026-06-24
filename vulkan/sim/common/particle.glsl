
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

struct Particle {
    vec4 PosLocA;              // xyz=position, w=active flag: 0 active, 1 inactive
    vec4 PosLocB;              // xyz=alternate position buffer, w=active flag
    vec4 VelRad;               // xyz=velocity, w=velocity angle

    vec4 Data;                 // x=radius, y=collision_stiffness_q, z=reserved, w=state/flags
    vec4 parms;                // x=mass, yzw=source-owned recoverable internal momentum

    lstr CornerList[8];

    uint contactCount;         // active entries in contacts
    uint colFlg;               // 1 if in collision, 0 if not

    float ptype;                // runtime particle type copied from binary pdata.ptype
    float temp_vel;            // reserved
};

struct boundStruct {
    bool inBX;
    bool inBY;
    bool inBZ;
};

layout(std430,binding = 4) buffer ParticleSSBOOut {
    Particle P[];
};
