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
#include "libconfig.h"
#include "mout2_0/mout.hpp"
#include "VerifyConfigObj.hpp"

int VerifyConfigObj::GetInt(std::string lookup, bool failFlag)
{
	int int_temp = 0;
	if (config_lookup_int(&m_cfg, lookup.c_str(), &int_temp))
		mout << "Cfg:" << lookup << " is:" << int_temp << ende;

	else if (failFlag == true)
	{
		
		std::string err = "GetInt - Unable to find:" + lookup  ;
		throw std::runtime_error(err.c_str());
	}
	return int_temp;
};

uint32_t VerifyConfigObj::GetUInt(std::string lookup, bool failFlag)
{

	if (config_lookup_int(&m_cfg, lookup.c_str(), &int_temp))
		mout << "Cfg:" << lookup << " is:" << int_temp << ende;
	else if (failFlag == true)
	{
		
		std::string err = "GetUInt - Unable to find:" + lookup ;
		throw std::runtime_error(err.c_str());
	}
	return static_cast<uint32_t>(int_temp);
};
const char* VerifyConfigObj::GetString(std::string lookup, bool failFlag)
{

	
	if (config_lookup_string(&m_cfg, lookup.c_str(), &str_temp))
		mout << "Cfg:" << lookup << " is:" << str_temp << ende;
	else if (failFlag == true)
	{
		std::string err = "GetString - Unable to find:" + lookup ;
		throw std::runtime_error(err.c_str());
	}
	return str_temp;
};

bool VerifyConfigObj::GetBool(std::string lookup, bool failFlag)
{

	if (config_lookup_bool(&m_cfg, lookup.c_str(), &int_temp))
		mout << "Cfg:" << lookup << " is:" << int_temp << ende;
	else if (failFlag == true)
	{
		
		std::string err = "Get Bool - Unable to find:" + lookup;
		throw std::runtime_error(err.c_str());
	}
	return int_temp;
};
float VerifyConfigObj::GetFloat(std::string lookup, bool failFlag)
{

	if (config_lookup_float(&m_cfg, lookup.c_str(), &float_temp))
		mout << "Cfg:" << lookup << " is:" << float_temp << ende;
	else if (failFlag == true)
	{
		
		std::string err = "GetFloat - Unable to find:" + lookup ;
		throw std::runtime_error(err.c_str());
	}
	return static_cast<float>(float_temp);
};
void VerifyConfigObj::ReadConfigFile(std::string FileName)
{
	int errline = 0;
	const char* errtxt = nullptr;
	if (!config_read_file(&m_cfg, FileName.c_str()))
	{
		errline = config_error_line(&m_cfg);
		errtxt = config_error_text(&m_cfg);
		std::ostringstream  objtxt;
		objtxt << FileName.c_str() << " ReadConfigFile- Error:" << errtxt 
			<< " Line:" << errline  << std::ends;
		throw std::runtime_error(objtxt.str().c_str());
	}
};

std::vector<const char*> VerifyConfigObj::GetArray(std::string Name)
{
	int count = 0;
	config_setting_t* cfg = StartStructure(Name, count);
	std::vector<const char*> vec;
	for (int i = 0; i < count; ++i)
	{
		vec.push_back(GetArrayElementString(cfg, i));
	}

	return vec;
}


config_setting_t* VerifyConfigObj::StartStructure(std::string Name, int& Count)
{

	setting = config_lookup(&m_cfg, Name.c_str());
	if (setting == NULL)
	{
		
		std::string err = "Start Structure Failed:" ;
		throw std::runtime_error(err.c_str());
	}
	m_Count = config_setting_length(setting);
	Count = m_Count;

	return setting;
}
config_setting_t* VerifyConfigObj::GetSubStructAddress(config_setting_t* setting, int index)
{

	return config_setting_get_elem(setting, index);

}

bool VerifyConfigObj::GetNextSubStruct(config_setting_t* setting, std::vector<pair> &pairs, int index)
{
	config_setting_t* ele = config_setting_get_elem(setting, index);
	if (ele == NULL)
	{
		util = ele->name;
		std::string err = "Can't find:" + util + " SubStructure";
		throw std::runtime_error(err.c_str());
	}


	for (int ii = 0; ii < pairs.size(); ii++)
	{
		
		if (pairs[ii].Type == STRC_FLOAT)
		{
			if (config_setting_lookup_float(ele, pairs[ii].Name.c_str(), &float_temp) != CONFIG_TRUE)
			{
				std::string err = "Pairs - Can't find:" + pairs[ii].Name;
				if(pairs[ii].retFlg == true)
					throw std::runtime_error(err.c_str());
				else
					mout << err << ende;
			}
			mout << "Cfg:" << pairs[ii].Name << " is:" << float_temp << ende;
			*((float*)pairs[ii].Value) = static_cast<float>(float_temp);
		}
		if (pairs[ii].Type == STRC_UINT)
		{
			if (config_setting_lookup_int(ele, pairs[ii].Name.c_str(), &int_temp) != CONFIG_TRUE)
			{
				std::string err = "pairs uint Can't find:" + pairs[ii].Name;
				if (pairs[ii].retFlg == true)
					throw std::runtime_error(err.c_str());
				else
					mout << err << ende;
			}
			mout << "Cfg:" << pairs[ii].Name << " is:" << float_temp << ende;
			*((int*)pairs[ii].Value) = int_temp;
		}
		if (pairs[ii].Type == STRC_INT)
		{
			if (config_setting_lookup_int(ele, pairs[ii].Name.c_str(), &int_temp) != CONFIG_TRUE)
			{
				std::string err = "paris int Can't find:" + pairs[ii].Name;
				if (pairs[ii].retFlg == true)
					throw std::runtime_error(err.c_str());
				else
					mout << err << ende;
			}
			mout << "Cfg:" << pairs[ii].Name << " is:" << float_temp << ende;
			*((int*)pairs[ii].Value) = int_temp;
		}
	}

	return true;
}
void VerifyConfigObj::GetArrayElementFloats(config_setting_t* setting, std::string Name, float* Ary, uint32_t Max, int index)
{
	config_setting_t* ele = config_setting_get_elem(setting, index);
	if (ele == NULL)
	{
		util = ele->name;
		std::string err = "Can't find:" + util + " SubStructure";
		throw std::runtime_error(err.c_str());
	}

	config_setting_t* cary = config_setting_get_member(ele, Name.c_str());
	if (cary != NULL)
	{
		uint32_t ccount = config_setting_length(cary);

		for (uint32_t j = 0; j < ccount && j < Max; j++)
		{
			float_temp = (config_setting_get_float_elem(cary, j));
			mout << "Cfg:" << lookup << " is:" << float_temp << ende;
			Ary[j] = static_cast<float>(float_temp);
		}

	}
}

const char* VerifyConfigObj::GetArrayElementString(config_setting_t* setting, int index)
{

	str_temp = config_setting_get_string_elem(setting, index);
	mout << "Cfg:" << lookup << " is:" << str_temp << ende;
	return str_temp;
}








