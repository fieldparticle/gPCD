#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
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



// Color of this particle from vertex shader.
layout(location = 0) in vec3 fragColor;
// The particle radius and type from vertex shader.
layout(location = 1) in vec2 parms;
//layout(location = 3) in vec3 matpos;
// The color of this fragment.
layout(location = 0) out vec4 outColor;
/**************************************************************
	This version assumes all of the work is done in the vertex 
	shader since we do not have a thread ID for which to assign 
	

***************************************************************/
void main() 
{
	
	// Get triangle number and if its index is zero return.
	uint index		= gl_PrimitiveID;
	if (index == 0)
	{	
		discard;
	}
	//outColor = vec4(1.0,0.0,0.0,1.0);
	outColor = vec4(fragColor,1.0);
		
}
