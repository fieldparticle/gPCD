/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/SwapChain.cpp $
% $Id: SwapChain.cpp 31 2023-06-12 20:17:58Z jb $
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
%*$Revision: 31 $
%*
%*
%******************************************************************/
#ifndef INPUT_HPP
#define INPUT_HPP

extern bool QuitEvent;
extern float ZoomX;
extern float Zoomy;
extern float Zoomz;
extern float ColorMap;
extern bool G_Boundary;
extern bool G_Stop;
extern float G_OrthoMin;
extern float G_OrthoMax;
extern float TranslateX;
extern float TranslateY;
extern float TranslateZ;
extern float RotateX;
extern float RotateY;
extern float RotateZ;
extern float rRotX;
extern float rRotY;
extern float rRotZ;

void SetCallBacks(VulkanObj* VO);
void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods);
void mouse_callback(GLFWwindow* window, double xposIn, double yposIn);
void scroll_callback(GLFWwindow* window, double xoffset, double yoffset);
void onMouseButton(GLFWwindow* window, int button, int action, int mods);

#endif