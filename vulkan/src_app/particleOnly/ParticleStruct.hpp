
#ifndef PARTICLE_STRUCT_HPP
#define PARTICLE_STRUCT_HPP
#include "VulkanObj/Core.hpp"
const uint32_t MAXSPCOLLS = 8;
constexpr uint32_t MAX_CONTACTS = 16;

struct lstr {
	uint32_t pindex;
	uint32_t typ;
	uint32_t fill;
};

struct NeoContactState {
	glm::uvec4 ids;   // x=target particle index or wall flag
	// y=type: 0=inactive, 1=particle, 2=wall
	// z=phase: 0=inactive, 1=compression, 2=rebound
	// w=flags

	glm::vec4 vel;    // xy=source first-contact velocity
	// zw=target first-contact velocity for particle contacts

	glm::vec4 geom;   // xy=first-contact normal
	// z=A_zero
	// w=zero center distance
};

struct Particle {
	glm::vec4 PosLocA; // xyz=position, w=active flag: 0 active, 1 inactive
	glm::vec4 PosLocB; // xyz=alternate position buffer, w=active flag
	glm::vec4 VelRad;  // xyz=velocity, w=velocity angle

	glm::vec4 Data;    // x=radius, y=collision_stiffness_q, z=rebound_min_fraction, w=state/flags
	glm::vec4 parms;   // x=mass, y=delta_vx, z=delta_vy, w=delta_speed

	lstr CornerList[8];

	NeoContactState ncs[MAX_CONTACTS];

	uint32_t contactCount; // active entries in ncs
	uint32_t colFlg;       // 1 if in collision, 0 if not

	float MolarMatter;     // reserved
	float temp_vel;        // reserved
};

#endif