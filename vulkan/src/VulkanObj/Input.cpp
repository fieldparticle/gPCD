
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
#include "VulkanObj/VulkanApp.hpp"
#include "Input.hpp"
bool QuitEvent=false;
float ZoomX = 1.0;
float ZoomY = 1.0;
float ZoomZ = 1.0;
float ColorMap = 0.0;
bool G_Boundary = true;
float G_OrthoMin =-100.0f;
float G_OrthoMax = 350.0f;
float TranslateX=0.0;
float TranslateY=0.0;
float TranslateZ=0.0;
bool G_Stop = true;
float RotateX=0.0;
float RotateY=0.0;
float RotateZ=0.0;
float rRotX;
float rRotY = 90.0;
float rRotZ;
float ox = -1;
float oy = -1;
bool rightMouse = false;

void GLFWError(int err, const char* err_str)
{
	mout << "Error Code:" << err << " Err Msg:" << err_str << ende;

}

void SetCallBacks(VulkanObj* VO)
{
// tell GLFW to capture our mouse
		// Ensure we can capture the escape key being pressed below
	//glfwSetInputMode(app.window, GLFW_STICKY_KEYS, GL_TRUE);
	// Hide the mouse and enable unlimited mouvement
	//glfwSetInputMode(app.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL);
	// Set the mouse at the center of the screen
	//glfwPollEvents();
	//glfwSetCursorPos(app.window, 800 / 2, 800 / 2);
	glfwSetCursorPosCallback(VO->GetGLFWWindow(), mouse_callback);
	glfwSetScrollCallback(VO->GetGLFWWindow(), scroll_callback);
	glfwSetKeyCallback(VO->GetGLFWWindow(), key_callback);
	glfwSetMouseButtonCallback(VO->GetGLFWWindow(), onMouseButton);
	QuitEvent = false;
}
void onMouseButton(GLFWwindow* window, int button, int action, int mods)
{
	if (button == GLFW_MOUSE_BUTTON_LEFT && action == GLFW_PRESS)
	{
		rightMouse = true;
	}
	if (button == GLFW_MOUSE_BUTTON_LEFT && action == GLFW_RELEASE)
	{
		rightMouse = false;
	}
	

}
void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods)
{
	if (key == GLFW_KEY_V && action == GLFW_PRESS)
	{
		ColorMap = 1.0;

	}
	if (key == GLFW_KEY_C && action == GLFW_PRESS)
	{
		ColorMap = 0.0;
	}
	if (key == GLFW_KEY_B && action == GLFW_PRESS)
	{
		if(G_Boundary == true)
			G_Boundary = false;
		else
			G_Boundary = true;
	}
	if (key == GLFW_KEY_N && action == GLFW_PRESS)
	{
		G_OrthoMin += 10.0;
		mout << "New ortho Min:" << G_OrthoMin << ende;
	}
	if (key == GLFW_KEY_E && action == GLFW_PRESS)
	{
		if(G_OrthoMax == 241.0)
		{
			G_OrthoMax = 400.0;
			G_OrthoMin = 100.0;
		}
		else
		{
			G_OrthoMax = 241.0;
			G_OrthoMin = 240.0;
		}

	}
	if (key == GLFW_KEY_M && action == GLFW_PRESS)
	{
		G_OrthoMax -= 1.0;
		mout << "New ortho Max:" << G_OrthoMax << ende;
	}
	if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS)
	{
		QuitEvent = 1;
	}
	if (key == GLFW_KEY_P && action == GLFW_PRESS)
	{
		TranslateX += 1.0;
		//std::cout << TranslateX << std::endl;
	}
	if (key == GLFW_KEY_X && action == GLFW_PRESS)
	{
		rRotX = rRotX += 15.0;
		mout << "RotX:" << rRotX << " RotY:" << rRotY << " RotZ:" << rRotZ << ende;
	}
	if (key == GLFW_KEY_Y && action == GLFW_PRESS)
	{
		rRotY = rRotY += 15.0;
		mout << "RotX:" << rRotX << " RotY:" << rRotY << " RotZ:" << rRotZ << ende;
	}
	if (key == GLFW_KEY_Z && action == GLFW_PRESS)
	{
		rRotZ = rRotZ += 15.0;
		mout << "RotX:" << rRotX << " RotY:" << rRotY << " RotZ:" << rRotZ << ende;
	}
	if (key == GLFW_KEY_S && action == GLFW_PRESS)
	{
		if(G_Stop == true)
			G_Stop = false;
		else
			G_Stop = true;
	
	}
	
	// process all input: query GLFW whether relevant keys are pressed/released this frame and react accordingly
	// ---------------------------------------------------------------------------------------------------------
	if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
		glfwSetWindowShouldClose(window, true);
		

}
// glfw: whenever the mouse moves, this callback is called
// -------------------------------------------------------
void mouse_callback(GLFWwindow* window, double xposIn, double yposIn)
{
#if 1
	if (rightMouse == true)
	{
		
		float X = static_cast<float>(xposIn);
		float Y = static_cast<float>(yposIn);
		const float TPI = (float)3.14159265359;

		RotateX += X - ox;
		if (RotateX > 360.) RotateX -= 360.;
		else if (RotateX < -360.) RotateX += 360.;

		RotateY += Y - oy;
		if (RotateY > 360.) RotateY -= 360.;
		else if (RotateY < -360.) RotateY += 360.;
		ox = X; oy = Y;

		rRotY = RotateY * RotateY / 360;
		rRotX = RotateY * RotateX / 360;
		//std::cout << "Rotate:" << RotateY << "  " << RotateY << std::endl;
	}
#endif
}

// glfw: whenever the mouse scroll wheel scrolls, this callback is called
// ----------------------------------------------------------------------
void scroll_callback(GLFWwindow* window, double xoffset, double yoffset)
{
	//std::cout << "scrool:" << yoffset << "  " << yoffset << std::endl;
		
	ZoomX += static_cast<float>(yoffset)*0.1f;
	//std::cout << "scrool:" << xoffset << ":"<< yoffset << std::endl;
}