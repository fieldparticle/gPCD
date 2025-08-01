/******************************************************************
%***      m PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date:  $
% $HeadURL:  $
% $Id:  $
%*******************************************************************
%***                         DESCRIPTION                         ***
%*******************************************************************
%@doc
%@module
%			@author: Jackie Michael Bell
%			COPYRIGHT <cp> Jackie Michael Bell
%			Property of Jackie Michael Bell<rtm>. All Rights Reserved.
%			This source code file contains proprietary
%			and confidential information.
%
%
%@head3 		Description. | 
%               
%@normal
%********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision:  $
%*
%*
%******************************************************************/
uint CalcMomentum(	uint Findex, 
					float Fm, float Ft,
					vec3 InPosF,
					vec3 InPosT,
					vec3 InVelF,
					vec3 InVelT,
					in out vec3 newVel)
{


	float m1, m2, x1, x2;
	vec3 v1temp, v1, v2, v1x, v2x, v1y, v2y; 
		
	///float xT = P[Findex].PosLoc.x;
   // float yT = P[Findex].PosLoc.y;
    //float zT = P[Findex].PosLoc.z;
	
	//float xP = P[Tindex].PosLoc.x;
   // float yP = P[Tindex].PosLoc.y;
   // float zP = P[Tindex].PosLoc.z;
	
	float tol = 0.00001;
	
	//vec3 x = vec3(xP-xT,yP-yT,zP-zT);
	vec3 x = InPosT-InPosF;

#if 0
	//	if(Findex == 1)
			debugPrintfEXT("Calulated V P:%d vx=%0.3f,vy=%0.3f,vz=%0.3f,mass %0.2f",
			Findex,x.x,x.y,x.z,P[Findex].MolarMatter);
#endif 	

	x = normalize(x);
	v1 = InVelF;
	x1 = dot(x,v1);
	v1x = x * x1;
	v1y = v1 - v1x;
	m1 = Fm;
	
#if 0
	//if(Findex == 489 && uint(ShaderFlags.frameNum) == 56)
	{
			debugPrintfEXT("Frame[%d], Calulated V P:%d x.x=%0.3f,x.y=%0.3f,x.z=%0.3f,v1.x=%0.3f,v1.y=%0.3f,v1.z=%0.3f,x1=%0.3f",
			uint(ShaderFlags.frameNum),Findex,x.x,x.y,x.z,v1.x,v1.y,v1.z,x1);
			
			debugPrintfEXT("Calulated V P:%d v1x.x=%0.3f,v1x.y=%0.3f,v1x.z=%0.3f,v1y.x=%0.3f,v1y.y=%0.3f,v1y.z=%0.3f",
			Findex,v1x.x,v1x.y,v1x.z,v1y.x,v1y.y,v1y.z);	
	}
#endif 	
	
	
	x = x*-1;
	v2 = InVelT;
	x2 = dot(x,v2);
	v2x = x * x2;
	v2y = v2 - v2x;
	m2 = Ft;
	
#if 0
	//if(Findex == 489 && uint(ShaderFlags.frameNum) == 56)
	{
			debugPrintfEXT("Frame[%d], Calulated V P:%d x.x=%0.3f,x.y=%0.3f,x.z=%0.3f,v2.x=%0.3f,v2.y=%0.3f,v2.z=%0.3f,x2=%0.3f",
			uint(ShaderFlags.frameNum),Findex,x.x,x.y,x.z,v2.x,v2.y,v2.z,x1);
			
			debugPrintfEXT("Calulated V P:%d v2x.x=%0.3f,v2x.y=%0.3f,v2x.z=%0.3f,v2y.x=%0.3f,v2y.y=%0.3f,v2y.z=%0.3f",
			Findex,v2x.x,v2x.y,v2x.z,v2y.x,v2y.y,v2y.z);	
	}
#endif 	

	
	
	newVel = vec3( v1x*(m1-m2)/(m1+m2) + v2x*(2*m2)/(m1+m2) + v1y );
#if 0
	//if(Findex == 489 && uint(ShaderFlags.frameNum) == 56)
		{
			debugPrintfEXT("Calulated NewVel P:%d m1=%0.3f,m2=%0.3f,ovx=%0.3f,ovy=%0.3f,ovz=%0.3f,nvx=%0.3f,nvy=%0.3f,nvz=%0.3f",
			Findex,m1,m2,P[Findex].VelRad.x,P[Findex].VelRad.y,P[Findex].VelRad.z,newVel.x,newVel.y,newVel.z);
		}
#endif 	



    return 0;
}

