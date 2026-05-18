// Geometry dynamics collision response kernel.
//
// This file is intentionally separate from dynamics_collision.glsl. The old
// overlap-momentum GPU response remains intact while this file carries the new
// overlap-geometry model.
//
// Design boundary:
// - One invocation owns one SourceID.
// - The invocation may read target particles, but it writes only P[SourceID].
// - Contact detection is still expected to populate P[SourceID].ccs.
// - Wall contacts are derived from the configured flat boundary box.
//
// Model notes:
// - Collision response is driven by current overlap area, not by a force
//   integrated through dt.
// - zero_velocity_overlap_fraction selects the designed A_zero for natural
//   contacts. A compile-time define can override the default value below.
// - Starting overlaps at frame 0 are treated as post-turnaround rebound
//   diagnostics. The cfg velocity is interpreted as the incoming first-contact
//   velocity and is converted to the current-overlap rebound velocity.
//
// GPU limitation:
// - The current Particle SSBO has no pair-level contact-state buffer. This file
//   therefore computes geometry predictions from the live contact list and the
//   current velocity. Exact CPU parity for multi-frame rebound/compression
//   phases will require a small per-contact state buffer that stores
//   first-contact velocities, phase, and A_zero.


#ifndef GEO_ZERO_VELOCITY_OVERLAP_FRACTION
#define GEO_ZERO_VELOCITY_OVERLAP_FRACTION 0.2
#endif

#ifndef GEO_ZERO_VELOCITY_OVERLAP_TOLERANCE
#define GEO_ZERO_VELOCITY_OVERLAP_TOLERANCE 0.01
#endif

#ifndef GEO_REBOUND_MIN_FRACTION
#define GEO_REBOUND_MIN_FRACTION 0.02
#endif

const uint GEO_CCS_CONTACT_ACTIVE = 1u;
const float GEO_EPSILON_DISTANCE = 1.0e-12;

struct GeoPairPrediction {
    bool valid;
    vec2 source_velocity;
    vec2 target_velocity;
    float overlap_area;
    float zero_overlap_area;
    float compression_fraction;
    bool rebound;
};

struct GeoWallPrediction {
    bool valid;
    vec2 source_velocity;
    float overlap_area;
    float zero_overlap_area;
    float compression_fraction;
    bool rebound;
};

vec2 GeoCurrentLocation(uint particle_id)
{
    Particle particle = P[particle_id];
    if (uint(ShaderFlags.positionBuffer) == 0u) {
        return particle.PosLocA.xy;
    }
    return particle.PosLocB.xy;
}

float GeoParticleRadius(uint particle_id)
{
    return P[particle_id].Data.x;
}

float GeoInverseSquareSoftening(uint particle_id)
{
    return max(P[particle_id].Data.y, GEO_EPSILON_DISTANCE);
}

float GeoMomentumPerArea(uint particle_id)
{
    return P[particle_id].Data.z;
}

float GeoParticleMass(uint particle_id)
{
    return max(P[particle_id].parms.x, GEO_EPSILON_DISTANCE);
}

float GeoCircleOverlapArea(float source_radius, float target_radius, float center_distance)
{
    // Match the current Python reference: equal-radius disk intersection only.
    if (abs(source_radius - target_radius) > 1.0e-12) {
        return 0.0;
    }

    float radius = source_radius;
    float distance = clamp(center_distance, 0.0, 2.0 * radius);
    return (
        2.0 * radius * radius * acos(distance / (2.0 * radius))
        - 0.5 * distance * sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
    );
}

float GeoInverseSquareWeight(uint source_id, float center_distance)
{
    float softening = GeoInverseSquareSoftening(source_id);
    return 1.0;// / max(center_distance * center_distance, softening * softening);
}

float GeoOverlapMomentum(uint source_id, float overlap_area, float center_distance)
{
    return GeoMomentumPerArea(source_id) * overlap_area * GeoInverseSquareWeight(source_id, center_distance);
}

