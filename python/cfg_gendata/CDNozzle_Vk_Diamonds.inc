// ============================================================================
// sub_CDNozCharLines Python data-generation configuration
//
// 	Speicifc Chnages:
// reservoir_starting_vx = 0.05; from 0.005 to 0.05
// 
// ============================================================================

// Required: simulation timestep.
dt								= 0.5;

// Required: binary particle file consumed by the Python runner.
output_file_prefix 				= "CDNozzle_Vk";
obj_file_name 					= "C:/_DJ/gPCD/vulkan/sim/CDNozzle/CDNozzle_Vk.obj";

// Required: Python viewer zoom.
zoom							= 15.2;

// ============================================================================


// Required for Python plotter: axis limits for the particle preview.
x_axis_lims 			= [0.0, 1175.0];
y_axis_lims 			= [25.0,100.0];
z_axis_lims 			= [0.75,1.25];


// Required: explicit cell counts for the cell-array domain.
cell_array_width 		= 1250;
cell_array_height 		= 100;
cell_array_depth 		= 5;

view_center 			= [1100, 62.5, 2];

// Frame when the piston begins moving.
piston_start_frame 		= 20;


//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];

death_bounds 			= [
							2.5, 1245,
							30, 95,
							0, 4
							];

// Optional: Vulkan clear/background color for generated scene review.
//clear_color = {red = 1.0; green = 1.0; blue = 1.0; alpha = 1.0;};
clear_color = {red = 0.0; green = 0.0; blue = 0.0; alpha = 1.0;};
particle_streams = (
  {
    name 						= "reservoir_substance";
	//ollisoins
    //material_id 				= 1;
	// HSV
	material_id 				= 3;
	//IA
	//material_id 				= 4;
    radius 						= 0.15;
    particle_separation_distance = 0.5;
    particle_spacing_x 			= 0.5;
    particle_spacing_y 			= 0.5;
    collision_stiffness_q 		= 16.0;
    compression_stiffness_gain 	= 8.0;
    compression_stiffness_power = 2.0;
    target_penetration_fraction = 0.5;
    hard_penetration_fraction 	= 0.75;
    min_compression_frames 		= 3.0;
    stream_velocity 			= [ 0.02, 0.0, 0.0 ];
    // Type: "directional" relaxes velocity toward temp_velocity.xyz.
    //temp_vel_type = "directional";
	temp_vel_type = "none";
    temp_velocity = [0.1, 0.0, 0.0, 0.0];
    temp_vel_rate = 0.00001;

  }
);

// 2D packing curves derive x/y packing bounds. Particles live on one Z cell center.
particle_plane_z 			= 1.5;

// Visual-only piston symbol written to the generated .tst for Vulkan display.
piston_visual = {
    enabled 		= true;
    y_min 			= 37.5;
    y_max 			= 87.5;
    head_length 	= 25.0;
    rod_length 		= 25.0;
    rod_height 		= 10.0;
    z 				= 1.5;
    head_color 		= {red = 0.0; green = 0.8; blue = 1.0; alpha = 1.0;};
    rod_color 		= {red = 0.0; green = 0.45; blue = 0.7; alpha = 1.0;};
};

