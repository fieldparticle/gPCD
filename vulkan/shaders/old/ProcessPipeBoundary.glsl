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
void ProcessPipeBoundary(uint Findex, uint Bindex, in out vec3 OutVel)
{

	uint startf = 1957;
	uint endf = 1962;
	uint particl = 5185;
	
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
#if 0	
	//if( xc == 1 && yc == 21 && zc == 11)
	if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
	{
			debugPrintfEXT("F:%u IN distB:%0.5f P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C<%u,%u,%u>",
			uint(ShaderFlags.frameNum),distB,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			uint(round(P[Bindex].PosLoc.x)),uint(round(P[Bindex].PosLoc.y)),uint(round(P[Bindex].PosLoc.z)));

	}
#endif
	// Boundary points are stored in velocity since
	// boudnaries are not moving. Boundaries with a zero
	// in a coordintate don't matter.
	if(P[Bindex].VelRad.y != 0.0 || P[Bindex].VelRad.z != 0.0 ) 
	{
		float xT = P[Findex].PosLoc.x;
		float yT = P[Findex].PosLoc.y;
		float zT = P[Findex].PosLoc.z;
		
		float angx = -atan2piPt(vec2(P[Findex].VelRad.y,P[Findex].VelRad.x));
		float zB = CENTER+RADIUS*cos(angx);
		float yB = CENTER+RADIUS*sin(angx);
		
		float dsq = RADIUS*RADIUS;
		float yr = (yT-CENTER)+P[Findex].PosLoc.w;
		float zr = (zT-CENTER)+P[Findex].PosLoc.w;
		float psq = ((yr*yr)+(zr*zr));	
		float rsq = ((P[Findex].PosLoc.w)*(P[Findex].PosLoc.w));	
	
			
#if 1
			if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
			{
			debugPrintfEXT("F:%u CELL psq:%0.4f dsq:%0.4f,P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C<%u,%u,%u>",
			uint(ShaderFlags.frameNum),psq,dsq,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			uint(round(P[Bindex].PosLoc.x)),uint(round(P[Bindex].PosLoc.y)),uint(round(P[Bindex].PosLoc.z)));
			}
#endif
	
		//P[Findex].VelRad.xyz = vec3(0.0,0.0,0.0);
		//if( xc == 1 && yc == 13 && zc == 21)
		#if 0
		//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
			{
				debugPrintfEXT("F:%u,zT:%0.5f,yT:%0.5f,zB:%0.5f,yB:%0.5f,dsq:%0.5f,psq:%0.5f,rsq:%0.5f,diff:%0.5f",uint(ShaderFlags.frameNum),zT,yT,zB,yB,dsq,psq,rsq,dsq-psq);
		
			}
		#endif
		
		
		if((dsq-psq) < rsq && P[Findex].bcs[0].clflg == 0)
		{
			
#if 1
			if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
			{
			debugPrintfEXT("F:%u IN psq:%0.4f dsq:%0.4f,P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> B<%0.3f,%0.3f,%0.3f>",
			uint(ShaderFlags.frameNum),psq,dsq,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			P[Bindex].PosLoc.x,P[Bindex].PosLoc.y,P[Bindex].PosLoc.z);
			}
#endif
			InVelB = vec3(-P[Findex].VelRad.x,-P[Findex].VelRad.y,-P[Findex].VelRad.z);
			InPosB = vec3(P[Bindex].PosLoc.x-0.2,P[Bindex].PosLoc.y,P[Bindex].PosLoc.z);
			//InPosB = vec3(P[Findex].PosLoc.x,yB,zB);
			CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
			//P[Findex].VelRad.y = -P[Findex].VelRad.y;
			//P[Findex].VelRad.z = -P[Findex].VelRad.z;
			P[Findex].VelRad.xyz = newVel;
			//P[Findex].VelRad.x *=-1.0f;
			P[Findex].bcs[0].clflg = 1;
			//float sqpen = (dsq-psq) - rsq;
			//float fpen = rsq/sqpen;
			//P[Findex].PosLoc.xyz += P[Findex].VelRad.xyz*5*dt; 
			//float pangx = atan2piPt(vec2(P[Findex].VelRad.y,P[Findex].VelRad.x));
			//float dy = P[Findex].PosLoc.w*cos(pangx)*1.1;
			//float dz = P[Findex].PosLoc.w*sin(pangx)*1.1;
			//P[Findex].PosLoc.y += dy;
			//P[Findex].PosLoc.z += dz;
			
			
#if 1
			if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) < endf) && Findex == particl)
			{
			debugPrintfEXT("F:%u OUT distB:%0.5f P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C<%u,%u,%u>",
			uint(ShaderFlags.frameNum),distB,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			uint(round(P[Bindex].PosLoc.x)),uint(round(P[Bindex].PosLoc.y)),uint(round(P[Bindex].PosLoc.z)));
			}
#endif			
		}
		else
			P[Findex].bcs[0].clflg = 0;

	}
		
	
	
}


