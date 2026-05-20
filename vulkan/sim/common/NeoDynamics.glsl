#ifndef NEO_DYNAMICS_GLSL
#define NEO_DYNAMICS_GLSL

const uint NEO_CONTACT_INACTIVE = 0u;
const uint NEO_CONTACT_PARTICLE = 1u;
const uint NEO_CONTACT_WALL = 2u;

const uint NEO_PHASE_INACTIVE = 0u;
const uint NEO_PHASE_COMPRESSION = 1u;
const uint NEO_PHASE_REBOUND = 2u;

const uint NEO_CONTACT_ACTIVE_THIS_FRAME = 1u;
const uint NEO_CONTACT_PENDING_THIS_FRAME = 2u;

const float NEO_EPSILON = 1.0e-12;

vec2 NeoCurrentLocation(uint particle_id)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[particle_id].PosLocA.xy
        : P[particle_id].PosLocB.xy;
}

float NeoRadius(uint particle_id)
{
    return P[particle_id].Data.x;
}

float NeoMass(uint particle_id)
{
    return max(P[particle_id].parms.x, NEO_EPSILON);
}

float NeoCollisionStiffness(uint source_id, uint target_id)
{
    float source_q = P[source_id].Data.y > 0.0 ? P[source_id].Data.y : NEO_COLLISION_STIFFNESS_Q;
    float target_q = P[target_id].Data.y > 0.0 ? P[target_id].Data.y : NEO_COLLISION_STIFFNESS_Q;
    return max(NEO_EPSILON, 0.5 * (source_q + target_q));
}

float NeoWallCollisionStiffness(uint source_id)
{
    return max(NEO_EPSILON, P[source_id].Data.y > 0.0 ? P[source_id].Data.y : NEO_COLLISION_STIFFNESS_Q);
}

float NeoReboundMinFraction(uint source_id)
{
    return max(0.0, P[source_id].Data.z > 0.0 ? P[source_id].Data.z : NEO_REBOUND_MIN_FRACTION);
}

float NeoCircleOverlapArea(float radius_i, float radius_j, float center_distance)
{
    if (abs(radius_i - radius_j) > 1.0e-12) {
        return 0.0;
    }

    float radius = radius_i;
    float distance = clamp(center_distance, 0.0, 2.0 * radius);
    return (
        2.0 * radius * radius * acos(distance / (2.0 * radius))
        - 0.5 * distance * sqrt(max(0.0, 4.0 * radius * radius - distance * distance))
    );
}

bool NeoParticleContactGeometry(
    uint source_id,
    uint target_id,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    vec2 delta = NeoCurrentLocation(target_id) - NeoCurrentLocation(source_id);
    center_distance = length(delta);

    float source_radius = NeoRadius(source_id);
    float target_radius = NeoRadius(target_id);
    float radius_sum = source_radius + target_radius;
    if (center_distance >= radius_sum) {
        return false;
    }

    normal = center_distance <= NEO_EPSILON ? vec2(1.0, 0.0) : delta / center_distance;
    overlap_area = NeoCircleOverlapArea(source_radius, target_radius, center_distance);
    return overlap_area > 0.0;
}

bool NeoWallContactGeometry(
    uint source_id,
    uint wall_flag,
    out vec2 normal,
    out float overlap_area,
    out float center_distance
) {
    vec2 location = NeoCurrentLocation(source_id);
    float radius = NeoRadius(source_id);
    float distance_to_wall = 0.0;

    if (wall_flag == 1u) {
        distance_to_wall = location.x - BOUNDARY_XMIN;
        normal = vec2(-1.0, 0.0);
    } else if (wall_flag == 2u) {
        distance_to_wall = BOUNDARY_XMAX - location.x;
        normal = vec2(1.0, 0.0);
    } else if (wall_flag == 3u) {
        distance_to_wall = location.y - BOUNDARY_YMIN;
        normal = vec2(0.0, -1.0);
    } else if (wall_flag == 4u) {
        distance_to_wall = BOUNDARY_YMAX - location.y;
        normal = vec2(0.0, 1.0);
    } else {
        return false;
    }

    if (distance_to_wall >= radius) {
        return false;
    }

    center_distance = max(0.0, 2.0 * distance_to_wall);
    overlap_area = NeoCircleOverlapArea(radius, radius, center_distance);
    return overlap_area > 0.0;
}

