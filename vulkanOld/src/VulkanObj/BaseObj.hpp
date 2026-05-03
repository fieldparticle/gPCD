/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/main.cpp $
% $Id: main.cpp 28 2023-05-03 19:30:42Z jb $
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
%*$Revision: 28 $
%*
%*
%******************************************************************/
#ifndef BASE_OBJ_HPP
#define BASE_OBJ_HPP

class VulkanObj;
class ConfigObj;
class BaseObj 
{
	public :
		std::string m_Name;
		std::string m_wkstr;
		uint32_t	m_Type=0;
		VulkanObj*	m_App = {};
		ConfigObj* m_ACfg = {};
		uint32_t	m_thisFramesBuffered;
		BaseObj() {};
		BaseObj(std::string Name, uint32_t Type, VulkanObj* App);
		
		uint32_t	GetType() {
			return m_Type;
		};
		std::string* getName()
		{
			return &m_Name;
		}
		virtual void Cleanup()=0;
};
#endif