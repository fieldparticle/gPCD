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


@head3 		Description. |
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/
void ProcessCubeBoundary(uint Findex, uint Bindex, in out vec3 OutVel)
{

	uint startf = 1497;
	uint endf = 1499;
	uint particl = 5199;
	
	if(Bindex > bbound)
		return;
		
		
	float tol = 0.5;
	vec3 InPosF = P[Findex].PosLoc.xyz;
	vec3 InVelF	= P[Findex].VelRad.xyz;
	vec3 InPosB;
	vec3 InVelB;
	float Fm 	= P[Findex].MolarMatter;
	float Ft 	= P[Bindex].MolarMatter;
	vec3 newVel = vec3(0.0,0.0,0.0);
	float distB = 0;
	uint xc = uint(round(P[Bindex].PosLoc.x));
	uint yc = uint(round(P[Bindex].PosLoc.y));
	uint zc = uint(round(P[Bindex].PosLoc.z));
	

	InVelB = vec3(-P[Findex].VelRad.x,-P[Findex].VelRad.y,-P[Findex].VelRad.z);
	// Boundary points are stored in velocity since
	// boudnaries are not moving. Boundaries with a zero
	// in a coordintate don't matter.
	if(P[Bindex].VelRad.x != 0.0) 
	{
		float diP = P[Bindex].VelRad.x-P[Findex].PosLoc.x;
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.x-P[Findex].PosLoc.x);
				
		// If distance is less than radius
		if( distB < P[Findex].PosLoc.w )
		{
			InPosB = vec3(P[Bindex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
			CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
			P[Findex].VelRad.x = newVel.x;
			if(P[Bindex].VelRad.x > 2 )
				P[Findex].PosLoc.x = (P[Bindex].VelRad.x-P[Findex].PosLoc.w*1.01);
			else
				P[Findex].PosLoc.x = (P[Bindex].VelRad.x+P[Findex].PosLoc.w*1.01);
		}
	}
		
	
	if(P[Bindex].VelRad.y != 0.0)
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.y-P[Findex].PosLoc.y);
		// If distance is less than radius
		if( distB < P[Findex].PosLoc.w )
		{
			InPosB = vec3(P[Findex].PosLoc.x,P[Bindex].PosLoc.y,P[Findex].PosLoc.z);
			CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
			P[Findex].VelRad.y = newVel.y;
			if(P[Bindex].VelRad.y > 2 )
				P[Findex].PosLoc.y = (P[Bindex].VelRad.y-P[Findex].PosLoc.w*1.01);
			else
				P[Findex].PosLoc.y = (P[Bindex].VelRad.y+P[Findex].PosLoc.w*1.01);
		}
	}
	
	
	if(P[Bindex].VelRad.z != 0.0 )
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.z-P[Findex].PosLoc.z);
		// If distance is less than radius
		if( distB <P[Findex].PosLoc.w )
		{
			InPosB = vec3(P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Bindex].PosLoc.z);
			CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
			P[Findex].VelRad.z = newVel.z;
			if(P[Bindex].VelRad.z > 2 )
				P[Findex].PosLoc.z = (P[Bindex].VelRad.z-P[Findex].PosLoc.w*1.01);
			else
				P[Findex].PosLoc.z = (P[Bindex].VelRad.z+P[Findex].PosLoc.w*1.01);	

		}
	}

}


