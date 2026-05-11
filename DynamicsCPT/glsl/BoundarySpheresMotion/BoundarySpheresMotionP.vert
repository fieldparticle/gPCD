#version 460
#extension GL_ARB_separate_shader_objects : enable
//#extension GL_ARB_shading_language_420pack : enable
#include "debug.glsl"
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
uint addUniqueCell(uint index, uint CornerLocation, uint Count)
{
    for(uint i = 0; i < Count; i++)
    {
        if(P[index].CornerList[i].ploc == CornerLocation)
            return 0;
    }

    P[index].CornerList[Count].ploc = CornerLocation;
    return 1;
}

///
// Use this one with 000_ParticleVerfPerfCountOnly.comp to
// see the effect of finding the particle AABB corners and eliminating duplicates.
//
////
void main(){
	
	int index 		= gl_VertexIndex;
	
#if defined(DEBUG)
	if(uint(ShaderFlags.frameNum) == 0 && index == 0)
	{
		//debugPrintfEXT("Testing Indexing H:%d,W:%d,CMEM %d, ACTMEM %d",HEIGHT,WIDTH,HEIGHT*HEIGHT*HEIGHT,);
		P[index].parms.w = 0;
		uint ret = TestArrayToIndex(0,10);
		
		if (ret != 0)
		{
			debugPrintfEXT("Indexing Failed H:%d,W:%d at #:%d",HEIGHT,WIDTH,ret);
			P[0].ColFlg = 1;
		}
		else
			debugPrintfEXT("Indexing passed H:%d,W:%d at #:%d",HEIGHT,WIDTH,ret);
	}
#endif

	if(index == 0)
	{
		collIn.numParticles = 0;
		return;
	}	

	
	
	// Set point size 
	gl_PointSize = 1.0;
	
	// Clear this paricles corner array
	for (uint kk = 0;kk<8;kk++)
		P[index].CornerList[kk].ploc = 0;

	float cx 		= P[index].PosLocA.x;
	float cy 		= P[index].PosLocA.y;
	float cz 		= P[index].PosLocA.z;
	float R			= P[index].Data.x;
	
	if (ShaderFlags.positionBuffer == 0u) 
	{
		cx 		= P[index].PosLocA.x;
		cy 		= P[index].PosLocA.y;
		cz 		= P[index].PosLocA.z;
	} 
	else{
		cx 		= P[index].PosLocB.x;
		cy 		= P[index].PosLocB.y;
		cz 		= P[index].PosLocB.z;
	}

	// Render the particle from the same selected position buffer used to build
	// the corner list and drive compute collision detection.
	vec3 particleCenter = vec3(cx, cy, cz);
	gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition.xyz + particleCenter, 1.0);

	uint duplist[8];
	uint dupcntr = 0;
	uint CornerLocation = 0;
	uint count = 0;
	#if 1
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz-R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy+R)),uint(round(cz+R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz+R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy+R)),uint(round(cz-R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz+R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx+R)),uint(round(cy-R)),uint(round(cz-R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz+R))));
	count += addUniqueCell(index, CornerLocation, count);
	CornerLocation = ArrayToIndex(uvec3(uint(round(cx-R)),uint(round(cy-R)),uint(round(cz-R))));
	count += addUniqueCell(index, CornerLocation, count);
	#endif
	
//#################################################################
//################### Populate the cell array with this particles corners
//#################################################################
	//Need this to get the number particles count correct (?!)
#ifdef DEBUG
	atomicAdd(collIn.numParticles,1);	
#endif

	// Traverse the particles corner array if there is not a global error 
	// which is stored in the 0th partcle parms emlent
	for( uint ii = 0; ii < 8 && P[index].CornerList[ii].ploc!=0; ii++)
	{
		// Location index for this slot.
		uint sltidx = 0;
		// Resrved slot
		uint slot 	= 0;
		
		
		// Get the first non-duplicate corner.
		sltidx = P[index].CornerList[ii].ploc;
		
	
		// If it's not zero then do nothing - 0 index or location <0,0,0> 
		// is not allowed
		if (sltidx == 0)
			break;
		
		
		if(sltidx >= MAX_CELL_ARRAY_LOCATIONS)
		{
			#if defined(DEBUG)
				debugPrintfEXT("ParticleVerfPerf sltidx > MaxLocation:P=%d,sltidx=%d,MaxLocation=%d",index,sltidx,MAX_CELL_ARRAY_LOCATIONS);
			#endif	
			collIn.ExcessSlots = sltidx;
			collIn.particleNumber = index;
			collIn.ErrorReturn = 3;
			collIn.maxCells = MAX_CELL_ARRAY_LOCATIONS;
			P[index].parms.w = 1.0;
			P[0].ColFlg = 1;
			break;
		}
		
		// Reserve a slot for this location in the cell array occupancy list
		// atomic add increments the value in the lock array and returns the 
		// *previous value*.
		slot = atomicAdd(L[sltidx],1);
		#if 1 && defined(DEBUG)
			if((uint(ShaderFlags.frameNum) == 55 || uint(ShaderFlags.frameNum) == 56) && ii <3)
				debugPrintfEXT("F:%d,P:%d,Slot:%d, Corner Loc:%d, loc<%f,%f,%f> R:%f",uint(ShaderFlags.frameNum),index,slot,sltidx,cx,cy,cz,R);
		#endif	
		// If the array at this index of the particle-cell hash 
		// does not have enough slots to handle the particle density
		// then report it.
		if(slot >= MAX_CELL_OCCUPANY)
		{
			uvec3 badloc;
			#if 0
			#if defined(DEBUG)
				//IndexToArray(sltidx,badloc);
				debugPrintfEXT("ParticleVerfPerf slot>F:%u,P:%d,MAX_CELL_OCCUPANY:%d,at loc: %d",
				uint(ShaderFlags.frameNum),index,MAX_CELL_OCCUPANY,slot);
			#endif
			#endif
			collIn.ExcessSlots = slot;
			collIn.ErrorReturn = 2;
			P[0].ColFlg = 1;
			P[index].parms.w = 2.0;
			break;
		}
		

		// Insert the location of this particle in the particle-cell 
		// hash table.
		
		#if 0 && defined(DEBUG)
			if(index == 3 && uint(ShaderFlags.frameNum) == 100)
			{
				debugPrintfEXT("VerfPerf particle %d added to cell %d slot %d.",index,sltidx,slot);
			}
		#endif	
		
	#if 0
		if(uint(ShaderFlags.frameNum) == 8 && index == 1)
		{
			debugPrintfEXT("P:%u,CNRIDX:%u,CNRL:%u,LOC:%u,SLT:%u ",index,ii,P[index].CornerList[ii].ploc, sltidx,slot);
		}
	#endif

		// If everythin is valid add this particles corner to the 
		// cell array at the indoctaed location and slot in the cell occupancy array
		// NOTE: particle 0 is a dummy particle so that the particle 0-based index matches
		// the particle number
		clink[sltidx].idx[slot] = index;
	
	#if defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 8 && index == 1)
		{
			debugPrintfEXT("P:%u,CNRIDX:%u,CELLARYVAL:%u ",index,ii,clink[sltidx].idx[slot]);
		}
	#endif
		
	}
	
	if(uint(P[index].ColFlg) == 1)
		fragColor = vec3(1.0,0.0,0.0);	
	else if(uint(P[index].ColFlg) == 0)
		fragColor = vec3(0.0,1.0,0.0);	
	
	
}
