#ifndef FORCE_DYNAMICS_GLSL
#define FORCE_DYNAMICS_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Core reusable force dynamics. Boundary-particle wall helpers are split
// into ForceDynamicsBoundaryParticle.glsl and ForceDynamicsCDNozzle.glsl.
// Do not hand edit generated dynamics content.

const float EPSILON = 1.0e-12;
const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;
const uint ERROR_NONE = 0u;
const uint ERROR_INVALID_SOURCE_ID = 1u;
const uint ERROR_INVALID_TARGET_ID = 2u;
const uint ERROR_INVALID_DT = 3u;
const uint ERROR_CONTACT_LIST_MISSING = 4u;
const uint ERROR_PARTICLE_OUT_OF_BOUNDS = 5u;
const uint ERROR_PARTICLE_TUNNELING = 6u;
const uint ERROR_MISSING_COLLISION_STIFFNESS_Q = 7u;
const uint ERROR_WALL_TUNNELING = 8u;
const uint ERROR_MAX_DEPTH_CONSTRAINT = 9u;
const uint ERROR_PENETRATION_STEP_TOO_LARGE = 10u;
const float MAXIMUM_PENETRATION_FRACTION = 0.5;
const uint CONTACT_INACTIVE = 0u;
const uint CONTACT_PARTICLE = 1u;
const uint CONTACT_WALL = 2u;
#ifndef horizontal_wall
#define horizontal_wall 1
#endif
#ifndef vertical_wall
#define vertical_wall 2
#endif
#ifndef cd_nozzle_wall
#define cd_nozzle_wall 3
#endif
#ifndef horizontal
#define horizontal 1
#endif
#ifndef vertical
#define vertical 2
#endif
#ifndef wall_guard
#define wall_guard 1
#endif
#ifndef cell_guard
#define cell_guard 2
#endif
#ifndef area
#define area 1
#endif
#ifndef depth
#define depth 2
#endif

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

struct BoundaryWallSegment {
    vec3 normal;
    float overlapArea;
    float centerDistance;
    uint wallFlag;
    bool valid;
};

struct ContactForceInput {
    uint targetID;
    uint contactType;
    vec3 normal;
    float overlapArea;
    float penetrationDepth;
    bool valid;
};

#ifndef MAX_SOURCE_DEPTH_CONSTRAINTS
#define MAX_SOURCE_DEPTH_CONSTRAINTS 16
#endif
uint maximumDepthConstraintOwner = 0xffffffffu;
uint maximumDepthConstraintCount = 0u;
vec3 maximumDepthConstraintNormals[MAX_SOURCE_DEPTH_CONSTRAINTS];
float maximumDepthConstraintLimits[MAX_SOURCE_DEPTH_CONSTRAINTS];

// Forward declarations for generated core methods.
float VelocityAngle(float vx, float vy);
vec4 particle_position(uint ParticleID, uint positionBuffer);
float particle_overlap_area(float source_radius, float target_radius, float center_distance);
float ParticleProximityMagnitude(float source_radius, float target_radius, float center_distance);
float ParticlePenetrationDepth(float source_radius, float target_radius, float center_distance);
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
bool CheckPenetrationStepResolution(uint SourceID, vec3 normal, float source_radius, vec3 target_velocity);
bool ProjectSourceVelocityToContactSet(vec3 candidate_velocity, out vec3 contained_velocity);
bool ApplySourceMaximumDepth(uint SourceID);
bool CalcVelocity(uint SourceID, vec3 totalForce);
float GetParticleMass(uint ParticleID);
bool CalcPosition(uint SourceID);
bool SetError(uint error_code);
bool IsParticleDead(uint ParticleID);
bool ApplyParticleDeathBounds(uint ParticleID);
vec4 GetParticleVelocity(uint ParticleID);
vec4 GetNextParticleVelocity(uint ParticleID);
void SetNextParticleVelocity(uint ParticleID, vec4 velocity);
bool RegisterMaximumDepthConstraint(uint SourceID, vec3 normal, float penetration_depth, float source_radius);
bool SolveMaximumDepthSystem(mat3 matrix, vec3 values, uint size, out vec3 solution);

// Python source: ForceDynamics.py:20
float VelocityAngle(float vx, float vy)
{
    return (vx != 0.0 || vy != 0.0) ? atan(vy, vx) : 0.0;
}

// Python source: ForceDynamics.py:25
vec4 particle_position(uint ParticleID, uint positionBuffer)
{
    return (positionBuffer == 0u)
        ? P[ParticleID].PosLocA
        : P[ParticleID].PosLocB;
}