float NeoParticleZeroArea(
    uint source_id,
    uint target_id,
    float rel_normal_velocity,
    float current_overlap_area,
    float current_center_distance,
    out float zero_center_distance
) {
    float incoming_speed = max(0.0, -rel_normal_velocity);
    float source_mass = NeoMass(source_id);
    float target_mass = NeoMass(target_id);
    float reduced_mass = (source_mass * target_mass) / max(source_mass + target_mass, NEO_EPSILON);
    float radius_sum = NeoRadius(source_id) + NeoRadius(target_id);

    float alpha_zero = 0.0;
    if (incoming_speed > 0.0) {
        alpha_zero = pow((3.0 * reduced_mass * incoming_speed * incoming_speed) / (2.0 * NeoCollisionStiffness(source_id, target_id)), 1.0 / 3.0);
        alpha_zero = clamp(alpha_zero, 0.0, radius_sum);
    }

    zero_center_distance = max(0.0, radius_sum - alpha_zero);
    float zero_area = NeoCircleOverlapArea(NeoRadius(source_id), NeoRadius(target_id), zero_center_distance);
    if (zero_area + NEO_EPSILON < current_overlap_area) {
        zero_area = current_overlap_area;
        zero_center_distance = current_center_distance;
    }
    return zero_area;
}

float NeoWallZeroArea(
    uint source_id,
    float normal_velocity,
    float current_overlap_area,
    float current_center_distance,
    out float zero_center_distance
) {
    float incoming_speed = max(0.0, normal_velocity);
    float radius = NeoRadius(source_id);
    float alpha_zero = 0.0;
    if (incoming_speed > 0.0) {
        alpha_zero = pow((3.0 * NeoMass(source_id) * incoming_speed * incoming_speed) / (2.0 * NeoWallCollisionStiffness(source_id)), 1.0 / 3.0);
        alpha_zero = clamp(alpha_zero, 0.0, 2.0 * radius);
    }

    zero_center_distance = max(0.0, 2.0 * radius - alpha_zero);
    float zero_area = NeoCircleOverlapArea(radius, radius, zero_center_distance);
    if (zero_area + NEO_EPSILON < current_overlap_area) {
        zero_area = current_overlap_area;
        zero_center_distance = current_center_distance;
    }
    return zero_area;
}

void NeoBeginContactFrame(uint source_id)
{
    P[source_id].colFlg = 0u;
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        if (P[source_id].ncs[slot].ids.y != NEO_CONTACT_INACTIVE) {
            P[source_id].ncs[slot].ids.w = NEO_CONTACT_PENDING_THIS_FRAME;
        }
    }
}

int NeoFindContactSlot(uint source_id, uint target_id, uint contact_type)
{
    for (uint slot = 0u; slot < MAX_CONTACTS; ++slot) {
        if (P[source_id].ncs[slot].ids.x == target_id && P[source_id].ncs[slot].ids.y == contact_type) {
            return int(slot);
        }
    }
    return -1;
}

int NeoFindReusableContactSlot(uint source_id)
{
    uint tracked_count = min(P[source_id].contactCount, MAX_CONTACTS);
    for (uint slot = 0u; slot < tracked_count; ++slot) {
        if (P[source_id].ncs[slot].ids.y == NEO_CONTACT_INACTIVE) {
            return int(slot);
        }
    }
    if (tracked_count < MAX_CONTACTS) {
        P[source_id].contactCount = tracked_count + 1u;
        return int(tracked_count);
    }
    return -1;
}

void NeoAddParticleContact(uint source_id, uint target_id)
{
    vec2 normal;
    float overlap_area;
    float center_distance;
    if (!NeoParticleContactGeometry(source_id, target_id, normal, overlap_area, center_distance)) {
        return;
    }

    int found_slot = NeoFindContactSlot(source_id, target_id, NEO_CONTACT_PARTICLE);
    int slot_index = found_slot >= 0 ? found_slot : NeoFindReusableContactSlot(source_id);
    if (slot_index < 0) {
        return;
    }

    uint slot = uint(slot_index);
    vec2 source_velocity = P[source_id].VelRad.xy;
    vec2 target_velocity = P[target_id].VelRad.xy;

    if (found_slot < 0 || P[source_id].ncs[slot].ids.y == NEO_CONTACT_INACTIVE) {
        vec2 rel_velocity = target_velocity - source_velocity;
        float rel_normal_velocity = dot(rel_velocity, normal);
        float zero_center_distance;
        float zero_area = NeoParticleZeroArea(source_id, target_id, rel_normal_velocity, overlap_area, center_distance, zero_center_distance);

        P[source_id].ncs[slot].ids = uvec4(target_id, NEO_CONTACT_PARTICLE, NEO_PHASE_COMPRESSION, NEO_CONTACT_ACTIVE_THIS_FRAME);
        P[source_id].ncs[slot].vel = vec4(source_velocity, target_velocity);
        P[source_id].ncs[slot].geom = vec4(normal, zero_area, zero_center_distance);
    } else {
        P[source_id].ncs[slot].ids.w = NEO_CONTACT_ACTIVE_THIS_FRAME;
    }

    P[source_id].colFlg = 1u;
}

