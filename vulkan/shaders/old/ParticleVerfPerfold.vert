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
		collIn.numParticles = 1;
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
	
	
	#if 0 && defined(DEBUG)
	if(index == 6000 && ShaderFlags.actualFrame == 500.0  )
		debugPrintfEXT("GRAPHPART velocity:%d vx=%0.3f,vy=%0.3f,vz=%0.3f,",
		0,P[index].VelRad.x,P[index].VelRad.y,P[index].VelRad.z);
	#endif	
	

	// If the particle is not live return.		
	if(uint(P[index].parms.x) > uint(ShaderFlags.actualFrame))
		return;	
		
	if(uint(P[index].prvvel.w) == 1)
		return;
	

	//clear zlink
	for(uint jj=0;jj<MAX_OCCUPANCY;jj++)
	{
		P[index].zlink[jj].ploc = 0;
		P[index].zlink[jj].pindex =0;
		//P[index].wary[jj].x = 0.0;
	}
	
	uint Loc[8];
	float cx 		= P[index].PosLoc.x;
	float cy 		= P[index].PosLoc.y;
	float cz 		= P[index].PosLoc.z;
	float R			= P[index].PosLoc.w;
	
	P[index].zlink[0].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[0].ploc == npos)
		return;
												//++-
	P[index].zlink[1].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[1].ploc == npos)
		return;
												//+--
	P[index].zlink[2].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	if(P[index].zlink[2].ploc == npos)
		return;
												//---
	P[index].zlink[3].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	if(P[index].zlink[3].ploc == npos)
		return;
		
	//##############
	P[index].zlink[4].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[4].ploc == npos)
		return;
												//-++
	P[index].zlink[5].ploc = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[5].ploc == npos)
		return;
												//-+-
	P[index].zlink[6].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	if(P[index].zlink[6].ploc == npos)
		return;
												//+-+
	P[index].zlink[7].ploc = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	if(P[index].zlink[7].ploc == npos)
		return;
#if 0
	
	if(uint(ShaderFlags.frameNum) == 8 && index == 16)
	{
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[0].ploc,uint(round(cx+R)), uint(round(cy+R)), uint(round(cz-R)),
			cx+R,cy+R,cz-R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[1].ploc,uint(round(cx+R)), uint(round(cy+R)), uint(round(cz+R)),
			cx+R,cy+R,cz+R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[2].ploc,uint(round(cx-R)), uint(round(cy+R)), uint(round(cz-R)),
			cx-R,cy+R,cz-R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[3].ploc,uint(round(cx-R)), uint(round(cy+R)), uint(round(cz+R)),
			cx-R,cy+R,cz+R);			
			
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[4].ploc,uint(round(cx+R)), uint(round(cy-R)), uint(round(cz+R)),
			cx+R,cy-R,cz+R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[5].ploc,uint(round(cx+R)), uint(round(cy-R)), uint(round(cz-R)),
			cx+R,cy-R,cz-R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[6].ploc,uint(round(cx-R)), uint(round(cy-R)), uint(round(cz+R)),
			cx-R,cy-R,cz+R);
		debugPrintfEXT("%u at <%u,%u,%u>,<%0.4f,%0.4f,%0.4f>",
			P[index].zlink[7].ploc,uint(round(cx-R)), uint(round(cy-R)), uint(round(cz-R)),
			cx-R,cy-R,cz-R);			
			
	}
	#endif
//Debug 	
#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 3 && index == 32)
	{
		debugPrintfEXT(",,,-------------------------");
		for(uint ii = 0; ii< MAX_OCCUPANCY;ii++)
			debugPrintfEXT("GRAPHPART:%d,%d,%d",index,ii,P[index].zlink[ii].ploc);
	}
#endif	

	// Orignal indexer
	uint kk = 0;

	//*******************************************************
	// Removed location duplicates.
	//*******************************************************
    for (uint ii = 0; ii < MAX_OCCUPANCY; ii++) 
	{
#if 1
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
#endif
	}
	
// DEBUG
#if 0 && defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 3 && index == 2)
	{
		debugPrintfEXT(",,,-------------------------");
		for(uint ii = 0; ii< MAX_OCCUPANCY;ii++)
			debugPrintfEXT("GRAPHPART:%d,%d,%d",index,ii,P[index].zlink[ii].ploc);
		
	}
#endif

	
		//*******************************************************
		// Populate particle-cell array
		//*******************************************************
		for( uint ii = 0; ii < MAX_OCCUPANCY ; ii++)
		{
			// Location index for this slot.
			uint sltidx = 0;
			// Resrved slot
			uint slot 	= 0;
			
			
			// Get the first non-duplicate corner occupancy.
			sltidx = P[index].zlink[ii].ploc;
			// DEBUG
	#if 0 && defined(DEBUG)
			if((ShaderFlags.frameNum)> 21000)
			{
				debugPrintfEXT("Boundary at frame %d, for P(%0.3f) at index %d :<%0.3f,%0.3f,%0.3f>",uint(ShaderFlags.frameNum),index,ii,cx,cy,cz);
			}
	#endif
			// If it's not zero then do nothing - 0 index or location <0,0,0> 
			// is not allowed
			if(sltidx != 0)
			{
			
				// Reserve a slot for this location in the parcirel-cell hash
				slot = atomicAdd(L[sltidx],1);

				// If the array at this index of the particle-cell hash 
				// does not have enough slots to handle the particle density
				// then report it.
				if(slot >= MAX_ARY)
				{
					uvec3 badloc;
					//IndexToArray(sltidx,badloc);
					debugPrintfEXT("GRAPHVERT F:%u,P:%d,R:%0.2f,Slots:%d,at loc: %d(%d,%d,%d), exceeds max array:%d",
					uint(ShaderFlags.frameNum),index,R,MAX_ARY,sltidx,badloc.x,badloc.y,badloc.z,slot);
					collIn.ExcessSlots = slot;
					collIn.ErrorReturn = 1;
					return;
				}
				
			if(sltidx > MaxLocation)
			{
				debugPrintfEXT("GRAPHVERT ERR2:P=%d,sltidx=%d,MaxLocation=%d",index,sltidx,MaxLocation);
		
				collIn.ExcessSlots = sltidx;
				collIn.ErrorReturn = 2;
				return;
			}

				// Insert the location of this particle in the particle-cell 
				// hash table.
				clink[sltidx].idx[slot] = index;
			}
		}
		
	// DEBUG
	#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 3 && index == 1)
		{
			debugPrintfEXT(",,,-------------------------");
			debugPrintfEXT("GRAPHPART: Out:%d,%d,%d,%d",index,P[index].VelRad.x,P[index].VelRad.y,P[index].VelRad.z);
		}
	#endif		
				
				
		if(uint(ShaderFlags.ColorMap) == 0)				
		{
			
			if(P[index].ColFlg == 1.0)
				fragColor = vec3(0.5,1.0,0.4);
			else
				fragColor = vec3(1.0,0.3,0.3);	
		}
		if(uint(ShaderFlags.ColorMap) == 1)				
		{
			fragColor  = hsv2rgb(vec3(P[index].FrcAng.w,1.0,1.0));
		}
		
	
	
}