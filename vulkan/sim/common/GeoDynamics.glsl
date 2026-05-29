#ifndef GEO_DYNAMICS_GLSL
#define GEO_DYNAMICS_GLSL

// Generated from the Python Geo path. Regenerate this file; do not patch it.

const float GEO_EPSILON = 1.0e-12;
const uint GEO_CONTACT_INACTIVE = 0u;
const uint GEO_CONTACT_PARTICLE = 1u;
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

void GeoBeginContactFrame(uint SourceID)
{
    P[SourceID].colFlg = 0u;
    P[SourceID].contactCount = 0u;
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        P[SourceID].contacts[slot].ids = uvec4(0u);
        P[SourceID].contacts[slot].geom = vec4(0.0);
        P[SourceID].contacts[slot].aux = vec4(0.0);
    }
}

void GeoAddParticleContact(uint SourceID, uint TargetID)
{
    if (SourceID == TargetID || TargetID >= NUMPARTS) {
        return;
    }

    uint tracked_count = min(P[SourceID].contactCount, MAX_CONTACTS);
    for (uint slot = 0u; slot < tracked_count; ++slot) {
        if (P[SourceID].contacts[slot].ids.x == TargetID
            && P[SourceID].contacts[slot].ids.y == GEO_CONTACT_PARTICLE) {
            return;
        }
    }
    if (tracked_count >= MAX_CONTACTS) {
        return;
    }

    GeoContactGeometry contact;
    if (!GeoParticleGeometry(SourceID, TargetID, contact)) {
        return;
    }

    uint slot = tracked_count;
    float source_radius = P[SourceID].Data.x;
    float target_radius = P[TargetID].Data.x;
    P[SourceID].contacts[slot].ids = uvec4(TargetID, GEO_CONTACT_PARTICLE, 0u, 0u);
    P[SourceID].contacts[slot].geom = vec4(contact.normal, contact.overlap_area);
    P[SourceID].contacts[slot].aux = vec4(
        contact.center_distance,
        source_radius + target_radius - contact.center_distance,
        0.0,
        0.0
    );
    P[SourceID].contactCount = tracked_count + 1u;
    P[SourceID].colFlg = 1u;
}

void GeoProcessCollisions(uint SourceID)
{
    if (P[SourceID].contactCount != 1u) {
        return;
    }

    uint TargetID = P[SourceID].contacts[0].ids.x;
    if (TargetID >= NUMPARTS) {
        return;
    }

    GeoContactGeometry contact;
    if (!GeoParticleGeometry(SourceID, TargetID, contact)) {
        return;
    }

    vec3 source_velocity = P[SourceID].VelRad.xyz;
    vec3 target_velocity = P[TargetID].VelRad.xyz;
    float relative_normal_velocity = dot(target_velocity - source_velocity, contact.normal);
    float stiffness_q = GeoPairStiffness(SourceID, TargetID);
    float impulse = stiffness_q * contact.overlap_area * ShaderFlags.dt;

    P[SourceID].VelRad.xyz -= (impulse / GeoMass(SourceID)) * contact.normal;
    P[SourceID].VelRad.w = length(P[SourceID].VelRad.xy) > 0.0
        ? atan(P[SourceID].VelRad.y, P[SourceID].VelRad.x)
        : 0.0;

    P[SourceID].contacts[0].geom = vec4(contact.normal, contact.overlap_area);
    P[SourceID].contacts[0].aux = vec4(
        contact.center_distance,
        P[SourceID].Data.x + P[TargetID].Data.x - contact.center_distance,
        relative_normal_velocity,
        impulse
    );
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