void NeoAddWallContact(uint source_id, uint wall_flag)
{
    vec2 normal;
    float overlap_area;
    float center_distance;
    if (!NeoWallContactGeometry(source_id, wall_flag, normal, overlap_area, center_distance)) {
        return;
    }

    int found_slot = NeoFindContactSlot(source_id, wall_flag, NEO_CONTACT_WALL);
    int slot_index = found_slot >= 0 ? found_slot : NeoFindReusableContactSlot(source_id);
    if (slot_index < 0) {
        return;
    }

    uint slot = uint(slot_index);
    vec2 source_velocity = P[source_id].VelRad.xy;
    if (found_slot < 0 || P[source_id].ncs[slot].ids.y == NEO_CONTACT_INACTIVE) {
        float normal_velocity = dot(source_velocity, normal);
        float zero_center_distance;
        float zero_area = NeoWallZeroArea(source_id, normal_velocity, overlap_area, center_distance, zero_center_distance);

        P[source_id].ncs[slot].ids = uvec4(wall_flag, NEO_CONTACT_WALL, NEO_PHASE_COMPRESSION, NEO_CONTACT_ACTIVE_THIS_FRAME);
        P[source_id].ncs[slot].vel = vec4(source_velocity, 0.0, 0.0);
        P[source_id].ncs[slot].geom = vec4(normal, zero_area, zero_center_distance);
    } else {
        P[source_id].ncs[slot].ids.w = NEO_CONTACT_ACTIVE_THIS_FRAME;
    }

    P[source_id].colFlg = 1u;
}

vec2 NeoPairVelocityPrediction(uint source_id, uint slot, float overlap_area)
{
    uint target_id = P[source_id].ncs[slot].ids.x;
    vec2 normal = P[source_id].ncs[slot].geom.xy;
    float zero_area = P[source_id].ncs[slot].geom.z;
    vec2 source_start = P[source_id].ncs[slot].vel.xy;
    vec2 target_start = P[source_id].ncs[slot].vel.zw;

    if (zero_area <= NEO_EPSILON) {
        return P[source_id].VelRad.xy;
    }

    float source_mass = NeoMass(source_id);
    float target_mass = NeoMass(target_id);
    float reduced_mass = (source_mass * target_mass) / max(source_mass + target_mass, NEO_EPSILON);
    vec2 start_rel = target_start - source_start;
    float incoming_momentum = max(0.0, -reduced_mass * dot(start_rel, normal));
    if (incoming_momentum <= 0.0) {
        P[source_id].ncs[slot].ids.z = NEO_PHASE_REBOUND;
        return P[source_id].VelRad.xy;
    }

    float compression_fraction = clamp(overlap_area / zero_area, 0.0, 1.0);
    if (P[source_id].ncs[slot].ids.z == NEO_PHASE_COMPRESSION && compression_fraction >= 1.0 - 1.0e-5) {
        P[source_id].ncs[slot].ids.z = NEO_PHASE_REBOUND;
    }

    vec2 turn_velocity = source_start - (incoming_momentum / source_mass) * normal;
    vec2 full_rebound_velocity = source_start - (2.0 * incoming_momentum / source_mass) * normal;

    if (P[source_id].ncs[slot].ids.z == NEO_PHASE_COMPRESSION) {
        float progress = 1.0 - sqrt(max(0.0, 1.0 - compression_fraction));
        return mix(source_start, turn_velocity, progress);
    }

    float rebound_velocity_fraction = sqrt(max(0.0, 1.0 - compression_fraction));
    vec2 predicted_velocity = mix(turn_velocity, full_rebound_velocity, rebound_velocity_fraction);

    vec2 target_turn_velocity = target_start + (incoming_momentum / target_mass) * normal;
    vec2 target_full_rebound_velocity = target_start + (2.0 * incoming_momentum / target_mass) * normal;
    vec2 predicted_target_velocity = mix(target_turn_velocity, target_full_rebound_velocity, rebound_velocity_fraction);

    float start_closing_speed = max(0.0, -dot(start_rel, normal));
    float minimum_outward_speed = NeoReboundMinFraction(source_id) * start_closing_speed;
    float rel_normal_velocity = dot(predicted_target_velocity - predicted_velocity, normal);
    if (rel_normal_velocity < minimum_outward_speed) {
        float correction = minimum_outward_speed - rel_normal_velocity;
        predicted_velocity -= 0.5 * correction * normal;
    }
    return predicted_velocity;
}

