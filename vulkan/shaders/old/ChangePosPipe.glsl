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
uint ChangePosPipe(uint index)	
{		
	vec3 ps = P[index].PosLoc.xyz;
	
	
	
	// Calulate change in podition.
	#if 1
	if(doMotion == 1 && uint(P[index].prvvel.w) == 0)
		P[index].PosLoc.xyz += P[index].VelRad.xyz*dt;
	#endif	
	
	if(P[index].PosLoc.x > 64.4)
		P[index].prvvel.w = 1.0;
	
	P[index].prvvel.xyz = P[index].VelRad.xyz;
	float dsq = RADIUS*RADIUS;
	float yT = P[index].PosLoc.y;
	float zT = P[index].PosLoc.z;
	float yr = (yT-CENTER);
	float zr = (zT-CENTER);
	float psq = ((yr*yr)+(zr*zr));	
return 0;
	if(psq > dsq && uint(P[index].prvvel.w) == 0)
	{
		debugPrintfEXT("MXBV:F:%d,P:%d dsq:%0.3f psq:%0.3f, cur<%0.5f,%0.5f,%0.5f>,cell<%u,%u,%u>",
			uint(ShaderFlags.frameNum),
			index,dsq,psq,
			P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z,
			uint(round(ps.x)),uint(round(ps.y)),uint(round(ps.z)));
			
		P[index].prvvel.w = 1.0;
			//debugPrintfEXT("--->,prev<%0.5f,%0.5f,%0.5f>diff<%0.5f,%0.5f,%0.5f>",
			//ps.x,ps.y,ps.z,P[index].PosLoc.x-ps.x,P[index].PosLoc.y-ps.y,P[index].PosLoc.z-ps.z,
			//));
	}
	
	
	return 0;
	
}	