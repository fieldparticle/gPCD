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
int CalcParticleResponse(uint crnr,uint Findex,uint Tindex)
{
	return 0;
	float Fm 	= P[Findex].MolarMatter;
	float Ft 	= P[Tindex].MolarMatter;
	vec3 InPosF = P[Findex].PosLoc.xyz;
	vec3 InPosT = P[Tindex].PosLoc.xyz;
	vec3 InVelF	= P[Findex].VelRad.xyz;
	vec3 InVelT	= P[Tindex].VelRad.xyz;
	vec3 newVel;
	int slot 	=  -2;
	
	slot = GetCflg(crnr,Findex,Tindex);
	if(slot == -1)
	{
		CalcMomentum(Findex,Fm,Ft,InPosF,InPosT,InVelF,InVelT,newVel);
		P[Findex].PosLoc.xyz = newVel;
		SetCflg(crnr, Findex, Tindex);
		atomicAdd(collOut.CollisionCount,1);
		return -1;
	}
		
    return slot ;
}

