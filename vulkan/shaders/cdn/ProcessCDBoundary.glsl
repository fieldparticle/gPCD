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
void ProcessCDBoundary(uint Findex, uint Bindex, in out vec3 OutVel)
{

	
	uint startf = 4309;
	uint endf = 4312;
	uint particl = 4688;
	
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
	uint xb = uint(round(P[Bindex].PosLoc.x));
	uint yb = uint(round(P[Bindex].PosLoc.y));
	uint zb = uint(round(P[Bindex].PosLoc.z));
	uint locidx = ArrayToIndex(uvec3(xb,yb,zb));
	
	uint xc = uint(round(P[Findex].PosLoc.x));
	uint yc = uint(round(P[Findex].PosLoc.y));
	uint zc = uint(round(P[Findex].PosLoc.z));
	
#if 0	
	//if( xb == 1 && yb == 21 && zb == 11)
	//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && Findex == particl)
	if(P[Findex].VelRad.z < 0.0)
	{
			debugPrintfEXT("F:%u INBOUND P:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C<%u,%u,%u>",
			uint(ShaderFlags.frameNum),Findex,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			xb,yb,zb);
			P[0].PosLoc.w  = 1.0;

	}
#endif
	// Boundary points are stored in velocity since
	// boudnaries are not moving. Boundaries with a zero
	// in a coordintate don't matter.
	if(P[Bindex].VelRad.x != 0.0 || P[Bindex].VelRad.y != 0.0 || P[Bindex].VelRad.z != 0.0 ) 
	{
		float xT = P[Findex].PosLoc.x;
		float yT = P[Findex].PosLoc.y;
		float zT = P[Findex].PosLoc.z;
		
		float angx = atan2piPt(vec2(P[Findex].PosLoc.y,P[Findex].PosLoc.x));
		float xB = CENTER+RADIUS*cos(angx);
		float yB = CENTER+RADIUS*sin(angx);
		float radius = GetCDRadius(P[Findex].PosLoc.z);
		float dsq = radius*radius;
		float yr = abs(yT-CENTER)+2*P[Findex].PosLoc.w;
		float xr = abs(xT-CENTER)+2*P[Findex].PosLoc.w;
		float psq = ((yr*yr)+(xr*xr));	
		float rsq = ((P[Findex].PosLoc.w)*(P[Findex].PosLoc.w));	
		
			
#if 0
			if( uint(ShaderFlags.frameNum) > startf && Findex == particl)
			//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && Findex == particl)
			//if(Findex == particl)
			{
			float prad = sqrt(psq);
			debugPrintfEXT("CELL F:%u FP:%d TP:%d cdrad:%0.4f,prad:%0.4f,psq:%0.4f dsq:%0.4f,CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C(%u)<%u,%u,%u>",
			uint(ShaderFlags.frameNum),Findex,Bindex,
			radius,prad,
			psq,dsq,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			locidx,xb,yb,zb);
			}
#endif
	
		//P[Findex].VelRad.xyz = vec3(0.0,0.0,0.0);
		//if( xb == 1 && yb == 13 && zb == 21)
#if 0
		if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && Findex == particl)
			{
				
				debugPrintfEXT("F:%u,FP:%d TP:%d,xT:%0.5f,yT:%0.5f,xB:%0.5f,yB:%0.5f,dsq:%0.5f,psq:%0.5f,rsq:%0.5f,diff:%0.5f C:(%u)<%u,%u,%u>,PC:<%u,%u,%u>",uint(ShaderFlags.frameNum),Findex,Bindex,
				xT,yT,
				xB,yB,
				dsq,psq,rsq,
				dsq-psq,
				locidx,xb,yb,zb,
				xc,yc,zc);
		
			}
#endif
		
		
		if(psq >= dsq && P[Findex].bcs[0].clflg == 0)
		{
			
#if 0
			//if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && Findex == particl)
			if(Findex == particl)
			{
			debugPrintfEXT("F:%u IN psq:%0.4f dsq:%0.4f,P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> B(%u)<%0.3f,%0.3f,%0.3f> C(%u)<%u,%u,%u>",
			uint(ShaderFlags.frameNum),psq,dsq,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			Bindex,P[Bindex].PosLoc.x,P[Bindex].PosLoc.y,P[Bindex].PosLoc.z,
			locidx,xb,yb,zb);
			}
#endif
			//InPosB = vec3(P[Bindex].PosLoc.x,P[Bindex].PosLoc.y,P[Bindex].PosLoc.z);
			//InVelB = vec3(-P[Findex].VelRad.x,-P[Findex].VelRad.y,P[Findex].VelRad.z);
			//CalcMomentum(Findex,Fm,Ft,InPosF,InPosB,InVelF,InVelB,newVel);	
			newVel = CalcBoundaryVel(Findex,InPosF,InVelF,CENTER);
			P[Findex].VelRad.xyz = newVel;
			//P[Findex].PosLoc.xy += P[Findex].VelRad.xy*0.1;
			P[Findex].bcs[0].clflg = 1;
			
			
#if 0
			if( (uint(ShaderFlags.frameNum) > startf && uint(ShaderFlags.frameNum) <= endf) && Findex == particl)
			//if(Findex == particl)
			{
			debugPrintfEXT("F:%u OUT distB:%0.5f P:%d CFL:%d V<%0.3f,%0.3f,%0.3f>,P<%0.3f,%0.3f,%0.3f> C(%u)<%u,%u,%u>",
			uint(ShaderFlags.frameNum),distB,Findex,P[Findex].bcs[0].clflg,
			P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,
			P[Findex].PosLoc.x,P[Findex].PosLoc.y,P[Findex].PosLoc.z,
			locidx,xb,yb,zb);
			}
#endif			
		}
		else
			if(P[Findex].bcs[0].clflg++ == 6)
				P[Findex].bcs[0].clflg = 0;

	}
		
	
	
	
}


