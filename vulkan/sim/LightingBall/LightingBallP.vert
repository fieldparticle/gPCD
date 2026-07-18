#version 460
#extension GL_ARB_separate_shader_objects : enable
//#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
//#extension GL_EXT_scalar_block_layout :enable

#include "params.glsl"
#include "material.glsl"
#include "../common/constants.glsl"
#include "../common/util.glsl"
#include "../common/push.glsl"
#include "../common/atomicg.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/Lockimage.glsl"
#include "../common/particle.glsl"
#include "../common/color_map.glsl"

out gl_PerVertex {
    vec4 gl_Position;
	float gl_PointSize;
};

layout(binding = 2) uniform UniformBufferObject{
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

layout(location = 0) in vec4 inPosition;
layout(location = 1) in vec4 incurvel;
layout(location = 2) in vec4 inColor;
layout(location = 3) in vec2 inParms;

layout(location = 0) out vec4 fragColor;
layout(location = 1) out vec2 outParms;
layout(location = 2) out vec3 matpos;

bool IsParticlePendingBirth(uint ParticleID)
{
	float stateFlag = P[ParticleID].Data.w;
	if (stateFlag <= 0.0)
		return false;
	return float(ShaderFlags.frameNum) < stateFlag;
}

bool IsParticleActiveForLifecycle(uint ParticleID)
{
	return ParticleID != 0u
		&& P[ParticleID].Data.w >= 0.0
		&& !IsParticlePendingBirth(ParticleID);
}

uint addUniqueCell(uint index, uint CornerLocation, uint Count)
{
    if (CornerLocation == npos) {
        return 0;
    }

    for(uint i = 0; i < Count; i++)
    {
        if(P[index].CornerList[i].ploc == CornerLocation)
            return 0;
    }

    P[index].CornerList[Count].ploc = CornerLocation;
    return 1;
}

#include "..\common\FPM.vert"

void main()
{
	fpm_vert_main();
}