vec2 NeoWallVelocityPrediction(uint source_id, uint slot, float overlap_area)
{
    vec2 normal = P[source_id].ncs[slot].geom.xy;
    float zero_area = P[source_id].ncs[slot].geom.z;
    vec2 start_velocity = P[source_id].ncs[slot].vel.xy;
    float incoming_speed = dot(start_velocity, normal);

    if (incoming_speed <= 0.0 || zero_area <= NEO_EPSILON) {
        P[source_id].ncs[slot].ids.z = NEO_PHASE_REBOUND;
        return P[source_id].VelRad.xy;
    }

    float compression_fraction = clamp(overlap_area / zero_area, 0.0, 1.0);
    if (P[source_id].ncs[slot].ids.z == NEO_PHASE_COMPRESSION && compression_fraction >= 1.0 - 1.0e-5) {
        P[source_id].ncs[slot].ids.z = NEO_PHASE_REBOUND;
    }

    vec2 turn_velocity = start_velocity - incoming_speed * normal;
    vec2 full_rebound_velocity = start_velocity - 2.0 * incoming_speed * normal;

    if (P[source_id].ncs[slot].ids.z == NEO_PHASE_COMPRESSION) {
        float progress = 1.0 - sqrt(max(0.0, 1.0 - compression_fraction));
        return mix(start_velocity, turn_velocity, progress);
    }

    float rebound_velocity_fraction = sqrt(max(0.0, 1.0 - compression_fraction));
    vec2 predicted_velocity = mix(turn_velocity, full_rebound_velocity, rebound_velocity_fraction);

    float minimum_outward_speed = NeoReboundMinFraction(source_id) * incoming_speed;
    float predicted_normal_velocity = dot(predicted_velocity, normal);
    if (predicted_normal_velocity > -minimum_outward_speed) {
        predicted_velocity -= (predicted_normal_velocity + minimum_outward_speed) * normal;
    }
    return predicted_velocity;
}

void NeoProcessCollision(uint source_id)
{
    if (BOUNDARY_ENABLED != 0u) {
        for (uint wall_flag = 1u; wall_flag <= 4u; ++wall_flag) {
            NeoAddWallContact(source_id, wall_flag);
        }
    }

    vec2 combined_velocity = P[source_id].VelRad.xy;
    bool has_prediction = false;
    uint tracked_count = min(P[source_id].contactCount, MAX_CONTACTS);

    for (uint slot = 0u; slot < tracked_count; ++slot) {
        if (P[source_id].ncs[slot].ids.w != NEO_CONTACT_ACTIVE_THIS_FRAME) {
            P[source_id].ncs[slot].ids.y = NEO_CONTACT_INACTIVE;
            P[source_id].ncs[slot].ids.z = NEO_PHASE_INACTIVE;
            continue;
        }

        vec2 predicted_velocity = P[source_id].VelRad.xy;
        if (P[source_id].ncs[slot].ids.y == NEO_CONTACT_PARTICLE) {
            uint target_id = P[source_id].ncs[slot].ids.x;
            vec2 normal;
            float overlap_area;
            float center_distance;
            if (!NeoParticleContactGeometry(source_id, target_id, normal, overlap_area, center_distance)) {
                continue;
            }
            predicted_velocity = NeoPairVelocityPrediction(source_id, slot, overlap_area);
        } else if (P[source_id].ncs[slot].ids.y == NEO_CONTACT_WALL) {
            uint wall_flag = P[source_id].ncs[slot].ids.x;
            vec2 normal;
            float overlap_area;
            float center_distance;
            if (!NeoWallContactGeometry(source_id, wall_flag, normal, overlap_area, center_distance)) {
                continue;
            }
            predicted_velocity = NeoWallVelocityPrediction(source_id, slot, overlap_area);
        } else {
            continue;
        }

        vec2 start_velocity = P[source_id].ncs[slot].vel.xy;
        if (!has_prediction) {
            combined_velocity = start_velocity;
            has_prediction = true;
        }
        combined_velocity += predicted_velocity - start_velocity;
    }

    if (has_prediction) {
        P[source_id].VelRad.xy = combined_velocity;
        P[source_id].VelRad.w = length(P[source_id].VelRad.xy) > 0.0 ? atan(P[source_id].VelRad.y, P[source_id].VelRad.x) : 0.0;
        P[source_id].colFlg = 1u;
    }
}

#endif
