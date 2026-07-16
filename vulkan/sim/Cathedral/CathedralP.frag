#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
#if defined(DEBUG)
	#extension GL_EXT_debug_printf : enable
#endif
//#extension GL_EXT_scalar_block_layout :enable
#extension GL_EXT_fragment_shading_rate:enable
//#extension GLSL_EXT_fragment_invocation_density:enable
//#extension EXT_fragment_invocation_density:enable
//#extension GL_KHR_shader_subgroup_basic:enable
//#extension GL_NV_fragment_shader_interlock : enable
//#extension GL_ARB_fragment_shader_interlock : enable
#include "../VerfPerf/params.glsl"
#include "../common/constants.glsl"
#include "../common/atomicg.glsl"
#include "../common/push.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/Lockimage.glsl"
#include "../common/particle.glsl"
#include "../common/util.glsl"

layout(location = 0) in vec4 fragColor;
layout(location = 1) in vec2 parms;

layout(location = 0) out vec4 outColor;

#include "..\common\FPM.frag"

void main()
{
	fpm_frag_main();
}