// Python source: ForceDynamics.py:32
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

// Python source: ForceDynamics.py:695
float ParticleProximityMagnitude(float source_radius, float target_radius, float center_distance)
{
    return max(0.0, center_distance - target_radius);
}

// Python source: ForceDynamics.py:700
float ParticlePenetrationDepth(float source_radius, float target_radius, float center_distance)
{
    float orientation_magnitude = source_radius;
    float proximity_magnitude = ParticleProximityMagnitude(
        source_radius,
        target_radius,
        center_distance
    );
    return orientation_magnitude - proximity_magnitude;
}

// Python source: ForceDynamics.py:66
bool ProcessParticleCollision(uint TargetID, uint SourceID, inout vec3 totalForce)
{
    ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);
    if (!geometry.valid) {
        return true;
    }
    float penetration_depth = ParticlePenetrationDepth(
        geometry.effectiveSourceRadius,
        geometry.effectiveTargetRadius,
        geometry.centerDistance
    );
    float directed_proximity = geometry.centerDistance
        - geometry.effectiveTargetRadius;
    if (directed_proximity < -EPSILON) {
        return SetError(ERROR_PARTICLE_TUNNELING);
    }
    if (!CheckPenetrationStepResolution(
            SourceID, geometry.normal, geometry.effectiveSourceRadius,
            GetStartFrameVelocity(TargetID).xyz)) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID, geometry.normal, penetration_depth,
            geometry.effectiveSourceRadius)) {
        return false;
    }
    ContactForceInput contact = ContactForceInput(
        TargetID,
        CONTACT_PARTICLE,
        geometry.normal,
        geometry.overlapArea,
        penetration_depth,
        geometry.valid
    );
    return AccumulateContactForce(SourceID, contact, totalForce);
}

// Python source: ForceDynamics.py:73
bool ProcessWallCollision(uint SourceID, uint wall, inout vec3 totalForce)
{
    WallGhostGeometry geometry = GetWallGhostGeometry(SourceID, wall);
    if (!geometry.valid) {
        return true;
    }
    float penetration_depth = ParticlePenetrationDepth(
        geometry.effectiveRadius,
        geometry.effectiveRadius,
        geometry.centerDistance
    );
    float maximum_depth_distance = geometry.effectiveRadius
        - WallContactOffsetDistance(geometry.effectiveRadius);
    if (geometry.centerDistance - maximum_depth_distance < -EPSILON) {
        return SetError(ERROR_WALL_TUNNELING);
    }
    if (!CheckPenetrationStepResolution(
            SourceID, geometry.normal, geometry.effectiveRadius, vec3(0.0))) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID, geometry.normal, penetration_depth,
            geometry.effectiveRadius)) {
        return false;
    }
    ContactForceInput contact = ContactForceInput(
        wall,
        CONTACT_WALL,
        geometry.normal,
        geometry.overlapArea,
        penetration_depth,
        geometry.valid
    );
    return AccumulateContactForce(SourceID, contact, totalForce);
}

// Python source: ForceDynamics.py:545
bool InitializeWallContactState(uint SourceID, uint wall)
{
    // TODO: generate body for InitializeWallContactState.
    return false;
}

// Python source: ForceDynamics.py:571
bool InitializeContactState(uint SourceID, uint TargetID)
{
    // TODO: generate body for InitializeContactState.
    return false;
}

// Python source: ForceDynamics.py:580
bool GetContactState(uint SourceID, uint TargetID)
{
    // TODO: generate body for GetContactState.
    return false;
}

// Python source: ForceDynamics.py:633
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

// Python source: ForceDynamics.py:880
vec4 GetParticlePosition(uint ParticleID)
{
    return particle_position(ParticleID, uint(ShaderFlags.positionBuffer));
}

// Python source: ForceDynamics.py:925
uint StartingParticleKey(uint SourceID, uint TargetID)
{
    // TODO: generate body for StartingParticleKey.
    return 0u;
}

// Python source: ForceDynamics.py:931
uint StartingWallKey(uint SourceID, uint wall_flag)
{
    // TODO: generate body for StartingWallKey.
    return 0u;
}

// Python source: ForceDynamics.py:935
void InitializeStartingContactState()
{
    // TODO: generate body for InitializeStartingContactState.
}

// Python source: ForceDynamics.py:998
float ParticleCenterDistance(uint SourceID, uint TargetID)
{
    vec4 source_position = GetParticlePosition(SourceID);
    vec4 target_position = GetParticlePosition(TargetID);
    vec3 delta = target_position.xyz - source_position.xyz;
    return length(delta);
}