float GeoMaxOverlapArea(float radius)
{
    return GeoCircleOverlapArea(radius, radius, 0.0);
}

float GeoConfiguredZeroOverlapArea(float source_radius, float target_radius)
{
    float max_overlap_area = GeoCircleOverlapArea(source_radius, target_radius, 0.0);
    return clamp(float(GEO_ZERO_VELOCITY_OVERLAP_FRACTION) * max_overlap_area, 0.0, max_overlap_area);
}

bool GeoParticleContactGeometry(
    uint source_id,
    uint target_id,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    vec2 source_location = GeoCurrentLocation(source_id);
    vec2 target_location = GeoCurrentLocation(target_id);
    vec2 delta = target_location - source_location;
    center_distance = length(delta);

    float source_radius = GeoParticleRadius(source_id);
    float target_radius = GeoParticleRadius(target_id);
    float radius_sum = source_radius + target_radius;
    if (center_distance >= radius_sum) {
        return false;
    }

    normal = center_distance <= GEO_EPSILON_DISTANCE ? vec2(1.0, 0.0) : delta / center_distance;

    // Keep the same effective contact distance used by the Python support
    // geometry for particle-particle contacts.
    float penetration = min(radius_sum - center_distance, min(source_radius, target_radius));
    float contact_distance = radius_sum - penetration;
    overlap_area = GeoCircleOverlapArea(source_radius, target_radius, contact_distance);
    return overlap_area > 0.0;
}

bool GeoBoundaryWallContactGeometry(
    uint source_id,
    uint wall_flag,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    vec2 source_location = GeoCurrentLocation(source_id);
    float radius = GeoParticleRadius(source_id);
    float distance_to_wall = 0.0;

    if (wall_flag == 1u) {
        distance_to_wall = source_location.x - BOUNDARY_XMIN;
        normal = vec2(-1.0, 0.0);
    } else if (wall_flag == 2u) {
        distance_to_wall = BOUNDARY_XMAX - source_location.x;
        normal = vec2(1.0, 0.0);
    } else if (wall_flag == 3u) {
        distance_to_wall = source_location.y - BOUNDARY_YMIN;
        normal = vec2(0.0, -1.0);
    } else if (wall_flag == 4u) {
        distance_to_wall = BOUNDARY_YMAX - source_location.y;
        normal = vec2(0.0, 1.0);
    } else {
        return false;
    }

    if (distance_to_wall >= radius) {
        return false;
    }

    // Wall overlap uses the mirrored-circle geometry: distance to wall maps to
    // a center distance between the particle and its mirror image.
    center_distance = max(0.0, 2.0 * distance_to_wall);
    overlap_area = GeoCircleOverlapArea(radius, radius, center_distance);
    return overlap_area > 0.0;
}

float GeoSolvedPairZeroOverlapArea(
    uint source_id,
    uint target_id,
    float incoming_relative_normal_momentum,
    float current_overlap_area
) {
    float source_radius = GeoParticleRadius(source_id);
    float target_radius = GeoParticleRadius(target_id);
    float max_overlap_area = GeoCircleOverlapArea(source_radius, target_radius, 0.0);
    float source_mpa = max(GeoMomentumPerArea(source_id), GEO_EPSILON_DISTANCE);
    float zero_overlap_area = incoming_relative_normal_momentum / source_mpa;
    return clamp(max(zero_overlap_area, current_overlap_area), 0.0, max_overlap_area);
}

float GeoSolvedWallZeroOverlapArea(
    uint source_id,
    float incoming_normal_momentum,
    float current_overlap_area
) {
    float radius = GeoParticleRadius(source_id);
    float max_overlap_area = GeoMaxOverlapArea(radius);
    float source_mpa = max(GeoMomentumPerArea(source_id), GEO_EPSILON_DISTANCE);
    float zero_overlap_area = incoming_normal_momentum / source_mpa;
    return clamp(max(zero_overlap_area, current_overlap_area), 0.0, max_overlap_area);
}

