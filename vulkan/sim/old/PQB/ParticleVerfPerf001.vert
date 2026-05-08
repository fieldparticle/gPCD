#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable


#include "../VerfPerf/params.glsl"
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
	if(uint(ShaderFlags.frameNum) == 10 && index == 0)
	{
		P[index].parms.w = 0;
		uint ret = TestArrayToIndex(0,10);
		if (ret != 0)
			P[0].ColFlg = 1;
	}
	if(index == 0)
	{
		collIn.numParticles = 0;
		return;
	}	
	if (P[0].ColFlg != 0)
	{
		fragColor = vec3(1.0,1.0,1.0);	
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
	
	
	

	float cx 		= P[index].PosLoc.x;
	float cy 		= P[index].PosLoc.y;
	float cz 		= P[index].PosLoc.z;
	float R			= P[index].PosLoc.w;
	
	uint duplist[8];
	uint dupcntr = 0;
	
	if (cx+R > 0.0 && cy+R > 0.0 && cz-R > 0.0)
	{
		duplist[0] = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
		if(duplist[0] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R)));
			#endif
			return;
		}							
	}
	else
	{
		duplist[0] = 0;
	}
	
	 P[index].zlink[dupcntr].ploc = duplist[dupcntr];
	
	if (cx+R > 0.0 && cy+R > 0.0 && cz+R > 0.0)
	{
		duplist[1] = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
		if(duplist[1] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R)));
			#endif
			return;
		}						
	}
	else
	{
		duplist[1] = 0;
	}
	
	if (duplist[0] != duplist[1])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[1];
		

	
	if (cx-R > 0.0 && cy+R > 0.0 && cz+R > 0.0)
	{
		duplist[2] = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
		if(duplist[2] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R)));
			#endif
			return;
		}											
	}
	else
	{
		duplist[2] = 0;
	}
	
	if (duplist[0] != duplist[2] && duplist[1] != duplist[2])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[2];
	
	
	if (cx-R > 0.0 && cy+R > 0.0 && cz-R > 0.0)
	{
		duplist[3] = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
		if(duplist[3] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R)));
			#endif
			return;
		}
	}
	else
	{
		duplist[3] = 0;
	}
	
	if (duplist[0] != duplist[3] && 
		duplist[1] != duplist[3] && 
		duplist[2] != duplist[3])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[3];
	
	
	
	if (cx+R > 0.0 && cy-R > 0.0 && cz-R > 0.0)
	{
		duplist[4] = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
		if(duplist[4] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R)));
			#endif
			return;
		}
	}
	else
	{
		duplist[4] = 0;
	}
		
	if (duplist[0] != duplist[4] && 
		duplist[1] != duplist[4] && 
		duplist[2] != duplist[4] && 
		duplist[3] != duplist[4])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[4];
	
	if (cx+R > 0.0 && cy-R > 0.0 && cz-R > 0.0)
	{
		duplist[5] = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
		if(duplist[5] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>",index,uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R)));
			#endif
			return;
		}											//-+-
	}
	else
	{
		duplist[5] = 0;
	}
	
	if (duplist[0] != duplist[5] && 
		duplist[1] != duplist[5] && 
		duplist[2] != duplist[5] && 
		duplist[3] != duplist[5] && 
		duplist[4] != duplist[5])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[5];
	
	
	
	if (cx-R > 0.0 && cy-R > 0.0 && cz+R > 0.0)
	{
		duplist[6] = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
		if(duplist[6] == npos)
		{
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>]",index,uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R)));
			#endif
			return;
		}											//+-+
	}
	else
	{
		duplist[6] = 0;
	}

	if (duplist[0] != duplist[6] && 
		duplist[1] != duplist[6] && 
		duplist[2] != duplist[6] && 
		duplist[3] != duplist[6] && 
		duplist[4] != duplist[6] && 
		duplist[5] != duplist[6])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[6];
		
	
	if (cx-R > 0.0 && cy-R > 0.0 && cz-R > 0.0)
	{
		duplist[7] = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));

		#if 0
			
				debugPrintfEXT("ParticleVerfPerf corner: Particle:%d corner %d <%d>",index,7,P[index].zlink[7].ploc);
		#endif
		if(duplist[7] == npos)
		{
		
			#ifdef DEBUG
				debugPrintfEXT("Particle:%d missed <%d,%d,%d>]",index,uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R)));
			#endif
			return;
		}
	}
	else
	{
	
		duplist[7] = 0;
	}
	
	if (duplist[0] != duplist[7] && 
		duplist[1] != duplist[7] && 
		duplist[2] != duplist[7] && 
		duplist[3] != duplist[7] && 
		duplist[4] != duplist[7] && 
		duplist[5] != duplist[7] && 
		duplist[6] != duplist[7])
		dupcntr++;
		P[index].zlink[dupcntr].ploc = duplist[7];
	
	uint kk = 0;

	

	//*******************************************************
	// Remove location duplicates.
	//*******************************************************
	#if 0
		if(index == 58 && uint(ShaderFlags.frameNum) == 100)
		{
			debugPrintfEXT("p:%d,H:%d,W:%d[%d,%d,%d,%d,%d,%d,%d,%d]",index,WIDTH,HEIGHT,
				P[index].zlink[0].ploc,
				P[index].zlink[1].ploc,
				P[index].zlink[2].ploc,
				P[index].zlink[3].ploc,
				P[index].zlink[4].ploc,
				P[index].zlink[5].ploc,
				P[index].zlink[6].ploc,
				P[index].zlink[7].ploc);
		}
			
	#endif
	//*******************************************************
	// Populate particle-cell array
	//*******************************************************
	for( uint ii = 0; ii < dupcntr && uint(P[index].parms[0])==0; ii++)
	{
		// Location index for this slot.
		uint sltidx = 0;
		// Resrved slot
		uint slot 	= 0;
		
		
		// Get the first non-duplicate corner occupancy.
		sltidx = P[index].zlink[ii].ploc;
		
		if(uint(ShaderFlags.frameNum) == 8 && index == 16)
		{
			#if 0 //#ifdef DEBUG 
				debugPrintfEXT("VERT %u at %u",index,P[index].zlink[ii].ploc);
			#endif
			
		}
		// If it's not zero then do nothing - 0 index or location <0,0,0> 
		// is not allowed
		if(sltidx != 0)
		{
		
			if(sltidx > MaxLocation)
			{
				#if defined(DEBUG)
					debugPrintfEXT("ParticleVerfPerf sltidx > MaxLocation:P=%d,sltidx=%d,MaxLocation=%d",index,sltidx,MaxLocation);
				#endif	
				collIn.ExcessSlots = sltidx;
				collIn.ErrorReturn = 2;
				P[index].parms.w = 1.0;
				P[0].ColFlg = 1;
				return;
			}
			
			// Reserve a slot for this location in the parcirel-cell hash
			slot = atomicAdd(L[sltidx],1);

			// If the array at this index of the particle-cell hash 
			// does not have enough slots to handle the particle density
			// then report it.
			if(slot >= MAX_ARY)
			{
				uvec3 badloc;
				#if defined(DEBUG)
					IndexToArray(sltidx,badloc);
					debugPrintfEXT("ParticleVerfPerf slot>F:%u,P:%d,R:%0.2f,MAX_ARY:%d,at loc: %d(%d,%d,%d), exceeds max array:%d",
					uint(ShaderFlags.frameNum),index,R,MAX_ARY,sltidx,badloc.x,badloc.y,badloc.z,slot);
				#endif
				collIn.ExcessSlots = slot;
				collIn.ErrorReturn = 1;
				P[0].ColFlg = 1;
				P[index].parms.w = 2.0;
				return;
			}
			
			

			// Insert the location of this particle in the particle-cell 
			// hash table.
			#if 0 && defined(DEBUG)
				if(ShaderFlags.frameNum == 8 && index == 16)
				{
					debugPrintfEXT("ParticleVerfPerf particle %d added to cell %d slot %d.",index,sltidx,slot);
				}
			#endif	
			clink[sltidx].idx[slot] = index;
		
		}
	}
	
		if (uint(P[index].parms.w)==0)
		{
			if(uint(P[index].ColFlg) == 1)
				fragColor = vec3(1.0,0.0,0.0);	
			else if(uint(P[index].ColFlg) == 0)
				fragColor = vec3(0.0,1.0,0.0);	
		}
		else
		{
			if(uint(P[index].parms.w) == 1)
				fragColor = vec3(1.0,0.0,0.0);	
			else if(uint(P[index].parms.w) == 2)
				fragColor = vec3(0.0,1.0,0.0);	
			else
				fragColor = vec3(1.0,0.64,0.0);	
		}
		
	
}