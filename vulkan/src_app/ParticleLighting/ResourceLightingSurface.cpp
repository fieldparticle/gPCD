/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%******************************************************************/
#include "VulkanObj/VulkanApp.hpp"
#include "VulkanObj/ObjLoader.hpp"


#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>

namespace
{
	glm::vec3 SafeNormalize(glm::vec3 value)
	{
		float length = glm::length(value);
		if (length <= 1.0e-6f)
			return glm::vec3(0.0f);
		return value / length;
	}

	struct LightingSurfaceObjectConfig
	{
		std::string objFile;
		std::string meshFile;
		uint32_t surfaceType = BOUNDARY_LIGHT_SURFACE_NONE;
		uint32_t surfaceID = 0u;
		uint32_t materialID = 0u;
		glm::vec4 initialSurfaceColor = glm::vec4(0.0f, 0.0f, 0.0f, 1.0f);
		uint32_t rectangleUSegments = 0u;
		uint32_t rectangleVSegments = 0u;
		uint32_t sphereLatSegments = 0u;
		uint32_t sphereLonSegments = 0u;
	};

	struct LightingSurfaceMeshObject
	{
		std::string surfaceTypeText;
		uint32_t surfaceType = BOUNDARY_LIGHT_SURFACE_NONE;
		uint32_t surfaceID = 0u;
		uint32_t materialID = 0u;
		uint32_t vertexOffset = 0u;
		uint32_t vertexCount = 0u;
		uint32_t indexOffset = 0u;
		uint32_t indexCount = 0u;
		std::vector<uint32_t> indices;
	};

	struct LightingSurfaceMeshSidecar
	{
		uint32_t vertexCount = 0u;
		std::vector<LightingSurfaceMeshObject> objects;
	};

	struct LightingSurfaceObjFaceVertex
	{
		int32_t positionIndex = -1;
		int32_t texCoordIndex = -1;
		int32_t normalIndex = -1;
	};

	struct LightingSurfaceObjRaw
	{
		std::vector<glm::vec3> positions;
		std::vector<glm::vec2> texCoords;
		std::vector<glm::vec3> normals;
		std::vector<glm::vec2> vertexTexCoords;
		std::vector<glm::vec3> vertexNormals;
		std::vector<bool> hasVertexTexCoord;
		std::vector<bool> hasVertexNormal;
	};

	int32_t ResolveObjIndex(
		int32_t objIndex,
		size_t arraySize,
		const std::string& objFile,
		uint32_t lineNumber)
	{
		if (objIndex == 0)
		{
			std::ostringstream errtxt;
			errtxt << objFile << ":" << lineNumber
				<< ": OBJ indices are 1-based; zero is invalid" << std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}

		int64_t resolved = objIndex > 0 ?
			static_cast<int64_t>(objIndex) - 1 :
			static_cast<int64_t>(arraySize) + static_cast<int64_t>(objIndex);
		if (resolved < 0 || resolved >= static_cast<int64_t>(arraySize))
		{
			std::ostringstream errtxt;
			errtxt << objFile << ":" << lineNumber
				<< ": OBJ index " << objIndex << " is outside available data"
				<< std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}
		return static_cast<int32_t>(resolved);
	}

	LightingSurfaceObjFaceVertex ParseObjFaceVertex(
		const std::string& token,
		const LightingSurfaceObjRaw& obj,
		const std::string& objFile,
		uint32_t lineNumber)
	{
		LightingSurfaceObjFaceVertex vertex{};
		std::vector<std::string> fields;
		size_t start = 0u;
		while (start <= token.size())
		{
			size_t slash = token.find('/', start);
			fields.push_back(token.substr(
				start,
				slash == std::string::npos ? std::string::npos : slash - start));
			if (slash == std::string::npos)
				break;
			start = slash + 1u;
		}
		if (fields.empty() || fields[0].empty())
		{
			std::ostringstream errtxt;
			errtxt << objFile << ":" << lineNumber
				<< ": face vertex is missing a position index" << std::ends;
			throw std::runtime_error(errtxt.str().c_str());
		}

		vertex.positionIndex = ResolveObjIndex(
			std::stoi(fields[0]),
			obj.positions.size(),
			objFile,
			lineNumber);
		if (fields.size() > 1u && !fields[1].empty())
		{
			vertex.texCoordIndex = ResolveObjIndex(
				std::stoi(fields[1]),
				obj.texCoords.size(),
				objFile,
				lineNumber);
		}
		if (fields.size() > 2u && !fields[2].empty())
		{
			vertex.normalIndex = ResolveObjIndex(
				std::stoi(fields[2]),
				obj.normals.size(),
				objFile,
				lineNumber);
		}
		return vertex;
	}

