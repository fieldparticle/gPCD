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
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cmath>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace
{
	uint32_t LightingSurfaceTypeID(const std::string& surfaceType)
	{
		if (surfaceType == "SPHERE")
			return 1u;
		if (surfaceType == "RECTANGLE_WALL")
			return 2u;
		if (surfaceType == "NONE")
			return 0u;

		std::ostringstream errtxt;
		errtxt << "Unknown lighting surface_type: " << surfaceType << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	uint32_t PhotonSurfaceBehaviorID(const std::string& behavior)
	{
		std::string normalized = behavior;
		normalized.erase(
			normalized.begin(),
			std::find_if(
				normalized.begin(),
				normalized.end(),
				[](unsigned char value) { return !std::isspace(value); }));
		normalized.erase(
			std::find_if(
				normalized.rbegin(),
				normalized.rend(),
				[](unsigned char value) { return !std::isspace(value); }).base(),
			normalized.end());
		std::transform(
			normalized.begin(),
			normalized.end(),
			normalized.begin(),
			[](unsigned char value) { return static_cast<char>(std::toupper(value)); });

		if (normalized == "NONE" || normalized == "PHOTON_SURFACE_BEHAVIOR_NONE")
			return 0u;
		if (normalized == "SURFACE_COLOR" || normalized == "PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR")
			return 1u;
		if (normalized == "ABSORB" || normalized == "PHOTON_SURFACE_BEHAVIOR_ABSORB")
			return 2u;
		if (normalized == "REFLECT" || normalized == "PHOTON_SURFACE_BEHAVIOR_REFLECT")
			return 3u;

		std::ostringstream errtxt;
		errtxt << "Unknown photon_surface_behavior: " << behavior << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	uint32_t MaterialPhotonSurfaceBehavior(config_setting_t* material, int index)
	{
		config_setting_t* behaviorSetting =
			config_setting_lookup(material, "photon_surface_behavior");
		if (behaviorSetting == nullptr)
			return 0u;

		int settingType = config_setting_type(behaviorSetting);
		if (settingType == CONFIG_TYPE_STRING)
			return PhotonSurfaceBehaviorID(config_setting_get_string(behaviorSetting));
		if (settingType == CONFIG_TYPE_INT)
		{
			int behavior = config_setting_get_int(behaviorSetting);
			if (behavior < 0 || behavior > 3)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_surface_behavior is outside the valid range");
			return static_cast<uint32_t>(behavior);
		}

		throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_surface_behavior must be a string or integer");
	}

	uint32_t ContactIlluminationID(const std::string& mode)
	{
		std::string normalized = mode;
		normalized.erase(
			normalized.begin(),
			std::find_if(
				normalized.begin(),
				normalized.end(),
				[](unsigned char value) { return !std::isspace(value); }));
		normalized.erase(
			std::find_if(
				normalized.rbegin(),
				normalized.rend(),
				[](unsigned char value) { return !std::isspace(value); }).base(),
			normalized.end());
		std::transform(
			normalized.begin(),
			normalized.end(),
			normalized.begin(),
			[](unsigned char value) { return static_cast<char>(std::toupper(value)); });

		if (normalized == "MAX" || normalized == "CONTACT_ILLUMINATION_MAX")
			return 0u;
		if (normalized == "MIN" || normalized == "CONTACT_ILLUMINATION_MIN")
			return 1u;
		if (normalized == "CURRENT" || normalized == "CONTACT_ILLUMINATION_CURRENT")
			return 2u;
		if (normalized == "FIRST" || normalized == "CONTACT_ILLUMINATION_FIRST")
			return 3u;

		std::ostringstream errtxt;
		errtxt << "Unknown contact_illumination: " << mode << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	uint32_t MaterialContactIllumination(config_setting_t* material, int index)
	{
		config_setting_t* modeSetting =
			config_setting_lookup(material, "contact_illumination");
		if (modeSetting == nullptr)
			return 0u;

		int settingType = config_setting_type(modeSetting);
		if (settingType == CONFIG_TYPE_STRING)
			return ContactIlluminationID(config_setting_get_string(modeSetting));
		if (settingType == CONFIG_TYPE_INT)
		{
			int mode = config_setting_get_int(modeSetting);
			if (mode < 0 || mode > 3)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].contact_illumination is outside the valid range");
			return static_cast<uint32_t>(mode);
		}

		throw std::runtime_error("material_properties[" + std::to_string(index) + "].contact_illumination must be a string or integer");
	}

	uint32_t CountObjFaceVertices(const std::string& objFile)
	{
		std::ifstream input(objFile);
		if (!input.is_open())
		{
			std::ostringstream errtxt;
			errtxt << "Unable to open lighting surface OBJ: " << objFile << std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}

		uint32_t vertexCount = 0u;
		std::string line;
		while (std::getline(input, line))
		{
			if (line.size() < 2u || line[0] != 'f' || line[1] != ' ')
				continue;

			std::istringstream face(line.substr(2u));
			std::string token;
			while (face >> token)
				vertexCount++;
		}

		return vertexCount;
	}

	struct LightingSurfaceObjectInfo
	{
		uint32_t surfaceType = 0u;
		uint32_t surfaceID = 0u;
		uint32_t materialID = 0u;
		uint32_t vertexOffset = 0u;
		uint32_t vertexCount = 0u;
		double initialSurfaceColor[4] = { 0.0, 0.0, 0.0, 1.0 };
		uint32_t rectangleUSegments = 0u;
		uint32_t rectangleVSegments = 0u;
		uint32_t sphereLatSegments = 0u;
		uint32_t sphereLonSegments = 0u;
	};

	uint32_t ReadPositiveUInt(config_setting_t* object, int objectIndex, const char* fieldName)
	{
		int value = 0;
		if (config_setting_lookup_int(object, fieldName, &value) != CONFIG_TRUE)
			throw std::runtime_error("lighting_surface_objects[" + std::to_string(objectIndex) + "]." + fieldName + " is required");
		if (value <= 0)
			throw std::runtime_error("lighting_surface_objects[" + std::to_string(objectIndex) + "]." + fieldName + " must be positive");
		return static_cast<uint32_t>(value);
	}

	void ReadInitialSurfaceColor(
		config_setting_t* object,
		int objectIndex,
		double (&color)[4])
	{
		config_setting_t* initialColor =
			config_setting_lookup(object, "initial_surface_color");
		if (initialColor == nullptr)
			return;

		if (config_setting_length(initialColor) != 4)
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"].initial_surface_color must contain four values"
			);
		}

		for (int channel = 0; channel < 4; ++channel)
		{
			double value = config_setting_get_float_elem(initialColor, channel);
			if (!std::isfinite(value) || value < 0.0 || value > 1.0)
			{
				throw std::runtime_error(
					"lighting_surface_objects[" + std::to_string(objectIndex) +
					"].initial_surface_color values must be finite and in [0, 1]"
				);
			}
			color[channel] = value;
		}
	}

	std::vector<LightingSurfaceObjectInfo> LightingSurfaceObjectOffsets(ConfigObj* cfg)
	{
		std::vector<LightingSurfaceObjectInfo> objects;

		int objectCount = 0;
		config_setting_t* objectList = nullptr;
		if (cfg->CheckKey("lighting_surface_objects"))
			objectList = cfg->StartStructure("lighting_surface_objects", objectCount);
		if (objectList == nullptr || objectCount == 0)
			return objects;

		uint32_t vertexOffset = 0u;
		for (uint32_t pass = 0u; pass < 2u; ++pass)
		{
			for (int index = 0; index < objectCount; ++index)
			{
				config_setting_t* object = cfg->GetSubStructAddress(objectList, index);
				if (object == nullptr)
					throw std::runtime_error("lighting_surface_objects contains an invalid object");

				const char* source = nullptr;
				const char* objFile = nullptr;
				const char* surfaceTypeText = nullptr;
				int surfaceID = 0;
				int materialID = 0;

				if (config_setting_lookup_string(object, "source", &source) != CONFIG_TRUE ||
					std::string(source) != "obj" ||
					config_setting_lookup_string(object, "obj_file", &objFile) != CONFIG_TRUE ||
					config_setting_lookup_string(object, "surface_type", &surfaceTypeText) != CONFIG_TRUE ||
					config_setting_lookup_int(object, "surface_id", &surfaceID) != CONFIG_TRUE ||
					config_setting_lookup_int(object, "material_id", &materialID) != CONFIG_TRUE)
				{
					std::ostringstream errtxt;
					errtxt << "lighting_surface_objects[" << index << "] must contain OBJ metadata" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}

				uint32_t surfaceType = LightingSurfaceTypeID(surfaceTypeText);
				bool wallPass = surfaceType == 2u;
				if ((pass == 0u && !wallPass) || (pass == 1u && wallPass))
					continue;

				LightingSurfaceObjectInfo info{};
				info.surfaceType = surfaceType;
				info.surfaceID = static_cast<uint32_t>(surfaceID);
				info.materialID = static_cast<uint32_t>(materialID);
				info.vertexOffset = vertexOffset;
				info.vertexCount = CountObjFaceVertices(objFile);
				ReadInitialSurfaceColor(object, index, info.initialSurfaceColor);
				if (surfaceType == 2u)
				{
					info.rectangleUSegments = ReadPositiveUInt(object, index, "rectangle_u_segments");
					info.rectangleVSegments = ReadPositiveUInt(object, index, "rectangle_v_segments");
				}
				else if (surfaceType == 1u)
				{
					info.sphereLatSegments = ReadPositiveUInt(object, index, "sphere_lat_segments");
					info.sphereLonSegments = ReadPositiveUInt(object, index, "sphere_lon_segments");
				}
				objects.push_back(info);
				vertexOffset += info.vertexCount;
			}
		}

		return objects;
	}

	const LightingSurfaceObjectInfo* FindLightingSurfaceObject(
		const std::vector<LightingSurfaceObjectInfo>& objects,
		uint32_t surfaceType,
		uint32_t surfaceID)
	{
		for (const LightingSurfaceObjectInfo& object : objects)
		{
			if (object.surfaceType == surfaceType && object.surfaceID == surfaceID)
				return &object;
		}
		return nullptr;
	}

}
void ShaderObj::Create(Resource* VPO, ResourceCollMatrix* CMO, ResourceLockMatrix* LMO, SwapChain* SCO)
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
	ostrm << "const uint COLOR_MODE_VELOCITY_ANGLE = 1u;\n";
	ostrm << "const uint COLOR_MODE_SOLID = 2u;\n";
	ostrm << "const uint COLOR_MODE_LUMENS = 3u;\n\n";
	ostrm << "const uint PARTICLE_TYPE_REGULAR = 0u;\n";
	ostrm << "const uint PARTICLE_TYPE_PHOTON = 1u;\n\n";
	ostrm << "const uint PARTICLE_TYPE_BOUNDARY = 2u;\n\n";
	ostrm << "const uint PHOTON_SURFACE_BEHAVIOR_NONE = 0u;\n";
	ostrm << "const uint PHOTON_SURFACE_BEHAVIOR_SURFACE_COLOR = 1u;\n";
	ostrm << "const uint PHOTON_SURFACE_BEHAVIOR_ABSORB = 2u;\n";
	ostrm << "const uint PHOTON_SURFACE_BEHAVIOR_REFLECT = 3u;\n\n";
	ostrm << "const uint CONTACT_ILLUMINATION_MAX = 0u;\n";
	ostrm << "const uint CONTACT_ILLUMINATION_MIN = 1u;\n";
	ostrm << "const uint CONTACT_ILLUMINATION_CURRENT = 2u;\n";
	ostrm << "const uint CONTACT_ILLUMINATION_FIRST = 3u;\n\n";

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
	ostrm << "    vec4 spectralResponseEnergy;\n";
	ostrm << "    vec4 spectralEmission;\n";
	ostrm << "    float photonCoupling;\n";
	ostrm << "    float photonMinRelativeMass;\n";
	ostrm << "    uint photonSurfaceBehavior;\n";
	ostrm << "    uint contactIllumination;\n";
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
		ostrm << "    MaterialProperty(0u, PARTICLE_TYPE_REGULAR, 1.000000000, 0.000000000, COLOR_MODE_VELOCITY_ANGLE, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), 0u, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), vec4(1.000000000, 1.000000000, 1.000000000, 0.000000000), 1.000000000, 0.001000000, PHOTON_SURFACE_BEHAVIOR_NONE, CONTACT_ILLUMINATION_MAX, 0.000000000)\n";
		ostrm << ");\n\n";
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
			double spectralResponseRed = 1.0;
			double spectralResponseGreen = 1.0;
			double spectralResponseBlue = 1.0;
			double spectralEmissionRed = 1.0;
			double spectralEmissionGreen = 1.0;
			double spectralEmissionBlue = 1.0;
			double photonEnergy = 1.0;
			double photonCoupling = 1.0;
			double photonMinRelativeMass = 0.001;
			uint32_t photonSurfaceBehavior = 0u;
			uint32_t contactIllumination = 0u;

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

			auto readSpectralRGB = [&](const char* key, double& red, double& green, double& blue)
			{
				config_setting_t* spectral = config_setting_lookup(material, key);
				if (spectral == nullptr)
					return;
				int spectralLength = config_setting_length(spectral);
				if (spectralLength != 3)
					throw std::runtime_error("material_properties[" + std::to_string(index) + "]." + key + " must contain 3 values");
				for (int spectralIndex = 0; spectralIndex < spectralLength; ++spectralIndex)
				{
					config_setting_t* element = config_setting_get_elem(spectral, spectralIndex);
					if (element == nullptr || config_setting_type(element) != CONFIG_TYPE_FLOAT)
						throw std::runtime_error("material_properties[" + std::to_string(index) + "]." + key + " values must be floats");
				}
				red = config_setting_get_float_elem(spectral, 0);
				green = config_setting_get_float_elem(spectral, 1);
				blue = config_setting_get_float_elem(spectral, 2);
			};
			readSpectralRGB("spectral_response", spectralResponseRed, spectralResponseGreen, spectralResponseBlue);
			readSpectralRGB("spectral_emission", spectralEmissionRed, spectralEmissionGreen, spectralEmissionBlue);

			if (config_setting_lookup_float(material, "photon_energy", &photonEnergy) == CONFIG_FALSE)
				photonEnergy = 1.0;
			if (photonEnergy < 0.0)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_energy must not be negative");

			if (config_setting_lookup_float(material, "photon_coupling", &photonCoupling) == CONFIG_FALSE)
				photonCoupling = 1.0;
			if (photonCoupling < 0.0 || photonCoupling > 1.0)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_coupling must be between 0.0 and 1.0");

			if (config_setting_lookup_float(material, "photon_min_relative_mass", &photonMinRelativeMass) == CONFIG_FALSE)
				photonMinRelativeMass = 0.001;
			if (photonMinRelativeMass < 0.0)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_min_relative_mass must not be negative");

			photonSurfaceBehavior = MaterialPhotonSurfaceBehavior(material, index);
			contactIllumination = MaterialContactIllumination(material, index);

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
				<< "vec4("
				<< std::fixed << std::setprecision(9) << spectralResponseRed << ", "
				<< std::fixed << std::setprecision(9) << spectralResponseGreen << ", "
				<< std::fixed << std::setprecision(9) << spectralResponseBlue << ", "
				<< std::fixed << std::setprecision(9) << photonEnergy << "), "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << spectralEmissionRed << ", "
				<< std::fixed << std::setprecision(9) << spectralEmissionGreen << ", "
				<< std::fixed << std::setprecision(9) << spectralEmissionBlue << ", "
				<< "0.000000000), "
				<< std::fixed << std::setprecision(9) << photonCoupling << ", "
				<< std::fixed << std::setprecision(9) << photonMinRelativeMass << ", "
				<< photonSurfaceBehavior << "u, "
				<< contactIllumination << "u, "
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

	ostrm
		<< "const float VELOCITY_ANGLE_COLOR_SAT = "
		<< std::fixed << std::setprecision(2)
		<< CfgApp->GetFloat("application.hsv_sat", true) << ";\n"
		<< "const float VELOCITY_ANGLE_COLOR_VAL = "
		<< std::fixed << std::setprecision(2)
		<< CfgApp->GetFloat("application.hsv_val", true) << ";\n";
	

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

	wall_str
		<< "struct LightingSurfaceObjectMetadata\n"
		<< "{\n"
		<< "    uint surfaceType;\n"
		<< "    uint surfaceID;\n"
		<< "    uint materialID;\n"
		<< "    uint vertexOffset;\n"
		<< "    uint vertexCount;\n"
		<< "    uint sphereLatSegments;\n"
		<< "    uint sphereLonSegments;\n"
		<< "    vec4 initialSurfaceColor;\n"
		<< "};\n\n";

	wall_str
		<< "struct LightingSurfaceWallMetadata\n"
		<< "{\n"
		<< "    vec3 origin;\n"
		<< "    vec3 uAxis;\n"
		<< "    vec3 vAxis;\n"
		<< "    float uLength;\n"
		<< "    float vLength;\n"
		<< "    uint uStepCount;\n"
		<< "    uint vStepCount;\n"
		<< "    uint wallFlag;\n"
		<< "};\n\n";

	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;
	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	std::vector<LightingSurfaceObjectInfo> surfaceObjects =
		LightingSurfaceObjectOffsets(CfgTst);

	wall_str
		<< "const uint LIGHTING_SURFACE_OBJECT_COUNT = "
		<< surfaceObjects.size() << "u;\n";
	if (surfaceObjects.empty())
	{
		wall_str
			<< "const LightingSurfaceObjectMetadata LIGHTING_SURFACE_OBJECTS[1] = "
			<< "LightingSurfaceObjectMetadata[1](\n"
			<< "    LightingSurfaceObjectMetadata(0u, 0u, 0u, 0u, 0u, 0u, 0u, "
			<< "vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000))\n"
			<< ");\n\n";
	}
	else
	{
		wall_str
			<< "const LightingSurfaceObjectMetadata LIGHTING_SURFACE_OBJECTS["
			<< surfaceObjects.size() << "] = LightingSurfaceObjectMetadata["
			<< surfaceObjects.size() << "](\n";
		for (size_t objectIndex = 0; objectIndex < surfaceObjects.size(); ++objectIndex)
		{
			const LightingSurfaceObjectInfo& object = surfaceObjects[objectIndex];
			wall_str
				<< "    LightingSurfaceObjectMetadata("
				<< object.surfaceType << "u, "
				<< object.surfaceID << "u, "
				<< object.materialID << "u, "
				<< object.vertexOffset << "u, "
				<< object.vertexCount << "u, "
				<< object.sphereLatSegments << "u, "
				<< object.sphereLonSegments << "u, "
				<< "vec4("
				<< object.initialSurfaceColor[0] << ", "
				<< object.initialSurfaceColor[1] << ", "
				<< object.initialSurfaceColor[2] << ", "
				<< object.initialSurfaceColor[3] << "))";
			if (objectIndex + 1u < surfaceObjects.size())
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n\n";
	}

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
			<< ");\n\n"
			<< "const uint LIGHTING_SURFACE_WALL_COUNT = 0u;\n"
			<< "const LightingSurfaceWallMetadata LIGHTING_SURFACE_WALLS[1] = "
			<< "LightingSurfaceWallMetadata[1](\n"
			<< "    LightingSurfaceWallMetadata("
			<< "vec3(0.000000000), "
			<< "vec3(1.000000000, 0.000000000, 0.000000000), "
			<< "vec3(0.000000000, 1.000000000, 0.000000000), "
			<< "0.000000000, 0.000000000, "
			<< "1u, 1u, 0u)\n"
			<< ");\n\n";
		return wall_str;
	}

	wall_str
		<< "const uint RECTANGLE_WALL_SEGMENT_COUNT = "
		<< segmentCount << "u;\n"
		<< "const RectangleWallSegment RECTANGLE_WALL_SEGMENTS["
		<< segmentCount << "] = RectangleWallSegment["
		<< segmentCount << "](\n";

	std::ostringstream surface_wall_str;
	surface_wall_str << std::fixed << std::setprecision(9);
	surface_wall_str
		<< "const uint LIGHTING_SURFACE_WALL_COUNT = "
		<< segmentCount << "u;\n"
		<< "const LightingSurfaceWallMetadata LIGHTING_SURFACE_WALLS["
		<< segmentCount << "] = LightingSurfaceWallMetadata["
		<< segmentCount << "](\n";

	for (int index = 0; index < segmentCount; ++index)
	{
		config_setting_t* segment = CfgTst->GetSubStructAddress(segmentList, index);

		int segmentLength = segment == nullptr ? 0 : config_setting_length(segment);
		if (segment == nullptr || (segmentLength != 15 && segmentLength != 16))
		{
			throw std::runtime_error(
				"rectangle_wall_segments[" + std::to_string(index) +
				"] must contain fifteen or sixteen values"
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
		const LightingSurfaceObjectInfo* surfaceObject =
			FindLightingSurfaceObject(surfaceObjects, 2u, wallFlag);
		uint32_t uStepCount = static_cast<uint32_t>(
			std::ceil(std::max(1.0, uLength))
			);
		uint32_t vStepCount = static_cast<uint32_t>(
			std::ceil(std::max(1.0, vLength))
			);
		if (surfaceObject != nullptr)
		{
			if (surfaceObject->rectangleUSegments > 0u)
				uStepCount = surfaceObject->rectangleUSegments;
			if (surfaceObject->rectangleVSegments > 0u)
				vStepCount = surfaceObject->rectangleVSegments;
		}

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

		surface_wall_str
			<< "    LightingSurfaceWallMetadata("
			<< "vec3(" << originX << ", " << originY << ", " << originZ << "), "
			<< "vec3(" << uAxisX << ", " << uAxisY << ", " << uAxisZ << "), "
			<< "vec3(" << vAxisX << ", " << vAxisY << ", " << vAxisZ << "), "
			<< uLength << ", "
			<< vLength << ", "
			<< uStepCount << "u, "
			<< vStepCount << "u, "
			<< wallFlag << "u)";

		if (index + 1 < segmentCount)
			surface_wall_str << ",";

		surface_wall_str << "\n";
	}

	wall_str << ");\n\n";
	surface_wall_str << ");\n\n";
	wall_str << surface_wall_str.str();
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
			<< "#define PHOTON_PERIODIC_RECYCLE_ENABLED "
				<< (CfgTst->CheckKey("photon_periodic_recycle_enabled") &&
						CfgTst->GetBool("photon_periodic_recycle_enabled", true)
					? "1u"
					: "0u") << "\n"
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
