#version 450

layout(local_size_x = 256) in;

// Output buffer
layout(set = 0, binding = 0) buffer RandomBuffer {
    uint values[];
};

// Simple integer hash RNG
uint wang_hash(uint seed)
{
    seed = (seed ^ 61u) ^ (seed >> 16u);
    seed *= 9u;
    seed = seed ^ (seed >> 4u);
    seed *= 0x27d4eb2du;
    seed = seed ^ (seed >> 15u);
    return seed;
}
uint pcg(uint v)
{
    uint state = v * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}
void main()
{
    uint id = gl_GlobalInvocationID.x;

    // Create unique seed per thread
    uint seed = id + 123456u;

    // Generate random uint
    uint rnd = wang_hash(seed);

    // Store result
    values[id] = rnd;
}