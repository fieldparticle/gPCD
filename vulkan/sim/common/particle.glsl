
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

struct NeoContactState {
    uvec4 ids;   // x=target particle index or wall flag
                 // y=type: 0=inactive, 1=particle, 2=wall
                 // z=phase: 0=inactive, 1=compression, 2=rebound
                 // w=flags

    vec4 vel;    // xy=source first-contact velocity
                 // zw=target first-contact velocity for particle contacts

    vec4 geom;   // xy=first-contact normal
                 // z=A_zero
                 // w=zero center distance
};

const uint MAX_CONTACTS = 16u;

struct Particle {
    vec4 PosLocA;              // xyz=position, w=active flag: 0 active, 1 inactive
    vec4 PosLocB;              // xyz=alternate position buffer, w=active flag
    vec4 VelRad;               // xyz=velocity, w=velocity angle

    vec4 Data;                 // x=radius, y=collision_stiffness_q, z=reserved, w=state/flags
    vec4 parms;                // x=mass, y=delta_vx, z=delta_vy, w=delta_speed

    lstr CornerList[8];

    NeoContactState ncs[MAX_CONTACTS];

    uint contactCount;         // active entries in ncs
    uint colFlg;               // 1 if in collision, 0 if not

    float MolarMatter;         // reserved
    float temp_vel;            // reserved
};

struct boundStruct {
    bool inBX;
    bool inBY;
    bool inBZ;
};

layout(binding = 4) buffer ParticleSSBOOut {
    Particle P[NUMPARTS];
};
