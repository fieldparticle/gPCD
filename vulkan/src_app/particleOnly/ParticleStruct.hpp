#ifndef PARTICLE_STRUCT_HPP
#define PARTICLE_STRUCT_HPP
#include "VulkanObj/Core.hpp"
const uint32_t MAXSPCOLLS = 8;
struct lstr {
	uint32_t pindex;
	uint32_t ploc;
	uint32_t fill;
};
struct bcoll {
	uint32_t clflg;
};
struct ccoll {
	uint32_t pindex;
	uint32_t clflg;
};
struct Particle {
	glm::vec4	PosLoc; //  x,y,z,radius16
	glm::vec4	VelRad;
	glm::vec4	FrcAng;
	glm::vec4	prvvel;
	glm::vec4	parms;
	lstr		zlink[8];
	bcoll		bcs[4];				// boundary collisions
	ccoll		ccs[12];		// boundary collisions
	uint32_t	pnum;
	uint32_t	colFlg;
	float		MolarMatter;
	float		temp_vel;
	
};
	
#endif