// ============================================================================
// sub_CDNozCharLines Python data-generation configuration
//
// 	Speicifc Chnages:
// reservoir_starting_vx = 0.05; from 0.005 to 0.05
// 
// ============================================================================

// Required: binary particle file consumed by the Python runner.
output_file_prefix 				= "CDNozzle_Vk001";
obj_file_name 					= "C:/_DJ/gPCD/vulkan/sim/CDNozzle/CDNozzle_Vk.obj";

// Required: Python viewer zoom.
zoom							= 5.5;

// ============================================================================


// Required for Python plotter: axis limits for the particle preview.
x_axis_lims 			= [0.0, 470.0];
y_axis_lims 			= [10.0,40.0];
z_axis_lims 			= [0.75,1.25];


// Required: explicit cell counts for the cell-array domain.
cell_array_width 		= 500;
cell_array_height 		= 40;
cell_array_depth 		= 5;

view_center 			= [450, 25, 2];

// Frame when the piston begins moving.
piston_start_frame 		= 20;


//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];

death_bounds 			= [
							1, 498,
							12, 38,
							0, 4
							];
// Required: simulation timestep.
dt								= 0.01;
particle_streams = (
  {
    name 						= "reservoir_substance";
    material_id 				= 3;
    radius 						= 0.15;
    particle_separation_distance = 0.005;
    particle_spacing_x 			= 0.005;
    particle_spacing_y 			= 0.005;
    collision_stiffness_q 		= 16.0;
    compression_stiffness_gain 	= 8.0;
    compression_stiffness_power = 2.0;
    target_penetration_fraction = 0.5;
    hard_penetration_fraction 	= 0.75;
    min_compression_frames 		= 3.0;
    stream_velocity 			= [ 0.1, 0.0, 0.0 ];
  }
);

// 2D packing curves derive x/y packing bounds. Particles live on one Z cell center.
particle_plane_z 			= 1.5;

// Visual-only piston symbol written to the generated .tst for Vulkan display.
piston_visual = {
    enabled 		= true;
    y_min 			= 15.0;
    y_max 			= 35.0;
    head_length 	= 10.0;
    rod_length 		= 10.0;
    rod_height 		= 4.0;
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
        function 						= "y_of_x";
        normal_sign 					= -1;
        wall_flag 						= 3;
		boundary_visual_material_id 	= 6;
		boundary_particle_material_id	= 6;
        segments = {
            wall3 = {
                boundary_kind 	= "reservoir";
                u_start 		= 2;
                length 			= 400;
                f_start 		= 15;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment03 = {
                boundary_kind 	= "regular";
                length 			= 10;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment05 = {
                boundary_kind 	= "regular";
                length 			= 20;
                a1 				= 0.325;
                a2 				= -0.008125;
                a3 				= 0;
            };
            segment07 = {
                boundary_kind 	= "regular";
                length 			= 5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment09 = {
                boundary_kind 	= "regular";
                length 			= 20;
                a1 				= 0;
                a2 				= -0.008125;
                a3 				= 0;
            };
            segment11 = {
                boundary_kind 	= "regular";
                length 			= 10;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
        };
    };
    upper_wall = {
        function 						= "y_of_x";
        normal_sign 					= 1;
        wall_flag 						= 4;
		boundary_visual_material_id 	= 5;
		boundary_particle_material_id	= 5;
        segments = {
            wall4 = {
                boundary_kind = "reservoir";
                u_start 		= 2;
                length 			= 400;
                f_start 		= 35;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment04 = {
                boundary_kind 	= "regular";
                length 			= 10;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment06 = {
                boundary_kind 	= "regular";
                length 			= 20;
                a1 				= -0.325;
                a2			 	= 0.008125;
                a3 				= 0;
            };
            segment08 = {
                boundary_kind 	= "regular";
                length 			= 5;
                a1 				= 0;
                a2 				= 0;
                a3 				= 0;
            };
            segment10 = {
                boundary_kind 	= "regular";
                length 			= 20;
                a1 				= 0;
                a2 				= 0.008125;
                a3 				= 0;
            };
            segment12 = {
                boundary_kind 	= "regular";
                length 			= 10;
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