float GeoVelocityFraction(float overlap_area, float zero_overlap_area)
{
    if (zero_overlap_area <= GEO_EPSILON_DISTANCE) {
        return 1.0;
    }

    float compression_fraction = clamp(overlap_area / zero_overlap_area, 0.0, 1.0);
    return sqrt(max(0.0, 1.0 - compression_fraction));
}

GeoPairPrediction GeoPredictPairFromStart(
    uint source_id,
    uint target_id,
    vec2 source_start_velocity,
    vec2 target_start_velocity,
    vec2 normal,
    float overlap_area,
    float zero_overlap_area,
    bool rebound
) {
    GeoPairPrediction prediction;
    prediction.valid = false;
    prediction.source_velocity = P[source_id].VelRad.xy;
    prediction.target_velocity = P[target_id].VelRad.xy;
    prediction.overlap_area = overlap_area;
    prediction.zero_overlap_area = zero_overlap_area;
    prediction.compression_fraction = zero_overlap_area > GEO_EPSILON_DISTANCE
        ? clamp(overlap_area / zero_overlap_area, 0.0, 1.0)
        : 0.0;
    prediction.rebound = rebound;

    vec2 start_relative_velocity = target_start_velocity - source_start_velocity;
    float start_relative_normal_velocity = dot(start_relative_velocity, normal);
    float source_mass = GeoParticleMass(source_id);
    float target_mass = GeoParticleMass(target_id);
    float reduced_mass = (source_mass * target_mass) / max(source_mass + target_mass, GEO_EPSILON_DISTANCE);
    float incoming_relative_normal_momentum = max(0.0, -reduced_mass * start_relative_normal_velocity);
    if (incoming_relative_normal_momentum <= 0.0 && rebound) {
        // Without a GPU contact-state buffer, the frame after turnaround may
        // see near-zero current velocity and forget the first-contact incoming
        // momentum. Reconstruct a source-owned rebound momentum from A_zero so
        // the contact can leave the zero-velocity point instead of sticking.
        incoming_relative_normal_momentum = GeoMomentumPerArea(source_id) * zero_overlap_area;
    }
    if (incoming_relative_normal_momentum <= 0.0 || zero_overlap_area <= GEO_EPSILON_DISTANCE) {
        return prediction;
    }

    float velocity_fraction = GeoVelocityFraction(overlap_area, zero_overlap_area);
    if (rebound) {
        velocity_fraction = max(velocity_fraction, float(GEO_REBOUND_MIN_FRACTION));
    }
    float compression_progress = 1.0 - velocity_fraction;

    vec2 source_turn_velocity = source_start_velocity - (incoming_relative_normal_momentum / source_mass) * normal;
    vec2 target_turn_velocity = target_start_velocity + (incoming_relative_normal_momentum / target_mass) * normal;
    vec2 source_full_velocity = source_start_velocity - (2.0 * incoming_relative_normal_momentum / source_mass) * normal;
    vec2 target_full_velocity = target_start_velocity + (2.0 * incoming_relative_normal_momentum / target_mass) * normal;

    if (rebound) {
        prediction.source_velocity = mix(source_turn_velocity, source_full_velocity, velocity_fraction);
        prediction.target_velocity = mix(target_turn_velocity, target_full_velocity, velocity_fraction);
    } else {
        prediction.source_velocity = mix(source_start_velocity, source_turn_velocity, compression_progress);
        prediction.target_velocity = mix(target_start_velocity, target_turn_velocity, compression_progress);
    }
    prediction.valid = true;
    return prediction;
}

