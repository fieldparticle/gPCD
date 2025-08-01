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


///
// Use this one with 000_ParticleVerfPerfCountOnly.comp to
// see the effect of finding the particle AABB corners and eliminating duplicates.
//
////
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
	//gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz, 1.0);
	
	
	
	if(uint(ShaderFlags.frameNum) == 10 && index == 16)
		debugPrintfEXT("Debug printf is working");
		
	
	float cx 		= P[index].PosLoc.x;
	float cy 		= P[index].PosLoc.y;
	float cz 		= P[index].PosLoc.z;
	float R			= P[index].PosLoc.w;
	
	
	
	P[index].zlink[0].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[0].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R)));
		return;
	}											//++-
	
	P[index].zlink[1].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[1].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R)));
		return;
	}											//+--
	
	P[index].zlink[2].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[2].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R)));
		return;
	}											//---
	
	P[index].zlink[3].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[3].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R)));
		return;
	}	
	
	//##############
	P[index].zlink[4].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[4].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R)));
		return;
	}
								//-++
	P[index].zlink[5].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[5].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R)));
		return;
	}											//-+-
	
	P[index].zlink[6].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[6].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>]",index,uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R)));
		return;
	}											//+-+
	#if 1				
	P[index].zlink[7].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[7].ploc == npos)
	{
		debugPrintfEXT("Particle:%d missed <%d,%d,%d>]",index,uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R)));
		return;
	}
	#endif
	
		// Orignal indexer
	uint kk = 0;

	//*******************************************************
	// Remove location duplicates.
	//*******************************************************
    for (uint ii = 0; ii < MAX_OCCUPANCY; ii++) 
	{

		for (uint jj = 0; jj < MAX_OCCUPANCY;jj++)
        {
			if (jj != ii)
			{
				if (P[index].zlink[ii].ploc == P[index].zlink[jj].ploc) 
				{
						P[index].zlink[jj].ploc = 0;
				}
				else
				{
					kk++;
				}
			}
		}

	}
	
	
	fragColor = vec3(1.0,0.3,0.3);	
	
}