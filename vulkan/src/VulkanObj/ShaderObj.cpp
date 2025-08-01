/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************GPO
% $Author: jb $
%
% $Date: 2023-06-12 16:17:58 -0400 (Mon, 12 Jun 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src_app/mfpm/DrawObj.cpp $
% $Id: DrawObj.cpp 31 2023-06-12 20:17:58Z jb $
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
void ShaderObj::Create(ResourceVertexParticle* VPO, ResourceCollMatrix* CMO, ResourceLockMatrix* LMO, SwapChain* SCO)
{
		m_VPO = VPO;
		m_CMO = CMO;
		m_SCO = SCO;
		m_LMO = LMO;
		std::string testtype = CfgApp->GetString("application.testtype", true);
		if(testtype.compare("cdn") == 0)
			WriteShaderHeaderCDNOZ();
		if(testtype.compare("VerfPerf") == 0)
			WriteShaderHeader();
		GenWorkGroups(testtype);
}
void ShaderObj::GenWorkGroups(std::string testType)
{

	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/" + testType + "/workgroups.glsl";
	{
		std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		ostrm << "layout(local_size_x = " << CfgTst->GetInt("workGroupsx", true) <<
			", local_size_y = " << CfgTst->GetInt("workGroupsy", true) <<
			", local_size_z = " << CfgTst->GetInt("workGroupsz", true) << ") in;\n";
	}
}
void  ShaderObj::WriteShaderHeaderCDNOZ()
{
	
	uint32_t compflag=0;
	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
    std::string filename = fildir + "/cdn/params.glsl";
    {
		std::string dbgflag = {};
#ifdef NDEBUG
		dbgflag = "RELEASE ";
#else
		dbgflag = "DEBUG ";
#endif
		
		std::string version = {};
		version = "VERCDNOZ ";
		
		uint32_t motion_str = 0;
		if(CfgApp->GetBool("application.doMotion", true) == true)
			motion_str = 1;
		

		
		uint32_t MaxLoc = static_cast<uint32_t>(CfgTst->GetUInt("CellAryW", true)
											  * CfgTst->GetUInt("CellAryH", true) 
											  * CfgTst->GetUInt("CellAryL", true));
        std::ofstream ostrm(filename);
		ostrm	<< "#define " << dbgflag << "\n"
				<< "#define " << version.c_str()  << "\n"
				<< "const uint WIDTH=" << CfgTst->GetUInt("CellAryW", true)  << ";\n"
				<< "const uint HEIGHT=" << CfgTst->GetUInt("CellAryH", true) << ";\n"
				<< "const uint DEPTH=" << CfgTst->GetUInt("CellAryL", true)  << ";\n"
				<< "const uint CENTER=" << CfgTst->GetFloat("PipeCenter", true) << ";\n"
				<< "const float RADIUS=" <<  CfgTst->GetFloat("PipeRadius", true)  << ";\n"
				<< "const uint MAX_ARY=" << CfgTst->GetInt("ColArySize", true) << ";\n"
				<< "const uint SCR_W =" << m_SCO->m_SwapWidth << ";\n"
				<< "const uint SCR_H =" << m_SCO->m_SwapHeight << ";\n"
				<< "const uint SCR_X =" << m_SCO->m_SwapX << ";\n"
				<< "const uint SCR_Y =" << m_SCO->m_SwapY << ";\n"
				<< "const uint NUMPARTS =" << m_VPO->m_NumParticles << ";\n"
				<< "const uint NUM_PARICLES_COLLIDING =" << CfgTst-> GetInt("num_particle_colliding", true) << ";\n"
				<< "const uint MAXSPCOLLS =" << m_VPO->m_MaxColls << ";\n"
				<< "const uint ColArySize=" << m_CMO->m_BufSize << ";\n"
				<< "const uint LockArySize=" << m_LMO->m_BufSize << ";\n"
				<< "const uint doMotion =" << motion_str  << ";\n"
				<< "const uint MaxLocation =" << m_CMO->m_CellArrayMax << ";\n"
				<< "const float dt =" << m_App->m_dt  << ";\n"
				<< "const uint compflag =" << compflag << ";\n"
				<< "const uint bbound =" << m_VPO->BoundaryParticleLimit << ";\n";
			
			
		ostrm.flush();
		ostrm.close();
    }
}


void  ShaderObj::WriteShaderHeader()
{
	// Dont compile shaders if using nsight.
	if(CfgApp->GetBool("application.nsight", true) == true)
		return;
	uint32_t compflag=0;
	uint32_t motion_str = 0;
	if(CfgApp->GetBool("application.doMotion", true) == true)
		motion_str = 1;

	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
    std::string filename = fildir + "/VerfPerf/params.glsl";
    {
		std::string dbgflag = {};
#ifdef NDEBUG
		dbgflag = "RELEASE ";
#else
		dbgflag = "DEBUG ";
#endif
		
		std::string version = {};
		version = "VERPONLY ";
		
		uint32_t MaxLoc = static_cast<uint32_t>(CfgTst->GetUInt("CellAryW", true)
											  * CfgTst->GetUInt("CellAryH", true) 
											  * CfgTst->GetUInt("CellAryL", true));
        std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		ostrm	<< "#define " << dbgflag << "\n"
				<< "#define " << version.c_str()  << "\n"
				<< "const uint WIDTH=" << CfgTst->GetUInt("CellAryW", true) << ";\n"
				<< "const uint HEIGHT=" << CfgTst->GetUInt("CellAryH", true)  << ";\n"
				<< "const uint DEPTH=" << CfgTst->GetUInt("CellAryL", true) << ";\n"
				//##JMB Get RID
				<< "const uint CENTER=" << 0.0 << ";\n"
				<< "const float RADIUS=" << 0.0 << ";\n"
				<< "const uint MAX_CELL_OCCUPANY=" << CfgTst->GetInt("cell_occupancy_list_size", true) << ";\n"
				<< "const uint SCR_W =" << m_SCO->m_SwapWidth << ";\n"
				<< "const uint SCR_H =" << m_SCO->m_SwapHeight << ";\n"
				<< "const uint SCR_X =" << m_SCO->m_SwapX << ";\n"
				<< "const uint SCR_Y =" << m_SCO->m_SwapY << ";\n"
				<< "const uint NUMPARTS =" << m_VPO->m_NumParticles << ";\n"
				<< "const uint NUM_PARICLES_COLLIDING =" << CfgTst-> GetInt("num_particle_colliding", true) << ";\n"
				<< "const uint MAXSPCOLLS =" << m_VPO->m_MaxColls << ";\n"
				<< "const uint ColArySize=" << m_CMO->m_BufSize << ";\n"
				<< "const uint LockArySize=" << m_LMO->m_BufSize << ";\n"
				<< "const uint ColAryLen=" << m_CMO->m_MaxLoc << ";\n"
				<< "const uint LockAryLen=" << m_LMO->m_MaxLoc << ";\n"
				<< "const uint doMotion = " << motion_str << ";\n"
				<< "const uint MAX_CELL_ARRAY_LOCATIONS =" << m_CMO->m_MaxLoc << ";\n"
				<< "const float dt =" << m_App->m_dt << ";\n"
				//##JMBDont know what this is
				<< "const uint compflag =" << compflag << ";\n"
				<< "const uint bbound =" << m_VPO->BoundaryParticleLimit << ";\n";
			
			
		ostrm.flush();
		ostrm.close();
    }
}

int ShaderObj::CompileShader(std::string ShaderGLSLName, 
		std::string ShaderSPVFileName, std::vector<char> &SPVBuffer, uint32_t type)
{
#if 0
	std::vector<std::string> InputArgs;

	//std::cout << cfg->m_CompileShaders << std::endl;
	if (CfgApp->GetBool("application.compileShaders", true) == true)
	{
		InputArgs.push_back("ParticleOnly.exe");
		InputArgs.push_back("--target-env=vulkan1.3");
		InputArgs.push_back("-g");
		if (type == SH_FRAG)
		{
			InputArgs.push_back("-fshader-stage=fragment");
		}
		else if (type == SH_VERT)
		{
			InputArgs.push_back("-fshader-stage=vertex");
		}
		else if (type == SH_COMP)
		{
			InputArgs.push_back("-fshader-stage=compute");
		}

		std::string infl = ShaderGLSLName;
		InputArgs.push_back(infl);
		InputArgs.push_back("-o");
		InputArgs.push_back(ShaderSPVFileName);

		//int ret =  glsl(InputArgs, SPVBuffer);
		if (ret != 0 || SPVBuffer.empty())
		{
			std::ostringstream  objtxt;
			objtxt << "Error from glsl in:" << m_Name 
				<< " Returns:" << ret << " for:" << ShaderGLSLName << std::ends;
			throw std::runtime_error(objtxt.str());
		}
		else
		{
			mout << "glsl success :" << m_Name
				<< " Returns:" << ret << " for:" << ShaderGLSLName 
				<< " Size:" << SPVBuffer.size() << ende;
			
		}
		std::string fname = ShaderGLSLName + ".bin";
		//WriteBinaryFile(fname, SPVBuffer);
		return ret;
	}
#endif
	return 0;

}
int ShaderObj::WriteBinaryFile(std::string fileName, std::vector<char> buffer)
{
	std::ofstream fout(fileName, std::ios::out | std::ios::binary);
	if (!fout.is_open())
	{
		std::string rpt = "Failed to open file:" + fileName;
		throw std::runtime_error(rpt.c_str());
	}

	size_t size = buffer.size();
	for (uint32_t ii = 0; ii < size; ii++)
	{
		char ch = (char)buffer[ii];
		fout.write(&ch, 1);
	}

	fout.flush();
	fout.close();
	return 0;
	
}