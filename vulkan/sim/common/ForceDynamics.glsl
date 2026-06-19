#ifndef FORCE_DYNAMICS_GLSL
#define FORCE_DYNAMICS_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Some direct read-only/math bodies are generated from explicit templates.
// Methods without templates remain non-functional stubs.
// Do not hand edit generated dynamics content.

const float EPSILON = 1.0e-12;
const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;
const uint ERROR_NONE = 0u;
const uint ERROR_INVALID_SOURCE_ID = 1u;
const uint ERROR_INVALID_TARGET_ID = 2u;
const uint ERROR_INVALID_DT = 3u;
const uint ERROR_CONTACT_LIST_MISSING = 4u;
const uint ERROR_PARTICLE_OUT_OF_BOUNDS = 5u;
const uint ERROR_TUNNELING = 6u;
const uint ERROR_MISSING_COLLISION_STIFFNESS_Q = 7u;
const uint CONTACT_INACTIVE = 0u;
const uint CONTACT_PARTICLE = 1u;
const uint CONTACT_WALL = 2u;

struct ParticleEffectiveContactGeometry {
    float sourceRadius;
    float targetRadius;
    float physicalSeparationLimit;
    float startingContact;
    float startingResolved;
    bool suppressContact;
};

struct ParticleGeometry {
    vec3 normal;
    float overlapArea;
    float centerDistance;
    float effectiveSourceRadius;
    float effectiveTargetRadius;
    float physicalSeparationLimit;
    float startingContact;
    float startingResolved;
    bool valid;
};

struct ParticlePotentialGeometry {
    float sourceRadius;
    float targetRadius;
    bool valid;
};

struct WallPhysicalGhostGeometry {
    vec3 normal;
    float overlapArea;
    float centerDistance;
    bool valid;
};

struct WallGhostGeometry {
    vec3 normal;
    float overlapArea;
    float centerDistance;
    float effectiveRadius;
    float physicalSeparationLimit;
    float startingContact;
    float startingResolved;
    bool valid;
};

struct ContactForceInput {
    uint targetID;
    uint contactType;
    vec3 normal;
    float overlapArea;
    bool valid;
};

// Forward declarations for generated methods.
float VelocityAngle(float vx, float vy);
vec4 particle_position(uint ParticleID, uint positionBuffer);
float particle_overlap_area(float source_radius, float target_radius, float center_distance);
bool ProcessParticleCollision(uint TargetID, uint SourceID, inout vec3 totalForce);
bool ProcessWallCollision(uint SourceID, uint wall, inout vec3 totalForce);
bool InitializeWallContactState(uint SourceID, uint wall);
bool InitializeContactState(uint SourceID, uint TargetID);
bool GetContactState(uint SourceID, uint TargetID);
ParticleGeometry GetParticleGeometry(uint SourceID, uint TargetID);
vec4 GetParticlePosition(uint ParticleID);
uint StartingParticleKey(uint SourceID, uint TargetID);
uint StartingWallKey(uint SourceID, uint wall_flag);
void InitializeStartingContactState();
float ParticleCenterDistance(uint SourceID, uint TargetID);
ParticleEffectiveContactGeometry GetParticleEffectiveContactGeometry(uint SourceID, uint TargetID, float center_distance);
ParticlePotentialGeometry GetParticlePotentialGeometry(uint SourceID, uint TargetID, float center_distance);
bool AppendContactSlot(uint SourceID, uint TargetID);
uint GetContactSlots(uint SourceID);
vec4 GetStartFrameVelocity(uint ParticleID);
bool AccumulateContactForce(uint SourceID, ContactForceInput contact, inout vec3 totalForce);
float GetPairStiffness(uint SourceID, uint TargetID);
float GetContactStiffness(uint SourceID, uint TargetID, uint contact_type);
float WallContactOffsetDistance(float radius);
WallPhysicalGhostGeometry GetPhysicalWallGhostGeometry(uint SourceID, uint wall_flag);
WallGhostGeometry GetWallGhostGeometry(uint SourceID, uint wall_flag);
bool AppendWallContactSlot(uint SourceID, uint wall_flag);
bool CalcVelocity(uint SourceID, vec3 totalForce);
float GetParticleMass(uint ParticleID);
bool CalcPosition(uint SourceID);
bool StartReservoir(uint SourceID);
bool RetireParticlePastXMax(uint SourceID);
bool SetError(uint error_code);

