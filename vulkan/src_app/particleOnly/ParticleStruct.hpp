
#ifndef PARTICLE_STRUCT_HPP
#define PARTICLE_STRUCT_HPP
#include "VulkanObj/Core.hpp"
const uint32_t MAXSPCOLLS = 8;
constexpr uint32_t MAX_CONTACTS = 16;

struct lstr {
	uint32_t pindex;
	uint32_t ploc;
	uint32_t fill;
};

struct ContactState {
	glm::uvec4 ids;   // x=target particle index, yzw=reserved/contact metadata
	glm::vec4 geom;   // xyz=current contact normal, w=current overlap area
	glm::vec4 aux;    // x=center distance, y=penetration depth, z=stored internal normal momentum, w=last impulse
};

struct Particle {
	glm::vec4 PosLocA; // xyz=position, w=active flag: 0 active, 1 inactive
	glm::vec4 PosLocB; // xyz=alternate position buffer, w=active flag
	glm::vec4 VelRadA;  // xyz=velocity, w=velocity angle
	glm::vec4 VelRadB;  // xyz=velocity, w=velocity angle

	glm::vec4 Data;    // x=radius, y=collision_stiffness_q, z=reserved, w=state/flags
	glm::vec4 parms;   // x=mass, y=delta_vx, z=delta_vy, w=delta_speed
	glm::vec4 collisionStartMomentum;  // xyz=mv at collision entry, w=active flag
	glm::vec4 collisionStoredMomentum; // xyz=display stored mv, w=magnitude

	lstr CornerList[8];

	//ContactState contacts[MAX_CONTACTS];

	uint32_t contactCount; // active entries in contacts
	uint32_t colFlg;       // 1 if in collision, 0 if not

	float ptype;           // runtime particle type copied from binary pdata.ptype
	float material_id;        // material/species id; independent of ptype boundary role
};
struct LightingParticle {
	glm::vec4 PosLocA; // xyz=position, w=active flag: 0 active, 1 inactive
	glm::vec4 PosLocB; // xyz=alternate position buffer, w=active flag
	glm::vec4 VelRadA;  // xyz=velocity, w=velocity angle
	glm::vec4 VelRadB;  // xyz=velocity, w=velocity angle

	glm::vec4 Data;    // x=radius, y=collision_stiffness_q, z=reserved, w=state/flags
	glm::vec4 parms;   // x=mass, y=delta_vx, z=delta_vy, w=delta_speed

	lstr CornerList[8];

	//ContactState contacts[MAX_CONTACTS];

	uint32_t contactCount; // active entries in contacts
	uint32_t colFlg;       // 1 if in collision, 0 if not

	float ptype;           // runtime particle type copied from binary pdata.ptype
	float material_id;        // material/species id; independent of ptype boundary role
	// Lighting-only extension fields.
	glm::vec4 initial_pos_birth;   // x,y,z, original release frame
	glm::vec4 initial_vel_energy;  // vx,vy,vz, reserved
	glm::vec4 photon_transport;    // lived_frames, cycle_count, flags, initial_relative_mass
	glm::vec4 photon_payload;      // r,g,b, valid; reflection photon carried light
};
#endif
