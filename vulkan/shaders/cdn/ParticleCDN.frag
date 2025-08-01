#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable
#extension GL_EXT_fragment_shading_rate:enable
//#extension GLSL_EXT_fragment_invocation_density:enable
//#extension EXT_fragment_invocation_density:enable
#extension GL_KHR_shader_subgroup_basic:enable
//#extension GL_NV_fragment_shader_interlock : enable
//#extension GL_ARB_fragment_shader_interlock : enable

#include "../cdn/params.glsl"
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
	#if 1 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 500  && index == 59)
	{
		debugPrintfEXT("FRAGPART particlenum=%d, gl_FragCord:<%0.2f,%0.2f,%0.2f,%0.2f>, gl_PointCoord:<%0.2f,%0.2f>,gl_SubgroupInvocationID:%u",
		index,gl_FragCoord.x,gl_FragCoord.y,gl_FragCoord.z,gl_FragCoord.w,gl_PointCoord.x,gl_PointCoord.y,gl_SubgroupInvocationID);
		//debugPrintfEXT(" gl_SubgroupInvocationID:%u, gl_SubgroupSize:%u",gl_SubgroupInvocationID,gl_SubgroupSize  );
	}
	#endif	

	if(uint(ShaderFlags.Boundary) == 0 && index <= bbound)
		discard;
	
	// If the particle is not live return.		
	if(uint(P[index].parms.x) > uint(ShaderFlags.frameNum))
		return;	
		

//DEBUG	
#if 0 && defined(DEBUG)
	if(ShaderFlags.frameNum == 1 && index == 1)
	{
		debugPrintfEXT("fragment:index %d:%0.3f,%0.3f,%0.3f",index,P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z);
	}
#endif
		outColor = vec4(fragColor,1.0);
		
}
