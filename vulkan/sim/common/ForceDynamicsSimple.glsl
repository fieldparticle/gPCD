#ifndef FORCE_DYNAMICS_SIMPLE_GLSL
#define FORCE_DYNAMICS_SIMPLE_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Clean simple dynamics target for GenericGenData/TestPythonBoundarySpheres.
// Do not hand edit generated dynamics content.

const float EPSILON = 1.0e-12;
const float MAXIMUM_DEPTH_SOLVER_EPSILON = 1.0e-6;
const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;
const float MAXIMUM_PENETRATION_FRACTION = 0.5;
const uint CONTACT_PARTICLE = 1u;
const uint CONTACT_WALL = 2u;
const uint CONTACT_ACTIVE_THIS_FRAME = 1u;
const uint ERROR_NONE = 0u;
const uint ERROR_INVALID_DT = 3u;
const uint ERROR_CONTACT_LIST_MISSING = 4u;
const uint ERROR_PARTICLE_OUT_OF_BOUNDS = 5u;
const uint ERROR_PARTICLE_TUNNELING = 6u;
const uint ERROR_WALL_TUNNELING = 8u;
const uint ERROR_MAX_DEPTH_CONSTRAINT = 9u;
const uint ERROR_PENETRATION_STEP_TOO_LARGE = 10u;

struct ParticleGeometry
{
    vec3 normal;
    float overlapArea;
    float centerDistance;
    float sourceRadius;
    float targetRadius;
    bool valid;
};

struct BoundaryWallSegment
{
    vec3 normal;
    float overlapArea;
    float centerDistance;
    uint wallFlag;
    bool valid;
};

struct ContactForceInput
{
    uint targetID;
    uint contactType;
    vec3 normal;
    float overlapArea;
    float penetrationDepth;
    vec3 targetVelocity;
    bool valid;
};

#ifndef MAX_SOURCE_DEPTH_CONSTRAINTS
#define MAX_SOURCE_DEPTH_CONSTRAINTS 16
#endif
uint maximumDepthConstraintOwner = 0xffffffffu;
uint maximumDepthConstraintCount = 0u;
vec3 maximumDepthConstraintNormals[MAX_SOURCE_DEPTH_CONSTRAINTS];
float maximumDepthConstraintLimits[MAX_SOURCE_DEPTH_CONSTRAINTS];

// Python source: ForceDynamics.py:19
float VelocityAngle(float vx, float vy)
{
    return (vx != 0.0 || vy != 0.0) ? atan(vy, vx) : 0.0;
}

// Python source: ForceDynamics.py:24
vec4 particle_position(uint ParticleID, uint positionBuffer)
{
    return (positionBuffer == 0u) ? P[ParticleID].PosLocA : P[ParticleID].PosLocB;
}

// Python source: ForceDynamics.py:31
float particle_overlap_area(float sourceRadius, float targetRadius, float centerDistance)
{
    if (centerDistance <= 0.0) {
        float minRadius = min(sourceRadius, targetRadius);
        return FORCE_DYNAMICS_PI * minRadius * minRadius;
    }
    if (centerDistance >= sourceRadius + targetRadius) { return 0.0; }
    if (centerDistance <= abs(sourceRadius - targetRadius)) {
        float minRadius = min(sourceRadius, targetRadius);
        return FORCE_DYNAMICS_PI * minRadius * minRadius;
    }

    float sourceTerm = (
        centerDistance * centerDistance + sourceRadius * sourceRadius
        - targetRadius * targetRadius) / (2.0 * centerDistance * sourceRadius);
    float targetTerm = (
        centerDistance * centerDistance + targetRadius * targetRadius
        - sourceRadius * sourceRadius) / (2.0 * centerDistance * targetRadius);
    sourceTerm = clamp(sourceTerm, -1.0, 1.0);
    targetTerm = clamp(targetTerm, -1.0, 1.0);
    float sourceArea = sourceRadius * sourceRadius * acos(sourceTerm);
    float targetArea = targetRadius * targetRadius * acos(targetTerm);
    float triangleArea = 0.5 * sqrt(max(
        0.0,
        (-centerDistance + sourceRadius + targetRadius)
        * (centerDistance + sourceRadius - targetRadius)
        * (centerDistance - sourceRadius + targetRadius)
        * (centerDistance + sourceRadius + targetRadius)));
    return sourceArea + targetArea - triangleArea;
}

// Python source: ForceDynamics.py:470
float ParticlePenetrationDepth(float sourceRadius, float targetRadius, float centerDistance)
{
    return sourceRadius + targetRadius - centerDistance;
}

bool IsNullParticle(uint ParticleID)
{
    return ParticleID == 0u && P[ParticleID].ptype < -0.5;
}

bool IsBoundaryParticle(uint ParticleID)
{
    return P[ParticleID].ptype > 0.5;
}

bool IsParticleDead(uint ParticleID)
{
    return P[ParticleID].Data.w < 0.0;
}

bool IsMobileParticleActiveForDynamics(uint ParticleID)
{
    return !IsNullParticle(ParticleID)
        && !IsBoundaryParticle(ParticleID)
        && !IsParticleDead(ParticleID);
}

