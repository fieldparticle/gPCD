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
function hdl = PlotParticleCircle(x,y,R)
    
    
    % ---------------------
    % Sub plot particle image.
    % ---------------------
    colorr = [1.0,0.0,0.0];
	[xcrc,ycrc] = CircleFields(x,y,R);
	plot(xcrc,ycrc,'LineWidth',2,'Color',colorr);


end
