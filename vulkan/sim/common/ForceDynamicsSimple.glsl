#ifndef FORCE_DYNAMICS_SIMPLE_GLSL
#define FORCE_DYNAMICS_SIMPLE_GLSL

// Generated from C:/_DJ/gPCD/python/base/ForceDynamics.py by tools/ExportForceDynamicsSimpleGLSL.py.
// Clean simple dynamics target for GenericGenData/TestPythonBoundarySpheres.
// Do not hand edit generated dynamics content.

const float EPSILON = 1.0e-12;
const float MAXIMUM_DEPTH_SOLVER_EPSILON = 1.0e-6;
const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;
const float TARGET_PENETRATION_FRACTION = 0.5;
const float HARD_PENETRATION_FRACTION = 0.75;
#ifndef FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN
#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN 8.0
#endif
#ifndef FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER
#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER 2.0
#endif
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

// Python source: ForceDynamics.py:536
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
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = 0u;
        collOut.holdPidx = 0u;
    }
    return false;
}

bool SetError(uint errorCode, uint SourceID)
{
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = SourceID;
        collOut.holdPidx = 0u;
    }
    return false;
}

bool SetErrorDetail(uint errorCode, uint SourceID, uint detail)
{
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = SourceID;
        collOut.holdPidx = detail;
    }
    return false;
}

float GetParticleMass(uint ParticleID)
{
    return max(P[ParticleID].parms.x, EPSILON);
}

float GetContactTargetDepth(float sourceRadius);
float GetContactHardDepth(float sourceRadius);
float GetContactRemainingDepth(float sourceRadius, float penetrationDepth);

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

float GetCompressionStiffnessGain()
{
    return max(0.0, FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN);
}

float GetCompressionStiffnessPower()
{
    return max(0.0, FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER);
}

float GetEffectiveContactStiffness(
    float baseStiffness, float penetrationDepth, float sourceRadius)
{
    float stiffness = max(0.0, baseStiffness);
    float gain = GetCompressionStiffnessGain();
    if (stiffness <= 0.0 || gain <= 0.0) {
        return stiffness;
    }

    float hardDepth = GetContactHardDepth(sourceRadius);
    if (hardDepth <= EPSILON) {
        return stiffness;
    }

    float compressionFraction = clamp(
        penetrationDepth / hardDepth, 0.0, 1.0);
    return stiffness * (
        1.0 + gain * pow(compressionFraction, GetCompressionStiffnessPower()));
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
    float penetrationReserve = GetContactHardDepth(sourceRadius);
    if (inwardDisplacement > penetrationReserve + EPSILON) {
        return SetErrorDetail(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID, 1001u);
    }
    return true;
}

float GetContactTargetDepth(float sourceRadius)
{
    return TARGET_PENETRATION_FRACTION * sourceRadius;
}

float GetContactHardDepth(float sourceRadius)
{
    return HARD_PENETRATION_FRACTION * sourceRadius;
}

float GetContactRemainingDepth(float sourceRadius, float penetrationDepth)
{
    return GetContactHardDepth(sourceRadius) - penetrationDepth;
}

float GetContactInwardDisplacement(
    uint SourceID, vec3 normal, vec3 targetVelocity, vec3 sourceVelocity)
{
    float relativeNormalVelocity = dot(targetVelocity - sourceVelocity, normal);
    return max(0.0, -relativeNormalVelocity * ShaderFlags.dt);
}

bool CheckResolvedContactStep(
    uint SourceID,
    vec3 normal,
    float penetrationDepth,
    float sourceRadius,
    vec3 targetVelocity)
{
    float remainingDepth = GetContactRemainingDepth(sourceRadius, penetrationDepth);
    if (penetrationDepth > GetContactHardDepth(sourceRadius) + EPSILON) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9001u);
    }

    vec3 resolvedVelocity = GetNextParticleVelocity(SourceID).xyz;
    float inwardDisplacement = GetContactInwardDisplacement(
        SourceID,
        normal,
        targetVelocity,
        resolvedVelocity);
    if (inwardDisplacement > remainingDepth + EPSILON) {
        return SetErrorDetail(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID, 1002u);
    }
    return true;
}

