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


@head3 		Description. |
@normal


********************************************************************
%***                     SVN CHANGE RECORD                       ***
%*******************************************************************
%*$Revision: 28 $
%*
%*
%******************************************************************/

#ifndef CONFIGOBJ_HPP
#define CONFIGOBJ_HPP
#include "libconfig/libconfig.h"
#include <iostream>
#include <vector>
#include <sstream>
#include "mout2_0/mout.hpp"
extern MsgStream			mout;   
class VulkanObj;
class ConfigObj 
{
public:

	bool						m_NSight = false;
	bool						m_NoCompute = false;
			
	//---------------------------- Read write used to record across instances
	int					_StructCount	= 0;
	uint32_t			m_StructIdx		= 0;
	std::string			m_cfg_file;
	config_t 			m_cfg;
	config_setting_t*	m_setting;
	int 				int_temp		= 0;
	const char*			str_temp;
	double				float_temp		= 0.0;
	std::string			lookup;
	std::string			util;
	int					m_Count=0;

	struct pair
	{
		std::string Name;
		void*		Value;
		uint32_t	Type;
		bool		retFlg;
	};
	uint32_t STRC_STRING = 1;
	uint32_t STRC_INT = 2;
	uint32_t STRC_UINT = 3;
	uint32_t STRC_FLOAT = 4;

	

	int GetInt(std::string lookup, bool failFlag)	;
	uint32_t GetUInt(std::string lookup, bool failFlag);
	const char* GetString(std::string lookup, bool failFlag);
	bool GetBool(std::string lookup, bool failFlag);
	float GetFloat(std::string lookup, bool failFlag);
	void ReadConfigFile(std::string FileName);
	void GetParticleSettings();
	void GetParticleSettingsV2(std::string TestName);
	std::vector<const char*> GetArray(std::string Name);
	config_setting_t* StartStructure(std::string Name, int& Count);
	config_setting_t* GetSubStructAddress(config_setting_t* setting, int index);
	bool GetNextSubStruct(config_setting_t* setting, std::vector<pair> &pairs, int index);
	const char* GetArrayElementString(config_setting_t* setting, int index);
	void GetArrayElementFloats(config_setting_t* setting, std::string Name, float *Ary, uint32_t Max,int index);

	VulkanObj* m_App;
	ConfigObj() {};
	virtual void Create(std::string cfg_file);
	void SetVulkanObj(VulkanObj* app)
	{
		m_App = app;
	}
	

};

#endif