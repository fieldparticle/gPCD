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
void ProcessCubeBoundary(uint Findex, uint Bindex, in out boundStruct ColQ)
{
	
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
	uint startf = 14610;
	uint endf = 14621;
	uint particl = 489;
	
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
		if( distB < P[Findex].PosLoc.w )
		{
				if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
				{
					debugPrintfEXT("F:%u IN distB:%0.5f P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C<%u,%u,%u>",
					uint(ShaderFlags.frameNum),distB,Findex,P[Findex].bcs[0].clflg,
					P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
					P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
					uint(round(P[Bindex].PosLoc.x)),uint(round(P[Bindex].PosLoc.y)),uint(round(P[Bindex].PosLoc.z)));
				}	
			
			if(P[Findex].bcs[0].clflg == 0 )
			{
				if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
				{
					debugPrintfEXT("OLD VEL P:%d V<%0.3f,%0.3f,%0.3f>",
					Findex,InVelF.x,InVelF.y,InVelF.z);
				}	
				InPosB = vec3(P[Bindex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
				P[Findex].VelRad.x = newVel.x;
				P[Findex].bcs[0].clflg = 1;
				if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
				{
					debugPrintfEXT("NEW VEL P:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f>",
					Findex,
					P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
					P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
				}	
				
			}
			else
			{
				// If it is skirting a boundary skip is off
				if(P[Findex].bcs[0].clflg++ == 14)
				{
					if(P[Bindex].VelRad.x > 2 )
						P[Findex].PosLoc.x = (P[Bindex].VelRad.x-P[Findex].PosLoc.w*1.01);
					else
						P[Findex].PosLoc.x = (P[Bindex].VelRad.x+P[Findex].PosLoc.w*1.01);
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
		if( distB < P[Findex].PosLoc.w )
		{
			if(P[Findex].bcs[1].clflg == 0)
			{
#if 0
				if( Findex == 494 )
				{
					debugPrintfEXT("P:%u Y Process Boundary F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[1].clflg);
					debugPrintfEXT("OLD V P:%d vx=%0.3f,vy=%0.3f,vz=%0.3f,",
					Findex,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z);
				}
#endif
						
				InPosB = vec3(P[Findex].PosLoc.x,P[Bindex].PosLoc.y,P[Findex].PosLoc.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].VelRad.y = newVel.y;
				P[Findex].bcs[1].clflg = 1;
				
#if 0				
				if( Findex == 494 )
				{
						debugPrintfEXT("P:%u Y RESET CFLG F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[0].clflg);
						debugPrintfEXT("NEW V P:%d B:%u vx=%0.3f,vy=%0.3f,vz=%0.3f,",
					Findex,Bindex,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z);
				}
#endif				
				
				//float tdt = abs((distB*(1.0f))/P[Findex].VelRad.y);
				//P[Findex].PosLoc.y += P[Findex].VelRad.y*tdt;
			}
			else
			{
				// If it is skirting a boundary skip is off
				if(P[Findex].bcs[1].clflg++ == 14)
				{
					if(P[Bindex].VelRad.y > 2 )
						P[Findex].PosLoc.y = (P[Bindex].VelRad.y-P[Findex].PosLoc.w*1.01);
					else
						P[Findex].PosLoc.y = (P[Bindex].VelRad.y+P[Findex].PosLoc.w*1.01);
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
		if( distB <P[Findex].PosLoc.w )
		{
			if(P[Findex].bcs[2].clflg == 0)
			{
				InPosB = vec3(P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Bindex].PosLoc.z);
				//InVelB = vec3(P[Findex].VelRad.x,P[Findex].VelRad.y,-P[Findex].VelRad.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].bcs[2].clflg = 1;
				P[Findex].VelRad.z = newVel.z;
				
			}
			else
			{
				
				// If it is skirting a boundary skip is off
				if(P[Findex].bcs[2].clflg++ == 14)
				{
					if(P[Bindex].VelRad.z > 2 )
						P[Findex].PosLoc.z = (P[Bindex].VelRad.z-P[Findex].PosLoc.w*1.01);
					else
						P[Findex].PosLoc.z = (P[Bindex].VelRad.z+P[Findex].PosLoc.w*1.01);	
				}
			}
		}
		else
			P[Findex].bcs[2].clflg = 0;
	}

}


