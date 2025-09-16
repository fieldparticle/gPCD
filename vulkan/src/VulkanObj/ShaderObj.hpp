/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/DrawObj.hpp $
% $Id: DrawObj.hpp 31 2023-06-12 20:17:58Z jb $
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


#ifndef GENSHADERS_HPP
#define GENSHADERS_HPP
class ResourceCollMatrix;
class ResourceLockMatrix;
class BaseObj;
class ShaderObj : public BaseObj
{
public:
	ResourceVertexParticle* m_VPO = {};
	ResourceCollMatrix* m_CMO = {};
	SwapChain* m_SCO = {};
	ResourceLockMatrix* m_LMO;

	uint32_t SH_VERT = 1;
	uint32_t SH_FRAG = 2;
	uint32_t SH_COMP = 3;


	ShaderObj(VulkanObj* App, std::string Name) : BaseObj(Name, 0, App) {};
	void GenWorkGroups(std::string testType);
	void WriteShaderHeader();
	void WriteShaderHeaderCDNOZ();
	int RemoteCompileShaders();
	std::vector<char> ReadSPVFile(const std::string& filename);
	int WriteBinaryFile(std::string fileName, std::vector<char> buffer);
	int CompileShader(std::string ShaderName, 
		std::string ShaderFileName,
		std::vector<char>& SPVBuffer,
		uint32_t type);
	void Create(ResourceVertexParticle* VPO, ResourceCollMatrix* CMO, ResourceLockMatrix* LMO,SwapChain* SCO);
	void Cleanup() {};

};
#endif