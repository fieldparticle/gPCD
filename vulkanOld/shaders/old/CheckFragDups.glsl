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

bool CheckFragDups(uint Findex, uint SltIdx, uint Corner)
{
	for(uint t = 0; t < Corner; t++)
	{
		if (P[Findex].zlink[t].ploc == SltIdx)
		{
#if 0 && defined(DEBUG)
					if(ShaderFlags.frameNum == 8 && Findex == 19)
						debugPrintfEXT("CheckFragDups TRUE t:%u SltIdx%u,Corner:%u",t,SltIdx,Corner);
#endif
			return true;
		}
	}
	
	return false;
}

