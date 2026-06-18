#ifndef STARTING_CONTACT_STATE_GLSL
#define STARTING_CONTACT_STATE_GLSL

// Persistent state for ForceDynamics contacts that are already overlapping
// when the simulation starts.  This file is intentionally separate from
// particle.glsl so the C++ descriptor/storage ABI can be wired independently.

const uint MAX_STARTING_CONTACTS = 32u;

const uint STARTING_CONTACT_NONE = 0u;
const uint STARTING_CONTACT_PARTICLE = 1u;
const uint STARTING_CONTACT_WALL = 2u;

const uint STARTING_CONTACT_INACTIVE = 0u;
const uint STARTING_CONTACT_ACTIVE = 1u;
const uint STARTING_CONTACT_RESOLVED = 2u;

struct StartingContactState {
    // x=source id, y=target particle id or wall flag,
    // z=STARTING_CONTACT_* kind, w=STARTING_CONTACT_* status.
    uvec4 ids;

    // x=starting center distance, y=physical separation limit,
    // z=effective source radius, w=effective target radius.
    vec4 geom;

    // x=compressed flag, yzw=reserved.
    vec4 aux;
};

struct StartingContactSlots {
    StartingContactState startingContacts[MAX_STARTING_CONTACTS];
};

layout(std430, binding = 7) coherent buffer StartingContactStateSSBO {
    StartingContactSlots StartingContact[];
};

#endif
