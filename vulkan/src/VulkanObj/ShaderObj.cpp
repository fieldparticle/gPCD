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

	uint32_t PhotonLifeTimeID(const std::string& mode)
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

		if (normalized == "PERIODIC" || normalized == "PHOTON_LIFE_TIME_PERIODIC")
			return 0u;
		if (normalized == "PERISH" || normalized == "PHOTON_LIFE_TIME_PERISH")
			return 1u;

		std::ostringstream errtxt;
		errtxt << "Unknown photon_life_time: " << mode << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	uint32_t MaterialPhotonLifeTime(config_setting_t* material, int index)
	{
		config_setting_t* modeSetting =
			config_setting_lookup(material, "photon_life_time");
		if (modeSetting == nullptr)
			return 0u;

		int settingType = config_setting_type(modeSetting);
		if (settingType == CONFIG_TYPE_STRING)
			return PhotonLifeTimeID(config_setting_get_string(modeSetting));
		if (settingType == CONFIG_TYPE_INT)
		{
			int mode = config_setting_get_int(modeSetting);
			if (mode < 0 || mode > 1)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_life_time is outside the valid range");
			return static_cast<uint32_t>(mode);
		}

		throw std::runtime_error("material_properties[" + std::to_string(index) + "].photon_life_time must be a string or integer");
	}

	struct LightingSurfaceObjectInfo
	{
		uint32_t surfaceType = 0u;
		uint32_t surfaceID = 0u;
		uint32_t materialID = 0u;
		uint32_t vertexOffset = 0u;
		uint32_t vertexCount = 0u;
		uint32_t indexCount = 0u;
		double initialSurfaceColor[4] = { 0.0, 0.0, 0.0, 1.0 };
		double depositRadius = 0.0;
		uint32_t rectangleUSegments = 0u;
		uint32_t rectangleVSegments = 0u;
		uint32_t sphereLatSegments = 0u;
		uint32_t sphereLonSegments = 0u;
		std::vector<uint32_t> sphereSurfaceMapMaterialIDs;
		std::vector<double> sphereSurfaceMapAlbedos;
		std::vector<uint32_t> sphereDecalRings;
		std::vector<uint32_t> sphereDecalSegments;
		std::vector<uint32_t> sphereDecalMaterialIDs;
		std::vector<double> sphereDecalAlbedos;
	};

	struct LightingSurfaceMeshCounts
	{
		uint32_t vertexCount = 0u;
		uint32_t indexCount = 0u;
		uint32_t sphereLatSegments = 0u;
		uint32_t sphereLonSegments = 0u;
		std::vector<uint32_t> sphereSurfaceMapMaterialIDs;
		std::vector<double> sphereSurfaceMapAlbedos;
		std::vector<uint32_t> sphereDecalRings;
		std::vector<uint32_t> sphereDecalSegments;
		std::vector<uint32_t> sphereDecalMaterialIDs;
		std::vector<double> sphereDecalAlbedos;
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

	uint32_t ReadMeshPositiveUInt(
		config_setting_t* object,
		const std::string& context,
		const char* fieldName)
	{
		int value = 0;
		if (config_setting_lookup_int(object, fieldName, &value) != CONFIG_TRUE)
			throw std::runtime_error(context + "." + fieldName + " is required");
		if (value <= 0)
			throw std::runtime_error(context + "." + fieldName + " must be positive");
		return static_cast<uint32_t>(value);
	}

	uint32_t ReadMeshOptionalUInt(
		config_setting_t* object,
		const char* fieldName,
		uint32_t defaultValue)
	{
		int value = 0;
		if (config_setting_lookup_int(object, fieldName, &value) != CONFIG_TRUE)
			return defaultValue;
		if (value < 0)
			throw std::runtime_error(std::string("mesh object ") + fieldName + " must not be negative");
		return static_cast<uint32_t>(value);
	}

	LightingSurfaceMeshCounts ReadLightingSurfaceMeshCounts(
		const std::string& meshFile,
		uint32_t surfaceType,
		uint32_t surfaceID,
		uint32_t materialID)
	{
		config_t meshConfig;
		config_init(&meshConfig);
		if (!config_read_file(&meshConfig, meshFile.c_str()))
		{
			std::ostringstream errtxt;
			errtxt << "Could not read lighting surface mesh file "
				<< meshFile << ":" << config_error_line(&meshConfig)
				<< ": " << config_error_text(&meshConfig) << std::ends;
			config_destroy(&meshConfig);
			throw std::runtime_error(errtxt.str().c_str());
		}

		config_setting_t* objects = config_lookup(&meshConfig, "objects");
		if (objects == nullptr || config_setting_length(objects) <= 0)
		{
			config_destroy(&meshConfig);
			throw std::runtime_error("lighting surface mesh objects is required and must not be empty");
		}

		int objectCount = config_setting_length(objects);
		for (int objectIndex = 0; objectIndex < objectCount; ++objectIndex)
		{
			config_setting_t* object = config_setting_get_elem(objects, objectIndex);
			if (object == nullptr)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error("lighting surface mesh object is invalid");
			}

			const char* surfaceTypeText = nullptr;
			int meshSurfaceID = 0;
			int meshMaterialID = 0;
			if (config_setting_lookup_string(object, "surface_type", &surfaceTypeText) != CONFIG_TRUE ||
				config_setting_lookup_int(object, "surface_id", &meshSurfaceID) != CONFIG_TRUE ||
				config_setting_lookup_int(object, "material_id", &meshMaterialID) != CONFIG_TRUE)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error(
					"lighting surface mesh objects[" + std::to_string(objectIndex) +
					"] must contain surface_type, surface_id, and material_id");
			}

			if (LightingSurfaceTypeID(surfaceTypeText) != surfaceType ||
				static_cast<uint32_t>(meshSurfaceID) != surfaceID ||
				static_cast<uint32_t>(meshMaterialID) != materialID)
			{
				continue;
			}

			std::string context =
				"lighting surface mesh objects[" + std::to_string(objectIndex) + "]";
			LightingSurfaceMeshCounts counts{};
			counts.vertexCount =
				ReadMeshPositiveUInt(object, context, "vertex_count");
			counts.indexCount =
				ReadMeshPositiveUInt(object, context, "index_count");
			counts.sphereLatSegments =
				ReadMeshOptionalUInt(object, "sphere_lat_segments", 0u);
			counts.sphereLonSegments =
				ReadMeshOptionalUInt(object, "sphere_lon_segments", 0u);

			config_setting_t* sphereSurfaceMap =
				config_setting_lookup(object, "sphere_surface_map");
			if (sphereSurfaceMap != nullptr)
			{
				uint32_t mapLatSegments =
					ReadMeshPositiveUInt(sphereSurfaceMap, context + ".sphere_surface_map", "lat_segments");
				uint32_t mapLonSegments =
					ReadMeshPositiveUInt(sphereSurfaceMap, context + ".sphere_surface_map", "lon_segments");
				uint32_t cellCount =
					ReadMeshPositiveUInt(sphereSurfaceMap, context + ".sphere_surface_map", "cell_count");
				if (mapLatSegments != counts.sphereLatSegments ||
					mapLonSegments != counts.sphereLonSegments ||
					cellCount != (mapLatSegments + 1u) * mapLonSegments)
				{
					config_destroy(&meshConfig);
					throw std::runtime_error(context + ".sphere_surface_map dimensions do not match sphere segments");
				}

				config_setting_t* materialIDs =
					config_setting_lookup(sphereSurfaceMap, "material_ids");
				config_setting_t* albedos =
					config_setting_lookup(sphereSurfaceMap, "albedos");
				if (materialIDs == nullptr ||
					albedos == nullptr ||
					static_cast<uint32_t>(config_setting_length(materialIDs)) != cellCount ||
					static_cast<uint32_t>(config_setting_length(albedos)) != cellCount)
				{
					config_destroy(&meshConfig);
					throw std::runtime_error(context + ".sphere_surface_map material_ids/albedos length must match cell_count");
				}

				counts.sphereSurfaceMapMaterialIDs.reserve(cellCount);
				counts.sphereSurfaceMapAlbedos.reserve(static_cast<size_t>(cellCount) * 4u);
				for (uint32_t cellIndex = 0u; cellIndex < cellCount; ++cellIndex)
				{
					int materialID =
						config_setting_get_int_elem(materialIDs, static_cast<int>(cellIndex));
					if (materialID < 0)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_surface_map material id must not be negative");
					}
					counts.sphereSurfaceMapMaterialIDs.push_back(
						static_cast<uint32_t>(materialID));

					config_setting_t* albedo =
						config_setting_get_elem(albedos, static_cast<int>(cellIndex));
					if (albedo == nullptr || config_setting_length(albedo) != 4)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_surface_map albedo must contain RGBA");
					}
					for (int channel = 0; channel < 4; ++channel)
						counts.sphereSurfaceMapAlbedos.push_back(
							config_setting_get_float_elem(albedo, channel));
				}
			}

			config_setting_t* sphereDecalMap =
				config_setting_lookup(object, "sphere_decal_map");
			if (sphereDecalMap != nullptr)
			{
				uint32_t mapLatSegments =
					ReadMeshPositiveUInt(sphereDecalMap, context + ".sphere_decal_map", "lat_segments");
				uint32_t mapLonSegments =
					ReadMeshPositiveUInt(sphereDecalMap, context + ".sphere_decal_map", "lon_segments");
				uint32_t cellCount =
					ReadMeshPositiveUInt(sphereDecalMap, context + ".sphere_decal_map", "cell_count");
				if (mapLatSegments != counts.sphereLatSegments ||
					mapLonSegments != counts.sphereLonSegments)
				{
					config_destroy(&meshConfig);
					throw std::runtime_error(context + ".sphere_decal_map dimensions do not match sphere segments");
				}

				config_setting_t* cells =
					config_setting_lookup(sphereDecalMap, "cells");
				if (cells == nullptr ||
					static_cast<uint32_t>(config_setting_length(cells)) != cellCount)
				{
					config_destroy(&meshConfig);
					throw std::runtime_error(context + ".sphere_decal_map cells length must match cell_count");
				}

				counts.sphereDecalRings.reserve(cellCount);
				counts.sphereDecalSegments.reserve(cellCount);
				counts.sphereDecalMaterialIDs.reserve(cellCount);
				counts.sphereDecalAlbedos.reserve(static_cast<size_t>(cellCount) * 4u);
				for (uint32_t cellIndex = 0u; cellIndex < cellCount; ++cellIndex)
				{
					config_setting_t* cell =
						config_setting_get_elem(cells, static_cast<int>(cellIndex));
					if (cell == nullptr)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_decal_map cell is invalid");
					}
					int ringValue = 0;
					int segmentValue = 0;
					if (config_setting_lookup_int(cell, "ring", &ringValue) != CONFIG_TRUE ||
						config_setting_lookup_int(cell, "segment", &segmentValue) != CONFIG_TRUE ||
						ringValue < 0 ||
						segmentValue < 0)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_decal_map cell ring/segment must be non-negative");
					}
					uint32_t ring = static_cast<uint32_t>(ringValue);
					uint32_t segment = static_cast<uint32_t>(segmentValue);
					uint32_t materialID =
						ReadMeshPositiveUInt(cell, context + ".sphere_decal_map.cells", "material_id");
					if (ring > counts.sphereLatSegments ||
						segment >= counts.sphereLonSegments)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_decal_map cell ring/segment is outside sphere");
					}

					config_setting_t* albedo =
						config_setting_lookup(cell, "albedo");
					if (albedo == nullptr || config_setting_length(albedo) != 4)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(context + ".sphere_decal_map albedo must contain RGBA");
					}
					counts.sphereDecalRings.push_back(ring);
					counts.sphereDecalSegments.push_back(segment);
					counts.sphereDecalMaterialIDs.push_back(materialID);
					for (int channel = 0; channel < 4; ++channel)
						counts.sphereDecalAlbedos.push_back(
							config_setting_get_float_elem(albedo, channel));
				}
			}
			config_destroy(&meshConfig);
			return counts;
		}

		std::ostringstream errtxt;
		errtxt << "Mesh file " << meshFile
			<< " has no object matching surface_type " << surfaceType
			<< ", surface_id " << surfaceID
			<< ", material_id " << materialID << std::ends;
		config_destroy(&meshConfig);
		throw std::runtime_error(errtxt.str().c_str());
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

	double ReadOptionalNonnegativeFloat(
		config_setting_t* object,
		int objectIndex,
		const char* fieldName,
		double defaultValue)
	{
		config_setting_t* setting = config_setting_lookup(object, fieldName);
		if (setting == nullptr)
			return defaultValue;

		int settingType = config_setting_type(setting);
		double value = 0.0;
		if (settingType == CONFIG_TYPE_FLOAT)
			value = config_setting_get_float(setting);
		else if (settingType == CONFIG_TYPE_INT)
			value = static_cast<double>(config_setting_get_int(setting));
		else
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"]." + fieldName + " must be numeric"
			);
		}
		if (!std::isfinite(value) || value < 0.0)
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"]." + fieldName + " must be finite and nonnegative"
			);
		}
		return value;
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
				const char* meshFile = nullptr;
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
					errtxt << "lighting_surface_objects[" << index
						<< "] must contain OBJ metadata" << std::ends;
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
				ReadInitialSurfaceColor(object, index, info.initialSurfaceColor);
				info.depositRadius = ReadOptionalNonnegativeFloat(
					object, index, "deposit_radius", 0.0);
				if (surfaceType == 2u)
				{
					info.rectangleUSegments =
						ReadPositiveUInt(object, index, "rectangle_u_segments");
					info.rectangleVSegments =
						ReadPositiveUInt(object, index, "rectangle_v_segments");
					info.vertexCount =
						(info.rectangleUSegments + 1u) *
						(info.rectangleVSegments + 1u);
					info.indexCount =
						info.rectangleUSegments *
						info.rectangleVSegments *
						6u;
				}
				else if (surfaceType == 1u)
				{
					if (config_setting_lookup_string(object, "mesh_file", &meshFile) != CONFIG_TRUE)
					{
						std::ostringstream errtxt;
						errtxt << "lighting_surface_objects[" << index
							<< "].mesh_file is required for SPHERE" << std::ends;
						throw std::runtime_error(errtxt.str().c_str());
					}
					LightingSurfaceMeshCounts meshCounts =
						ReadLightingSurfaceMeshCounts(
							meshFile,
							info.surfaceType,
							info.surfaceID,
							info.materialID);
					info.vertexCount = meshCounts.vertexCount;
					info.indexCount = meshCounts.indexCount;
					info.sphereLatSegments = meshCounts.sphereLatSegments;
					info.sphereLonSegments = meshCounts.sphereLonSegments;
					info.sphereSurfaceMapMaterialIDs =
						meshCounts.sphereSurfaceMapMaterialIDs;
					info.sphereSurfaceMapAlbedos =
						meshCounts.sphereSurfaceMapAlbedos;
					info.sphereDecalRings =
						meshCounts.sphereDecalRings;
					info.sphereDecalSegments =
						meshCounts.sphereDecalSegments;
					info.sphereDecalMaterialIDs =
						meshCounts.sphereDecalMaterialIDs;
					info.sphereDecalAlbedos =
						meshCounts.sphereDecalAlbedos;
					if (info.sphereLatSegments == 0u)
						info.sphereLatSegments =
							ReadPositiveUInt(object, index, "sphere_lat_segments");
					if (info.sphereLonSegments == 0u)
						info.sphereLonSegments =
							ReadPositiveUInt(object, index, "sphere_lon_segments");
				}
				else
				{
					std::ostringstream errtxt;
					errtxt << "Unsupported lighting surface type for indexed metadata: "
						<< surfaceType << " from " << objFile << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
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
	ostrm << "const uint COLOR_MAP_HSV = 0u;\n";
	ostrm << "const uint COLOR_MAP_GRAYSCALE = 1u;\n";
	ostrm << "const uint COLOR_MAP_HEAT = 2u;\n";
	ostrm << "const uint COLOR_MAP_SOLID = 3u;\n\n";
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
	ostrm << "    uint colorMap;\n";
	ostrm << "    float pointSize;\n";
	ostrm << "    uint captureAngleOffset;\n";
	ostrm << "    uint captureAngleCount;\n";
	ostrm << "    vec4 color;\n";
	ostrm << "    vec4 collisionColor;\n";
	ostrm << "    vec4 nonCollisionColor;\n";
	ostrm << "    uint debugVisible;\n";
	ostrm << "    vec4 debugColor;\n";
	ostrm << "    vec4 spectralResponseEnergy;\n";
	ostrm << "    vec4 spectralEmission;\n";
	ostrm << "    float photonCoupling;\n";
	ostrm << "    float photonMinRelativeMass;\n";
	ostrm << "    uint photonSurfaceBehavior;\n";
	ostrm << "    uint photonLifeTime;\n";
	ostrm << "    uint contactIllumination;\n";
	ostrm << "    float cellDensity;\n";
	ostrm << "};\n\n";

	int materialCount = 0;
	config_setting_t* materialList = nullptr;
	struct CaptureAngleRecord
	{
		double centerRadians;
		double plusRadians;
		double minusRadians;
	};
	std::vector<CaptureAngleRecord> captureAngleRecords;
	const double degreeToRadians = 0.017453292519943295;
	double defaultPointSize = CfgTst->CheckKey("gl_point_size")
		? CfgTst->GetFloat("gl_point_size", true)
		: 3.0;
	if (defaultPointSize <= 0.0)
		throw std::runtime_error("gl_point_size must be positive");

	if (CfgTst->CheckKey("material_properties"))
		materialList = CfgTst->StartStructure("material_properties", materialCount);

	if (materialList == nullptr || materialCount <= 0)
	{
		ostrm << "const uint MATERIAL_PROPERTY_COUNT = 1u;\n";
		ostrm << "const MaterialProperty MATERIAL_PROPERTIES[1] = MaterialProperty[1](\n";
		ostrm << "    MaterialProperty(0u, PARTICLE_TYPE_REGULAR, 1.000000000, 0.000000000, COLOR_MODE_VELOCITY_ANGLE, COLOR_MAP_HSV, "
			<< std::fixed << std::setprecision(9) << defaultPointSize
			<< ", 0u, 0u, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), vec4(1.000000000, 0.000000000, 0.000000000, 1.000000000), vec4(0.000000000, 1.000000000, 0.000000000, 1.000000000), 0u, vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), vec4(1.000000000, 1.000000000, 1.000000000, 1.000000000), vec4(1.000000000, 1.000000000, 1.000000000, 0.000000000), 1.000000000, 0.001000000, PHOTON_SURFACE_BEHAVIOR_NONE, 0u, CONTACT_ILLUMINATION_MAX, 0.000000000)\n";
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
			int colorMap = 0;
			int particleType = 0;
			double pointSize = defaultPointSize;
			uint32_t captureAngleOffset = 0u;
			uint32_t captureAngleCount = 0u;
			double relativeMass = 1.0;
			double tempVel = 0.0;
			double cellDensity = 0.0;
			double colorRed = 1.0;
			double colorGreen = 1.0;
			double colorBlue = 1.0;
			double colorAlpha = 1.0;
			double collisionRed = 1.0;
			double collisionGreen = 0.0;
			double collisionBlue = 0.0;
			double collisionAlpha = 1.0;
			double nonCollisionRed = 0.0;
			double nonCollisionGreen = 1.0;
			double nonCollisionBlue = 0.0;
			double nonCollisionAlpha = 1.0;
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
			uint32_t photonLifeTime = 0u;
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
			if (config_setting_lookup_int(material, "color_map", &colorMap) == CONFIG_FALSE)
			{
				if (colorMode == 1)
					colorMap = 0;
				else
					colorMap = 3;
			}
			if (colorMap < 0 || colorMap > 3)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].color_map is outside the valid range");
			if (config_setting_lookup_float(material, "point_size", &pointSize) == CONFIG_FALSE)
				pointSize = defaultPointSize;
			if (pointSize <= 0.0)
				throw std::runtime_error("material_properties[" + std::to_string(index) + "].point_size must be positive");

			captureAngleOffset = static_cast<uint32_t>(captureAngleRecords.size());
			config_setting_t* captureAngles = config_setting_lookup(material, "capture_angles");
			if (captureAngles != nullptr)
			{
				captureAngleCount = static_cast<uint32_t>(config_setting_length(captureAngles));
				for (uint32_t captureIndex = 0u; captureIndex < captureAngleCount; ++captureIndex)
				{
					config_setting_t* captureAngle = config_setting_get_elem(captureAngles, static_cast<unsigned int>(captureIndex));
					if (captureAngle == nullptr || config_setting_length(captureAngle) != 3)
						throw std::runtime_error("material_properties[" + std::to_string(index) + "].capture_angles entries must contain 3 values");
					double centerDegrees = config_setting_get_float_elem(captureAngle, 0);
					double plusDegrees = config_setting_get_float_elem(captureAngle, 1);
					double minusDegrees = config_setting_get_float_elem(captureAngle, 2);
					if (plusDegrees < 0.0 || minusDegrees < 0.0)
						throw std::runtime_error("material_properties[" + std::to_string(index) + "].capture_angles ranges must not be negative");
					captureAngleRecords.push_back(
						{
							centerDegrees * degreeToRadians,
							plusDegrees * degreeToRadians,
							minusDegrees * degreeToRadians
						}
					);
				}
			}

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

			auto readOptionalRGBA = [&](const char* key, double& red, double& green, double& blue, double& alpha)
			{
				config_setting_t* rgba = config_setting_lookup(material, key);
				if (rgba == nullptr)
					return;
				int colorLength = config_setting_length(rgba);
				if (colorLength != 3 && colorLength != 4)
					throw std::runtime_error("material_properties[" + std::to_string(index) + "]." + key + " must contain 3 or 4 values");
				red = config_setting_get_float_elem(rgba, 0);
				green = config_setting_get_float_elem(rgba, 1);
				blue = config_setting_get_float_elem(rgba, 2);
				if (colorLength == 4)
					alpha = config_setting_get_float_elem(rgba, 3);
			};
			readOptionalRGBA("collision_color", collisionRed, collisionGreen, collisionBlue, collisionAlpha);
			readOptionalRGBA("non_collision_color", nonCollisionRed, nonCollisionGreen, nonCollisionBlue, nonCollisionAlpha);

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
			photonLifeTime = MaterialPhotonLifeTime(material, index);
			contactIllumination = MaterialContactIllumination(material, index);

			if (config_setting_lookup_float(material, "cell_density", &cellDensity) == CONFIG_FALSE)
				cellDensity = 0.0;

			ostrm << "    MaterialProperty("
				<< materialID << "u, "
				<< particleType << "u, "
				<< std::fixed << std::setprecision(9) << relativeMass << ", "
				<< std::fixed << std::setprecision(9) << tempVel << ", "
				<< colorMode << "u, "
				<< colorMap << "u, "
				<< std::fixed << std::setprecision(9) << pointSize << ", "
				<< captureAngleOffset << "u, "
				<< captureAngleCount << "u, "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << colorRed << ", "
				<< std::fixed << std::setprecision(9) << colorGreen << ", "
				<< std::fixed << std::setprecision(9) << colorBlue << ", "
				<< std::fixed << std::setprecision(9) << colorAlpha << "), "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << collisionRed << ", "
				<< std::fixed << std::setprecision(9) << collisionGreen << ", "
				<< std::fixed << std::setprecision(9) << collisionBlue << ", "
				<< std::fixed << std::setprecision(9) << collisionAlpha << "), "
				<< "vec4("
				<< std::fixed << std::setprecision(9) << nonCollisionRed << ", "
				<< std::fixed << std::setprecision(9) << nonCollisionGreen << ", "
				<< std::fixed << std::setprecision(9) << nonCollisionBlue << ", "
				<< std::fixed << std::setprecision(9) << nonCollisionAlpha << "), "
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
				<< photonLifeTime << "u, "
				<< contactIllumination << "u, "
				<< std::fixed << std::setprecision(9) << cellDensity << ")";

			if (index + 1 < materialCount)
				ostrm << ",";

			ostrm << "\n";
		}

		ostrm << ");\n\n";
	}


	ostrm << "struct CaptureAngle\n";
	ostrm << "{\n";
	ostrm << "    float center;\n";
	ostrm << "    float plusRange;\n";
	ostrm << "    float minusRange;\n";
	ostrm << "};\n\n";
	ostrm << "const uint CAPTURE_ANGLE_COUNT = " << captureAngleRecords.size() << "u;\n";
	if (captureAngleRecords.empty())
	{
		ostrm << "const CaptureAngle CAPTURE_ANGLES[1] = CaptureAngle[1](\n";
		ostrm << "    CaptureAngle(0.000000000, 0.000000000, 0.000000000)\n";
		ostrm << ");\n\n";
	}
	else
	{
		ostrm << "const CaptureAngle CAPTURE_ANGLES[" << captureAngleRecords.size() << "] = CaptureAngle["
			<< captureAngleRecords.size() << "](\n";
		for (size_t captureIndex = 0; captureIndex < captureAngleRecords.size(); ++captureIndex)
		{
			const CaptureAngleRecord& captureAngle = captureAngleRecords[captureIndex];
			ostrm << "    CaptureAngle("
				<< std::fixed << std::setprecision(9) << captureAngle.centerRadians << ", "
				<< std::fixed << std::setprecision(9) << captureAngle.plusRadians << ", "
				<< std::fixed << std::setprecision(9) << captureAngle.minusRadians << ")";
			if (captureIndex + 1 < captureAngleRecords.size())
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
			<< "const float piston_dt=" << std::fixed << std::setprecision(9)
			<< CfgTst->GetFloat("DT", true) << ";\n"

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
	bool show_boundary_as_obj = CfgApp->GetBool("application.boundary_as_obj", true);
	bool has_lighting_ball = CfgTst->CheckKey("Lighting_ball");

	std::string wlflg = "0u";
	wlflg = "1u;";
	
	std::ostringstream boundary;
	if (show_cell_boundary_cube == true || show_wall_as_boundary_cube == true || show_boundary_as_obj == true)
	{
		boundary << "#define HAS_BOUNDARY" << "\n";

	}
	if (has_lighting_ball)
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
		<< "    uint indexCount;\n"
		<< "    uint sphereLatSegments;\n"
		<< "    uint sphereLonSegments;\n"
		<< "    vec4 initialSurfaceColor;\n"
		<< "    float depositRadius;\n"
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
			<< "    LightingSurfaceObjectMetadata(0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, "
			<< "vec4(0.000000000, 0.000000000, 0.000000000, 1.000000000), "
			<< "0.000000000)\n"
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
				<< object.indexCount << "u, "
				<< object.sphereLatSegments << "u, "
				<< object.sphereLonSegments << "u, "
				<< "vec4("
				<< object.initialSurfaceColor[0] << ", "
				<< object.initialSurfaceColor[1] << ", "
				<< object.initialSurfaceColor[2] << ", "
				<< object.initialSurfaceColor[3] << "), "
				<< object.depositRadius << ")";
			if (objectIndex + 1u < surfaceObjects.size())
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n\n";
	}

	const bool enableSphereSurfaceMap =
		CfgTst->CheckKey("enable_sphere_surface_map") &&
		CfgTst->GetBool("enable_sphere_surface_map", true);
	const LightingSurfaceObjectInfo* sphereSurfaceMapObject = nullptr;
	if (enableSphereSurfaceMap)
	{
		for (const LightingSurfaceObjectInfo& object : surfaceObjects)
		{
			if (object.surfaceType == LightingSurfaceTypeID("SPHERE") &&
				!object.sphereSurfaceMapMaterialIDs.empty() &&
				object.sphereSurfaceMapAlbedos.size() ==
					static_cast<size_t>(object.sphereSurfaceMapMaterialIDs.size()) * 4u)
			{
				sphereSurfaceMapObject = &object;
				break;
			}
		}
	}

	if (sphereSurfaceMapObject == nullptr)
	{
		wall_str
			<< "#define LIGHTING_SPHERE_SURFACE_MAP_DEFINED 1\n"
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_SURFACE_ID = 0u;\n"
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_COUNT = 0u;\n"
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_MATERIAL_IDS[1] = uint[1](0u);\n"
			<< "const vec4 LIGHTING_SPHERE_SURFACE_MAP_ALBEDOS[1] = vec4[1](vec4(0.0));\n\n";
	}
	else
	{
		const size_t mapCount =
			sphereSurfaceMapObject->sphereSurfaceMapMaterialIDs.size();
		wall_str
			<< "#define LIGHTING_SPHERE_SURFACE_MAP_DEFINED 1\n"
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_SURFACE_ID = "
			<< sphereSurfaceMapObject->surfaceID << "u;\n"
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_COUNT = "
			<< mapCount << "u;\n";

		wall_str
			<< "const uint LIGHTING_SPHERE_SURFACE_MAP_MATERIAL_IDS["
			<< mapCount << "] = uint[" << mapCount << "](\n";
		for (size_t cellIndex = 0u; cellIndex < mapCount; ++cellIndex)
		{
			wall_str
				<< "    "
				<< sphereSurfaceMapObject->sphereSurfaceMapMaterialIDs[cellIndex]
				<< "u";
			if (cellIndex + 1u < mapCount)
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n";

		wall_str
			<< "const vec4 LIGHTING_SPHERE_SURFACE_MAP_ALBEDOS["
			<< mapCount << "] = vec4[" << mapCount << "](\n";
		for (size_t cellIndex = 0u; cellIndex < mapCount; ++cellIndex)
		{
			size_t albedoIndex = cellIndex * 4u;
			wall_str
				<< "    vec4("
				<< sphereSurfaceMapObject->sphereSurfaceMapAlbedos[albedoIndex] << ", "
				<< sphereSurfaceMapObject->sphereSurfaceMapAlbedos[albedoIndex + 1u] << ", "
				<< sphereSurfaceMapObject->sphereSurfaceMapAlbedos[albedoIndex + 2u] << ", "
				<< sphereSurfaceMapObject->sphereSurfaceMapAlbedos[albedoIndex + 3u] << ")";
			if (cellIndex + 1u < mapCount)
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n\n";
	}

	const LightingSurfaceObjectInfo* sphereDecalMapObject = nullptr;
	for (const LightingSurfaceObjectInfo& object : surfaceObjects)
	{
		if (object.surfaceType == LightingSurfaceTypeID("SPHERE") &&
			!object.sphereDecalRings.empty() &&
			object.sphereDecalSegments.size() == object.sphereDecalRings.size() &&
			object.sphereDecalMaterialIDs.size() == object.sphereDecalRings.size() &&
			object.sphereDecalAlbedos.size() ==
				static_cast<size_t>(object.sphereDecalRings.size()) * 4u)
		{
			sphereDecalMapObject = &object;
			break;
		}
	}

	if (sphereDecalMapObject == nullptr)
	{
		wall_str
			<< "#define LIGHTING_SPHERE_DECAL_MAP_DEFINED 1\n"
			<< "const uint LIGHTING_SPHERE_DECAL_MAP_SURFACE_ID = 0u;\n"
			<< "const uint LIGHTING_SPHERE_DECAL_MAP_COUNT = 0u;\n"
			<< "const uvec4 LIGHTING_SPHERE_DECAL_MAP_CELLS[1] = uvec4[1](uvec4(0u));\n"
			<< "const vec4 LIGHTING_SPHERE_DECAL_MAP_ALBEDOS[1] = vec4[1](vec4(0.0));\n\n";
	}
	else
	{
		const size_t mapCount = sphereDecalMapObject->sphereDecalRings.size();
		wall_str
			<< "#define LIGHTING_SPHERE_DECAL_MAP_DEFINED 1\n"
			<< "const uint LIGHTING_SPHERE_DECAL_MAP_SURFACE_ID = "
			<< sphereDecalMapObject->surfaceID << "u;\n"
			<< "const uint LIGHTING_SPHERE_DECAL_MAP_COUNT = "
			<< mapCount << "u;\n";

		wall_str
			<< "const uvec4 LIGHTING_SPHERE_DECAL_MAP_CELLS["
			<< mapCount << "] = uvec4[" << mapCount << "](\n";
		for (size_t cellIndex = 0u; cellIndex < mapCount; ++cellIndex)
		{
			wall_str
				<< "    uvec4("
				<< sphereDecalMapObject->sphereDecalRings[cellIndex] << "u, "
				<< sphereDecalMapObject->sphereDecalSegments[cellIndex] << "u, "
				<< sphereDecalMapObject->sphereDecalMaterialIDs[cellIndex] << "u, "
				<< "0u)";
			if (cellIndex + 1u < mapCount)
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n";

		wall_str
			<< "const vec4 LIGHTING_SPHERE_DECAL_MAP_ALBEDOS["
			<< mapCount << "] = vec4[" << mapCount << "](\n";
		for (size_t cellIndex = 0u; cellIndex < mapCount; ++cellIndex)
		{
			size_t albedoIndex = cellIndex * 4u;
			wall_str
				<< "    vec4("
				<< sphereDecalMapObject->sphereDecalAlbedos[albedoIndex] << ", "
				<< sphereDecalMapObject->sphereDecalAlbedos[albedoIndex + 1u] << ", "
				<< sphereDecalMapObject->sphereDecalAlbedos[albedoIndex + 2u] << ", "
				<< sphereDecalMapObject->sphereDecalAlbedos[albedoIndex + 3u] << ")";
			if (cellIndex + 1u < mapCount)
				wall_str << ",";
			wall_str << "\n";
		}
		wall_str << ");\n\n";
	}

	bool reflectingWallLightMapEnabled =
		CfgTst->CheckKey("reflecting_wall_light_map.enabled") &&
		CfgTst->GetBool("reflecting_wall_light_map.enabled", true);
	uint32_t reflectingWallLightMapSurfaceID = 0u;
	uint32_t reflectingWallLightMapWidth = 1u;
	uint32_t reflectingWallLightMapHeight = 1u;
	uint32_t reflectingWallPhotonSplatCount = 1u;
	float reflectingWallPhotonSplatRadius = 10.0f;
	float reflectingWallPhotonSplatAlpha = 0.06f;
	glm::vec4 reflectingWallGlassTint(0.08f, 0.12f, 0.14f, 0.35f);
	float reflectingWallReflectionGain = 1.5f;
	float reflectingWallFresnelStrength = 0.25f;
	if (reflectingWallLightMapEnabled)
	{
		reflectingWallLightMapSurfaceID =
			CfgTst->GetUInt("reflecting_wall_light_map.surface_id", true);
		reflectingWallLightMapWidth =
			CfgTst->GetUInt("reflecting_wall_light_map.width", true);
		reflectingWallLightMapHeight =
			CfgTst->GetUInt("reflecting_wall_light_map.height", true);
		if (reflectingWallLightMapWidth == 0u ||
			reflectingWallLightMapHeight == 0u)
		{
			throw std::runtime_error(
				"reflecting_wall_light_map width/height must be positive");
		}
		reflectingWallPhotonSplatCount =
			CfgTst->CheckKey("reflecting_wall_light_map.splat_capacity")
			? CfgTst->GetUInt("reflecting_wall_light_map.splat_capacity", true)
			: CfgTst->GetUInt("num_particles", true) + 1u;
		if (reflectingWallPhotonSplatCount == 0u)
		{
			throw std::runtime_error(
				"reflecting_wall_light_map.splat_capacity must be positive");
		}
		if (CfgTst->CheckKey("reflecting_wall_light_map.splat_radius"))
			reflectingWallPhotonSplatRadius =
				CfgTst->GetFloat("reflecting_wall_light_map.splat_radius", true);
		if (CfgTst->CheckKey("reflecting_wall_light_map.splat_alpha"))
			reflectingWallPhotonSplatAlpha =
				CfgTst->GetFloat("reflecting_wall_light_map.splat_alpha", true);
		if (CfgTst->CheckKey("reflecting_wall_light_map.glass_tint"))
		{
			config_setting_t* glassTint =
				CfgTst->CheckKey("reflecting_wall_light_map.glass_tint");
			if (glassTint == nullptr || config_setting_length(glassTint) != 4)
				throw std::runtime_error(
					"reflecting_wall_light_map.glass_tint must contain 4 values");
			reflectingWallGlassTint =
				glm::vec4(
					static_cast<float>(config_setting_get_float_elem(glassTint, 0)),
					static_cast<float>(config_setting_get_float_elem(glassTint, 1)),
					static_cast<float>(config_setting_get_float_elem(glassTint, 2)),
					static_cast<float>(config_setting_get_float_elem(glassTint, 3)));
		}
		if (CfgTst->CheckKey("reflecting_wall_light_map.reflection_gain"))
			reflectingWallReflectionGain =
				CfgTst->GetFloat("reflecting_wall_light_map.reflection_gain", true);
		if (CfgTst->CheckKey("reflecting_wall_light_map.fresnel_strength"))
			reflectingWallFresnelStrength =
				CfgTst->GetFloat("reflecting_wall_light_map.fresnel_strength", true);
		if (reflectingWallPhotonSplatRadius <= 0.0f)
			throw std::runtime_error(
				"reflecting_wall_light_map.splat_radius must be positive");
		if (reflectingWallPhotonSplatAlpha < 0.0f ||
			reflectingWallPhotonSplatAlpha > 1.0f)
			throw std::runtime_error(
				"reflecting_wall_light_map.splat_alpha must be between 0 and 1");
		if (reflectingWallGlassTint.a < 0.0f || reflectingWallGlassTint.a > 1.0f)
			throw std::runtime_error(
				"reflecting_wall_light_map.glass_tint alpha must be between 0 and 1");
		if (reflectingWallReflectionGain < 0.0f)
			throw std::runtime_error(
				"reflecting_wall_light_map.reflection_gain must be non-negative");
		if (reflectingWallFresnelStrength < 0.0f)
			throw std::runtime_error(
				"reflecting_wall_light_map.fresnel_strength must be non-negative");
	}
	wall_str
		<< "#define REFLECTING_WALL_LIGHT_MAP_DEFINED 1\n"
		<< "const uint REFLECTING_WALL_LIGHT_MAP_ENABLED = "
		<< (reflectingWallLightMapEnabled ? 1u : 0u) << "u;\n"
		<< "const uint REFLECTING_WALL_LIGHT_MAP_SURFACE_ID = "
		<< reflectingWallLightMapSurfaceID << "u;\n"
		<< "const uint REFLECTING_WALL_LIGHT_MAP_WIDTH = "
		<< reflectingWallLightMapWidth << "u;\n"
		<< "const uint REFLECTING_WALL_LIGHT_MAP_HEIGHT = "
		<< reflectingWallLightMapHeight << "u;\n"
		<< "const uint REFLECTING_WALL_LIGHT_MAP_COUNT = "
		<< reflectingWallLightMapWidth * reflectingWallLightMapHeight
		<< "u;\n"
		<< "const uint REFLECTING_WALL_PHOTON_SPLAT_COUNT = "
		<< reflectingWallPhotonSplatCount
		<< "u;\n"
		<< "const float REFLECTING_WALL_PHOTON_SPLAT_RADIUS = "
		<< reflectingWallPhotonSplatRadius
		<< ";\n"
		<< "const float REFLECTING_WALL_PHOTON_SPLAT_ALPHA = "
		<< reflectingWallPhotonSplatAlpha
		<< ";\n"
		<< "const vec4 REFLECTING_WALL_GLASS_TINT = vec4("
		<< reflectingWallGlassTint.r << ", "
		<< reflectingWallGlassTint.g << ", "
		<< reflectingWallGlassTint.b << ", "
		<< reflectingWallGlassTint.a << ");\n"
		<< "const float REFLECTING_WALL_REFLECTION_GAIN = "
		<< reflectingWallReflectionGain
		<< ";\n"
		<< "const float REFLECTING_WALL_FRESNEL_STRENGTH = "
		<< reflectingWallFresnelStrength
		<< ";\n\n";

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