GeoPairPrediction GeoPredictPair(uint source_id, uint target_id)
{
    GeoPairPrediction prediction;
    prediction.valid = false;
    prediction.source_velocity = P[source_id].VelRad.xy;
    prediction.target_velocity = P[target_id].VelRad.xy;
    prediction.overlap_area = 0.0;
    prediction.zero_overlap_area = 0.0;
    prediction.compression_fraction = 0.0;
    prediction.rebound = false;

    vec2 normal;
    float overlap_area;
    float center_distance;
    if (!GeoParticleContactGeometry(source_id, target_id, normal, overlap_area, center_distance)) {
        return prediction;
    }

    vec2 source_velocity = P[source_id].VelRad.xy;
    vec2 target_velocity = P[target_id].VelRad.xy;
    vec2 relative_velocity = target_velocity - source_velocity;
    float relative_normal_velocity = dot(relative_velocity, normal);
    float zero_overlap_area = GeoConfiguredZeroOverlapArea(
        GeoParticleRadius(source_id),
        GeoParticleRadius(target_id)
    );

    bool starting_overlap = uint(ShaderFlags.frameNum) == 0u;
    bool rebound = relative_normal_velocity >= 0.0;
    if (starting_overlap) {
        float source_mass = GeoParticleMass(source_id);
        float target_mass = GeoParticleMass(target_id);
        float reduced_mass = (source_mass * target_mass) / max(source_mass + target_mass, GEO_EPSILON_DISTANCE);
        float incoming_momentum = max(0.0, -reduced_mass * relative_normal_velocity);
        zero_overlap_area = GeoSolvedPairZeroOverlapArea(
            source_id,
            target_id,
            incoming_momentum,
            overlap_area
        );
        rebound = true;
    } else if (overlap_area >= zero_overlap_area * (1.0 - float(GEO_ZERO_VELOCITY_OVERLAP_TOLERANCE))) {
        rebound = true;
    }

    return GeoPredictPairFromStart(
        source_id,
        target_id,
        source_velocity,
        target_velocity,
        normal,
        overlap_area,
        zero_overlap_area,
        rebound
    );
}

GeoWallPrediction GeoPredictWallFromStart(
    uint source_id,
    vec2 source_start_velocity,
    vec2 normal,
    float overlap_area,
    float zero_overlap_area,
    bool rebound
) {
    GeoWallPrediction prediction;
    prediction.valid = false;
    prediction.source_velocity = P[source_id].VelRad.xy;
    prediction.overlap_area = overlap_area;
    prediction.zero_overlap_area = zero_overlap_area;
    prediction.compression_fraction = zero_overlap_area > GEO_EPSILON_DISTANCE
        ? clamp(overlap_area / zero_overlap_area, 0.0, 1.0)
        : 0.0;
    prediction.rebound = rebound;

    float incoming_speed = dot(source_start_velocity, normal);
    if (incoming_speed <= 0.0 && rebound) {
        // Same stateless rebound fallback as particle pairs, converted back to
        // speed for a wall where the wall has effectively infinite mass.
        incoming_speed = (GeoMomentumPerArea(source_id) * zero_overlap_area) / GeoParticleMass(source_id);
    }
    if (incoming_speed <= 0.0 || zero_overlap_area <= GEO_EPSILON_DISTANCE) {
        return prediction;
    }

    float velocity_fraction = GeoVelocityFraction(overlap_area, zero_overlap_area);
    if (rebound) {
        velocity_fraction = max(velocity_fraction, float(GEO_REBOUND_MIN_FRACTION));
    }
    float compression_progress = 1.0 - velocity_fraction;

    vec2 turn_velocity = source_start_velocity - incoming_speed * normal;
    vec2 full_velocity = source_start_velocity - 2.0 * incoming_speed * normal;
    prediction.source_velocity = rebound
        ? mix(turn_velocity, full_velocity, velocity_fraction)
        : mix(source_start_velocity, turn_velocity, compression_progress);
    prediction.valid = true;
    return prediction;
}

