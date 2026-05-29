#ifndef GEO_DYNAMICS_GLSL
#define GEO_DYNAMICS_GLSL

// Generated from the Python Geo path. Regenerate this file; do not patch it.

const float GEO_EPSILON = 1.0e-12;
const uint GEO_CONTACT_INACTIVE = 0u;
const uint GEO_CONTACT_PARTICLE = 1u;
const uint GEO_PHASE_INACTIVE = 0u;
const uint GEO_PHASE_COMPRESSION = 1u;
const uint GEO_PHASE_RETURNING = 2u;
const uint GEO_CONTACT_ACTIVE_THIS_FRAME = 1u;
const uint GEO_POSITION_BUFFER_A = 0u;

struct GeoContactGeometry {
    vec3 normal;
    float overlap_area;
    float center_distance;
};

vec3 GeoCurrentLocation(uint ParticleID)
{
    return uint(ShaderFlags.positionBuffer) == GEO_POSITION_BUFFER_A
        ? P[ParticleID].PosLocA.xyz
        : P[ParticleID].PosLocB.xyz;
}

float GeoMass(uint ParticleID)
{
    return max(P[ParticleID].parms.x, GEO_EPSILON);
}

float GeoPairStiffness(uint SourceID, uint TargetID)
{
    return max(GEO_EPSILON, 0.5 * (P[SourceID].Data.y + P[TargetID].Data.y));
}

float GeoCircleOverlapArea(float source_radius, float target_radius, float center_distance)
{
    if (center_distance <= 0.0) {
        float radius = min(source_radius, target_radius);
        return PI * radius * radius;
    }
    if (center_distance >= source_radius + target_radius) {
        return 0.0;
    }
    if (center_distance <= abs(source_radius - target_radius)) {
        float radius = min(source_radius, target_radius);
        return PI * radius * radius;
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

bool GeoParticleGeometry(uint SourceID, uint TargetID, out GeoContactGeometry contact)
{
    vec3 delta = GeoCurrentLocation(TargetID) - GeoCurrentLocation(SourceID);
    contact.center_distance = length(delta);

    float source_radius = P[SourceID].Data.x;
    float target_radius = P[TargetID].Data.x;
    float radius_sum = source_radius + target_radius;
    if (contact.center_distance >= radius_sum) {
        return false;
    }

    contact.normal = contact.center_distance <= GEO_EPSILON
        ? vec3(1.0, 0.0, 0.0)
        : delta / contact.center_distance;
    contact.overlap_area = GeoCircleOverlapArea(source_radius, target_radius, contact.center_distance);
    return contact.overlap_area > 0.0;
}

void GeoContactContext(uint SourceID, out float total_overlap_area, out float available_source_momentum)
{
    total_overlap_area = 0.0;
    available_source_momentum = 0.0;
    vec3 source_velocity = P[SourceID].VelRad.xyz;

    for (uint TargetID = 0u; TargetID < NUMPARTS; ++TargetID) {
        if (TargetID == SourceID) {
            continue;
        }

        GeoContactGeometry contact;
        if (!GeoParticleGeometry(SourceID, TargetID, contact)) {
            continue;
        }

        vec3 target_velocity = P[TargetID].VelRad.xyz;
        float relative_normal_velocity = dot(target_velocity - source_velocity, contact.normal);
        float source_normal_velocity = dot(source_velocity, contact.normal);
        total_overlap_area += max(0.0, contact.overlap_area);
        if (relative_normal_velocity < -GEO_EPSILON) {
            available_source_momentum = max(
                available_source_momentum,
                GeoMass(SourceID) * max(0.0, source_normal_velocity)
            );
        }
    }
}

void GeoClearContactSlot(uint SourceID, uint slot)
{
    P[SourceID].contacts[slot].ids = uvec4(0u);
    P[SourceID].contacts[slot].geom = vec4(0.0);
    P[SourceID].contacts[slot].aux = vec4(0.0);
}

void GeoBeginContactFrame(uint SourceID)
{
    P[SourceID].colFlg = 0u;
    P[SourceID].contactCount = 0u;
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        if (P[SourceID].contacts[slot].ids.w != GEO_CONTACT_ACTIVE_THIS_FRAME) {
            GeoClearContactSlot(SourceID, slot);
            continue;
        }
        P[SourceID].contacts[slot].ids.w = 0u;
        P[SourceID].contacts[slot].geom = vec4(0.0);
        P[SourceID].contacts[slot].aux.x = 0.0;
        P[SourceID].contacts[slot].aux.y = 0.0;
        P[SourceID].contacts[slot].aux.w = 0.0;
    }
}

void GeoAddParticleContact(uint SourceID, uint TargetID)
{
    if (SourceID == TargetID || TargetID >= NUMPARTS) {
        return;
    }

    uint contact_slot = MAX_CONTACTS;
    uint free_slot = MAX_CONTACTS;
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        if (P[SourceID].contacts[slot].ids.x == TargetID
            && P[SourceID].contacts[slot].ids.y == GEO_CONTACT_PARTICLE) {
            contact_slot = slot;
            break;
        }
        if (free_slot == MAX_CONTACTS
            && P[SourceID].contacts[slot].ids.y == GEO_CONTACT_INACTIVE) {
            free_slot = slot;
        }
    }

    GeoContactGeometry contact;
    if (!GeoParticleGeometry(SourceID, TargetID, contact)) {
        return;
    }

    if (contact_slot == MAX_CONTACTS) {
        if (free_slot == MAX_CONTACTS) {
            return;
        }
        contact_slot = free_slot;
        P[SourceID].contacts[contact_slot].ids = uvec4(
            TargetID,
            GEO_CONTACT_PARTICLE,
            GEO_PHASE_COMPRESSION,
            GEO_CONTACT_ACTIVE_THIS_FRAME
        );
        P[SourceID].contacts[contact_slot].aux.z = 0.0;
    } else if (P[SourceID].contacts[contact_slot].ids.w == GEO_CONTACT_ACTIVE_THIS_FRAME) {
        return;
    }

    float source_radius = P[SourceID].Data.x;
    float target_radius = P[TargetID].Data.x;
    P[SourceID].contacts[contact_slot].ids.w = GEO_CONTACT_ACTIVE_THIS_FRAME;
    P[SourceID].contacts[contact_slot].geom = vec4(contact.normal, contact.overlap_area);
    P[SourceID].contacts[contact_slot].aux.x = contact.center_distance;
    P[SourceID].contacts[contact_slot].aux.y = source_radius + target_radius - contact.center_distance;
    P[SourceID].contacts[contact_slot].aux.w = 0.0;
    P[SourceID].contactCount = min(P[SourceID].contactCount + 1u, MAX_CONTACTS);
    P[SourceID].colFlg = 1u;
}