// Python source: ForceDynamics.py:1007
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

// Python source: ForceDynamics.py:1045
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

// Python source: ForceDynamics.py:1065
bool AppendContactSlot(uint SourceID, uint TargetID)
{
    // TODO: generate body for AppendContactSlot.
    return false;
}

// Python source: ForceDynamics.py:1086
uint GetContactSlots(uint SourceID)
{
    // TODO: generate body for GetContactSlots.
    return 0u;
}

// Python source: ForceDynamics.py:1090
vec4 GetStartFrameVelocity(uint ParticleID)
{
    return GetParticleVelocity(ParticleID);
}

// Python source: ForceDynamics.py:1101
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
    #if defined(CONTACT_FORCE_MEASURE) && CONTACT_FORCE_MEASURE == depth
    float contact_measure = contact.penetrationDepth;
    #else
    float contact_measure = contact.overlapArea;
    #endif
    float force_magnitude = stiffness * max(0.0, contact_measure);
    float impulse = force_magnitude * ShaderFlags.dt;
    vec3 source_velocity = GetParticleVelocity(SourceID).xyz;
    vec3 target_velocity = (contact.contactType == CONTACT_WALL)
        ? vec3(0.0)
        : GetParticleVelocity(contact.targetID).xyz;
    float rel_vn = dot(target_velocity - source_velocity, contact.normal);
    vec3 internal_momentum = P[SourceID].parms.yzw;
    if (rel_vn < -EPSILON) {
        internal_momentum += impulse * contact.normal;
    } else if (rel_vn > EPSILON) {
        float stored_along_normal = dot(internal_momentum, contact.normal);
        float release_impulse = min(max(0.0, stored_along_normal), impulse);
        internal_momentum -= release_impulse * contact.normal;
    }
    P[SourceID].parms.yzw = internal_momentum;
    P[SourceID].Data.z = length(internal_momentum);
    totalForce.x -= force_magnitude * contact.normal.x;
    totalForce.y -= force_magnitude * contact.normal.y;
    totalForce.z -= force_magnitude * contact.normal.z;
    return true;
}

// Python source: ForceDynamics.py:1121
float GetPairStiffness(uint SourceID, uint TargetID)
{
    float source_q = P[SourceID].Data.y;
    float target_q = P[TargetID].Data.y;
    return max(0.0, 0.5 * (source_q + target_q));
}

// Python source: ForceDynamics.py:1127
float GetContactStiffness(uint SourceID, uint TargetID, uint contact_type)
{
    if (contact_type == CONTACT_WALL) {
        return max(0.0, P[SourceID].Data.y);
    }
    return GetPairStiffness(SourceID, TargetID);
}

// Python source: ForceDynamics.py:1133
float WallContactOffsetDistance(float radius)
{
    return min(radius, radius * wall_contact_offset);
}

// Python source: ForceDynamics.py:1137
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

// Python source: ForceDynamics.py:1189
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

// Python source: ForceDynamics.py:1251
bool AppendWallContactSlot(uint SourceID, uint wall_flag)
{
    // TODO: generate body for AppendWallContactSlot.
    return false;
}

// Python source: ForceDynamics.py:104
bool CheckPenetrationStepResolution(uint SourceID, vec3 normal, float source_radius, vec3 target_velocity)
{
    vec3 source_velocity = GetStartFrameVelocity(SourceID).xyz;
    float relative_normal_velocity = dot(
        target_velocity - source_velocity, normal);
    float inward_displacement = max(
        0.0, -relative_normal_velocity * ShaderFlags.dt);
    float penetration_reserve =
        (1.0 - MAXIMUM_PENETRATION_FRACTION) * source_radius;
    if (inward_displacement > penetration_reserve + EPSILON) {
        return SetError(ERROR_PENETRATION_STEP_TOO_LARGE);
    }
    return true;
}

