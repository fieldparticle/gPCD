%******************************************************************
%***      m PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2022-02-10 13:08:17 -0800 (Thu, 10 Feb 2022) $
% $HeadURL: https://jbworkstation/svn/svnroot/svnmatlab/common/@Scene/PlotMultiEval.m $
% $Id: PlotMultiEval.m 54 2022-02-10 21:08:17Z jb $
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
%@normal
%********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 54 $
%*
%*
%******************************************************************/
function [xcrc,ycrc] = CircleFields(xpos,ypos,radius)

rr = 0:0.01:2*pi();
lenr = length(rr);

xcrc = [];
ycrc = [];

% Draw fields at new location.
	for itr = 1:lenr

		xcrc(itr)... 
			= double(xpos)+radius*cos(rr(itr));
		
		ycrc(itr)...  
			= double(ypos)+radius*sin(rr(itr));
	end

end