	LightingSurfaceObjRaw LoadLightingSurfaceObjRaw(
		const std::string& objFile)
	{
		std::ifstream input(objFile);
		if (!input.is_open())
		{
			throw std::runtime_error("Could not open lighting surface OBJ file " + objFile);
		}

		LightingSurfaceObjRaw obj{};
		std::string line;
		uint32_t lineNumber = 0u;
		while (std::getline(input, line))
		{
			lineNumber++;
			size_t comment = line.find('#');
			if (comment != std::string::npos)
				line = line.substr(0u, comment);

			std::istringstream lineStream(line);
			std::string kind;
			lineStream >> kind;
			if (kind.empty())
				continue;

			if (kind == "v")
			{
				glm::vec3 position(0.0f);
				if (!(lineStream >> position.x >> position.y >> position.z))
				{
					std::ostringstream errtxt;
					errtxt << objFile << ":" << lineNumber
						<< ": malformed vertex position" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}
				obj.positions.push_back(position);
				obj.vertexTexCoords.push_back(glm::vec2(0.0f));
				obj.vertexNormals.push_back(glm::vec3(0.0f));
				obj.hasVertexTexCoord.push_back(false);
				obj.hasVertexNormal.push_back(false);
			}
			else if (kind == "vt")
			{
				glm::vec2 texCoord(0.0f);
				if (!(lineStream >> texCoord.x >> texCoord.y))
				{
					std::ostringstream errtxt;
					errtxt << objFile << ":" << lineNumber
						<< ": malformed texture coordinate" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}
				obj.texCoords.push_back(texCoord);
			}
			else if (kind == "vn")
			{
				glm::vec3 normal(0.0f);
				if (!(lineStream >> normal.x >> normal.y >> normal.z))
				{
					std::ostringstream errtxt;
					errtxt << objFile << ":" << lineNumber
						<< ": malformed vertex normal" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}
				obj.normals.push_back(SafeNormalize(normal));
			}
			else if (kind == "f")
			{
				std::string token;
				std::vector<LightingSurfaceObjFaceVertex> faceVertices;
				while (lineStream >> token)
				{
					faceVertices.push_back(ParseObjFaceVertex(
						token,
						obj,
						objFile,
						lineNumber));
				}
				if (faceVertices.size() < 3u)
				{
					std::ostringstream errtxt;
					errtxt << objFile << ":" << lineNumber
						<< ": face must contain at least three vertices" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}

				for (const LightingSurfaceObjFaceVertex& faceVertex : faceVertices)
				{
					uint32_t positionIndex =
						static_cast<uint32_t>(faceVertex.positionIndex);
					if (faceVertex.texCoordIndex >= 0 &&
						!obj.hasVertexTexCoord[positionIndex])
					{
						obj.vertexTexCoords[positionIndex] =
							obj.texCoords[static_cast<uint32_t>(faceVertex.texCoordIndex)];
						obj.hasVertexTexCoord[positionIndex] = true;
					}
					if (faceVertex.normalIndex >= 0 &&
						!obj.hasVertexNormal[positionIndex])
					{
						obj.vertexNormals[positionIndex] =
							obj.normals[static_cast<uint32_t>(faceVertex.normalIndex)];
						obj.hasVertexNormal[positionIndex] = true;
					}
				}
			}
		}

		if (obj.positions.empty())
			throw std::runtime_error("Lighting surface OBJ file has no vertices: " + objFile);

		return obj;
	}

	uint32_t ReadMeshRequiredUInt(
		config_setting_t* object,
		const std::string& context,
		const char* fieldName,
		bool allowZero = false)
	{
		int value = 0;
		if (config_setting_lookup_int(object, fieldName, &value) != CONFIG_TRUE)
		{
			throw std::runtime_error(context + "." + fieldName + " is required");
		}
		if (value < 0 || (!allowZero && value == 0))
		{
			throw std::runtime_error(
				context + "." + fieldName +
				(allowZero ? " must not be negative" : " must be positive"));
		}
		return static_cast<uint32_t>(value);
	}

