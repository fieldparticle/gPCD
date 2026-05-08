/***      m PROPRIETARY SOURCE FILE IDENTIFICATION               ***
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
// Takes the index of two particles and detemines the distance between them
// If the distance is less than the sum of radii squared the are in comllsion.
// If collsiong increment the collsion counter.

uint isParticleContact(uint crnr, uint Findex, uint Tindex)
{

	if(Findex == Tindex )
		return 0;

	float xT = P[Findex].PosLocA.x;
    float yT = P[Findex].PosLocA.y;
    float zT = P[Findex].PosLocA.z;
	
	float xP = P[Tindex].PosLocA.x;
    float yP = P[Tindex].PosLocA.y;
    float zP = P[Tindex].PosLocA.z;
		 // Get distance between centers
    float dsq = ((xP-xT)*(xP-xT)+
                    (yP-yT)*(yP-yT)+
                    (zP-zT)*(zP-zT));
	
	//float rsq = ((P[Findex].PosLoc.w+P[Tindex].PosLoc.w)*(P[Findex].PosLoc.w+P[Tindex].PosLoc.w));
	float rsq = ((P[Findex].Data.x+P[Tindex].Data.x)*(P[Findex].Data.x+P[Tindex].Data.x));
	// If square of distance is less than square of radii there is a collision.
	float tdt = rsq/dsq;
	#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 3 && Findex == 5)
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.8f,rsq:%0.8f,rddiff:%0.8f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			Findex,
			Tindex,dsq,rsq,dsq-rsq,P[Findex].Data.x,P[Tindex].Data.x);
	#endif
	
	float rddiff = dsq-rsq;	
	//if (dsq <= rsq )
	if(rddiff < 0.00001 || rddiff < 0.0)
    {
		#if 0 && defined(DEBUG)
		if(uint(ShaderFlags.frameNum) == 3)// && Findex == 1)
			debugPrintfEXT("Collison Frame(%0.1f),FRM:%d,TO:%d dsq:%0.4f,rsq:%0.4f,Radius1:%0.4f,Radius2:%0.4f",
			ShaderFlags.frameNum,
			Findex,
			Tindex,dsq,rsq,P[Findex].PosLoc.w,P[Tindex].PosLoc.w);
		#endif	
	
		return 1;
	}

	return 0;
}