// Python source: ForceDynamics.py:13
float VelocityAngle(float vx, float vy)
{
    return (vx != 0.0 || vy != 0.0) ? atan(vy, vx) : 0.0;
}

// Python source: ForceDynamics.py:18
vec4 particle_position(uint ParticleID, uint positionBuffer)
{
    return (positionBuffer == 0u)
        ? P[ParticleID].PosLocA
        : P[ParticleID].PosLocB;
}

// Python source: ForceDynamics.py:25
float particle_overlap_area(float source_radius, float target_radius, float center_distance)
{
    if (center_distance <= 0.0) {
        float min_radius = min(source_radius, target_radius);
        return FORCE_DYNAMICS_PI * min_radius * min_radius;
    }
    if (center_distance >= source_radius + target_radius) {
        return 0.0;
    }
    if (center_distance <= abs(source_radius - target_radius)) {
        float min_radius = min(source_radius, target_radius);
        return FORCE_DYNAMICS_PI * min_radius * min_radius;
    }

    float source_term = (
        center_distance * center_distance
        + source_radius * source_radius
        - target_radius * target_radius
    ) / (2.0 * center_distance * source_radius);
    float target_term = (
        center_distance * center_distance
        + target_radius * target_radius
        - source_radius * source_radius
    ) / (2.0 * center_distance * target_radius);
    source_term = clamp(source_term, -1.0, 1.0);
    target_term = clamp(target_term, -1.0, 1.0);
    float source_area = source_radius * source_radius * acos(source_term);
    float target_area = target_radius * target_radius * acos(target_term);
    float triangle_area = 0.5 * sqrt(max(
        0.0,
        (-center_distance + source_radius + target_radius)
        * (center_distance + source_radius - target_radius)
        * (center_distance - source_radius + target_radius)
        * (center_distance + source_radius + target_radius)
    ));
    return source_area + target_area - triangle_area;
}

// Python source: ForceDynamics.py:59
bool ProcessParticleCollision(uint TargetID, uint SourceID, inout vec3 totalForce)
{
    ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);
    ContactForceInput contact = ContactForceInput(
        TargetID,
        CONTACT_PARTICLE,
        geometry.normal,
        geometry.overlapArea,
        geometry.valid
    );
    return AccumulateContactForce(SourceID, contact, totalForce);
}

// Python source: ForceDynamics.py:66
bool ProcessWallCollision(uint SourceID, uint wall, inout vec3 totalForce)
{
    WallGhostGeometry geometry = GetWallGhostGeometry(SourceID, wall);
    ContactForceInput contact = ContactForceInput(
        wall,
        CONTACT_WALL,
        geometry.normal,
        geometry.overlapArea,
        geometry.valid
    );
    return AccumulateContactForce(SourceID, contact, totalForce);
}

// Python source: ForceDynamics.py:73
bool InitializeWallContactState(uint SourceID, uint wall)
{
    // TODO: generate body for InitializeWallContactState.
    return false;
}

// Python source: ForceDynamics.py:80
bool InitializeContactState(uint SourceID, uint TargetID)
{
    // TODO: generate body for InitializeContactState.
    return false;
}

// Python source: ForceDynamics.py:89
bool GetContactState(uint SourceID, uint TargetID)
{
    // TODO: generate body for GetContactState.
    return false;
}