bool CheckResolvedParticleContactStep(
    uint SourceID,
    uint TargetID,
    ParticleGeometry geometry)
{
    if (!geometry.valid) { return true; }
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        geometry.normal,
        penetrationDepth,
        geometry.sourceRadius,
        GetStartFrameVelocity(TargetID).xyz);
}

bool CheckResolvedFunctionWallContactStep(
    uint SourceID,
    BoundaryWallSegment segment)
{
    if (!segment.valid) { return true; }
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        vec3(0.0));
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

    float targetDepth = GetContactTargetDepth(sourceRadius);
    if (penetrationDepth < targetDepth - EPSILON) {
        return true;
    }

    float normalLength = length(normal);
    if (normalLength <= MAXIMUM_DEPTH_SOLVER_EPSILON
            || isnan(normalLength) || isinf(normalLength)
            || any(isnan(targetVelocity)) || any(isinf(targetVelocity))) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9002u);
    }
    vec3 unitNormal = normal / normalLength;
    float limit = dot(targetVelocity, unitNormal);
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        float alignment = dot(
            maximumDepthConstraintNormals[index], unitNormal);
        if (alignment >= 1.0 - MAXIMUM_DEPTH_SOLVER_EPSILON) {
            maximumDepthConstraintLimits[index] = min(
                maximumDepthConstraintLimits[index], limit);
            return true;
        }
    }

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9003u);
    }
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = unitNormal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] = limit;
    maximumDepthConstraintCount += 1u;
    return true;
}

bool RegisterContactStepConstraint(
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

    float hardDepth = GetContactHardDepth(sourceRadius);
    if (penetrationDepth > hardDepth + EPSILON) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9001u);
    }

    float dt = ShaderFlags.dt;
    if (dt <= 0.0) { return SetError(ERROR_INVALID_DT, SourceID); }

    float normalLength = length(normal);
    if (normalLength <= MAXIMUM_DEPTH_SOLVER_EPSILON
            || isnan(normalLength) || isinf(normalLength)
            || any(isnan(targetVelocity)) || any(isinf(targetVelocity))) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9002u);
    }

    vec3 unitNormal = normal / normalLength;
    float remainingDepth = max(0.0, hardDepth - penetrationDepth);
    float limit = dot(targetVelocity, unitNormal) + remainingDepth / dt;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        float alignment = dot(
            maximumDepthConstraintNormals[index], unitNormal);
        if (alignment >= 1.0 - MAXIMUM_DEPTH_SOLVER_EPSILON) {
            maximumDepthConstraintLimits[index] = min(
                maximumDepthConstraintLimits[index], limit);
            return true;
        }
    }

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9003u);
    }
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = unitNormal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] = limit;
    maximumDepthConstraintCount += 1u;
    return true;
}

bool SolveMaximumDepthSystem(
    mat3 matrix,
    vec3 values,
    uint size,
    out vec3 solution)
{
    solution = vec3(0.0);
    if (size == 1u) {
        if (abs(matrix[0][0]) <= MAXIMUM_DEPTH_SOLVER_EPSILON) {
            return false;
        }
        solution.x = values.x / matrix[0][0];
        return !any(isnan(solution)) && !any(isinf(solution));
    }
    if (size == 2u) {
        float det = matrix[0][0] * matrix[1][1]
            - matrix[1][0] * matrix[0][1];
        if (abs(det) <= MAXIMUM_DEPTH_SOLVER_EPSILON) {
            return false;
        }
        solution.x = (values.x * matrix[1][1]
            - matrix[1][0] * values.y) / det;
        solution.y = (matrix[0][0] * values.y
            - values.x * matrix[0][1]) / det;
        return !any(isnan(solution)) && !any(isinf(solution));
    }
    return false;
}

bool AccumulateContactForce(
    uint SourceID, ContactForceInput contact, inout vec3 totalForce)
{
    if (!contact.valid) { return true; }
    float baseStiffness = GetContactStiffness(
        SourceID, contact.targetID, contact.contactType);
    float stiffness = GetEffectiveContactStiffness(
        baseStiffness,
        max(0.0, contact.penetrationDepth),
        P[SourceID].Data.x);
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

bool ProcessFunctionWallCollision(
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

bool RegisterResolvedParticleContactStep(
    uint SourceID,
    uint TargetID,
    ParticleGeometry geometry)
{
    if (!geometry.valid) { return true; }
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        geometry.normal,
        penetrationDepth,
        geometry.sourceRadius,
        GetStartFrameVelocity(TargetID).xyz);
}

bool RegisterResolvedFunctionWallContactStep(
    uint SourceID,
    BoundaryWallSegment segment)
{
    if (!segment.valid) { return true; }
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        vec3(0.0));
}

