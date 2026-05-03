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

bool CheckCompDups(uint Findex, uint Tindex, uint SltIdx, uint jloc, uint iloc)
{

#if 0 && defined(DEBUG)
					if(uint(ShaderFlags.frameNum) == 8 && Findex == 1)
						debugPrintfEXT("CheckCompDups IN F:%u,Findex:%u Tindex:%u,SltIdx:%u,jloc:%u, iloc:%u",
									uint(ShaderFlags.frameNum),Findex,Tindex,SltIdx,jloc,iloc);
#endif	
	for(uint t = 0; t < jloc; t++)
	{
		if (clink[SltIdx].idx[t] == Tindex)
		{
#if 0 && defined(DEBUG)
					if(uint(ShaderFlags.frameNum) == 8 && Findex == 1)
						debugPrintfEXT("CheckCompDups TRUE Findex:%u Tindex:%u,SltIdx:%u,jloc:%u",
									Findex,Tindex,SltIdx,jloc);
#endif
			return true;
		}
	}
#if 0 && defined(DEBUG)
					if(uint(ShaderFlags.frameNum) == 8 && Findex == 1)
						debugPrintfEXT("CheckCompDups FALSE F:%u,Findex:%u Tindex:%u,SltIdx:%u,jloc:%u, iloc:%u",
									uint(ShaderFlags.frameNum),Findex,Tindex,SltIdx,jloc,iloc);
#endif	
	return false;
}	