vec4 GetParticlePosition(uint ParticleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].PosLocA
        : P[ParticleID].PosLocB;
}

vec4 GetNextParticlePosition(uint ParticleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].PosLocB
        : P[ParticleID].PosLocA;
}

vec4 GetParticleVelocity(uint ParticleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].VelRadA
        : P[ParticleID].VelRadB;
}

vec4 GetStartFrameVelocity(uint ParticleID)
{
    return GetParticleVelocity(ParticleID);
}

vec4 GetNextParticleVelocity(uint ParticleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].VelRadB
        : P[ParticleID].VelRadA;
}

void SetNextParticleVelocity(uint ParticleID, vec4 velocity)
{
    if (uint(ShaderFlags.positionBuffer) == 0u) {
        P[ParticleID].VelRadB = velocity;
    } else {
        P[ParticleID].VelRadA = velocity;
    }
}

bool SetError(uint errorCode)
{
    collOut.ErrorNumber = errorCode;
    collOut.FrameNumber = uint(ShaderFlags.frameNum);
    return false;
}

bool SetError(uint errorCode, uint SourceID)
{
    collOut.ErrorNumber = errorCode;
    collOut.FrameNumber = uint(ShaderFlags.frameNum);
    collOut.ParticleNumber = SourceID;
    return false;
}

float GetParticleMass(uint ParticleID)
{
    return max(P[ParticleID].parms.x, EPSILON);
}

float GetPairStiffness(uint SourceID, uint TargetID)
{
    return max(0.0, 0.5 * (P[SourceID].Data.y + P[TargetID].Data.y));
}

float GetContactStiffness(uint SourceID, uint TargetID, uint contactType)
{
    if (contactType == CONTACT_WALL) {
        return max(0.0, P[SourceID].Data.y);
    }
    return GetPairStiffness(SourceID, TargetID);
}

float WallContactOffsetDistance(float radius)
{
    return min(radius, radius * wall_contact_offset);
}

ParticleGeometry GetParticleGeometry(uint SourceID, uint TargetID)
{
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 targetPosition = GetParticlePosition(TargetID).xyz;
    vec3 delta = targetPosition - sourcePosition;
    float centerDistance = length(delta);
    float sourceRadius = P[SourceID].Data.x;
    float targetRadius = P[TargetID].Data.x;
    if (centerDistance >= sourceRadius + targetRadius) {
        return ParticleGeometry(vec3(0.0), 0.0, centerDistance,
            sourceRadius, targetRadius, false);
    }

    vec3 normal = (centerDistance <= EPSILON)
        ? vec3(1.0, 0.0, 0.0)
        : delta / centerDistance;
    float overlapArea = particle_overlap_area(
        sourceRadius, targetRadius, centerDistance);
    return ParticleGeometry(normal, overlapArea, centerDistance,
        sourceRadius, targetRadius, true);
}

bool CheckPenetrationStepResolution(
    uint SourceID, vec3 normal, float sourceRadius, vec3 targetVelocity)
{
    vec3 sourceVelocity = GetStartFrameVelocity(SourceID).xyz;
    float relativeNormalVelocity = dot(targetVelocity - sourceVelocity, normal);
    float inwardDisplacement = max(
        0.0, -relativeNormalVelocity * ShaderFlags.dt);
    float penetrationReserve =
        (1.0 - MAXIMUM_PENETRATION_FRACTION) * sourceRadius;
    if (inwardDisplacement > penetrationReserve + EPSILON) {
        return SetError(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID);
    }
    return true;
}

ParticleGeometry GetPhysicalParticleContact(uint SourceID, uint TargetID)
{
    ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);
    if (!geometry.valid) { return geometry; }

    float physicalProximity =
        geometry.centerDistance - geometry.targetRadius;
    if (physicalProximity < -EPSILON) {
        SetError(ERROR_PARTICLE_TUNNELING, SourceID);
        return ParticleGeometry(vec3(0.0), 0.0, geometry.centerDistance,
            geometry.sourceRadius, geometry.targetRadius, false);
    }
    if (!CheckPenetrationStepResolution(
            SourceID,
            geometry.normal,
            geometry.sourceRadius,
            GetStartFrameVelocity(TargetID).xyz)) {
        return ParticleGeometry(vec3(0.0), 0.0, geometry.centerDistance,
            geometry.sourceRadius, geometry.targetRadius, false);
    }
    return geometry;
}

bool RegisterMaximumDepthConstraint(
    uint SourceID,
    vec3 normal,
    float penetrationDepth,
    float sourceRadius,
    vec3 targetVelocity)
{
    if (maximumDepthConstraintOwner != SourceID) {
        maximumDepthConstraintOwner = SourceID;
        maximumDepthConstraintCount = 0u;
    }

    float maximumDepth = MAXIMUM_PENETRATION_FRACTION * sourceRadius;
    if (penetrationDepth < maximumDepth - EPSILON) {
        return true;
    }

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT, SourceID);
    }
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = normal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] =
        dot(targetVelocity, normal);
    maximumDepthConstraintCount += 1u;
    return true;
}

