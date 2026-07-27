
/*******************************************************************
%***      C PROPRIETARY SOURCE FILE IDENTIFICATION               ***
%*******************************************************************
% $Author: jb $
%
% $Date: 2023-05-03 15:30:42 -0400 (Wed, 03 May 2023) $
% $HeadURL: https://jbworkstation/svn/svnrootr5/svnvulcan/src/vulkan/DescriptorSSBO.hpp $
% $Id: DescriptorSSBO.hpp 28 2023-05-03 19:30:42Z jb $
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


#ifndef LIGHTINGRECORDS_HPP
#define LIGHTINGRECORDS_HPP

constexpr uint32_t BOUNDARY_LIGHT_SURFACE_NONE = 0u;
constexpr uint32_t BOUNDARY_LIGHT_SURFACE_SPHERE = 1u;
constexpr uint32_t BOUNDARY_LIGHT_SURFACE_RECTANGLE_WALL = 2u;

struct BoundaryLightRecord
{
    alignas(16) glm::vec4 rgb_valid;
    // xyz = persistent boundary-space light RGB
    // w   = valid flag

    alignas(16) glm::vec4 normal_material;
    // xyz = normal
    // w   = material_id as float

    alignas(16) glm::uvec4 ids;
    // x = particle_id
    // y = surface_type
    // z = surface_id / wall_flag
    // w = reserved

};
#endif