// Python source: ForceDynamics.py:140
ParticleGeometry GetParticleGeometry(uint SourceID, uint TargetID)
{
    vec4 source_position = GetParticlePosition(SourceID);
    vec4 target_position = GetParticlePosition(TargetID);
    vec3 delta = target_position.xyz - source_position.xyz;
    float center_distance = length(delta);

    ParticleEffectiveContactGeometry effective =
        GetParticleEffectiveContactGeometry(SourceID, TargetID, center_distance);
    if (effective.suppressContact) {
        return ParticleGeometry(vec3(0.0), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, false);
    }
    if (center_distance >= effective.sourceRadius + effective.targetRadius) {
        return ParticleGeometry(vec3(0.0), 0.0, center_distance, effective.sourceRadius, effective.targetRadius, effective.physicalSeparationLimit, effective.startingContact, effective.startingResolved, false);
    }

    vec3 normal = (center_distance <= EPSILON)
        ? vec3(1.0, 0.0, 0.0)
        : delta / center_distance;
    float overlap_area = particle_overlap_area(
        effective.sourceRadius,
        effective.targetRadius,
        center_distance
    );
    return ParticleGeometry(
        normal,
        overlap_area,
        center_distance,
        effective.sourceRadius,
        effective.targetRadius,
        effective.physicalSeparationLimit,
        effective.startingContact,
        effective.startingResolved,
        true
    );
}

// Python source: ForceDynamics.py:199
vec4 GetParticlePosition(uint ParticleID)
{
    return particle_position(ParticleID, uint(ShaderFlags.positionBuffer));
}

// Python source: ForceDynamics.py:213
uint StartingParticleKey(uint SourceID, uint TargetID)
{
    // TODO: generate body for StartingParticleKey.
    return 0u;
}

// Python source: ForceDynamics.py:219
uint StartingWallKey(uint SourceID, uint wall_flag)
{
    // TODO: generate body for StartingWallKey.
    return 0u;
}

// Python source: ForceDynamics.py:223
void InitializeStartingContactState()
{
    // TODO: generate body for InitializeStartingContactState.
}

// Python source: ForceDynamics.py:280
float ParticleCenterDistance(uint SourceID, uint TargetID)
{
    vec4 source_position = GetParticlePosition(SourceID);
    vec4 target_position = GetParticlePosition(TargetID);
    vec3 delta = target_position.xyz - source_position.xyz;
    return length(delta);
}

// Python source: ForceDynamics.py:289
ParticleEffectiveContactGeometry GetParticleEffectiveContactGeometry(uint SourceID, uint TargetID, float center_distance)
{
    float source_radius = P[SourceID].Data.x;
    float target_radius = P[TargetID].Data.x;
    float physical_limit = source_radius + target_radius;

    // Step 6 ordinary-contact fallback: starting-contact effective radii
    // are added later through StartingContactState buffer logic.
    return ParticleEffectiveContactGeometry(
        source_radius,
        target_radius,
        physical_limit,
        0.0,
        0.0,
        false
    );
}

// Python source: ForceDynamics.py:327
ParticlePotentialGeometry GetParticlePotentialGeometry(uint SourceID, uint TargetID, float center_distance)
{
    ParticleEffectiveContactGeometry effective =
        GetParticleEffectiveContactGeometry(SourceID, TargetID, center_distance);
    if (effective.suppressContact) {
        return ParticlePotentialGeometry(0.0, 0.0, false);
    }
    if (center_distance >= effective.sourceRadius + effective.targetRadius) {
        return ParticlePotentialGeometry(effective.sourceRadius, effective.targetRadius, false);
    }
    return ParticlePotentialGeometry(effective.sourceRadius, effective.targetRadius, true);
}

// Python source: ForceDynamics.py:347
bool AppendContactSlot(uint SourceID, uint TargetID)
{
    // TODO: generate body for AppendContactSlot.
    return false;
}

// Python source: ForceDynamics.py:368
uint GetContactSlots(uint SourceID)
{
    // TODO: generate body for GetContactSlots.
    return 0u;
}

// Python source: ForceDynamics.py:372
vec4 GetStartFrameVelocity(uint ParticleID)
{
    return P[ParticleID].VelRad;
}

