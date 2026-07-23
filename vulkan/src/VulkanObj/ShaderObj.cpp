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
		WriteMaterials();
		WriteSphere();
		Piston();
		GenWorkGroups();
}

void ShaderObj::WriteMaterials()
{
	bool usesVelocityColor = false;
	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/material.glsl";

	std::ofstream ostrm(filename);
	if (!ostrm.is_open())
	{
		std::string rpt = "Failed to open file:" + filename;
		throw std::runtime_error(rpt.c_str());
	}

	ostrm << "#ifndef MATERIAL_GLSL\n";
	ostrm << "#define MATERIAL_GLSL\n\n";

	ostrm << "const uint COLOR_MODE_COLLISION = 0u;\n";
	ostrm << "const uint COLOR_MODE_VELOCITY = 1u;\n";
	ostrm << "const uint COLOR_MODE_SOLID = 2u;\n";
	ostrm << "const uint COLOR_MODE_LUMENS = 3u;\n\n";
	ostrm << "const uint PARTICLE_TYPE_REGULAR = 0u;\n";
	ostrm << "const uint PARTICLE_TYPE_PHOTON = 1u;\n\n";

	ostrm << "struct MaterialProperty\n";
	ostrm << "{\n";
	ostrm << "    uint materialID;\n";
	ostrm << "    uint particleType;\n";
	ostrm << "    float relativeMass;\n";
	ostrm << "    float tempVel;\n";
	ostrm << "    uint colorMode;\n";
	ostrm << "    vec4 color;\n";
	ostrm << "    uint debugVisible;\n";
	ostrm << "    vec4 debugColor;\n";
	ostrm << "    float cellDensity;\n";
	ostrm << "};\n\n";

	int materialCount = 0;
	config_setting_t* materialList = nullptr;

	if (CfgTst->CheckKey("material_properties"))
		materialList = CfgTst->StartStructure("material_properties", materialCount);

	if (materialList == nullptr || materialCount <= 0)
	{
		ostrm << "const uint MATERIAL_PROPERTY_COUNT = 1u;\n";
		ostrm << "const MaterialProperty MATERIAL_PROPERTIES[1] = MaterialProperty[1](\n";
		ostrm << "    MaterialProperty(0u, PARTICLE_TYPE_REGULAR, 1.000000000, 0.000000000, COLOR_MODE_VELOCITY, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), 0u, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), 0.000000000)\n";
		ostrm << ");\n\n";
		usesVelocityColor = true;
	}
	else
	{
		ostrm << "const uint MATERIAL_PROPERTY_COUNT = " << materialCount << "u;\n";
		ostrm << "const MaterialProperty MATERIAL_PROPERTIES[" << materialCount << "] = MaterialProperty["
			<< materialCount << "](\n";

		for (int index = 0; index < materialCount; ++index)
		{
			config_setting_t* material = CfgTst->GetSubStructAddress(materialList, index);
			if (material == nullptr)
			{
				throw std::runtime_error(
					"material_properties[" + std::to_string(index) + "] is invalid"
				);
			}

			int materialID = 0;
			int colorMode = 0;
			int particleType = 0;
			double relativeMass = 1.0;
			double tempVel = 0.0;
			double cellDensity = 0.0;
			double colorRed = 1.0;
			double colorGreen = 1.0;
			double colorBlue = 1.0;
			double colorAlpha = 1.0;
			int debugVisible = 0;
			double debugRed = 1.0;
			double debugGreen = 1.0;
			double debugBlue = 1.0;
			double debugAlpha = 1.0;

			if (config_setting_lookup_int(material, "material_id", &materialID) == CONFIG_FALSE)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].material_id missing");

			if (config_setting_lookup_int(material, "particle_type", &particleType) == CONFIG_FALSE)
				particleType = 0;

			if (config_setting_lookup_float(material, "relative_mass", &relativeMass) == CONFIG_FALSE)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].relative_mass missing");

			if (config_setting_lookup_float(material, "temp_vel", &tempVel) == CONFIG_FALSE
				&& config_setting_lookup_float(material, "thermal_velocity", &tempVel) == CONFIG_FALSE)
				throw std::runtime_error(
					"material_properties[" + std::to_string(index) +
					"].temp_vel/thermal_velocity missing"
				);

			if (config_setting_lookup_int(material, "color_mode", &colorMode) == CONFIG_FALSE)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].color_mode missing");

			config_setting_t* color = config_setting_lookup(material, "color");
			if (color != nullptr)
			{
				int colorLength = config_setting_length(color);
				if (colorLength != 3 && colorLength != 4)
					throw std::runtime_error("material_properties[" + std::to_string(index) + "].color must contain 3 or 4 values");

				colorRed = config_setting_get_float_elem(color, 0);
				colorGreen = config_setting_get_float_elem(color, 1);
				colorBlue = config_setting_get_float_elem(color, 2);
				if (colorLength == 4)
					colorAlpha = config_setting_get_float_elem(color, 3);
			}

			config_setting_t* debugVisibleSetting = config_setting_lookup(material, "debug_visible");
			if (debugVisibleSetting != nullptr)
			{
				if (config_setting_type(debugVisibleSetting) != CONFIG_TYPE_BOOL)
					throw std::runtime_error("material_properties[" + std::to_string(index) + "].debug_visible must be a boolean");
				debugVisible = config_setting_get_bool(debugVisibleSetting);
			}

			config_setting_t* debugColor = config_setting_lookup(material, "debug_color");
			if (debugColor != nullptr)
			{
				int colorLength = config_setting_length(debugColor);
				if (colorLength != 3 && colorLength != 4)
					throw std::runtime_error("material_properties[" + std::to_string(index) + "].debug_color must contain 3 or 4 values");
				for (int colorIndex = 0; colorIndex < colorLength; ++colorIndex)
				{
					config_setting_t* element = config_setting_get_elem(debugColor, colorIndex);
					if (element == nullptr || config_setting_type(element) != CONFIG_TYPE_FLOAT)
						throw std::runtime_error("material_properties[" + std::to_string(index) + "].debug_color values must be floats");
				}
				debugRed = config_setting_get_float_elem(debugColor, 0);
				debugGreen = config_setting_get_float_elem(debugColor, 1);
				debugBlue = config_setting_get_float_elem(debugColor, 2);
				if (colorLength == 4)
					debugAlpha = config_setting_get_float_elem(debugColor, 3);
			}

			if (static_cast<uint32_t>(colorMode) == 1u)
				usesVelocityColor = true;


			if (config_setting_lookup_float(material, "cell_density", &cellDensity) == CONFIG_FALSE)
				cellDensity = 0.0;

			ostrm << "    MaterialProperty("
				<< materialID << "u, "
				<< particleType << "u, "
				<< std::fixed << std::setprecision(9) << relativeMass << ", "
				<< std::fixed << std::setprecision(9) << tempVel << ", "
				<< colorMode << "u, "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << colorRed << ", "
				<< std::fixed << std::setprecision(9) << colorGreen << ", "
				<< std::fixed << std::setprecision(9) << colorBlue << ", "
				<< std::fixed << std::setprecision(9) << colorAlpha << "), "
				<< (debugVisible ? "1u" : "0u") << ", "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << debugRed << ", "
				<< std::fixed << std::setprecision(9) << debugGreen << ", "
				<< std::fixed << std::setprecision(9) << debugBlue << ", "
				<< std::fixed << std::setprecision(9) << debugAlpha << "), "
				<< std::fixed << std::setprecision(9) << cellDensity << ")";

			if (index + 1 < materialCount)
				ostrm << ",";

			ostrm << "\n";
		}

		ostrm << ");\n\n";
	}


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
	
	if (usesVelocityColor == true)
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
	ostrm << hsv_color_on.str() << hsv_sat.str() << hsv_val.str();
	

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
	
	ostrm << "vec3 ncolcolor = "
		<< ncol_color.str() << ";\n"
		<< "vec3 colcolor = "
		<< col_color.str() << ";\n";
	
	ostrm << "#endif\n";
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
	config_setting_t* segmentList = nullptr;

	if (CfgTst->CheckKey("curve_wall_segments"))
		segmentList = CfgTst->StartStructure("curve_wall_segments", segmentCount);

	if (segmentList == nullptr || segmentCount <= 0)
	{
		wall_str
			<< "const uint CURVE_WALL_SEGMENT_COUNT = 0u;\n"
			<< "const FunctionWallSegment CURVE_WALL_SEGMENTS[1] = "
			<< "FunctionWallSegment[1](\n"
			<< "    FunctionWallSegment("
			<< "0u, 0u, "
			<< "0.000000000, 0.000000000, 0.000000000, "
			<< "0.000000000, 0.000000000, 0.000000000, "
			<< "1.000000000, 0u)\n"
			<< ");\n\n";
		return wall_str;
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
void ShaderObj::WriteSphere()
{
	if (!CfgTst->CheckKey("Lighting_ball"))
		return;


	std::string fildir = CfgApp->GetString("application.gen_glsl_dir", true);
	std::string filename = fildir + "/sphere.glsl";

	std::ofstream ostrm(filename);
	if (!ostrm.is_open())
	{
		std::string rpt = "Failed to open file:" + filename;
		throw std::runtime_error(rpt.c_str());
	}

	ostrm << "#ifndef SPHERE_GLSL\n#define SPHERE_GLSL\n";
	ostrm << std::fixed << std::setprecision(9);

	if (!CfgTst->CheckKey("Lighting_ball"))
	{
		ostrm
			<< "const uint LIGHTING_BALL_ENABLED = 0u;\n"
			<< "const vec3 LIGHTING_BALL_CENTER = vec3(0.000000000, 0.000000000, 0.000000000);\n"
			<< "const float LIGHTING_BALL_RADIUS = 0.000000000;\n"
			<< "const uint LIGHTING_BALL_MATERIAL_ID = 0u;\n"
			<< "const uint LIGHTING_BALL_WALL_FLAG = 1000u;\n"
			<< "#endif\n";
		return;
	}

	double centerX = CfgTst->GetFloat("Lighting_ball.x", true);
	double centerY = CfgTst->GetFloat("Lighting_ball.y", true);
	double centerZ = CfgTst->GetFloat("Lighting_ball.z", true);
	double radius = CfgTst->GetFloat("Lighting_ball.radius", true);

	if (radius <= 0.0)
		throw std::runtime_error("Lighting_ball.radius must be greater than zero");

	uint32_t materialID = 0u;
	if (CfgTst->CheckKey("Lighting_ball.material_id"))
		materialID = static_cast<uint32_t>(
			CfgTst->GetInt("Lighting_ball.material_id", false)
			);

	uint32_t wallFlag = 1000u;
	if (CfgTst->CheckKey("Lighting_ball.wall_flag"))
		wallFlag = static_cast<uint32_t>(
			CfgTst->GetInt("Lighting_ball.wall_flag", false)
			);

	ostrm
		<< "const uint LIGHTING_BALL_ENABLED = 1u;\n"
		<< "const vec3 LIGHTING_BALL_CENTER = vec3("
		<< centerX << ", " << centerY << ", " << centerZ << ");\n"
		<< "const float LIGHTING_BALL_RADIUS = " << radius << ";\n"
		<< "const uint LIGHTING_BALL_MATERIAL_ID = " << materialID << "u;\n"
		<< "const uint LIGHTING_BALL_WALL_FLAG = " << wallFlag << "u;\n"
		<< "#endif\n";
}
// This function is only for walls that are passed to glsl.
// It is up to the glsl version to use it or not. It has nothing to
// do with drawing the boundaries. That is in ResourceVertexCube.cpp
void ShaderObj::WriteWalls()
{

	bool show_cell_boundary_cube = CfgApp->GetBool("application.show_cell_boundary_cube", true);
	bool show_wall_as_boundary_cube = CfgApp->GetBool("application.show_wall_as_boundary_cube", true);
	bool particle_as_spheres = CfgApp->GetBool("application.particle_as_spheres", true);
	bool show_boundary_as_obj = CfgApp->GetBool("application.boundary_as_obj", true);

	std::string wlflg = "0u";
	wlflg = "1u;";
	
	std::ostringstream boundary;
	if (show_cell_boundary_cube == true || show_wall_as_boundary_cube == true || show_boundary_as_obj == true)
	{
		boundary << "#define HAS_BOUNDARY" << "\n";

	}
	if (particle_as_spheres == true)
		boundary << "#define HAS_SPHERE" << "\n";

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
		std::ostringstream rectangle_ostr = RectangleWalls();
		ostrm << rectangle_ostr.str();
		ostrm << boundary.str();
		ostrm << "#endif\n";
	}

	
}
std::ostringstream ShaderObj::RectangleWalls()
{
	std::ostringstream wall_str;
	wall_str << std::fixed << std::setprecision(9);

	wall_str
		<< "struct RectangleWallSegment\n"
		<< "{\n"
		<< "    vec3 origin;\n"
		<< "    vec3 uAxis;\n"
		<< "    vec3 vAxis;\n"
		<< "    float uLength;\n"
		<< "    float vLength;\n"
		<< "    vec3 inwardNormal;\n"
		<< "    uint wallFlag;\n"
		<< "};\n\n";

	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;

	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	if (segmentList == nullptr || segmentCount <= 0)
	{
		wall_str
			<< "const uint RECTANGLE_WALL_SEGMENT_COUNT = 0u;\n"
			<< "const RectangleWallSegment RECTANGLE_WALL_SEGMENTS[1] = "
			<< "RectangleWallSegment[1](\n"
			<< "    RectangleWallSegment("
			<< "vec3(0.000000000), "
			<< "vec3(1.000000000, 0.000000000, 0.000000000), "
			<< "vec3(0.000000000, 1.000000000, 0.000000000), "
			<< "0.000000000, 0.000000000, "
			<< "vec3(0.000000000, 0.000000000, 1.000000000), "
			<< "0u)\n"
			<< ");\n\n";
		return wall_str;
	}

	wall_str
		<< "const uint RECTANGLE_WALL_SEGMENT_COUNT = "
		<< segmentCount << "u;\n"
		<< "const RectangleWallSegment RECTANGLE_WALL_SEGMENTS["
		<< segmentCount << "] = RectangleWallSegment["
		<< segmentCount << "](\n";

	for (int index = 0; index < segmentCount; ++index)
	{
		config_setting_t* segment = CfgTst->GetSubStructAddress(segmentList, index);

		if (segment == nullptr || config_setting_length(segment) != 15)
		{
			throw std::runtime_error(
				"rectangle_wall_segments[" + std::to_string(index) +
				"] must contain fifteen values"
			);
		}

		double originX = config_setting_get_float_elem(segment, 0);
		double originY = config_setting_get_float_elem(segment, 1);
		double originZ = config_setting_get_float_elem(segment, 2);

		double uAxisX = config_setting_get_float_elem(segment, 3);
		double uAxisY = config_setting_get_float_elem(segment, 4);
		double uAxisZ = config_setting_get_float_elem(segment, 5);

		double vAxisX = config_setting_get_float_elem(segment, 6);
		double vAxisY = config_setting_get_float_elem(segment, 7);
		double vAxisZ = config_setting_get_float_elem(segment, 8);

		double uLength = config_setting_get_float_elem(segment, 9);
		double vLength = config_setting_get_float_elem(segment, 10);

		double normalX = config_setting_get_float_elem(segment, 11);
		double normalY = config_setting_get_float_elem(segment, 12);
		double normalZ = config_setting_get_float_elem(segment, 13);

		uint32_t wallFlag = static_cast<uint32_t>(
			config_setting_get_float_elem(segment, 14)
			);

		wall_str
			<< "    RectangleWallSegment("
			<< "vec3(" << originX << ", " << originY << ", " << originZ << "), "
			<< "vec3(" << uAxisX << ", " << uAxisY << ", " << uAxisZ << "), "
			<< "vec3(" << vAxisX << ", " << vAxisY << ", " << vAxisZ << "), "
			<< uLength << ", "
			<< vLength << ", "
			<< "normalize(vec3(" << normalX << ", " << normalY << ", " << normalZ << ")), "
			<< wallFlag << "u)";

		if (index + 1 < segmentCount)
			wall_str << ",";

		wall_str << "\n";
	}

	wall_str << ");\n\n";
	return wall_str;
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
		ostrm 
			<< "layout(local_size_x = " 
				<< CfgTst->GetInt("workGroupsx", true) 
			<< ", local_size_y = " 
				<< CfgTst->GetInt("workGroupsy", true) <<
			", local_size_z = " 
				<< CfgTst->GetInt("workGroupsz", true) << ") in;\n";
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
			<< "const uint CENTER="
				<< 0.0 << ";\n"
			<< "const float RADIUS="
				<< 0.0 << ";\n"
			<< "const uint MAX_CELL_OCCUPANY="
				<< CfgTst->GetInt("cell_occupancy_list_size", true) << ";\n"
			<< "const uint SCR_W ="
				<< m_SCO->m_SwapWidth << ";\n"
			<< "const uint SCR_H ="
				<< m_SCO->m_SwapHeight << ";\n"
			<< "const uint SCR_X ="
				<< m_SCO->m_SwapX << ";\n"
			<< "const uint SCR_Y ="
				<< m_SCO->m_SwapY << ";\n"
			<< "const uint NUMPARTS ="
				<< m_VPO->m_NumParticles << ";\n"
			<< "const uint NUM_PARICLES_COLLIDING ="
				<< CfgTst->GetInt("num_particle_colliding", true) << ";\n"
			<< "const uint MAXSPCOLLS ="
				<< m_VPO->m_MaxColls << ";\n"
			<< "const uint ColArySize="
				<< m_CMO->m_BufSize << ";\n"
			<< "const uint LockArySize="
				<< m_LMO->m_BufSize << ";\n"
			<< "const uint ColAryLen="
				<< m_CMO->m_MaxLoc << ";\n"
			<< "const uint LockAryLen="
				<< m_LMO->m_MaxLoc << ";\n"
			<< "const uint MAX_CELL_ARRAY_LOCATIONS ="
				<< m_CMO->m_MaxLoc << ";\n"
			<< "const uint bbound ="
				<< m_VPO->BoundaryParticleLimit << ";\n"
			<< "const float point_size = "
				<< std::fixed << std::setprecision(2) << CfgTst->GetFloat("gl_point_size", true) << ";\n"
			<< "#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN "
				<< std::setprecision(9) << CfgTst->GetFloat("compression_stiffness_gain", true) << "\n"
			<< "#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER " <<
				std::setprecision(9) << CfgTst->GetFloat("compression_stiffness_power", true) << "\n"
			<< "const uint DUP_LIST_SIZE = "
				<< CfgTst->GetInt("duplicates_list_size", true) << ";\n";
		
			
					
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
