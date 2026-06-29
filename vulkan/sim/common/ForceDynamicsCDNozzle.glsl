#ifndef FORCE_DYNAMICS_CD_NOZZLE_GLSL
#define FORCE_DYNAMICS_CD_NOZZLE_GLSL

// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.
// CD nozzle boundary-particle wall helpers. Requires ForceDynamics.glsl
// and ForceDynamicsBoundaryParticle.glsl.
// Do not hand edit generated dynamics content.

// Forward declarations for CD nozzle methods.
uint BoundaryParticleCDNozzleWallFlag(uint SourceID, uint BoundaryID);
float CDNozzleRadius(float axial_position);
float CDNozzleRadiusSlope(float axial_position);
BoundaryWallSegment EvaluateCDNozzleWallSegment(uint SourceID, uint BoundaryID);

// Python source: ForceDynamics.py:126
uint BoundaryParticleCDNozzleWallFlag(uint SourceID, uint BoundaryID)
{
    if (!IsBoundaryParticle(BoundaryID)) {
        return 0u;
    }

    vec4 boundary_position = GetParticlePosition(BoundaryID);
    return (boundary_position.y < CD_NOZZLE_CENTER_Y) ? 3u : 4u;
}

// Python source: ForceDynamics.py:160
float CDNozzleRadius(float axial_position)
{
    float inlet_end = CD_NOZZLE_INLET_LENGTH;
    float converge_end = inlet_end + CD_NOZZLE_CONVERGE_LENGTH;
    float throat_end = converge_end + CD_NOZZLE_THROAT_LENGTH;
    float diverge_end = throat_end + CD_NOZZLE_DIVERGE_LENGTH;

    if (axial_position >= 1.0 && axial_position < inlet_end) {
        return CD_NOZZLE_INLET_RADIUS;
    }
    if (axial_position >= inlet_end && axial_position < converge_end) {
        float span = max(CD_NOZZLE_CONVERGE_LENGTH, EPSILON);
        float t = (axial_position - inlet_end) / span;
        return CD_NOZZLE_INLET_RADIUS
            + t * (CD_NOZZLE_THROAT_RADIUS - CD_NOZZLE_INLET_RADIUS);
    }
    if (axial_position >= converge_end && axial_position < throat_end) {
        return CD_NOZZLE_THROAT_RADIUS;
    }
    if (axial_position >= throat_end && axial_position < diverge_end) {
        float span = max(CD_NOZZLE_DIVERGE_LENGTH, EPSILON);
        float t = (axial_position - throat_end) / span;
        return CD_NOZZLE_THROAT_RADIUS
            + t * (CD_NOZZLE_EXIT_RADIUS - CD_NOZZLE_THROAT_RADIUS);
    }
    if (axial_position >= diverge_end) {
        return CD_NOZZLE_EXIT_RADIUS;
    }
    return CD_NOZZLE_INLET_RADIUS;
}

// Python source: ForceDynamics.py:193
float CDNozzleRadiusSlope(float axial_position)
{
    float inlet_end = CD_NOZZLE_INLET_LENGTH;
    float converge_end = inlet_end + CD_NOZZLE_CONVERGE_LENGTH;
    float throat_end = converge_end + CD_NOZZLE_THROAT_LENGTH;
    float diverge_end = throat_end + CD_NOZZLE_DIVERGE_LENGTH;

    if (axial_position >= inlet_end && axial_position < converge_end) {
        return (CD_NOZZLE_THROAT_RADIUS - CD_NOZZLE_INLET_RADIUS)
            / max(CD_NOZZLE_CONVERGE_LENGTH, EPSILON);
    }
    if (axial_position >= throat_end && axial_position < diverge_end) {
        return (CD_NOZZLE_EXIT_RADIUS - CD_NOZZLE_THROAT_RADIUS)
            / max(CD_NOZZLE_DIVERGE_LENGTH, EPSILON);
    }
    return 0.0;
}

// Python source: ForceDynamics.py:319
BoundaryWallSegment EvaluateCDNozzleWallSegment(uint SourceID, uint BoundaryID)
{
    uint wall_flag = BoundaryParticleCDNozzleWallFlag(SourceID, BoundaryID);
    if (wall_flag == 0u) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);
    }

    vec4 source_position = GetParticlePosition(SourceID);
    float radius = P[SourceID].Data.x;
    float axial = source_position.x - CD_NOZZLE_START_X + 1.0;
    float total_length = CD_NOZZLE_INLET_LENGTH
        + CD_NOZZLE_CONVERGE_LENGTH
        + CD_NOZZLE_THROAT_LENGTH
        + CD_NOZZLE_DIVERGE_LENGTH
        + CD_NOZZLE_EXIT_LENGTH;
    if (axial < 1.0 || axial > total_length) {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);
    }

    float nozzle_radius = CDNozzleRadius(axial);
    float radius_slope = CDNozzleRadiusSlope(axial);
    float offset = WallContactOffsetDistance(radius);
    float wall_y = 0.0;
    vec3 normal = vec3(0.0);

    if (wall_flag == 3u) {
        wall_y = CD_NOZZLE_CENTER_Y - nozzle_radius;
        normal = normalize(vec3(-radius_slope, -1.0, 0.0));
    } else if (wall_flag == 4u) {
        wall_y = CD_NOZZLE_CENTER_Y + nozzle_radius;
        normal = normalize(vec3(-radius_slope, 1.0, 0.0));
    } else {
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);
    }

    vec3 wall_point = vec3(source_position.x, wall_y, source_position.z);
    vec3 ghost = wall_point + normal * (radius - offset);
    vec3 delta = ghost - source_position.xyz;
    float center_distance = length(delta);
    if (center_distance >= 2.0 * radius) {
        return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);
    }

    float overlap_area = particle_overlap_area(radius, radius, center_distance);
    return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);
}


#endif
