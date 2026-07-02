#version 460
#extension GL_ARB_separate_shader_objects : enable
//#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
//#extension GL_EXT_scalar_block_layout :enable


#include "params.glsl"
#include "../common/constants.glsl"
#include "../common/util.glsl"
#include "../common/push.glsl"
#include "../common/atomicg.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/Lockimage.glsl"
#include "../common/particle.glsl"

out gl_PerVertex {
    vec4 gl_Position;
    float gl_PointSize;
};

layout(binding = 2) uniform UniformBufferObject {
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

struct ParticleCellLocation {
    uint pindex;
    uint ploc;
    uint fill;
};

struct Particle {
    vec4 PosLocA;
    vec4 PosLocB;
    vec4 VelRad;
    vec4 Data;
    vec4 parms;
    ParticleCellLocation CornerList[8];
    uint contactCount;
    uint colFlg;
    float ptype;
    float temp_vel;
};

layout(std430, binding = 4) readonly buffer ParticleBuffer {
    Particle particles[];
};

layout(location = 0) in vec4 inPosition;
layout(location = 1) in vec4 inVelocity;
layout(location = 2) in vec4 inColor;
layout(location = 3) in vec4 inData;

layout(location = 0) out vec3 fragColor;
layout(location = 1) flat out float particleType;

void main()
{
    uint index = uint(gl_VertexIndex);
    if (index == 0u) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        gl_PointSize = 0.0;
        particleType = 0.0;
        fragColor = vec3(0.0);
        return;
    }

    vec3 position = particles[index].PosLocA.xyz;
    float radius = max(particles[index].Data.x, 0.0);
    float type = particles[index].ptype;

    gl_Position = ubo.proj * ubo.view * ubo.model * vec4(position, 1.0);

    gl_PointSize = max(2.0, 2.0 * radius);
	if(HSV_ON == 1)
	{
		if (P[index].ptype == 0)
			fragColor = colorizeVelocity(P[index].VelRad.w,HSV_SAT,HSV_VAL);
		else
			fragColor = vec3{1.0,1.0,1.0);
	}
	else
	{
		if(uint(P[index].colFlg) == 1)
			fragColor = vec3(1.0,0.0,0.0);	
		else if(uint(P[index].colFlg) == 0)
			fragColor = vec3(0.0,1.0,0.0);	
	}
}
