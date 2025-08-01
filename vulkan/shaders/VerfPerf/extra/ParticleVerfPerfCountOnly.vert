#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable



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
layout(binding = 2) uniform UniformBufferObject{
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

// From vertex assembler position of 
// this particle (vertex)
layout(location = 0) in vec4 inPosition;
// Current velocity of this particle.
layout(location = 1) in vec4 incurvel;
// Color of this particle
layout(location = 2) in vec4 inColor;
// Radius and type of this particle.
layout(location = 3) in vec2 inParms;

// Output to fragment shader.
layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 outParms;
layout(location = 2) out vec3 matpos;


void main(){
	
	
	
	int index 		= gl_VertexIndex;
	if(index == 0)
	{
		collIn.numParticles = 0;
		return;
	}	
	
	#ifdef DEBUG
		atomicAdd(collIn.numParticles,1);	
	#endif
	
	// Set point size 
	gl_PointSize = 1.0;
	
	// Apply view to location
	vec3 posLocNDC =  P[index].PosLoc.xyz;
  	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	
	
	fragColor = vec3(1.0,0.3,0.3);	
	
	
}