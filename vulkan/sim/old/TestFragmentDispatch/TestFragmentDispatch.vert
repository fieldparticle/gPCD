#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
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

layout(binding = 2) uniform UniformBufferObject{
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

// this particle (vertex)
layout(location = 0) in vec4 inPosition;
// Current velocity of this particle.
layout(location = 1) in vec4 incurvel;
// Color of this particle
layout(location = 2) in vec4 inColor;
// Radius and type of this particle.
layout(location = 3) in vec2 inParms;

layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 outParms;
layout(location = 2) out vec3 matpos;




void main()
{
	if (gl_VertexIndex == 0)
		return ;
		
	gl_PointSize = 1.0;
    // If using instancing: gl_VertexIndex is 0..7 per particle
    int cornerID = gl_VertexIndex & 7;  // safer than %
	outParms[0] = float(gl_VertexIndex);
    outParms[1] = float(gl_InstanceIndex);
	
	
    vec3 offset = vec3(
        ((cornerID & 1) != 0) ? 1.0 : -1.0,
        ((cornerID & 2) != 0) ? 1.0 : -1.0,
        ((cornerID & 4) != 0) ? 1.0 : -1.0
    );

	//if(uint(ShaderFlags.frameNum) == 3 && gl_VertexIndex == 1)
	//if(uint(ShaderFlags.frameNum) == 3 && gl_InstanceIndex == 0)
		//debugPrintfEXT("P:%d,C:%d,xyz:<%f,%f,%f>,outInv:%f",gl_VertexIndex,gl_InstanceIndex,inPosition[0],inPosition[1],inPosition[2],outParms[1]);

	
    //vec3 cornerPos = inParticlePos + offset;
	fragColor = vec3(1.0,0.0,0.0);
    gl_Position = ubo.proj * ubo.view * inPosition;
}