// Python source: ForceDynamics.py:741
bool ProjectSourceVelocityToContactSet(vec3 candidate_velocity, out vec3 contained_velocity)
{
    contained_velocity = candidate_velocity;
    bool candidate_valid = true;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        if (dot(maximumDepthConstraintNormals[index], candidate_velocity)
                > maximumDepthConstraintLimits[index] + EPSILON) {
            candidate_valid = false;
        }
    }
    if (candidate_valid) {
        return true;
    }

    bool found = false;
    float best_distance_sq = 0.0;
    for (uint i = 0u; i < maximumDepthConstraintCount; ++i) {
        for (uint j_code = 0u; j_code <= maximumDepthConstraintCount; ++j_code) {
            for (uint k_code = 0u; k_code <= maximumDepthConstraintCount; ++k_code) {
                uint active_count = 1u;
                uint j = 0u;
                uint k = 0u;
                if (j_code > 0u) {
                    j = j_code - 1u;
                    if (j <= i) { continue; }
                    active_count = 2u;
                } else if (k_code > 0u) {
                    continue;
                }
                if (k_code > 0u) {
                    k = k_code - 1u;
                    if (active_count != 2u || k <= j) { continue; }
                    active_count = 3u;
                }

                vec3 n0 = maximumDepthConstraintNormals[i];
                vec3 n1 = active_count >= 2u
                    ? maximumDepthConstraintNormals[j] : vec3(0.0);
                vec3 n2 = active_count >= 3u
                    ? maximumDepthConstraintNormals[k] : vec3(0.0);
                vec3 limits = vec3(
                    maximumDepthConstraintLimits[i],
                    active_count >= 2u ? maximumDepthConstraintLimits[j] : 0.0,
                    active_count >= 3u ? maximumDepthConstraintLimits[k] : 0.0);
                mat3 gram = mat3(0.0);
                gram[0][0] = dot(n0, n0);
                if (active_count >= 2u) {
                    gram[0][1] = dot(n0, n1);
                    gram[1][0] = gram[0][1];
                    gram[1][1] = dot(n1, n1);
                }
                if (active_count >= 3u) {
                    gram[0][2] = dot(n0, n2);
                    gram[2][0] = gram[0][2];
                    gram[1][2] = dot(n1, n2);
                    gram[2][1] = gram[1][2];
                    gram[2][2] = dot(n2, n2);
                }
                vec3 residual = vec3(
                    dot(n0, candidate_velocity),
                    active_count >= 2u ? dot(n1, candidate_velocity) : 0.0,
                    active_count >= 3u ? dot(n2, candidate_velocity) : 0.0
                ) - limits;
                vec3 multipliers;
                if (!SolveMaximumDepthSystem(
                        gram, residual, active_count, multipliers)) {
                    continue;
                }
                if (multipliers.x < -EPSILON
                        || (active_count >= 2u && multipliers.y < -EPSILON)
                        || (active_count >= 3u && multipliers.z < -EPSILON)) {
                    continue;
                }
                vec3 velocity = candidate_velocity - multipliers.x * n0;
                if (active_count >= 2u) { velocity -= multipliers.y * n1; }
                if (active_count >= 3u) { velocity -= multipliers.z * n2; }
                bool satisfies_all = true;
                for (uint constraint = 0u;
                        constraint < maximumDepthConstraintCount; ++constraint) {
                    if (dot(maximumDepthConstraintNormals[constraint], velocity)
                            > maximumDepthConstraintLimits[constraint] + EPSILON) {
                        satisfies_all = false;
                    }
                }
                if (!satisfies_all) { continue; }
                float distance_sq = dot(
                    candidate_velocity - velocity, candidate_velocity - velocity);
                if (!found || distance_sq < best_distance_sq) {
                    found = true;
                    best_distance_sq = distance_sq;
                    contained_velocity = velocity;
                }
            }
        }
    }
    return found;
}

// Python source: ForceDynamics.py:803
bool ApplySourceMaximumDepth(uint SourceID)
{
    if (maximumDepthConstraintOwner != SourceID
            || maximumDepthConstraintCount == 0u) {
        return true;
    }
    vec3 candidate = GetNextParticleVelocity(SourceID).xyz;
    vec3 contained;
    if (!ProjectSourceVelocityToContactSet(candidate, contained)) {
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT);
    }
    float source_mass = GetParticleMass(SourceID);
    P[SourceID].parms.yzw +=
        source_mass * (candidate - contained);
    P[SourceID].Data.z = length(P[SourceID].parms.yzw);
    SetNextParticleVelocity(SourceID, vec4(
        contained, VelocityAngle(contained.x, contained.y)));
    maximumDepthConstraintCount = 0u;
    return true;
}

// Python source: ForceDynamics.py:1298
bool CalcVelocity(uint SourceID, vec3 totalForce)
{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {
        return SetError(ERROR_INVALID_DT);
    }

    float source_mass = GetParticleMass(SourceID);
    vec4 start_velocity = GetStartFrameVelocity(SourceID);
    vec3 candidate_velocity = start_velocity.xyz + totalForce * dt / source_mass;
    SetNextParticleVelocity(SourceID, vec4(
        candidate_velocity,
        VelocityAngle(candidate_velocity.x, candidate_velocity.y)
    ));
    return ApplySourceMaximumDepth(SourceID);
}