// Python source: ForceDynamics.py:383
bool AccumulateContactForce(uint SourceID, ContactForceInput contact, inout vec3 totalForce)
{
    if (!contact.valid) {
        return true;
    }

    float stiffness = GetContactStiffness(
        SourceID,
        contact.targetID,
        contact.contactType
    );
    float force_magnitude = stiffness * max(0.0, contact.overlapArea);
    totalForce.x -= force_magnitude * contact.normal.x;
    totalForce.y -= force_magnitude * contact.normal.y;
    totalForce.z -= force_magnitude * contact.normal.z;
    return true;
}

// Python source: ForceDynamics.py:399
float GetPairStiffness(uint SourceID, uint TargetID)
{
    float source_q = P[SourceID].Data.y;
    float target_q = P[TargetID].Data.y;
    return max(0.0, 0.5 * (source_q + target_q));
}

// Python source: ForceDynamics.py:405
float GetContactStiffness(uint SourceID, uint TargetID, uint contact_type)
{
    if (contact_type == CONTACT_WALL) {
        return max(0.0, P[SourceID].Data.y);
    }
    return GetPairStiffness(SourceID, TargetID);
}

// Python source: ForceDynamics.py:411
float WallContactOffsetDistance(float radius)
{
    return min(radius, radius * wall_contact_offset);
}

// Python source: ForceDynamics.py:415
WallPhysicalGhostGeometry GetPhysicalWallGhostGeometry(uint SourceID, uint wall_flag)
{
    vec4 position = GetParticlePosition(SourceID);
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(0.0);
    vec3 normal = vec3(0.0);

    if (wall_flag == 1u) {
        ghost = vec3(BOUNDARY_XMIN - radius + offset, position.y, position.z);
        normal = vec3(-1.0, 0.0, 0.0);
    } else if (wall_flag == 2u) {
        ghost = vec3(BOUNDARY_XMAX + radius - offset, position.y, position.z);
        normal = vec3(1.0, 0.0, 0.0);
    } else if (wall_flag == 3u) {
        ghost = vec3(position.x, BOUNDARY_YMIN - radius + offset, position.z);
        normal = vec3(0.0, -1.0, 0.0);
    } else if (wall_flag == 4u) {
        ghost = vec3(position.x, BOUNDARY_YMAX + radius - offset, position.z);
        normal = vec3(0.0, 1.0, 0.0);
    } else {
        return WallPhysicalGhostGeometry(vec3(0.0), 0.0, 0.0, false);
    }

    vec3 delta = ghost - position.xyz;
    float center_distance = length(delta);
    if (center_distance >= 2.0 * radius) {
        return WallPhysicalGhostGeometry(normal, 0.0, center_distance, false);
    }
    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return WallPhysicalGhostGeometry(normal, overlap_area, center_distance, true);
}

// Python source: ForceDynamics.py:467
WallGhostGeometry GetWallGhostGeometry(uint SourceID, uint wall_flag)
{
    WallPhysicalGhostGeometry physical =
        GetPhysicalWallGhostGeometry(SourceID, wall_flag);
    if (!physical.valid) {
        return WallGhostGeometry(
            physical.normal,
            0.0,
            physical.centerDistance,
            0.0,
            0.0,
            0.0,
            0.0,
            false
        );
    }

    float radius = P[SourceID].Data.x;
    float physical_limit = 2.0 * radius;
    float effective_radius = radius;

    // Step 7 ordinary-wall fallback: starting-wall effective radius
    // is added later through StartingContactState buffer logic.
    if (physical.centerDistance >= 2.0 * effective_radius) {
        return WallGhostGeometry(
            physical.normal,
            0.0,
            physical.centerDistance,
            effective_radius,
            physical_limit,
            0.0,
            0.0,
            false
        );
    }
    float overlap_area = particle_overlap_area(
        effective_radius,
        effective_radius,
        physical.centerDistance
    );
    return WallGhostGeometry(
        physical.normal,
        overlap_area,
        physical.centerDistance,
        effective_radius,
        physical_limit,
        0.0,
        0.0,
        true
    );
}

// Python source: ForceDynamics.py:529
bool AppendWallContactSlot(uint SourceID, uint wall_flag)
{
    // TODO: generate body for AppendWallContactSlot.
    return false;
}

