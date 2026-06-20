#ifndef PIPE_RESERVOIR_ENTRY_GLSL
#define PIPE_RESERVOIR_ENTRY_GLSL

const uint PRE_STATE_RESERVOIR = 0u;
const uint PRE_STATE_ACTIVE = 1u;
const uint PRE_STATE_ESCAPED = 2u;
const uint PRE_STATE_RETAINED = 3u;

const uint PRE_ESCAPE_RESERVOIR = 0u;
const uint PRE_ESCAPE_ESCAPED = 1u;
const uint PRE_ESCAPE_RETAINED = 2u;

uint PipeReservoirState(uint particle_id)
{
    return uint(P[particle_id].Data.w + 0.5);
}

bool PipeReservoirLocationIsValid(uint particle_id, uint position_buffer)
{
    vec3 location = position_buffer == POSITION_BUFFER_A
        ? P[particle_id].PosLocA.xyz
        : P[particle_id].PosLocB.xyz;
    float radius = P[particle_id].Data.x;

    return location.x - radius >= 0.0
        && location.y - radius >= 0.0
        && location.z - radius >= 0.0
        && location.x + radius < float(WIDTH)
        && location.y + radius < float(HEIGHT)
        && location.z + radius < float(DEPTH);
}

bool PipeReservoirIsReservoir(uint particle_id)
{
    uint state = PipeReservoirState(particle_id);
    if (state == PRE_STATE_RESERVOIR) {
        return true;
    }

    return state == PRE_STATE_ACTIVE
        && !PipeReservoirLocationIsValid(particle_id, uint(ShaderFlags.positionBuffer));
}

bool PipeReservoirIsActive(uint particle_id)
{
    return PipeReservoirState(particle_id) == PRE_STATE_ACTIVE
        && PipeReservoirLocationIsValid(particle_id, uint(ShaderFlags.positionBuffer));
}

float PipeReservoirRand01(uint particle_id)
{
    float seed = float(particle_id) * 12.9898 + floor(ShaderFlags.frameNum) * 78.233;
    return fract(sin(seed) * 43758.5453123);
}

void PipeReservoirSetLocation(uint particle_id, vec2 location, uint position_buffer)
{
    P[particle_id].PosLocA.xy = location;
    P[particle_id].PosLocB.xy = location;
    P[particle_id].PosLocA.z = max(P[particle_id].PosLocA.z, P[particle_id].Data.x);
    P[particle_id].PosLocB.z = P[particle_id].PosLocA.z;
    P[particle_id].PosLocA.w = position_buffer == POSITION_BUFFER_A ? 0.0 : 1.0;
    P[particle_id].PosLocB.w = position_buffer == POSITION_BUFFER_B ? 0.0 : 1.0;
}

uint PipeReservoirReleaseLimit()
{
    float elapsed = max(0.0, ShaderFlags.frameNum * ShaderFlags.dt);
    return min(uint(floor(elapsed * PARTICLE_RATE)), NUMPARTS - 1u);
}

void PipeReservoirMaybeRelease(uint particle_id, uint position_buffer)
{
    if (!PipeReservoirIsReservoir(particle_id)) {
        return;
    }
    if (particle_id > PipeReservoirReleaseLimit()) {
        return;
    }

    float radius = P[particle_id].Data.x;
    float y_min = PIPE_Y_MIN + radius;
    float y_max = PIPE_Y_MAX - radius;
    float y = y_max >= y_min
        ? mix(y_min, y_max, PipeReservoirRand01(particle_id))
        : 0.5 * (PIPE_Y_MIN + PIPE_Y_MAX);

    P[particle_id].VelRad.xy = vec2(INLET_VELOCITY, 0.0);
    P[particle_id].VelRad.w = INLET_VELOCITY == 0.0 ? 0.0 : atan(0.0, INLET_VELOCITY);
    PipeReservoirSetLocation(particle_id, vec2(INLET_X + radius, y), position_buffer);
    P[particle_id].Data.w = float(PRE_STATE_ACTIVE);
}

void PipeReservoirApplyOutlet(uint particle_id, uint position_buffer)
{
    if (!PipeReservoirIsActive(particle_id)) {
        return;
    }

    float x = position_buffer == POSITION_BUFFER_A
        ? P[particle_id].PosLocA.x
        : P[particle_id].PosLocB.x;
    float radius = P[particle_id].Data.x;
    if (x - radius <= OUTLET_X) {
        return;
    }

    if (ESCAPE_MODE == PRE_ESCAPE_ESCAPED) {
        P[particle_id].Data.w = float(PRE_STATE_ESCAPED);
    } else if (ESCAPE_MODE == PRE_ESCAPE_RETAINED) {
        P[particle_id].Data.w = float(PRE_STATE_RETAINED);
    } else {
        P[particle_id].Data.w = float(PRE_STATE_RESERVOIR);
    }
    P[particle_id].VelRad.xy = vec2(0.0);
    P[particle_id].VelRad.w = 0.0;
}

#endif
