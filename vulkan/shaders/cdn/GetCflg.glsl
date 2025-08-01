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

void ClearDups( uint Findex)
{
	P[Findex].sltnum = 0;
	for (uint ii = 0; ii < 12; ii++)
	{
		P[Findex].ccs[ii].pindex = 0;
	}
}

bool inColl(uint Findex, uint Tindex)
{
	uint slot = 0;
	for (uint ii = 0; ii < 12 ; ii++)
	{
		if(P[Findex].ccs[ii].pindex == Tindex)
		{
			//debugPrintfEXT("True");
			return true;
		}
		if(P[Findex].ccs[ii].pindex == 0)
		{
			slot = ii;
			break;
		}
	}

	P[Findex].ccs[slot].pindex = Tindex;
	//debugPrintfEXT("False slot:%u TO:%u",slot,Tindex);
	return false;
}

void ClearCflg(uint Findex, uint Tindex)
{
	for (uint ii = 0; ii < 12 ; ii++)
	{
			
		if(P[Findex].ccs[ii].pindex == Tindex)
		{
			P[Findex].ccs[ii].pindex = 0;
			return;
		}
		
	}
}
#if 0

int GetCflg(uint crnr, uint Findex, uint Tindex)
{

	for(int ii = 0; ii < 12; ii++)
	{
		if(P[Findex].ccs[crnr][ii].pindex == Tindex)
			return ii;
	}
	return -1;
}
int SetCflg(uint crnr, uint Findex, uint Tindex)
{
	for(int ii = 0; ii < 4; ii++)
	{
		if(P[Findex].ccs[crnr][ii].pindex == 0)
		{
			P[Findex].ccs[crnr][ii].pindex = Tindex;
			return ii;
		}
	}
	return -1;
}



#endif