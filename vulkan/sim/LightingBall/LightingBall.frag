#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
#extension GL_EXT_scalar_block_layout :enable

layout(location = 0) out vec4 outColor;
layout(location = 0) in vec4 fragColor;
layout(location = 1) in vec3 surfaceNormal;
layout(location = 2) flat in uint surfaceCellId;

#include "params.glsl"
#include "sphere.glsl"
#include "..\common\BoundaryLightRecord.glsl"

#include "..\common\BoundaryLight.frag"

void main() 
{
	boundary_light_main();
}