void GeoProcessCollisions(uint SourceID)
{
    if (P[SourceID].contactCount == 0u) {
        return;
    }

    float total_overlap_area = 0.0;
    float available_source_momentum = 0.0;
    vec3 source_velocity = P[SourceID].VelRad.xyz;
    GeoContactContext(SourceID, total_overlap_area, available_source_momentum);

    if (total_overlap_area <= GEO_EPSILON) {
        return;
    }

    vec3 delta_momentum = vec3(0.0);
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        if (P[SourceID].contacts[slot].ids.w != GEO_CONTACT_ACTIVE_THIS_FRAME) {
            continue;
        }

        uint TargetID = P[SourceID].contacts[slot].ids.x;
        if (TargetID >= NUMPARTS) {
            continue;
        }

        GeoContactGeometry contact;
        if (!GeoParticleGeometry(SourceID, TargetID, contact)) {
            continue;
        }

        vec3 target_velocity = P[TargetID].VelRad.xyz;
        float relative_normal_velocity = dot(target_velocity - source_velocity, contact.normal);
        float area_weight = max(0.0, contact.overlap_area / total_overlap_area);
        float target_total_overlap_area = 0.0;
        float target_available_momentum = 0.0;
        GeoContactContext(TargetID, target_total_overlap_area, target_available_momentum);
        float target_area_weight = target_total_overlap_area > GEO_EPSILON
            ? max(0.0, contact.overlap_area / target_total_overlap_area)
            : 0.0;
        float stiffness_q = GeoPairStiffness(SourceID, TargetID);
        float raw_impulse = stiffness_q * contact.overlap_area * ShaderFlags.dt;
        float source_available_share = available_source_momentum * area_weight;
        float target_available_share = target_available_momentum * target_area_weight;
        float weighted_available_momentum = min(source_available_share, target_available_share);
        float stored_internal_momentum = max(0.0, P[SourceID].contacts[slot].aux.z);
        float applied_impulse = 0.0;

        if (P[SourceID].contacts[slot].ids.z != GEO_PHASE_RETURNING
            && relative_normal_velocity < -GEO_EPSILON) {
            float compression_impulse = min(raw_impulse, weighted_available_momentum);
            applied_impulse += compression_impulse;
            stored_internal_momentum += compression_impulse;
            if (compression_impulse < raw_impulse) {
                P[SourceID].contacts[slot].ids.z = GEO_PHASE_RETURNING;
            } else {
                P[SourceID].contacts[slot].ids.z = GEO_PHASE_COMPRESSION;
            }
        }

        if (P[SourceID].contacts[slot].ids.z == GEO_PHASE_RETURNING) {
            float release_impulse = min(raw_impulse, stored_internal_momentum);
            applied_impulse += release_impulse;
            stored_internal_momentum -= release_impulse;
            if (stored_internal_momentum <= GEO_EPSILON) {
                stored_internal_momentum = 0.0;
            }
        }

        P[SourceID].contacts[slot].aux.z = stored_internal_momentum;
        delta_momentum -= applied_impulse * contact.normal;

        P[SourceID].contacts[slot].geom = vec4(contact.normal, contact.overlap_area);
        P[SourceID].contacts[slot].aux.x = contact.center_distance;
        P[SourceID].contacts[slot].aux.y =
            P[SourceID].Data.x + P[TargetID].Data.x - contact.center_distance;
        P[SourceID].contacts[slot].aux.w = applied_impulse;
    }

    P[SourceID].VelRad.xyz += delta_momentum / GeoMass(SourceID);
    P[SourceID].VelRad.w = length(P[SourceID].VelRad.xy) > 0.0
        ? atan(P[SourceID].VelRad.y, P[SourceID].VelRad.x)
        : 0.0;
}

void GeoMoveParticle(uint SourceID, uint positionBuffer, float dt)
{
    vec3 velocity = P[SourceID].VelRad.xyz;

    if (positionBuffer == GEO_POSITION_BUFFER_A) {
        P[SourceID].PosLocB.xyz = P[SourceID].PosLocA.xyz + velocity * dt;
        P[SourceID].PosLocA.w = 1.0;
        P[SourceID].PosLocB.w = 0.0;
    } else {
        P[SourceID].PosLocA.xyz = P[SourceID].PosLocB.xyz + velocity * dt;
        P[SourceID].PosLocA.w = 0.0;
        P[SourceID].PosLocB.w = 1.0;
    }
}

#endif