bool AccumulateContactForce(
    uint SourceID, ContactForceInput contact, inout vec3 totalForce)
{
    if (!contact.valid) { return true; }
    float stiffness = GetContactStiffness(
        SourceID, contact.targetID, contact.contactType);
    float forceMagnitude = stiffness * max(0.0, contact.penetrationDepth);
    totalForce -= forceMagnitude * contact.normal;
    P[SourceID].colFlg = 1u;
    return true;
}

bool ProcessParticleCollision(
    uint TargetID,
    uint SourceID,
    inout vec3 totalForce,
    ParticleGeometry geometry)
{
    if (!geometry.valid) { return true; }
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            geometry.normal,
            penetrationDepth,
            geometry.sourceRadius,
            GetStartFrameVelocity(TargetID).xyz)) {
        return false;
    }
    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        TargetID,
        CONTACT_PARTICLE,
        geometry.normal,
        geometry.overlapArea,
        penetrationDepth,
        GetStartFrameVelocity(TargetID).xyz,
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}

bool ProcessParametricWallCollision(
    uint SourceID, BoundaryWallSegment segment, inout vec3 totalForce)
{
    if (!segment.valid) { return true; }
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius, sourceRadius, segment.centerDistance);
    float maximumDepthDistance =
        sourceRadius - WallContactOffsetDistance(sourceRadius);
    if (segment.centerDistance - maximumDepthDistance < -EPSILON) {
        return SetError(ERROR_WALL_TUNNELING, SourceID);
    }
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, sourceRadius, vec3(0.0))) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            segment.normal,
            penetrationDepth,
            sourceRadius,
            vec3(0.0))) {
        return false;
    }
    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag,
        CONTACT_WALL,
        segment.normal,
        segment.overlapArea,
        penetrationDepth,
        vec3(0.0),
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}

bool ProjectSourceVelocityToContactSet(
    vec3 candidateVelocity, out vec3 containedVelocity)
{
    containedVelocity = candidateVelocity;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        vec3 normal = maximumDepthConstraintNormals[index];
        float limit = maximumDepthConstraintLimits[index];
        float current = dot(containedVelocity, normal);
        if (current > limit + EPSILON) {
            containedVelocity -= (current - limit) * normal;
        }
    }
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        if (dot(containedVelocity, maximumDepthConstraintNormals[index])
                > maximumDepthConstraintLimits[index] + EPSILON) {
            return false;
        }
    }
    return true;
}

bool ApplySourceMaximumDepth(uint SourceID)
{
    if (maximumDepthConstraintOwner != SourceID
            || maximumDepthConstraintCount == 0u) {
        return true;
    }

    vec4 candidate = GetNextParticleVelocity(SourceID);
    vec3 containedVelocity = vec3(0.0);
    if (!ProjectSourceVelocityToContactSet(
            candidate.xyz, containedVelocity)) {
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT, SourceID);
    }
    candidate.xyz = containedVelocity;
    candidate.w = VelocityAngle(candidate.x, candidate.y);
    SetNextParticleVelocity(SourceID, candidate);
    return true;
}

bool CalcVelocity(uint SourceID, vec3 totalForce)
{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) { return SetError(ERROR_INVALID_DT, SourceID); }
    float mass = GetParticleMass(SourceID);
    vec4 startVelocity = GetStartFrameVelocity(SourceID);
    vec4 nextVelocity = startVelocity;
    nextVelocity.xyz = startVelocity.xyz + totalForce * dt / mass;
    nextVelocity.w = VelocityAngle(nextVelocity.x, nextVelocity.y);
    SetNextParticleVelocity(SourceID, nextVelocity);
    return true;
}

bool CalcPosition(uint SourceID)
{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) { return SetError(ERROR_INVALID_DT, SourceID); }

    vec4 position = GetParticlePosition(SourceID);
    vec4 velocity = GetNextParticleVelocity(SourceID);
    vec3 nextPosition = position.xyz + velocity.xyz * dt;

    if (nextPosition.x < 0.0 || nextPosition.x >= float(WIDTH)
            || nextPosition.y < 0.0 || nextPosition.y >= float(HEIGHT)
            || nextPosition.z < 0.0 || nextPosition.z >= float(DEPTH)) {
        return SetError(ERROR_PARTICLE_OUT_OF_BOUNDS, SourceID);
    }

    if (uint(ShaderFlags.positionBuffer) == 0u) {
        P[SourceID].PosLocB = vec4(nextPosition, 0.0);
        P[SourceID].PosLocA.w = 1.0;
    } else {
        P[SourceID].PosLocA = vec4(nextPosition, 0.0);
        P[SourceID].PosLocB.w = 1.0;
    }

    if (nextPosition.x < death_x_min || nextPosition.x > death_x_max
            || nextPosition.y < death_y_min || nextPosition.y > death_y_max
            || nextPosition.z < death_z_min || nextPosition.z > death_z_max) {
        P[SourceID].Data.w = -1.0;
    }
    return true;
}

#endif