bool ProjectSourceVelocityToContactSet(
    vec3 candidateVelocity, out vec3 containedVelocity)
{
    containedVelocity = candidateVelocity;
    if (any(isnan(candidateVelocity)) || any(isinf(candidateVelocity))) {
        return false;
    }

    bool candidateValid = true;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {
        if (dot(maximumDepthConstraintNormals[index], candidateVelocity)
                > maximumDepthConstraintLimits[index]
                    + MAXIMUM_DEPTH_SOLVER_EPSILON) {
            candidateValid = false;
        }
    }
    if (candidateValid) {
        return true;
    }

    bool found = false;
    float bestDistanceSq = 0.0;
    for (uint i = 0u; i < maximumDepthConstraintCount; ++i) {
        for (uint jCode = 0u; jCode <= maximumDepthConstraintCount; ++jCode) {
            uint activeCount = 1u;
            uint j = 0u;
            if (jCode > 0u) {
                j = jCode - 1u;
                if (j <= i) { continue; }
                activeCount = 2u;
            }

            vec3 n0 = maximumDepthConstraintNormals[i];
            vec3 n1 = activeCount == 2u
                ? maximumDepthConstraintNormals[j] : vec3(0.0);
            vec3 limits = vec3(
                maximumDepthConstraintLimits[i],
                activeCount == 2u ? maximumDepthConstraintLimits[j] : 0.0,
                0.0);
            mat3 gram = mat3(0.0);
            gram[0][0] = dot(n0, n0);
            if (activeCount == 2u) {
                gram[0][1] = dot(n0, n1);
                gram[1][0] = gram[0][1];
                gram[1][1] = dot(n1, n1);
            }
            vec3 residual = vec3(
                dot(n0, candidateVelocity),
                activeCount == 2u ? dot(n1, candidateVelocity) : 0.0,
                0.0) - limits;
            vec3 multipliers;
            if (!SolveMaximumDepthSystem(
                    gram, residual, activeCount, multipliers)) {
                continue;
            }
            if (multipliers.x < -MAXIMUM_DEPTH_SOLVER_EPSILON
                    || (activeCount == 2u
                        && multipliers.y < -MAXIMUM_DEPTH_SOLVER_EPSILON)) {
                continue;
            }
            vec3 velocity = candidateVelocity - multipliers.x * n0;
            if (activeCount == 2u) { velocity -= multipliers.y * n1; }
            if (any(isnan(velocity)) || any(isinf(velocity))) { continue; }
            bool satisfiesAll = true;
            for (uint constraint = 0u;
                    constraint < maximumDepthConstraintCount;
                    ++constraint) {
                if (dot(maximumDepthConstraintNormals[constraint], velocity)
                        > maximumDepthConstraintLimits[constraint]
                            + MAXIMUM_DEPTH_SOLVER_EPSILON) {
                    satisfiesAll = false;
                }
            }
            if (!satisfiesAll) { continue; }
            float distanceSq = dot(
                candidateVelocity - velocity,
                candidateVelocity - velocity);
            if (isnan(distanceSq) || isinf(distanceSq)) { continue; }
            if (!found || distanceSq < bestDistanceSq) {
                found = true;
                bestDistanceSq = distanceSq;
                containedVelocity = velocity;
            }
        }
    }
    return found;
}

bool ApplySourceMaximumDepth(uint SourceID, uint failureDetail)
{
    if (maximumDepthConstraintOwner != SourceID
            || maximumDepthConstraintCount == 0u) {
        return true;
    }

    vec4 candidate = GetNextParticleVelocity(SourceID);
    vec3 containedVelocity = vec3(0.0);
    if (!ProjectSourceVelocityToContactSet(
            candidate.xyz, containedVelocity)) {
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, failureDetail);
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