// Python source: ForceDynamics.py:1314
float GetParticleMass(uint ParticleID)
{
    return max(P[ParticleID].parms.x, EPSILON);
}

// Python source: ForceDynamics.py:1318
bool CalcPosition(uint SourceID)
{
    uint position_buffer = uint(ShaderFlags.positionBuffer);
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {
        return SetError(ERROR_INVALID_DT);
    }

    vec4 position = GetParticlePosition(SourceID);
    vec4 velocity = GetNextParticleVelocity(SourceID);
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

// Python source: ForceDynamics.py:1516
bool SetError(uint error_code)
{
    collOut.ErrorNumber = error_code;
    return false;
}

// Custom GLSL helper: IsParticleDead
bool IsParticleDead(uint ParticleID)
{
    return P[ParticleID].Data.w < 0.0;
}

// Custom GLSL helper: ApplyParticleDeathBounds
bool ApplyParticleDeathBounds(uint ParticleID)
{
    if (P[ParticleID].ptype > 0.5) {
        return true;
    }
    vec4 next_position = (uint(ShaderFlags.positionBuffer) == 0u)
        ? P[ParticleID].PosLocB
        : P[ParticleID].PosLocA;
    if (next_position.x < death_x_min
            || next_position.x > death_x_max
            || next_position.y < death_y_min
            || next_position.y > death_y_max
            || next_position.z < death_z_min
            || next_position.z > death_z_max) {
        P[ParticleID].Data.w = -1.0;
        return false;
    }
    return true;
}

// Custom GLSL helper: GetParticleVelocity
vec4 GetParticleVelocity(uint ParticleID)
{
    return (uint(ShaderFlags.positionBuffer) == 0u)
        ? P[ParticleID].VelRadA
        : P[ParticleID].VelRadB;
}

// Custom GLSL helper: GetNextParticleVelocity
vec4 GetNextParticleVelocity(uint ParticleID)
{
    return (uint(ShaderFlags.positionBuffer) == 0u)
        ? P[ParticleID].VelRadB
        : P[ParticleID].VelRadA;
}

// Custom GLSL helper: SetNextParticleVelocity
void SetNextParticleVelocity(uint ParticleID, vec4 velocity)
{
    if (uint(ShaderFlags.positionBuffer) == 0u) {
        P[ParticleID].VelRadB = velocity;
    } else {
        P[ParticleID].VelRadA = velocity;
    }
}

// Custom GLSL helper: RegisterMaximumDepthConstraint
bool RegisterMaximumDepthConstraint(uint SourceID, vec3 normal, float penetration_depth, float source_radius)
{
    if (maximumDepthConstraintOwner != SourceID) {
        maximumDepthConstraintOwner = SourceID;
        maximumDepthConstraintCount = 0u;
    }
    float maximum_depth = MAXIMUM_PENETRATION_FRACTION * source_radius;
    if (penetration_depth < maximum_depth - EPSILON) {
        return true;
    }
    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT);
    }
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = normal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] = 0.0;
    maximumDepthConstraintCount += 1u;
    return true;
}

// Custom GLSL helper: SolveMaximumDepthSystem
bool SolveMaximumDepthSystem(mat3 matrix, vec3 values, uint size, out vec3 solution)
{
    solution = vec3(0.0);
    if (size == 1u) {
        if (abs(matrix[0][0]) <= EPSILON) { return false; }
        solution.x = values.x / matrix[0][0];
        return true;
    }
    if (size == 2u) {
        float det = matrix[0][0] * matrix[1][1]
            - matrix[1][0] * matrix[0][1];
        if (abs(det) <= EPSILON) { return false; }
        solution.x = (values.x * matrix[1][1]
            - matrix[1][0] * values.y) / det;
        solution.y = (matrix[0][0] * values.y
            - values.x * matrix[0][1]) / det;
        return true;
    }
    if (size == 3u) {
        float det = determinant(matrix);
        if (abs(det) <= EPSILON) { return false; }
        mat3 mx = matrix;
        mat3 my = matrix;
        mat3 mz = matrix;
        mx[0] = values;
        my[1] = values;
        mz[2] = values;
        solution = vec3(
            determinant(mx), determinant(my), determinant(mz)) / det;
        return true;
    }
    return false;
}

#endif
