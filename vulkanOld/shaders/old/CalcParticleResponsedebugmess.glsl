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
void ProcessCubeBoundary(uint Findex, uint Bindex, inout cs)
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
	

	InVelB = vec3(-P[Findex].VelRad.x,-P[Findex].VelRad.y,-P[Findex].VelRad.z);
	// Boundary points are stored in velocity since
	// boudnaries are not moving. Boundaries with a zero
	// in a coordintate don't matter.
	if(P[Bindex].VelRad.x != 0.0 )
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.x-P[Findex].PosLoc.x);
		// If distance is less than radius
		if( distB < tol)
		{
			
			if(P[Findex].bcs[0].clflg == 0 )
			{
				if(Findex == 490 || Findex == 492)
				{
					debugPrintfEXT("P:%u X Process Boundary F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[0].clflg);
					debugPrintfEXT("OLD V P:%d vx=%0.3f,vy=%0.3f,vz=%0.3f,",
					Findex,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z);
				}
				colQ.inBX = true;
				InPosB = vec3(P[Bindex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
				P[Findex].VelRad.xyz = newVel;
				P[Findex].bcs[0].clflg = 1;
			}
			else
			{

				if(Findex == 490 ||Findex == 492 )
					{
						debugPrintfEXT("P:%u X RESET CFLG F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[0].clflg);
						debugPrintfEXT("NEW V P:%d B:%u vx=%0.3f,vy=%0.3f,vz=%0.3f,",
					Findex,Bindex,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z);
				if(P[Findex].bcs[0].clflg++ == 10)
				{
					P[Findex].bcs[0].clflg = 0;
					P[Findex].PosLoc.x += P[Findex].VelRad.x*100;
					}
				}
				
			}
		}
		else
		{
			//if(Findex == 490)
			//	debugPrintfEXT("490 OUT F:%u cflg:%u",uint(ShaderFlags.frameNum),P[Findex].bcs[0].clflg);
			P[Findex].bcs[0].clflg = 0;
		}
	}
	
	
	
	if(P[Bindex].VelRad.y != 0.0 && P[Findex].prvvel.y == false)
	{
		
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.y-P[Findex].PosLoc.y);
		// If distance is less than radius
		if( distB < tol  )
		{
			if(P[Findex].bcs[1].clflg == 0)
			{
				colQ.inBY = true;
				InPosB = vec3(P[Findex].PosLoc.x,P[Bindex].PosLoc.y,P[Findex].PosLoc.z);
				//InVelB = vec3(P[Findex].VelRad.x,-P[Findex].VelRad.y,P[Findex].VelRad.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].bcs[1].clflg = 1;
				P[Findex].VelRad.xyz = newVel;
			}
			else
			{
				if(Findex == 490 ||Findex == 492 )
					debugPrintfEXT("P:%u Y Inc CFLG F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[1].clflg);
				
				
				if(P[Findex].bcs[1].clflg++ == 4)
					P[Findex].PosLoc.y += P[Findex].VelRad.y*.5;
				
			}
		}
		else
			P[Findex].bcs[1].clflg = 0;
	}
	
	
	if(P[Bindex].VelRad.z != 0.0 && P[Findex].prvvel.z == false)
	{
		// Get distance between x of particl eand x of 
		// boundary
		distB = abs(P[Bindex].VelRad.z-P[Findex].PosLoc.z);
		// If distance is less than radius
		if( distB < tol)
		{
			if(P[Findex].bcs[2].clflg == 0)
			{
				colQ.inBZ = true;
				InPosB = vec3(P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Bindex].PosLoc.z);
				//InVelB = vec3(P[Findex].VelRad.x,P[Findex].VelRad.y,-P[Findex].VelRad.z);
				CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);			
				P[Findex].bcs[2].clflg = 1;
				P[Findex].VelRad.xyz = newVel;
			}
			else
			{
				if(Findex == 490 ||Findex == 492 )
					debugPrintfEXT("P:%u Z Inc CFLG F:%u cflg:%u",Findex,uint(ShaderFlags.frameNum),P[Findex].bcs[2].clflg);
				
				
				if(P[Findex].bcs[2].clflg++ == 4)
					P[Findex].PosLoc.z += P[Findex].VelRad.z*.5;
				
			}
		}
		else
			P[Findex].bcs[2].clflg = 0;
	}
	


}


