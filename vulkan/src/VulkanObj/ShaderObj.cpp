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
		Reservoir();
		GenWorkGroups();
}

void ShaderObj::Reservoir()
{
	std::string fileDir =
		CfgApp->GetString("application.gen_glsl_dir", true);
	std::string fileName = fileDir + "/reservoir.glsl";

	std::ofstream ostrm(fileName);
	if (!ostrm.is_open())
	{
		throw std::runtime_error(
			"Failed to open file: " + fileName
		);
	}

	ostrm << std::fixed << std::setprecision(9);

	// ------------------------------------------------------------
	// Piston and chamber
	// ------------------------------------------------------------
	ostrm
		<< "#ifndef RESERVOIR_GLSL\n"
		<< "#define RESERVOIR_GLSL\n\n"

		<< "const uint BOUNDARY_EVALUATOR_LINEAR = 4u;\n"

		<< "const uint PISTON_START_FRAME = "
		<< CfgTst->GetUInt("piston_start_frame", true)
		<< "u;\n"

		<< "const vec3 CHAMBER_MIN = vec3("
		<< CfgTst->GetFloat("chamber_x_start", true) << ", "
		<< CfgTst->GetFloat("chamber_y_bottom", true) << ", "
		<< CfgTst->GetFloat("chamber_z_front", true)
		<< ");\n"

		<< "const vec3 CHAMBER_MAX = vec3("
		<< CfgTst->GetFloat("chamber_x_end", true) << ", "
		<< CfgTst->GetFloat("chamber_y_top", true) << ", "
		<< CfgTst->GetFloat("chamber_z_back", true)
		<< ");\n"

		<< "const vec3 PISTON_VELOCITY = vec3("
		<< CfgTst->GetFloat("piston_velocity_x", true) << ", "
		<< CfgTst->GetFloat("piston_velocity_y", true) << ", "
		<< CfgTst->GetFloat("piston_velocity_z", true)
		<< ");\n\n"

		<< "struct LinearWallSegment\n"
		<< "{\n"
		<< "    vec3 abc;\n"
		<< "    vec4 endpoints;\n"
		<< "    uint wallFlag;\n"
		<< "};\n\n";

	auto writeSegmentArray =
		[&](const std::string& cfgName,
			const std::string& glslName,
			const std::string& countName)
		{
			int segmentCount = 0;
			config_setting_t* segmentList =
				CfgTst->StartStructure(cfgName, segmentCount);

			if (segmentCount <= 0)
			{
				throw std::runtime_error(
					cfgName + " must contain at least one segment"
				);
			}

			ostrm
				<< "const uint " << countName << " = "
				<< segmentCount << "u;\n"
				<< "const LinearWallSegment " << glslName
				<< "[" << segmentCount << "] = "
				<< "LinearWallSegment[" << segmentCount << "](\n";

			for (int index = 0; index < segmentCount; ++index)
			{
				config_setting_t* segment =
					CfgTst->GetSubStructAddress(segmentList, index);

				if (segment == nullptr ||
					config_setting_length(segment) != 8)
				{
					throw std::runtime_error(
						cfgName + "[" + std::to_string(index) +
						"] must contain eight values"
					);
				}

				double a = config_setting_get_float_elem(segment, 0);
				double b = config_setting_get_float_elem(segment, 1);
				double c = config_setting_get_float_elem(segment, 2);
				double xStart = config_setting_get_float_elem(segment, 3);
				double yStart = config_setting_get_float_elem(segment, 4);
				double xEnd = config_setting_get_float_elem(segment, 5);
				double yEnd = config_setting_get_float_elem(segment, 6);
				uint32_t wallFlag = static_cast<uint32_t>(
					config_setting_get_float_elem(segment, 7)
					);

				ostrm
					<< "    LinearWallSegment("
					<< "vec3(" << a << ", " << b << ", " << c << "), "
					<< "vec4(" << xStart << ", " << yStart << ", "
					<< xEnd << ", " << yEnd << "), "
					<< wallFlag << "u)";

				if (index + 1 < segmentCount)
					ostrm << ",";

				ostrm << "\n";
			}

			ostrm << ");\n\n";
		};

	writeSegmentArray(
		"linear_chamber_segments",
		"LINEAR_CHAMBER_SEGMENTS",
		"LINEAR_CHAMBER_SEGMENT_COUNT"
	);

	writeSegmentArray(
		"linear_wall_segments",
		"LINEAR_WALL_SEGMENTS",
		"LINEAR_WALL_SEGMENT_COUNT"
	);

	ostrm << "#endif\n";
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

#if 1	
	std::ostringstream wall_str;
	wall_str 
			
		<< "const float BOUNDARY_XMIN = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_x_min", true) << ";\n"

		<< "const float BOUNDARY_XMAX = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_x_max", true) << ";\n"

		<< "const float BOUNDARY_YMIN = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_y_min", true) << ";\n"

		<< "const float BOUNDARY_YMAX = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_y_max", true) << ";\n"

		<< "const float BOUNDARY_ZMIN = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_z_min", true) << ";\n"

		<< "const float BOUNDARY_ZMAX = " << std::fixed << std::setprecision(9)
		<< CfgTst->GetFloat("boundary_z_max", true) << ";\n";
#endif
	
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
			"const float wall_contact_offset = " << std::fixed << std::setprecision(9) << 
				CfgTst->GetFloat("wall_contact_offset", true) << ";\n"
			"#define CONTACT_FORCE_MEASURE  " << CfgTst->GetString("contact_force_measure", true) << "\n"
			"#define " << CfgTst->GetString("wall_type", true) << "\n";
			
		ostrm << wall_str.str();
		ostrm << death_str.str();
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
