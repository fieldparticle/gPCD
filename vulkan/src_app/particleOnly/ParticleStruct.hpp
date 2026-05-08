#ifndef PARTICLE_STRUCT_HPP
#define PARTICLE_STRUCT_HPP
#include "VulkanObj/Core.hpp"
const uint32_t MAXSPCOLLS = 8;
struct lstr {
	uint32_t pindex;
	uint32_t typ;
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
	glm::vec4	PosLocA; // First position buffer.x, y, z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	glm::vec4	PosLocB; // Second position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	glm::vec4	VelRad;  // Velocity, vx,vy,vz, w = velocity angle.
	glm::vec4	Data; // 
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