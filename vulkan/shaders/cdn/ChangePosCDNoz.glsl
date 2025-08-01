/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.cpp $
% $Id: DescriptorSSBO.cpp 28 2023-05-03 19:30:42Z jb $
%*******************************************************************
%***                         DESCRIPTION                         ***
%*******************************************************************
@doc
@module
			@author: Jackie Michael Bell<nl>
			COPYRIGHT <cp> Jackie Michael Bell<nl>
			Property of Jackie Michael Bell<rtm>. All Rights Reserved.<nl>
			This source code file contains proprietary<nl>
			and confidential information.<nl>


@head3 		Description. 
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/
uint ChangePosCDNoz(uint index)	
{		
	vec3 ps = P[index].PosLoc.xyz;
	if( uint(ShaderFlags.actualFrame) == 100 && index == 6000)
	{
		debugPrintfEXT("MXBVCDNOZ:F:%d,P:%d P[0].PosLoc.w:%u",
			uint(ShaderFlags.frameNum),index,uint(P[0].PosLoc.w));
	
	}
	if(P[0].PosLoc.w == 1.0)
		return 1;
		
	P[index].prvvel.xyz = P[index].VelRad.xyz;
	
	float radius = GetCDRadius(P[index].PosLoc.z);
	
	float dsq = radius*radius;
	float yT = P[index].PosLoc.y;
	float xT = P[index].PosLoc.x;
	float yr = (yT-CENTER);
	float xr = (xT-CENTER);
	float psq = ((yr*yr)+(xr*xr));	
	

	if(psq > dsq && uint(P[index].prvvel.w) == 0)
	{
		float pradius = sqrt(psq);
		if( uint(ShaderFlags.actualFrame) == 100 && index == 6000)
		{	
			debugPrintfEXT("MXBVCDNOZ:F:%d,P:%d cdrad:%0.4f prad:%0.4f dsq:%0.3f psq:%0.3f, cur<%0.5f,%0.5f,%0.5f>,cell<%u,%u,%u>",
				uint(ShaderFlags.frameNum),
				index,radius,pradius,
				dsq,psq,
				P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z,
				uint(round(ps.x)),uint(round(ps.y)),uint(round(ps.z)));
		}
			
		P[index].prvvel.w = 1.0;
			//debugPrintfEXT("--->,prev<%0.5f,%0.5f,%0.5f>diff<%0.5f,%0.5f,%0.5f>",
			//ps.x,ps.y,ps.z,P[index].PosLoc.x-ps.x,P[index].PosLoc.y-ps.y,P[index].PosLoc.z-ps.z,
			//));
		//P[0].PosLoc.w = 1.0;
			
		return 1;
	}
	
	// Calulate change in podition.
	#if 1
	if(doMotion == 1 && uint(P[index].prvvel.w) == 0 && uint(ShaderFlags.StopFlg) == 0)
		P[index].PosLoc.xyz += P[index].VelRad.xyz*dt;
	#endif
	
	vec2 angnorm = normalize(P[index].VelRad.zy);			
	float angletmp = atan2piPt(angnorm); 
	P[index].FrcAng.w = atan2piPt(angnorm)/(2*PI);
#if 0
	if( uint(ShaderFlags.frameNum) >= 9017 && uint(ShaderFlags.frameNum) < 9020 && index == 6000)
		debugPrintfEXT("MXBVCDNOZ:F:%d,P:%d vang:%0.4f, hsv:%0.5f, V<%0.3f,%0.3f,%0.3f>", 
			uint(ShaderFlags.frameNum),index,angletmp,P[index].FrcAng.w,
			P[index].VelRad.x,P[index].VelRad.y,P[index].VelRad.z);
			

#endif	
	if(isnan(P[index].FrcAng.w) || isnan(P[index].VelRad.x) || isnan(P[index].VelRad.y) || isnan(P[index].VelRad.z))
	{
		collIn.ErrorReturn = 7;
		//atomicAdd(collIn.particleNumber,1);	
		collIn.particleNumber = index;
			
	}
	if(P[index].PosLoc.z > 64.4)
		P[index].prvvel.w = 1.0;
	return 0;
	
}	