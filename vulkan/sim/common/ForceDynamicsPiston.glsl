#ifndef FORCE_DYNAMICS_PISTON_GLSL
#define FORCE_DYNAMICS_PISTON_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// Analytic moving-piston helpers. Requires reservoir.glsl,
// ForceDynamics.glsl, and ForceDynamicsBoundaryParticle.glsl.
// Do not hand edit generated dynamics content.

// Forward declarations for piston methods.
float GetPistonPosition(uint frame);
vec3 GetPistonVelocity(uint frame);
BoundaryWallSegment EvaluatePistonWall(uint SourceID);
bool ProcessPistonCollision(uint SourceID, inout vec3 totalForce);

// Python source: ForceDynamics.py:559
float GetPistonPosition(uint frame)
{
    if (frame <= PISTON_START_FRAME) { return CHAMBER_MIN.x; }
    float elapsed_frames = float(frame - PISTON_START_FRAME);
    float position = CHAMBER_MIN.x
        + elapsed_frames * ShaderFlags.dt * PISTON_VELOCITY.x;
    return min(position, CHAMBER_MAX.x);
}

// Python source: ForceDynamics.py:582
vec3 GetPistonVelocity(uint frame)
{
    if (frame < PISTON_START_FRAME
            || GetPistonPosition(frame) >= CHAMBER_MAX.x) {
        return vec3(0.0);
    }
    return PISTON_VELOCITY;
}

// Python source: ForceDynamics.py:593
BoundaryWallSegment EvaluatePistonWall(uint SourceID)
{
    vec3 source_position = GetParticlePosition(SourceID).xyz;
    if (source_position.y < CHAMBER_MIN.y || source_position.y > CHAMBER_MAX.y
            || source_position.z < CHAMBER_MIN.z || source_position.z > CHAMBER_MAX.z) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 1u, false);
    }
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    float piston_x = GetPistonPosition(uint(ShaderFlags.frameNum));
    vec3 normal = vec3(-1.0, 0.0, 0.0);
    vec3 ghost = vec3(piston_x - radius + offset, source_position.yz);
    float center_distance = length(ghost - source_position);
    if (center_distance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, center_distance, 1u, false);
    }
    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return BoundaryWallSegment(normal, overlap_area, center_distance, 1u, true);
}

// Python source: ForceDynamics.py:618
bool ProcessPistonCollision(uint SourceID, inout vec3 totalForce)
{
    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) { return true; }
    float source_radius = P[SourceID].Data.x;
    float penetration_depth = ParticlePenetrationDepth(
        source_radius, source_radius, segment.centerDistance);
    float maximum_depth_distance = source_radius
        - WallContactOffsetDistance(source_radius);
    if (segment.centerDistance - maximum_depth_distance < -EPSILON) {
        return SetError(ERROR_WALL_TUNNELING);
    }
    vec3 piston_velocity = GetPistonVelocity(uint(ShaderFlags.frameNum));
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, source_radius, piston_velocity)) {
        return false;
    }
    if (!RegisterMaximumDepthConstraint(
            SourceID, segment.normal, penetration_depth, source_radius,
            piston_velocity)) {
        return false;
    }
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag, CONTACT_WALL, segment.normal,
        segment.overlapArea, penetration_depth, piston_velocity, true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}


#endif
