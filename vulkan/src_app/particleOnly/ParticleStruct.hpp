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
	glm::vec4	PosLocA;		// First position buffer.x, y, z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	glm::vec4	PosLocB;		// Second position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
	glm::vec4	VelRad;			// Velocity, vx,vy,vz, w = velocity angle.
	glm::vec4	Data;			// Particle Data x=particle radius, y=inverse_square_softening, z=momentum_per_area, w not used
	glm::vec4	parms;			// x is mass, y is particle type, z is 1 = live 0 dead, w unused.
	lstr		CornerList[8];	// Particle Corner List (see lstr)
	bcoll		bcs[4];			// Wall contact flags: 1=left, 2=right, 3=bottom, 4=top.
	ccoll		ccs[12];		// TBD
	uint32_t	sltnum;			// Use to store contact count.
	uint32_t	colFlg;			// 1 if in collision, 0 if not.
	float		MolarMatter;	// TBD
	float		temp_vel;		// TBD
	
};
	
#endif