
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

struct BoundaryLightRecord
{
    alignas(16) glm::vec4 pos_area;
    // xyz = boundary sample position
    // w   = sample area/weight

    alignas(16) glm::vec4 normal_material;
    // xyz = normal
    // w   = material_id as float

    alignas(16) glm::uvec4 ids;
    // x = sample_id
    // y = particle_id
    // z = surface_type
    // w = surface_id / wall_flag

    alignas(16) glm::vec4 current;
    // xyz = current-frame deposited RGB
    // w   = hit_count or debug

    alignas(16) glm::vec4 filtered;
    // xyz = filtered RGB for rendering
    // w   = flags/reserved
};
#endif