	uint32_t MeshSurfaceTypeID(const std::string& surfaceType)
	{
		if (surfaceType == "SPHERE")
			return BOUNDARY_LIGHT_SURFACE_SPHERE;
		if (surfaceType == "RECTANGLE_WALL")
			return BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL;
		if (surfaceType == "NONE")
			return BOUNDARY_LIGHT_SURFACE_NONE;

		throw std::runtime_error("Unknown mesh surface_type: " + surfaceType);
	}

	LightingSurfaceMeshSidecar LoadLightingSurfaceMeshSidecar(
		const std::string& meshFile)
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

		LightingSurfaceMeshSidecar mesh{};
		int vertexCount = 0;
		if (config_lookup_int(&meshConfig, "vertex_count", &vertexCount) != CONFIG_TRUE ||
			vertexCount <= 0)
		{
			config_destroy(&meshConfig);
			throw std::runtime_error(
				"lighting surface mesh vertex_count is required and must be positive");
		}
		mesh.vertexCount = static_cast<uint32_t>(vertexCount);

		config_setting_t* objects = config_lookup(&meshConfig, "objects");
		if (objects == nullptr || config_setting_length(objects) <= 0)
		{
			config_destroy(&meshConfig);
			throw std::runtime_error(
				"lighting surface mesh objects is required and must not be empty");
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

			std::string context =
				"lighting surface mesh objects[" + std::to_string(objectIndex) + "]";
			const char* surfaceTypeText = nullptr;
			if (config_setting_lookup_string(
				object, "surface_type", &surfaceTypeText) != CONFIG_TRUE)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error(context + ".surface_type is required");
			}

			LightingSurfaceMeshObject meshObject{};
			meshObject.surfaceTypeText = surfaceTypeText;
			meshObject.surfaceType = MeshSurfaceTypeID(meshObject.surfaceTypeText);
			meshObject.surfaceID =
				ReadMeshRequiredUInt(object, context, "surface_id");
			meshObject.materialID =
				ReadMeshRequiredUInt(object, context, "material_id", true);
			meshObject.vertexOffset =
				ReadMeshRequiredUInt(object, context, "vertex_offset", true);
			meshObject.vertexCount =
				ReadMeshRequiredUInt(object, context, "vertex_count");
			meshObject.indexOffset =
				ReadMeshRequiredUInt(object, context, "index_offset", true);
			meshObject.indexCount =
				ReadMeshRequiredUInt(object, context, "index_count");

			config_setting_t* indices = config_setting_lookup(object, "indices");
			if (indices == nullptr)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error(context + ".indices is required");
			}
			int triangleCount = config_setting_length(indices);
			if (triangleCount <= 0)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error(context + ".indices must not be empty");
			}
			meshObject.indices.reserve(static_cast<size_t>(triangleCount) * 3u);
			for (int triangleIndex = 0; triangleIndex < triangleCount; ++triangleIndex)
			{
				config_setting_t* triangle =
					config_setting_get_elem(indices, triangleIndex);
				if (triangle == nullptr || config_setting_length(triangle) != 3)
				{
					config_destroy(&meshConfig);
					throw std::runtime_error(
						context + ".indices[" + std::to_string(triangleIndex) +
						"] must contain exactly three vertex indices");
				}
				for (int corner = 0; corner < 3; ++corner)
				{
					int vertexIndex = config_setting_get_int_elem(triangle, corner);
					if (vertexIndex < 0 ||
						static_cast<uint32_t>(vertexIndex) >= mesh.vertexCount)
					{
						config_destroy(&meshConfig);
						throw std::runtime_error(
							context + ".indices[" + std::to_string(triangleIndex) +
							"] contains a vertex index outside vertex_count");
					}
					meshObject.indices.push_back(static_cast<uint32_t>(vertexIndex));
				}
			}
			if (meshObject.indices.size() != meshObject.indexCount)
			{
				config_destroy(&meshConfig);
				throw std::runtime_error(
					context + ".index_count does not match indices length");
			}

			mesh.objects.push_back(meshObject);
		}

		config_destroy(&meshConfig);
		return mesh;
	}

	uint32_t ReadPositiveUInt(
		config_setting_t* object,
		int objectIndex,
		const char* fieldName)
	{
		int value = 0;
		if (config_setting_lookup_int(object, fieldName, &value) != CONFIG_TRUE)
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"]." + fieldName + " is required"
			);
		}
		if (value <= 0)
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"]." + fieldName + " must be a positive integer"
			);
		}
		return static_cast<uint32_t>(value);
	}

	glm::vec4 ReadInitialSurfaceColor(
		config_setting_t* object,
		int objectIndex)
	{
		config_setting_t* initialColor =
			config_setting_lookup(object, "initial_surface_color");
		if (initialColor == nullptr)
			return glm::vec4(0.0f, 0.0f, 0.0f, 1.0f);

		if (config_setting_length(initialColor) != 4)
		{
			throw std::runtime_error(
				"lighting_surface_objects[" + std::to_string(objectIndex) +
				"].initial_surface_color must contain four values"
			);
		}

		glm::vec4 color(0.0f, 0.0f, 0.0f, 1.0f);
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
			color[channel] = static_cast<float>(value);
		}

		return color;
	}
}

