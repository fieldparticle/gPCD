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
void ProcessCubeBoundary(uint Findex, uint Bindex)
{
	
	if(Bindex > bbound || Findex < bbound)
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
	if( (uint(ShaderFlags.frameNum) > 2769 && uint(ShaderFlags.frameNum) < 2780) && Findex == 489)
				{
					debugPrintfEXT("OLD VEL P:%d V<%0.3f,%0.3f,%0.3f>",
					Findex,InVelF.x,InVelF.y,InVelF.z);
				}	
	
		if( (uint(ShaderFlags.frameNum) > 3540 && uint(ShaderFlags.frameNum) < 3550) && Findex == 533)
		{
			debugPrintfEXT("F:%d,P:%d,B:%d,CF:%d,B.x:%0.4f,P.x:%0.4f,distB:%0.5f,CELL<%u,%u,%u>",
			uint(ShaderFlags.frameNum),
			Findex,
			Bindex,
			P[Findex].bcs[0].clflg,
			P[Bindex].VelRad.x,
			P[Findex].PosLoc.x,
			P[Bindex].VelRad.x-P[Findex].PosLoc.x,
			uint(round(P[Bindex].PosLoc.x)),uint(round(P[Bindex].PosLoc.y)),uint(round(P[Bindex].PosLoc.z)));
			
		}	
	InVelB = vec3(-P[Findex].VelRad.x,-P[Findex].VelRad.y,-P[Findex].VelRad.z);
	// Boundary points are stored in velocity since
	// boudnaries are not moving. Boundaries with a zero
	// in a coordintate don't matter.
	if(P[Bindex].VelRad.x != 0.0)
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.x-P[Findex].PosLoc.x);
		
		// If distance is less than radius
		if( distB < P[Findex].PosLoc.w && P[Findex].bcs[0].clflg == 0 )
		{
			if( Findex == 533 )
			{
			debugPrintfEXT("COLLOSION###F:%d,P:%d,B:%d,CF:%d,B.x:%0.4f,P.x:%0.4f,distB:%0.5f",
			uint(ShaderFlags.frameNum),
			Findex,
			Bindex,
			P[Findex].bcs[0].clflg,
			P[Bindex].VelRad.x,
			P[Findex].PosLoc.x,
			P[Bindex].VelRad.x-P[Findex].PosLoc.x);

			}			
			if(P[Findex].bcs[0].clflg == 0)
			{
				
				InPosB = vec3(P[Bindex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
				P[Findex].VelRad.xyz = newVel;
				P[Findex].bcs[0].clflg = 1;
				if( (uint(ShaderFlags.frameNum) > 2769 && uint(ShaderFlags.frameNum) < 2780) && Findex == 489)
				{
					debugPrintfEXT("NEW VEL P:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f>",
					Findex,
					P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
					P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
				}	
				float tdt = abs((distB*(1.10f))/P[Findex].VelRad.x);
				P[Findex].PosLoc.x += P[Findex].VelRad.x*tdt;
			}
			else
			{

				if(P[Findex].bcs[0].clflg++ == 9)
				{
					P[Findex].bcs[0].clflg = 0;
					
				}
				
			}
		}
		else
		{
			P[Findex].bcs[0].clflg = 0;
		}
	}
	
	
	
	if(P[Bindex].VelRad.y != 0.0)
	{
		
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.y-P[Findex].PosLoc.y);
		// If distance is less than radius
		if( distB < P[Findex].PosLoc.w  && P[Findex].bcs[1].clflg == 0 )
		{
			if(P[Findex].bcs[1].clflg == 0)
			{
			
			if( Findex == 494 )
			{
			debugPrintfEXT("COLLOSION###F:%d,P:%d,B:%d,CF:%d,B.x:%0.4f,P.x:%0.4f,distB:%0.5f",
			uint(ShaderFlags.frameNum),
			Findex,
			Bindex,
			P[Findex].bcs[0].clflg,
			P[Bindex].VelRad.x,
			P[Findex].PosLoc.x,
			P[Bindex].VelRad.x-P[Findex].PosLoc.x);

			}		
				InPosB = vec3(P[Findex].PosLoc.x,P[Bindex].PosLoc.y,P[Findex].PosLoc.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].bcs[1].clflg = 1;
				P[Findex].VelRad.xyz = newVel;
				float tdt = abs((distB*(1.10f))/P[Findex].VelRad.y);
				P[Findex].PosLoc.y += P[Findex].VelRad.y*tdt;
			}
			else
			{
				if(P[Findex].bcs[1].clflg++ == 9)
				{
					P[Findex].bcs[1].clflg = 0;
					
				}
				
			}
		}
		else
			P[Findex].bcs[1].clflg = 0;
	}
	
	
	if(P[Bindex].VelRad.z != 0.0 )
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.z-P[Findex].PosLoc.z);
		// If distance is less than radius
		if( distB <P[Findex].PosLoc.w && P[Findex].bcs[2].clflg == 0 )
		{
			if(P[Findex].bcs[2].clflg == 0)
			{
				InPosB = vec3(P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Bindex].PosLoc.z);
				//InVelB = vec3(P[Findex].VelRad.x,P[Findex].VelRad.y,-P[Findex].VelRad.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].bcs[2].clflg = 1;
				P[Findex].VelRad.xyz = newVel;
				float tdt = abs((distB*(1.10f))/P[Findex].VelRad.z);
				P[Findex].PosLoc.z += P[Findex].VelRad.z*tdt;
			}
			else
			{
				
				if(P[Findex].bcs[2].clflg++ == 9)
				{
					P[Findex].bcs[2].clflg = 0;
					
				}

				
			}
		}
		else
			P[Findex].bcs[2].clflg = 0;
	}
	


}