GeoWallPrediction GeoPredictWall(uint source_id, uint wall_flag)
{
    GeoWallPrediction prediction;
    prediction.valid = false;
    prediction.source_velocity = P[source_id].VelRad.xy;
    prediction.overlap_area = 0.0;
    prediction.zero_overlap_area = 0.0;
    prediction.compression_fraction = 0.0;
    prediction.rebound = false;

    vec2 normal;
    float overlap_area;
    float center_distance;
    if (!GeoBoundaryWallContactGeometry(source_id, wall_flag, normal, overlap_area, center_distance)) {
        return prediction;
    }

    vec2 source_velocity = P[source_id].VelRad.xy;
    float normal_velocity = dot(source_velocity, normal);
    float zero_overlap_area = GeoConfiguredZeroOverlapArea(
        GeoParticleRadius(source_id),
        GeoParticleRadius(source_id)
    );

    bool starting_overlap = uint(ShaderFlags.frameNum) == 0u;
    bool rebound = normal_velocity <= 0.0;
    vec2 first_contact_velocity = source_velocity;
    if (starting_overlap) {
        if (normal_velocity < 0.0) {
            first_contact_velocity = source_velocity - 2.0 * normal_velocity * normal;
        }
        float incoming_momentum = GeoParticleMass(source_id) * max(0.0, dot(first_contact_velocity, normal));
        zero_overlap_area = GeoSolvedWallZeroOverlapArea(source_id, incoming_momentum, overlap_area);
        rebound = true;
    } else if (overlap_area >= zero_overlap_area * (1.0 - float(GEO_ZERO_VELOCITY_OVERLAP_TOLERANCE))) {
        rebound = true;
    }

    return GeoPredictWallFromStart(
        source_id,
        first_contact_velocity,
        normal,
        overlap_area,
        zero_overlap_area,
        rebound
    );
}

void GeoProcessParticleContacts(uint SourceID, inout vec2 velocity_delta)
{
    uint contact_count = min(P[SourceID].sltnum, 12u);
    for (uint slot = 0u; slot < contact_count; ++slot) {
        ccoll contact_record = P[SourceID].ccs[slot];
        if (contact_record.clflg != GEO_CCS_CONTACT_ACTIVE) {
            continue;
        }

        uint TargetID = contact_record.pindex;
        if (TargetID >= NUMPARTS || TargetID == SourceID) {
            continue;
        }

        GeoPairPrediction prediction = GeoPredictPair(SourceID, TargetID);
        if (!prediction.valid) {
            continue;
        }

        P[SourceID].ColFlg = 1u;
        velocity_delta += prediction.source_velocity - P[SourceID].VelRad.xy;
    }
}

void GeoProcessBoundaryContacts(uint SourceID, inout vec2 velocity_delta)
{
    if (BOUNDARY_ENABLED == 0u) {
        return;
    }

    for (uint wall_flag = 1u; wall_flag <= 4u; ++wall_flag) {
        GeoWallPrediction prediction = GeoPredictWall(SourceID, wall_flag);
        if (!prediction.valid) {
            continue;
        }

        P[SourceID].ColFlg = 1u;
        velocity_delta += prediction.source_velocity - P[SourceID].VelRad.xy;
    }
}

void GeoProcessCollision(uint SourceID)
{
    vec2 velocity_delta = vec2(0.0);
    GeoProcessParticleContacts(SourceID, velocity_delta);
    GeoProcessBoundaryContacts(SourceID, velocity_delta);

    P[SourceID].VelRad.xy += velocity_delta;
    P[SourceID].VelRad.w = length(P[SourceID].VelRad.xy) > 0.0
        ? atan(P[SourceID].VelRad.y, P[SourceID].VelRad.x)
        : 0.0;

    // Diagnostic compatibility with the old report slots. GeoDynamics writes
    // velocity deltas rather than overlap momentum.
    P[SourceID].parms.y = velocity_delta.x;
    P[SourceID].parms.z = velocity_delta.y;
    P[SourceID].parms.w = length(velocity_delta);
}