// Function wall format:
//   -1 for lower walls where outward is below the conduit
//    1 for upper walls where outward is above the conduit
// Grouped curves inherit function, normal_sign, wall_flag,
// boundary_visual_material_id, and boundary_particle_material_id.
// The first segment in each curve needs u_start, f_start, and length.
// Later segments continue from the previous segment and only need length.
// Boundary particles are cell-locality sentinels; they are not wall geometry.
curve_wall_segments = {
    lower_wall = {
        function 							= "y_of_x";
        normal_sign 						= -1;
        wall_flag 							= 3;
		wall_collision_stiffness_q 			= 0.05;
		wall_target_penetration_fraction 	= 0.10; wall_hard_penetration_fraction 		= 0.19;
		wall_compression_stiffness_gain 	= 5.0;
		wall_compression_stiffness_power 	= 16.0;
        segments = {
            wall3 = {
                boundary_kind 	= "reservoir";
                u_start 		= 5;
                length 			= 1000;
                f_start 		= 37.5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment03 = {
                boundary_kind 	= "regular";
                length 			= 5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment05 = {
                boundary_kind 	= "regular";
                length 			= 125;
                a1 				= 0;
                a2 				= 0.0012;
                a3 				= -0.0000064;
            };
            segment07 = {
                boundary_kind 	= "regular";
                length 			= 12.5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment09 = {
                boundary_kind 	= "regular";
                length 			= 50;
                a1 				= 0;
                a2 				= -0.0025;
                a3 				= 0;
            };
            segment11 = {
                boundary_kind 	= "regular";
                length 			= 25;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
        };
    };
    upper_wall = {
        function 		= "y_of_x";
        normal_sign 	= 1;
        wall_flag 		= 4;
        wall_collision_stiffness_q = 4.0;
        wall_target_penetration_fraction = 0.35;
        wall_hard_penetration_fraction = 0.55;
        wall_compression_stiffness_gain = 8.0;
        wall_compression_stiffness_power = 2.0;
        segments = {
            wall4 = {
                boundary_kind = "reservoir";
                u_start 		= 5;
                length 			= 1000;
                f_start 		= 87.5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment04 = {
                boundary_kind 	= "regular";
                length 			= 5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment06 = {
                boundary_kind 	= "regular";
                length 			= 125;
                a1 				= 0;
                a2			 	= -0.0012;
                a3 				= 0.0000064;
            };
            segment08 = {
                boundary_kind 	= "regular";
                length 			= 12.5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment10 = {
                boundary_kind 	= "regular";
                length 			= 50;
                a1 				= 0;
                a2 				= 0.0025;
                a3 				= 0;
            };
            segment12 = {
                boundary_kind 	= "regular";
                length 			= 25;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
        };
    };
};

// Required: tells ForceDynamicsBase to load particles from bin_file.
pdata_from_file 		= true;



// Required when study is true; otherwise kept at zero.
num_studies 			= 0;

// LIVE: material table. Particles default to material_id 0 unless explicitly tagged.
material_properties = (
  {
    material_id 		= 0;
    name 				= "substance";
    relative_mass 		= 1.0;
    thermal_velocity 	= 0.0;
    color_mode 			= "VELOCITY_ANGLE";
    color_map 			= "HSV";
    point_size 			= 1.5;
    cell_density 		= 0.0;
  },
  {
    material_id 		= 1;
    name 				= "collision substance";
    relative_mass 		= 1.0;
    thermal_velocity 	= 0.0;
    color_mode 			= "COLLISION";
    color_map 			= "SOLID";
    collision_color 	= [1.0, 0.0, 0.0, 1.0];
    non_collision_color = [0.0, 1.0, 0.0, 1.0];
    point_size 			= 3.0;
    cell_density 		= 0.0;
  },
  {
    material_id 		= 3;
    name 				= "substance_color_lim";
    relative_mass 		= 1.0;
    thermal_velocity 	= 0.0;
    color_mode 			= "VELOCITY_ANGLE";
    color_map 			= "HSV";
    point_size 			= 3.0;
    cell_density 		= 0.0;
	//capture_angle0 		= [0.0, 2.0, 2.0];

  },
  {
    material_id 		= 4;
    name 				= "substance_internal_energy";
    relative_mass 		= 1.0;
    thermal_velocity 	= 0.0;
    color_mode 			= "INTERNAL_MOMENTUM";
    color_map 			= "GRAY_LINEAR";
	start_mom			= 0.0;
	end_mom				= 0.1;
    point_size 			= 3.0;
    cell_density 		= 0.0;

  },
  {
    // Boundary particles are cell-locality sentinels only. Analytic wall
    // segments own the boundary geometry and collision behavior.
    material_id 				= 5;
    name 						= "boundary sentinel";
    particle_type 				= "BOUNDARY";
    relative_mass 				= 1.0;
    thermal_velocity 			= 0.0;
    color_mode 					= "SOLID";
    color_map 					= "SOLID";
    color 						= [0.0, 0.0, 0.0, 1.0];
    point_size 					= 1.0;
    cell_density 				= 0.0;
    debug_visible 				= false;
    debug_color 				= [0.0, 1.0, 0.0, 1.0];
  },
{
    // Boundary particles are cell-locality sentinels only. Analytic wall
    // segments own the boundary geometry and collision behavior.
    material_id 				= 6;
    name 						= "boundary sentinel";
    particle_type 				= "BOUNDARY";
    relative_mass 				= 1.0;
    thermal_velocity 			= 0.0;
    color_mode 					= "SOLID";
    color_map 					= "SOLID";
    color 						= [1.0, 1.0, 1.0, 1.0];
    point_size 					= 1.0;
    cell_density 				= 0.0;
    debug_visible 				= false;
    debug_color 				= [0.0, 1.0, 0.0, 1.0];
  }
);