void ResourceLightingSurface::Create(uint32_t BindPoint, Resource* particle)
{
	std::ostringstream objtxt;
	std::ostringstream indexObjTxt;

	m_BindPoint = BindPoint;
	m_thisFramesBuffered = 1;
	CreateLayout();
	LoadLightingSurfaceObjects();

	m_NumElements = static_cast<uint64_t>(m_SurfaceIndices.size());
	if (m_SurfaceVertices.empty())
	{
		LightingSurfaceVertex dummy{};
		m_SurfaceVertices.push_back(dummy);
	}
	if (m_SurfaceIndices.empty())
		m_SurfaceIndices.push_back(0u);

	m_BufSize = static_cast<uint64_t>(sizeof(LightingSurfaceVertex)) *
		static_cast<uint64_t>(m_SurfaceVertices.size());
	uint64_t indexBufSize = static_cast<uint64_t>(sizeof(uint32_t)) *
		static_cast<uint64_t>(m_SurfaceIndices.size());
	m_Buffers.resize(2);
	m_BuffersMemory.resize(2);
	m_BuffersMapped.resize(2);
	m_BufferInfo.resize(1);
	m_DescriptorWrite.resize(1);
	m_Allocation.resize(2);

	objtxt << m_Name << " Number:" << 0 << std::ends;
	VkBufferUsageFlags usage =
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_VERTEX_BUFFER_BIT |
		VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;

	m_App->VMACreateDeviceBuffer(
		m_BufSize,
		usage,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[0],
		m_Allocation[0],
		objtxt.str());

	m_BufferInfo[0].buffer = m_Buffers[0];
	m_BufferInfo[0].offset = 0;
	m_BufferInfo[0].range = m_BufSize;

	m_DescriptorWrite[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
	m_DescriptorWrite[0].dstBinding = m_BindPoint;
	m_DescriptorWrite[0].dstArrayElement = 0;
	m_DescriptorWrite[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_DescriptorWrite[0].descriptorCount = 1;
	m_DescriptorWrite[0].pBufferInfo = &m_BufferInfo[0];

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		m_SurfaceVertices.data(),
		m_Allocation[0],
		0,
		m_BufSize);

	indexObjTxt << m_Name << " Index Number:" << 0 << std::ends;
	m_App->VMACreateDeviceBuffer(
		indexBufSize,
		VK_BUFFER_USAGE_TRANSFER_DST_BIT |
		VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
		VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
		m_Buffers[1],
		m_Allocation[1],
		indexObjTxt.str());

	vmaCopyMemoryToAllocation(
		m_App->m_vmaAllocator,
		m_SurfaceIndices.data(),
		m_Allocation[1],
		0,
		indexBufSize);

	m_SurfaceVertices.clear();
	std::vector<LightingSurfaceVertex> empty;
	m_SurfaceVertices.swap(empty);
	m_SurfaceIndices.clear();
	std::vector<uint32_t> emptyIndices;
	m_SurfaceIndices.swap(emptyIndices);
}

void ResourceLightingSurface::CreateLayout()
{
	m_LayoutBinding.resize(1);
	m_LayoutBinding[0].binding = m_BindPoint;
	m_LayoutBinding[0].descriptorCount = 1;
	m_LayoutBinding[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
	m_LayoutBinding[0].pImmutableSamplers = nullptr;
	m_LayoutBinding[0].stageFlags = VK_SHADER_STAGE_ALL;
}

uint32_t ResourceLightingSurface::SurfaceTypeID(const std::string& surfaceType)
{
	if (surfaceType == "SPHERE")
		return BOUNDARY_LIGHT_SURFACE_SPHERE;
	if (surfaceType == "RECTANGLE_WALL")
		return BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL;
	if (surfaceType == "NONE")
		return BOUNDARY_LIGHT_SURFACE_NONE;

	std::ostringstream errtxt;
	errtxt << "Unknown lighting surface_type: " << surfaceType << std::ends;
	throw std::runtime_error(errtxt.str().c_str());
}

void ResourceLightingSurface::AppendSurfaceVertex(
	const glm::vec3& position,
	const glm::vec3& normal,
	const glm::vec2& uv,
	uint32_t surfaceType,
	uint32_t surfaceID,
	uint32_t materialID,
	const glm::vec4& initialSurfaceColor,
	uint32_t& emittedVertexID)
{
	LightingSurfaceVertex vertex{};
	vertex.pos = glm::vec4(position, static_cast<float>(surfaceID));
	vertex.normal_flag = glm::vec4(SafeNormalize(normal), static_cast<float>(materialID));
	vertex.light = initialSurfaceColor;
	vertex.meta = glm::vec4(
		uv.x,
		uv.y,
		static_cast<float>(emittedVertexID),
		static_cast<float>(surfaceType));

	m_SurfaceVertices.push_back(vertex);
	emittedVertexID++;
}

void ResourceLightingSurface::BuildRectangleSurface(
	uint32_t surfaceID,
	uint32_t materialID,
	const glm::vec4& initialSurfaceColor,
	uint32_t rectangleUSegments,
	uint32_t rectangleVSegments,
	uint32_t& emittedVertexID)
{
	int segmentCount = 0;
	config_setting_t* segmentList = nullptr;
	if (CfgTst->CheckKey("rectangle_wall_segments"))
		segmentList = CfgTst->StartStructure("rectangle_wall_segments", segmentCount);

	config_setting_t* selected = nullptr;
	for (int index = 0; segmentList != nullptr && index < segmentCount; ++index)
	{
		config_setting_t* segment = CfgTst->GetSubStructAddress(segmentList, index);
		if (segment == nullptr || config_setting_length(segment) < 15)
			continue;
		uint32_t wallFlag =
			static_cast<uint32_t>(config_setting_get_float_elem(segment, 14));
		if (wallFlag == surfaceID)
		{
			selected = segment;
			break;
		}
	}

	if (selected == nullptr)
	{
		std::ostringstream errtxt;
		errtxt << "No rectangle_wall_segments entry for lighting surface "
			<< surfaceID << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	glm::vec3 origin(
		static_cast<float>(config_setting_get_float_elem(selected, 0)),
		static_cast<float>(config_setting_get_float_elem(selected, 1)),
		static_cast<float>(config_setting_get_float_elem(selected, 2)));
	glm::vec3 uAxis = SafeNormalize(glm::vec3(
		static_cast<float>(config_setting_get_float_elem(selected, 3)),
		static_cast<float>(config_setting_get_float_elem(selected, 4)),
		static_cast<float>(config_setting_get_float_elem(selected, 5))));
	glm::vec3 vAxis = SafeNormalize(glm::vec3(
		static_cast<float>(config_setting_get_float_elem(selected, 6)),
		static_cast<float>(config_setting_get_float_elem(selected, 7)),
		static_cast<float>(config_setting_get_float_elem(selected, 8))));
	float uLength = static_cast<float>(config_setting_get_float_elem(selected, 9));
	float vLength = static_cast<float>(config_setting_get_float_elem(selected, 10));
	glm::vec3 normal = SafeNormalize(glm::vec3(
		static_cast<float>(config_setting_get_float_elem(selected, 11)),
		static_cast<float>(config_setting_get_float_elem(selected, 12)),
		static_cast<float>(config_setting_get_float_elem(selected, 13))));

	uint32_t baseVertex = static_cast<uint32_t>(m_SurfaceVertices.size());
	for (uint32_t uIndex = 0u; uIndex <= rectangleUSegments; ++uIndex)
	{
		float uCoord = uLength * static_cast<float>(uIndex) /
			static_cast<float>(rectangleUSegments);
		for (uint32_t vIndex = 0u; vIndex <= rectangleVSegments; ++vIndex)
		{
			float vCoord = vLength * static_cast<float>(vIndex) /
				static_cast<float>(rectangleVSegments);
			glm::vec3 position = origin + uAxis * uCoord + vAxis * vCoord;
			glm::vec2 uv(
				uLength <= 0.0f ? 0.0f : uCoord / uLength,
				vLength <= 0.0f ? 0.0f : vCoord / vLength);
			AppendSurfaceVertex(
				position,
				normal,
				uv,
				BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL,
				surfaceID,
				materialID,
				initialSurfaceColor,
				emittedVertexID);
		}
	}

	uint32_t rowStride = rectangleVSegments + 1u;
	for (uint32_t uIndex = 0u; uIndex < rectangleUSegments; ++uIndex)
	{
		for (uint32_t vIndex = 0u; vIndex < rectangleVSegments; ++vIndex)
		{
			uint32_t p00 = baseVertex + uIndex * rowStride + vIndex;
			uint32_t p10 = baseVertex + (uIndex + 1u) * rowStride + vIndex;
			uint32_t p11 = baseVertex + (uIndex + 1u) * rowStride + vIndex + 1u;
			uint32_t p01 = baseVertex + uIndex * rowStride + vIndex + 1u;

			m_SurfaceIndices.push_back(p00);
			m_SurfaceIndices.push_back(p10);
			m_SurfaceIndices.push_back(p11);
			m_SurfaceIndices.push_back(p00);
			m_SurfaceIndices.push_back(p11);
			m_SurfaceIndices.push_back(p01);
		}
	}
}

void ResourceLightingSurface::BuildSphereSurface(
	uint32_t surfaceID,
	uint32_t materialID,
	const glm::vec4& initialSurfaceColor,
	uint32_t sphereLatSegments,
	uint32_t sphereLonSegments,
	uint32_t& emittedVertexID)
{
	if (!CfgTst->CheckKey("Lighting_ball"))
		throw std::runtime_error("Lighting_ball is required for sphere lighting surface");

	glm::vec3 center(
		CfgTst->GetFloat("Lighting_ball.x", true),
		CfgTst->GetFloat("Lighting_ball.y", true),
		CfgTst->GetFloat("Lighting_ball.z", true));
	float radius = CfgTst->GetFloat("Lighting_ball.radius", true);
	uint32_t baseVertex = static_cast<uint32_t>(m_SurfaceVertices.size());
	const float pi = 3.14159265358979323846f;

	for (uint32_t ringIndex = 0u; ringIndex <= sphereLatSegments; ++ringIndex)
	{
		float theta = pi * static_cast<float>(ringIndex) /
			static_cast<float>(sphereLatSegments);
		float sinTheta = std::sin(theta);
		float cosTheta = std::cos(theta);
		for (uint32_t segmentIndex = 0u; segmentIndex < sphereLonSegments; ++segmentIndex)
		{
			float phi = 2.0f * pi * static_cast<float>(segmentIndex) /
				static_cast<float>(sphereLonSegments);
			glm::vec3 normal(
				sinTheta * std::cos(phi),
				sinTheta * std::sin(phi),
				cosTheta);
			glm::vec3 position = center + radius * normal;
			glm::vec2 uv(
				static_cast<float>(segmentIndex) / static_cast<float>(sphereLonSegments),
				static_cast<float>(ringIndex) / static_cast<float>(sphereLatSegments));
			AppendSurfaceVertex(
				position,
				normal,
				uv,
				BOUNDARY_LIGHT_SURFACE_SPHERE,
				surfaceID,
				materialID,
				initialSurfaceColor,
				emittedVertexID);
		}
	}

	for (uint32_t ringIndex = 0u; ringIndex < sphereLatSegments; ++ringIndex)
	{
		for (uint32_t segmentIndex = 0u; segmentIndex < sphereLonSegments; ++segmentIndex)
		{
			uint32_t nextSegment = (segmentIndex + 1u) % sphereLonSegments;
			uint32_t p00 = baseVertex + ringIndex * sphereLonSegments + segmentIndex;
			uint32_t p10 = baseVertex + ringIndex * sphereLonSegments + nextSegment;
			uint32_t p01 = baseVertex + (ringIndex + 1u) * sphereLonSegments + segmentIndex;
			uint32_t p11 = baseVertex + (ringIndex + 1u) * sphereLonSegments + nextSegment;

			if (ringIndex == 0u)
			{
				m_SurfaceIndices.push_back(p00);
				m_SurfaceIndices.push_back(p11);
				m_SurfaceIndices.push_back(p01);
			}
			else if (ringIndex + 1u == sphereLatSegments)
			{
				m_SurfaceIndices.push_back(p00);
				m_SurfaceIndices.push_back(p10);
				m_SurfaceIndices.push_back(p01);
			}
			else
			{
				m_SurfaceIndices.push_back(p00);
				m_SurfaceIndices.push_back(p10);
				m_SurfaceIndices.push_back(p11);
				m_SurfaceIndices.push_back(p00);
				m_SurfaceIndices.push_back(p11);
				m_SurfaceIndices.push_back(p01);
			}
		}
	}
}

void ResourceLightingSurface::LoadObjSurface(
	const std::string& objFile,
	const std::string& meshFile,
	uint32_t surfaceType,
	uint32_t surfaceID,
	uint32_t materialID,
	const glm::vec4& initialSurfaceColor,
	uint32_t rectangleUSegments,
	uint32_t rectangleVSegments,
	uint32_t sphereLatSegments,
	uint32_t sphereLonSegments,
	uint32_t& emittedVertexID)
{
	(void)sphereLatSegments;
	(void)sphereLonSegments;

	if (surfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL)
	{
		BuildRectangleSurface(
			surfaceID,
			materialID,
			initialSurfaceColor,
			rectangleUSegments,
			rectangleVSegments,
			emittedVertexID);
		return;
	}

	LightingSurfaceMeshSidecar meshSidecar =
		LoadLightingSurfaceMeshSidecar(meshFile);
	const LightingSurfaceMeshObject* selectedMeshObject = nullptr;
	for (const LightingSurfaceMeshObject& meshObject : meshSidecar.objects)
	{
		if (meshObject.surfaceType == surfaceType &&
			meshObject.surfaceID == surfaceID &&
			meshObject.materialID == materialID)
		{
			selectedMeshObject = &meshObject;
			break;
		}
	}
	if (selectedMeshObject == nullptr)
	{
		std::ostringstream errtxt;
		errtxt << "Mesh file " << meshFile
			<< " has no object matching surface_type " << surfaceType
			<< ", surface_id " << surfaceID
			<< ", material_id " << materialID << std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	LightingSurfaceObjRaw obj = LoadLightingSurfaceObjRaw(objFile);
	if (obj.positions.size() != meshSidecar.vertexCount)
	{
		std::ostringstream errtxt;
		errtxt << "OBJ file " << objFile << " has " << obj.positions.size()
			<< " vertices but mesh file " << meshFile
			<< " declares vertex_count " << meshSidecar.vertexCount
			<< std::ends;
		throw std::runtime_error(errtxt.str().c_str());
	}

	uint32_t baseVertex = static_cast<uint32_t>(m_SurfaceVertices.size());
	for (uint32_t vertexIndex = 0u; vertexIndex < meshSidecar.vertexCount; ++vertexIndex)
	{
		glm::vec3 normal =
			obj.hasVertexNormal[vertexIndex] ?
			obj.vertexNormals[vertexIndex] :
			SafeNormalize(obj.positions[vertexIndex]);
		glm::vec2 uv =
			obj.hasVertexTexCoord[vertexIndex] ?
			obj.vertexTexCoords[vertexIndex] :
			glm::vec2(0.0f);

		AppendSurfaceVertex(
			obj.positions[vertexIndex],
			normal,
			uv,
			surfaceType,
			surfaceID,
			materialID,
			initialSurfaceColor,
			emittedVertexID);
	}

	for (uint32_t index : selectedMeshObject->indices)
	{
		m_SurfaceIndices.push_back(baseVertex + index);
	}
}

void ResourceLightingSurface::LoadLightingSurfaceObjects()
{
	m_SurfaceVertices.clear();
	m_SurfaceIndices.clear();

	int objectCount = 0;
	config_setting_t* objectList = nullptr;
	if (CfgTst->CheckKey("lighting_surface_objects"))
		objectList = CfgTst->StartStructure("lighting_surface_objects", objectCount);

	if (objectList == nullptr || objectCount == 0)
		throw std::runtime_error("lighting_surface_objects is required and must not be empty for ParticleLighting");

	uint32_t emittedVertexID = 0u;

	for (uint32_t pass = 0u; pass < 2u; ++pass)
	{
		for (int index = 0; index < objectCount; ++index)
		{
			config_setting_t* object = CfgTst->GetSubStructAddress(objectList, index);
			if (object == nullptr)
				throw std::runtime_error("lighting_surface_objects contains an invalid object");

			const char* source = nullptr;
			const char* objFile = nullptr;
			const char* meshFile = nullptr;
			const char* surfaceTypeText = nullptr;
			int surfaceID = 0;
			int materialID = 0;

			if (config_setting_lookup_string(object, "source", &source) != CONFIG_TRUE ||
				std::string(source) != "obj")
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].source must be \"obj\"" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_string(object, "obj_file", &objFile) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].obj_file is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_string(object, "surface_type", &surfaceTypeText) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].surface_type is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_int(object, "surface_id", &surfaceID) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].surface_id is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}
			if (config_setting_lookup_int(object, "material_id", &materialID) != CONFIG_TRUE)
			{
				std::ostringstream errtxt;
				errtxt << "lighting_surface_objects[" << index << "].material_id is required" << std::ends;
				throw std::runtime_error(errtxt.str().c_str());
			}

			LightingSurfaceObjectConfig surfaceConfig{};
			surfaceConfig.objFile = objFile;
			uint32_t surfaceType = SurfaceTypeID(surfaceTypeText);
			surfaceConfig.surfaceType = surfaceType;
			surfaceConfig.surfaceID = static_cast<uint32_t>(surfaceID);
			surfaceConfig.materialID = static_cast<uint32_t>(materialID);
			surfaceConfig.initialSurfaceColor =
				ReadInitialSurfaceColor(object, index);
			if (surfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL)
			{
				surfaceConfig.rectangleUSegments =
					ReadPositiveUInt(object, index, "rectangle_u_segments");
				surfaceConfig.rectangleVSegments =
					ReadPositiveUInt(object, index, "rectangle_v_segments");
			}
			if (surfaceType == BOUNDARY_LIGHT_SURFACE_SPHERE)
			{
				if (config_setting_lookup_string(object, "mesh_file", &meshFile) != CONFIG_TRUE)
				{
					std::ostringstream errtxt;
					errtxt << "lighting_surface_objects[" << index
						<< "].mesh_file is required for SPHERE" << std::ends;
					throw std::runtime_error(errtxt.str().c_str());
				}
				surfaceConfig.meshFile = meshFile;
				surfaceConfig.sphereLatSegments =
					ReadPositiveUInt(object, index, "sphere_lat_segments");
				surfaceConfig.sphereLonSegments =
					ReadPositiveUInt(object, index, "sphere_lon_segments");
			}
			bool wallPass = surfaceType == BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL;
			if ((pass == 0u && !wallPass) || (pass == 1u && wallPass))
				continue;

			LoadObjSurface(
				surfaceConfig.objFile,
				surfaceConfig.meshFile,
				surfaceConfig.surfaceType,
				surfaceConfig.surfaceID,
				surfaceConfig.materialID,
				surfaceConfig.initialSurfaceColor,
				surfaceConfig.rectangleUSegments,
				surfaceConfig.rectangleVSegments,
				surfaceConfig.sphereLatSegments,
				surfaceConfig.sphereLonSegments,
				emittedVertexID);
		}
	}
}

VkVertexInputBindingDescription* ResourceLightingSurface::GetBindingDescription()
{
	m_BindingDescription.binding = 0;
	m_BindingDescription.stride = sizeof(LightingSurfaceVertex);
	m_BindingDescription.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
	return &m_BindingDescription;
}

std::vector<VkVertexInputAttributeDescription>* ResourceLightingSurface::GetAttributeDescriptions()
{
	m_AttributeDescriptions.clear();

	VkVertexInputAttributeDescription ad{};
	ad.binding = 0;
	ad.location = 0;
	ad.format = VK_FORMAT_R32G32B32A32_SFLOAT;
	ad.offset = offsetof(LightingSurfaceVertex, pos);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 1;
	ad.offset = offsetof(LightingSurfaceVertex, normal_flag);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 2;
	ad.offset = offsetof(LightingSurfaceVertex, light);
	m_AttributeDescriptions.push_back(ad);

	ad.location = 3;
	ad.offset = offsetof(LightingSurfaceVertex, meta);
	m_AttributeDescriptions.push_back(ad);

	return &m_AttributeDescriptions;
}