// Python source: ForceDynamics.py:572
bool CalcVelocity(uint SourceID, vec3 totalForce)
{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {
        return SetError(ERROR_INVALID_DT);
    }

    float source_mass = GetParticleMass(SourceID);
    vec4 start_velocity = GetStartFrameVelocity(SourceID);
    P[SourceID].VelRad.x = start_velocity.x + totalForce.x * dt / source_mass;
    P[SourceID].VelRad.y = start_velocity.y + totalForce.y * dt / source_mass;
    P[SourceID].VelRad.z = start_velocity.z + totalForce.z * dt / source_mass;
    P[SourceID].VelRad.w = VelocityAngle(P[SourceID].VelRad.x, P[SourceID].VelRad.y);
    return true;
}

// Python source: ForceDynamics.py:588
float GetParticleMass(uint ParticleID)
{
    return max(P[ParticleID].parms.x, EPSILON);
}

// Python source: ForceDynamics.py:592
bool CalcPosition(uint SourceID)
{
    uint position_buffer = uint(ShaderFlags.positionBuffer);
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {
        return SetError(ERROR_INVALID_DT);
    }

    vec4 position = GetParticlePosition(SourceID);
    vec4 velocity = P[SourceID].VelRad;
    vec4 output_position;
    if (position_buffer == 0u) {
        P[SourceID].PosLocB.x = position.x + velocity.x * dt;
        P[SourceID].PosLocB.y = position.y + velocity.y * dt;
        P[SourceID].PosLocB.z = position.z + velocity.z * dt;
        P[SourceID].PosLocA.w = 1.0;
        P[SourceID].PosLocB.w = 0.0;
        output_position = P[SourceID].PosLocB;
    } else {
        P[SourceID].PosLocA.x = position.x + velocity.x * dt;
        P[SourceID].PosLocA.y = position.y + velocity.y * dt;
        P[SourceID].PosLocA.z = position.z + velocity.z * dt;
        P[SourceID].PosLocA.w = 0.0;
        P[SourceID].PosLocB.w = 1.0;
        output_position = P[SourceID].PosLocA;
    }

    if (ShaderFlags.Boundary == 0.0 && (output_position.x < 1.0 || output_position.y < 1.0)) {
        return SetError(ERROR_PARTICLE_OUT_OF_BOUNDS);
    }
    return true;
}

bool StartReservoir(uint SourceID)
{
    float state_flag = P[SourceID].Data.w;
    if (state_flag < 0.0) {
        return false;
    }
    if (state_flag == 0.0) {
        return true;
    }
    if (ShaderFlags.frameNum < state_flag) {
        return false;
    }

    uint position_buffer = uint(ShaderFlags.positionBuffer);
    vec4 current_position = particle_position(SourceID, position_buffer);
    float radius = P[SourceID].Data.x;
    float inlet_x = BOUNDARY_XMIN;
#ifdef INLET_X
    inlet_x = INLET_X;
#endif

    vec3 start_position = vec3(
        inlet_x + 2.2 * radius,
        current_position.y,
        current_position.z
    );
    P[SourceID].PosLocA.xyz = start_position;
    P[SourceID].PosLocB.xyz = start_position;
    P[SourceID].PosLocA.w = position_buffer == 0u ? 0.0 : 1.0;
    P[SourceID].PosLocB.w = position_buffer == 0u ? 1.0 : 0.0;
    P[SourceID].Data.w = 0.0;
    return true;
}

bool RetireParticlePastXMax(uint SourceID)
{
    uint next_position_buffer = 1u - uint(ShaderFlags.positionBuffer);
    vec4 next_position = particle_position(SourceID, next_position_buffer);
    if (next_position.x > BOUNDARY_XMAX) {
        P[SourceID].Data.w = -1.0;
        return false;
    }
    return true;
}

// Python source: ForceDynamics.py:735
bool SetError(uint error_code)
{
    collOut.ErrorNumber = error_code;
    return false;
}

#endif
