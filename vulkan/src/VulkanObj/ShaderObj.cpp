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
	//	WriteCDNoz();
		WriteWalls();
		
		Piston();
		GenWorkGroups();
}
std::ostringstream ShaderObj::FunctionWalls()
{
	std::ostringstream wall_str;
	wall_str << std::fixed << std::setprecision(9);

	wall_str
		<< "struct FunctionWallSegment\n"
		<< "{\n"
		<< "    uint boundaryKind;\n"
		<< "    uint independentAxis;\n"
		<< "    float uStart;\n"
		<< "    float uEnd;\n"
		<< "    float fStart;\n"
		<< "    float a1;\n"
		<< "    float a2;\n"
		<< "    float a3;\n"
		<< "    float normalSign;\n"
		<< "    uint wallFlag;\n"
		<< "};\n\n";

	int segmentCount = 0;
	config_setting_t* segmentList =
		CfgTst->StartStructure("curve_wall_segments", segmentCount);

	if (segmentCount <= 0)
	{
		throw std::runtime_error(
			"curve_wall_segments must contain at least one segment"
		);
	}

	wall_str
		<< "const uint CURVE_WALL_SEGMENT_COUNT = "
		<< segmentCount << "u;\n"
		<< "const FunctionWallSegment CURVE_WALL_SEGMENTS["
		<< segmentCount << "] = FunctionWallSegment["
		<< segmentCount << "](\n";

	for (int index = 0; index < segmentCount; ++index)
	{
		config_setting_t* segment =
			CfgTst->GetSubStructAddress(segmentList, index);

		if (segment == nullptr || config_setting_length(segment) != 10)
		{
			throw std::runtime_error(
				"curve_wall_segments[" + std::to_string(index) +
				"] must contain ten values"
			);
		}

		uint32_t boundaryKind = static_cast<uint32_t>(
			config_setting_get_float_elem(segment, 0)
			);
		uint32_t independentAxis = static_cast<uint32_t>(
			config_setting_get_float_elem(segment, 1)
			);
		double uStart = config_setting_get_float_elem(segment, 2);
		double uEnd = config_setting_get_float_elem(segment, 3);
		double fStart = config_setting_get_float_elem(segment, 4);
		double a1 = config_setting_get_float_elem(segment, 5);
		double a2 = config_setting_get_float_elem(segment, 6);
		double a3 = config_setting_get_float_elem(segment, 7);
		double normalSign = config_setting_get_float_elem(segment, 8);
		uint32_t wallFlag = static_cast<uint32_t>(
			config_setting_get_float_elem(segment, 9)
			);

		wall_str
			<< "    FunctionWallSegment("
			<< boundaryKind << "u, "
			<< independentAxis << "u, "
			<< uStart << ", "
			<< uEnd << ", "
			<< fStart << ", "
			<< a1 << ", "
			<< a2 << ", "
			<< a3 << ", "
			<< normalSign << ", "
			<< wallFlag << "u)";

		if (index + 1 < segmentCount)
			wall_str << ",";

		wall_str << "\n";
	}

	wall_str << ");\n\n";

	return wall_str;
}
void ShaderObj::Piston()
{

	if (CfgTst->CheckKey("piston_enabled") == 0)
		return;
	if (CfgTst->GetInt("piston_enabled", true) == 0)
		return;
	std::ostringstream outStream;
	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/piston.glsl";
	{
		std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		
		ostrm
			<< "const float piston_x_start=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("piston_x_start", true) << ";\n"

			<< "const float piston_x_stop=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("piston_x_stop", true) << ";\n"

			<< "const float piston_velocity_x=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("piston_velocity_x", true) << ";\n"

			<< "const float piston_velocity_y=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("piston_velocity_y", true) << ";\n"

			<< "const float piston_velocity_z=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("piston_velocity_z", true) << ";\n"

			<< "const float piston_start_frame=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetInt("piston_start_frame", true) << ";\n";
	}
}
// This function is only for walls that are passed to glsl.
// It is up to the glsl version to use it or not. It has nothing to
// do with drawing the boundaries. That is in ResourceVertexCube.cpp
void ShaderObj::WriteWalls()
{
	std::string wlflg = "0u";
	wlflg = "1u;";
	
	std::ostringstream death_str;
	death_str
		<< "const float death_x_min = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_x_min", true) << ";\n"
		<< "const float death_x_max = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_x_max", true) << ";\n"
		<< "const float death_y_min = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_y_min", true) << ";\n"
		<< "const float death_y_max = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_y_max", true) << ";\n"
		<< "const float death_z_min = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_z_min", true) << ";\n"
		<< "const float death_z_max = " << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("death_z_max", true) << ";\n";


	
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

			"const uint BOUNDARY_ENABLED = " 
				<< wlflg << "\n" <<
			"const float wall_contact_offset = " << std::fixed << std::setprecision(9) 
				<< CfgTst->GetFloat("wall_contact_offset", true) << ";\n";
			
		
		ostrm << death_str.str();
		std::ostringstream curve_ostr = FunctionWalls();
		ostrm << curve_ostr.str();

		ostrm << "#endif\n";
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
	
	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
    std::string filename = fildir + "/params.glsl";
    {
		std::string dbgflag = {};

		std::string version = {};
		version = "VERPONLY ";
		

		float col_red = CfgApp->GetFloat("application.col_color.red", true);
		float col_green = CfgApp->GetFloat("application.col_color.green", true);
		float col_blue = CfgApp->GetFloat("application.col_color.blue", true);
		float col_alpha = CfgApp->GetFloat("application.col_color.alpha", true);

		float ncol_red = CfgApp->GetFloat("application.ncol_color.red", true);
		float ncol_green = CfgApp->GetFloat("application.ncol_color.green", true);
		float ncol_blue = CfgApp->GetFloat("application.ncol_color.blue", true);
		float ncol_alpha = CfgApp->GetFloat("application.ncol_color.alpha", true);

		std::ostringstream hsv_color_on;
		std::ostringstream hsv_sat;
		std::ostringstream hsv_val;
		
		
		if (CfgApp->CheckKey("application.hsv_color"))
		{
			if (CfgApp->GetBool("application.hsv_color", true) == 1)
			{
				hsv_color_on << "const uint HSV_ON = 1u;\n";
				hsv_sat << "const float HSV_SAT = " << std::fixed << std::setprecision(2) << CfgApp->GetFloat("application.hsv_sat", true) << ";\n";
				hsv_val << "const float HSV_VAL = " << std::fixed << std::setprecision(2) << CfgApp->GetFloat("application.hsv_val", true) << ";\n";
			}
			else
			{
				hsv_color_on << "const uint HSV_ON = 0u;\n";
				hsv_sat << "const float HSV_SAT = 0.000f" << ";\n";
				hsv_val << "const float HSV_VAL = 0.000f" << ";\n";
			}
			
		}

		std::ostringstream col_color;
		col_color << "vec3("
			<< std::fixed << std::setprecision(1) << col_red << "f,"
			<< std::fixed << std::setprecision(1) << col_green << "f,"
			<< std::fixed << std::setprecision(1) << col_blue << "f)";

		std::ostringstream ncol_color;
		ncol_color << "vec3("
			<< std::fixed << std::setprecision(1) << ncol_red << "f,"
			<< std::fixed << std::setprecision(1) << ncol_green << "f,"
			<< std::fixed << std::setprecision(1) << ncol_blue << "f)";
			
        std::ofstream ostrm(filename);
		if (!ostrm.is_open())
		{
			std::string rpt = "Failed to open file:" + filename;
			throw std::runtime_error(rpt.c_str());
		}
		ostrm << "#define " << version.c_str() << "\n"
			<< "const uint WIDTH=" << CfgTst->GetUInt("CellAryW", true) << ";\n"
			<< "const uint HEIGHT=" << CfgTst->GetUInt("CellAryH", true) << ";\n"
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
			<< "const uint NUM_PARICLES_COLLIDING =" << CfgTst->GetInt("num_particle_colliding", true) << ";\n"
			<< "const uint MAXSPCOLLS =" << m_VPO->m_MaxColls << ";\n"
			<< "const uint ColArySize=" << m_CMO->m_BufSize << ";\n"
			<< "const uint LockArySize=" << m_LMO->m_BufSize << ";\n"
			<< "const uint ColAryLen=" << m_CMO->m_MaxLoc << ";\n"
			<< "const uint LockAryLen=" << m_LMO->m_MaxLoc << ";\n"
			<< "const uint MAX_CELL_ARRAY_LOCATIONS =" << m_CMO->m_MaxLoc << ";\n"
			<< "const uint bbound =" << m_VPO->BoundaryParticleLimit << ";\n"
			<< "const float point_size = " << std::fixed << std::setprecision(2) << CfgApp->GetFloat("application.gl_point_size", true) << ";\n"
			<< "vec3 ncolcolor = " << ncol_color.str() << ";\n"
			<< "vec3 colcolor = " << col_color.str() << ";\n";
		
			ostrm << hsv_color_on.str() << hsv_sat.str() << hsv_val.str();
					
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
