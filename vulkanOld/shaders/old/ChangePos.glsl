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
uint ChangePos(uint index)	
{		
	vec3 ps = P[index].PosLoc.xyz;
	
	
	
	// Calulate change in podition.
	#if 1
	if(doMotion == 1 && uint(P[index].prvvel.w) == 0)
		P[index].PosLoc.xyz += P[index].VelRad.xyz*dt;
	#endif	
	
	P[index].prvvel.xyz = P[index].VelRad.xyz;
	
	if( (P[index].PosLoc.x > WIDTH-1.0 || P[index].PosLoc.y > WIDTH-1.0 || P[index].PosLoc.z > WIDTH-1.0) && uint(P[index].prvvel.w) == 0)
	{
		P[index].prvvel.w = ShaderFlags.frameNum;
		
		debugPrintfEXT("MXBV:F:%d,P:%d cur<%0.5f,%0.5f,%0.5f>,prev<%0.5f,%0.5f,%0.5f>",
			uint(P[index].prvvel.w),
			index,P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z,
			ps.x,ps.y,ps.z);
		debugPrintfEXT("--->diff<%0.5f,%0.5f,%0.5f>,cell<%u,%u,%u>",
			P[index].PosLoc.x-ps.x,P[index].PosLoc.y-ps.y,P[index].PosLoc.z-ps.z,
			uint(round(ps.x)),uint(round(ps.y)),uint(round(ps.z)));
	}
	
	if( (P[index].PosLoc.x < 1.0 || P[index].PosLoc.y < 1.0 || P[index].PosLoc.z < 1.0) && uint(P[index].prvvel.w) == 0)
	{
		P[index].prvvel.w = ShaderFlags.frameNum;
		
		debugPrintfEXT("ChangePos MIN Boundary Violation:FRM:%d,P:%d cx=%0.5f,cy=%0.5f,cz=%0.5f,px=%0.5f,py=%0.5f,pz=%0.5f,cell<%d,%d,%d>",
			uint(P[index].prvvel.w),index,P[index].PosLoc.x,P[index].PosLoc.y,P[index].PosLoc.z,
			ps.x,ps.y,ps.z,
			uint(round(ps.x)),uint(round(ps.y)),uint(round(ps.z)));
	}
		
	return 0;
	
}	