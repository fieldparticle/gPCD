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

		WriteShaderHeader();
		WriteShaderDbgHeader();
		WriteWalls();
		Reservoir();
		GenWorkGroups();
}
void ShaderObj::Reservoir()
{

	std::string pipe_reservoir_entry = CfgTst->GetString("flow_type", true);
	if (pipe_reservoir_entry.compare("pipe_reservoir_entry")==0)
	{
		std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
		std::string filename = fildir + "/flow.glsl";
		{
			std::ofstream ostrm(filename);
			if (!ostrm.is_open())
			{
				std::string rpt = "Failed to open file:" + filename;
				throw std::runtime_error(rpt.c_str());
			}
			ostrm << "const float PARTICLE_RATE =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("particle_rate", true) << ";\n";
			ostrm << "const float INLET_VELOCITY =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("inlet_velocity", true) << ";\n";
			ostrm << "const float INLET_X =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("inlet_x", true) << ";\n";
			ostrm << "const float OUTLET_X =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("outlet_x", true) << ";\n";
			ostrm << "const float PIPE_Y_MIN =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("pipe_y_min", true) << ";\n";
			ostrm << "const float PIPE_Y_MAX =" << std::fixed << std::setprecision(2) << CfgTst->GetFloat("pipe_y_max", true) << ";\n";
			ostrm << "const uint  ESCAPE_MODE=" << CfgTst->GetUInt("escape_mode", true) << "u;\n";

		}
	}


}



void ShaderObj::WriteWalls()
{
	std::vector<double> walls = { 0.0, 0.0, 0.0, 0.0 };
	bool walls_on = CfgApp->GetBool("application.walls_on", true);
	bool has_walls = false;

	config_setting_t* setting;
	setting = config_lookup(&CfgApp->m_cfg, "application.walls");

	if (setting != NULL && config_setting_is_array(setting))
	{
		int count = config_setting_length(setting);

		for (int i = 0; i < count && i < static_cast<int>(walls.size()); i++)
		{
			walls[i] =
				config_setting_get_float_elem(setting, i);
		}
		has_walls = count >= static_cast<int>(walls.size());
	}
	if (!has_walls && walls_on)
	{
		walls[0] = CfgTst->GetFloat("wallXMIN", true);
		walls[1] = CfgTst->GetFloat("wallXMAX", true);
		walls[2] = CfgTst->GetFloat("wallYMIN", true);
		walls[3] = CfgTst->GetFloat("wallYMAX", true);
	}
	
	std::string wlflg = "0u";

	if (walls_on == true)
		wlflg = "1u;";
	else
		wlflg = "0u;";

	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/boundary.glsl";
	{
		std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		ostrm << "#ifndef BOUNDARY_GLSL\n#define BOUNDARY_GLSL\n" <<
			
			"const uint BOUNDARY_ENABLED = " << wlflg << "\n" << 
			"const float BOUNDARY_XMIN = " << std::fixed << std::setprecision(2) << walls[0] << ";\n"
			"const float BOUNDARY_XMAX  = " << std::fixed << std::setprecision(2) << walls[1] << ";\n"
			"const float BOUNDARY_YMIN  = " << std::fixed << std::setprecision(2) << walls[2] << ";\n"
			"const float BOUNDARY_YMAX  = " << std::fixed << std::setprecision(2) << walls[3] << ";\n"
			"#endif\n";
	}
}
void ShaderObj::GenWorkGroups()
{

	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/workgroups.glsl";
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

void ShaderObj::WriteShaderDbgHeader()
{
	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/debug.glsl";
	{
		std::string dbgflag = {};
		#ifdef NDEBUG
				dbgflag = "#define RELEASE";
		#else
				dbgflag = "#define DEBUG";
		#endif
		std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		ostrm << dbgflag.c_str() << "\n";
		ostrm.flush();
		ostrm.close();
	}
}
void  ShaderObj::WriteShaderHeader()
{
	// Dont compile shaders if using nsight.
//if(CfgApp->GetBool("application.nsight", true) == true)
//		return;
	uint32_t compflag=0;
	uint32_t motion_str = 0;
	float dt = 0.0;
	if (CfgApp->GetBool("application.doMotion", true) == true)
	{
		dt = CfgApp->GetBool("application.dt", true);
		dt = CfgApp->GetBool("application.inverse_square_softening", true);
		motion_str = 1;
	}

	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
    std::string filename = fildir + "/params.glsl";
    {
		std::string dbgflag = {};

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
		ostrm	<< "#define " << version.c_str()  << "\n"
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
				//##JMBDont know what this is
				<< "const uint compflag =" << compflag << ";\n"
				<< "const uint bbound =" << m_VPO->BoundaryParticleLimit << ";\n";
			
			
		ostrm.flush();
		ostrm.close();
    }
	
}

int ShaderObj::CompileShader(std::string ShaderGLSLName,
	std::string ShaderSPVFileName, std::vector<char>& SPVBuffer, uint32_t type)
{

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
		int ret = glsl(InputArgs, SPVBuffer);
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
	else
	{
		SPVBuffer = ReadSPVFile(ShaderSPVFileName);
		return 0;
	}
	return 0;
}

#if 0
int ShaderObj::CompileShader(std::string ShaderGLSLName,
	std::string ShaderSPVFileName, std::vector<char>& SPVBuffer, uint32_t type)
{



	std::string dir = CfgApp->GetString("application.gen_glsl_dir", true);

	std::string filename = dir + "/" + ShaderSPVFileName;
	std::ifstream file(filename, std::ios::ate | std::ios::binary);

	if (!file.is_open())
	{
		throw std::runtime_error("failed to open file!");
	}


	size_t fileSize = (size_t)file.tellg();
	std::vector<char> buffer(fileSize);
	file.seekg(0);
	file.read(buffer.data(), fileSize);
	SPVBuffer = buffer;



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
}
#endif
	
std::vector<char> ShaderObj::ReadSPVFile(const std::string& filename) 
{
	std::ifstream file(filename, std::ios::ate | std::ios::binary);

	if (!file.is_open()) 
	{
		throw std::runtime_error("failed to open file!");
	}
	size_t fileSize = (size_t)file.tellg();
	std::vector<char> buffer(fileSize);
	file.seekg(0);
	file.read(buffer.data(), fileSize);
	file.close();

	return buffer;
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
