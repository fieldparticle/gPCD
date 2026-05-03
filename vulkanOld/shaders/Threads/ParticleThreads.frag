#version 460
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable
#extension GL_EXT_debug_printf : enable
#extension GL_EXT_scalar_block_layout :enable
#include "../params.glsl"
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
layout(location = 1) in vec4 center;
//layout(location = 3) in varying vec3 matpos;
// The color of this fragment.
layout(location = 0) out vec4 outColor;

void main() 
{
	
	// Get vertex number and if its index is zero return.
	uint index		= gl_PrimitiveID;
	if (index == 0)
	{	
		discard;
	}
		
	//If there was a previous error return.
	if(collIn.ErrorReturn > 0)
		return;
	
	// 	Calulate the 2D screen coordinate of the center pixel.
	vec2 FCCenter = vec2(0.0,0.0);
	FCCenter.x = SCR_X + SCR_W*(1+center.x)/2.0;
	FCCenter.y = SCR_Y + SCR_H*(1+center.y)/2.0;
	
	float r = FCCenter.x;
	float s = FCCenter.y;
	float T = FCCenter.x;
	float S = FCCenter.y;
	float X = round(S)-S;
	float Y = round(T)-T;
	
	if(X < 0.0)
		S = round(S)+0.5;
	else
		S = round(S)-0.5;
	
	if(Y < 0.0)
		T = round(T)+0.5;
	else
		T = round(T)-0.5;
	
	float ss = gl_FragCoord.x - T;
	float rr = gl_FragCoord.y - S;	
	
	// If the particle is not live return.		
	if(uint(P[index].parms.x) > uint(ShaderFlags.frameNum))
		return;	


	
	int A 			= int(ss);
	int B 			= int(rr);
	float cx 		= P[index].PosLoc.x;
	float cy 		= P[index].PosLoc.y;
	float cz 		= P[index].PosLoc.z;
	
	float R			= P[index].PosLoc.w;
	uint cornerIdx 	= 0;
#if 0	
	if(ShaderFlags.frameNum == 8 && index == 1)
		debugPrintfEXT("%u at <%0.4f,%0.4f,%0.4f>,<%d,%d>",P[index].zlink[0].ploc,cx,cy,cz,A,B);
#endif
	if(A == -1 && B == -1)
	{
		cornerIdx = 0;
		
	}
	else if (A == 0 && B == -1)
	{
		cornerIdx = 1;
	
	}
	else if(A == -1 && B == 0)
	{
		cornerIdx = 2;	
	}
	else if(A == 0 && B == 0)
	{		
		cornerIdx = 3;
	}
	else if(A == -1 && B == -1 )
	{
		cornerIdx = 4;
	}
	else if(A == 0 && B == 1)
	{
		cornerIdx = 5;
	}

	else if(A == 1 && B == -1 )
	{
		cornerIdx = 6;
	}	
	else if(A == 1 && B == 0 )
	{
		
		cornerIdx = 7;
	}
	else if(A == 1 && B == 1 )
	{
		cornerIdx = 99;
	}
	else
	{
		collIn.particleNumber = index;
		collIn.ErrorReturn = 0;
		
		return;
	}
	
		
	
#if 0
if(index == 18)
	{
		debugPrintfEXT("%u at <%0.4f,%0.4f,%0.4f>",
			P[index].zlink[0].ploc,cx,cy,cz);
			
			
	}
#endif
#if 0
	if(uint(ShaderFlags.frameNum) == 8  && (index == 1 ))
	{
		debugPrintfEXT("%u,%d,<%f,%f>",
		uint(ShaderFlags.frameNum),index,
		gl_PointCoord.x,gl_PointCoord.y);
		
	}
#endif
	// Location index for this slot.
	uint sltidx = 0;
	// Resrved slot
	uint slot 	= 0;
	
	if(cornerIdx < 10)
	{
		// Get the first non-duplicate corner occupancy.
		sltidx = P[index].zlink[cornerIdx].ploc;
		
		// DEBUG
		#if 0 && defined(DEBUG)
		if((ShaderFlags.frameNum)> 21000)
		{
			debugPrintfEXT("Boundary at frame %d, for P(%0.3f) at index %d :<%0.3f,%0.3f,%0.3f>",uint(ShaderFlags.frameNum),index,cornerIdx,cx,cy,cz);
		}
		#endif
		
		if(sltidx > MaxLocation)
		{
			#if 1 && defined(DEBUG)
				debugPrintfEXT("GRAPHVERT ERR2:P=%d,sltidx=%d,MaxLocation=%d",index,sltidx,MaxLocation);
			#endif
			
			collIn.ExcessSlots = sltidx;
			collIn.ErrorReturn = 2;
			return;
		}

		// If it's not zero then do nothing - 0 index or location <0,0,0> 
		// is not allowed
		if(sltidx != 0)
		{
			
		#if 0
			if(ShaderFlags.frameNum == 8 && index == 1)
			{
				for(uint ii =0;ii <= L[sltidx];ii++)
				{
					#if 1 && defined(DEBUG)
						if(ShaderFlags.frameNum == 8 && index == 1)
							debugPrintfEXT("DUPSLOT ii:%u L[%u]:%u,clink:%u",ii,sltidx,(L[sltidx]),clink[sltidx].idx[ii]);
							//debugPrintfEXT("DUPSLOT clink[%u].idx[%u]:%u:,L[%u]:%u,slot:%u",sltidx,ii,clink[sltidx].idx[ii],sltidx,L[sltidx],slot);
					#endif		
					
				}
			}	
			#endif
			
			
			slot = atomicAdd(L[sltidx],1);
			#if 0
			if(ShaderFlags.frameNum == 8 && index == 1)
			{
				if(ShaderFlags.frameNum == 8 && index == 1)
					debugPrintfEXT("DUPSLOT ii:%u L[%u]:%u,clink:%u",slot,sltidx,(L[sltidx]),clink[sltidx].idx[slot]);
							//debugPrintfEXT("DUPSLOT clink[%u].idx[%u]:%u:,L[%u]:%u,slot:%u",sltidx,ii,clink[sltidx].idx[ii],sltidx,L[sltidx],slot);
					
				
			}	
			#endif
		
			#if 0 && defined(DEBUG)
				debugPrintfEXT("FRAGSLOTS F:%u,P:%d,Crnr:%d,R:%0.2f,Slots:%d,loc:%d (%d,%d,%d),slot:%d",
				uint(ShaderFlags.frameNum),
				index,
				cornerIdx,
				R,
				MAX_ARY,sltidx,
				uint(round(cx)),uint(round(cy)),uint(round(cz)),slot);
			#endif
			// If the array at this index of the particle-cell hash 
			// does not have enough slots to handle the particle density
			// then report it.
			if(slot >= MAX_ARY)
			{
				uvec3 badloc;
				//debugPrintfEXT("%u at <%0.4f,%0.4f,%0.4f>",	P[index].zlink[0].ploc,cx,cy,cz);
				#if 1 && defined(DEBUG)
					debugPrintfEXT("FRAGSLOTS P:%d,Crnr:%d,R:%0.2f,Slots:%d,loc:%d (%d,%d,%d),slot:%d",
					index,
					cornerIdx,
					R,
					MAX_ARY,sltidx,
					uint(round(cx)),uint(round(cy)),uint(round(cz)),slot);
				#endif
				collIn.ExcessSlots = slot;
				collIn.ErrorReturn = 1;
				return;
			}
			
		
			// Insert the location of this particle in the particle-cell 
			// hash table.
			clink[sltidx].idx[slot] = index;
			
			
			#if 0 && defined(DEBUG)
				if(ShaderFlags.frameNum == 8 && index == 1)
					debugPrintfEXT("ENDSLOT clink[%u].idx[%u]:%u",sltidx,slot,clink[sltidx].idx[slot]);
			#endif	
			
		}
	}
//DEBUG	
#if 0 && defined(DEBUG)
	if(ShaderFlags.frameNum == 1 && index == 1)
	{
		debugPrintfEXT("fragment:index %d:%0.3f,%0.3f,%0.3f",index,P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z);
	}
#endif
		outColor = vec4(fragColor,1.0);
		
}
