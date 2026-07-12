// ============================================================================
// sub_CDNozCharLines Python data-generation configuration
//
// 	Speicifc Chnages:
// reservoir_starting_vx = 0.05; from 0.005 to 0.05
// 
// ============================================================================

// Required: default particle-owned contact stiffness written to Data.y.
collision_stiffness_q 			= 16.0;

// Required: depth-dependent stiffness shape for current contact dynamics.
compression_stiffness_gain 	= 8.0;
compression_stiffness_power 	= 2.0;

// Required: penetration-depth limits for contact compression.
target_penetration_fraction 	= 0.5;
hard_penetration_fraction 		= 0.75;

// Required: generation-time compression feasibility threshold.
min_compression_frames 			= 3.0;

// Required: simulation timestep.
dt								= 0.025;

// Required: mobile particle radius used for generation and collision.
radius 							= 0.15;
//  Distance between particle perimiters
particle_separation_distance 	= 0.0005;


// Required: binary particle file consumed by the Python runner.
output_file_prefix 				= "CDNozzle_Vk";

// Temporary upper bound that includes the chamber packing and wall markers.
particle_range 					= [1,500];

// Required: Python viewer zoom.
zoom							= 1.5;

// ============================================================================


// Required for Python plotter: axis limits for the particle preview.
x_axis_lims 			= [0.0, 170.0];
y_axis_lims 			= [10.0,40.0];
z_axis_lims 			= [0.75,1.25];


// Required: explicit cell counts for the cell-array domain.
cell_array_width 		= 200;
cell_array_height 		= 40;
cell_array_depth 		= 5;

view_center 			= [150, 25, 2];

// Frame when the piston begins moving.
piston_start_frame 		= 20;


//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];

death_bounds 			= [
							1, 198,
							12, 38,
							0, 4
							];

initial_particle_velocity 	= [ 0.5, 0.0, 0.0 ];
piston_velocity 			= [ 0.5, 0.0, 0.0 ];

// 2D packing curves derive x/y packing bounds. Z is configured separately.
packing_z_bounds 			= [0, 3];

// Function wall format:
// [boundary_kind, independent_axis, u_start, u_end,
//  f_start, a1, a2, a3, normal_sign, wall_flag]
// boundary_kind: 0 = regular collision boundary, 1 = reservoir packing boundary
// independent_axis: 0 = y=f(x), 1 = x=f(y)
// f(u) = f_start + a1*du + a2*du^2 + a3*du^3, du = u - u_start
// normal_sign selects the outward normal from the local slope:
//   -1 for lower walls where outward is below the conduit
//    1 for upper walls where outward is above the conduit
// wall_flag is the physical wall identity used for contact diagnostics.
// Boundary particles are cell-locality sentinels; they are not wall geometry.
curve_wall_segments = (
    // Chamber: x=2 through x=102
    [1, 0,   2, 102, 15,  0,        0,        0, -1, 3],
    [1, 0,   2, 102, 35,  0,        0,        0,  1, 4],

    // Inlet: x=102 through x=112
    [0, 0, 102, 112, 15,  0,        0,        0, -1, 3],
    [0, 0, 102, 112, 35,  0,        0,        0,  1, 4],

    // Convergence: x=112 through x=132
    [0, 0, 112, 132, 15,  0.25,    -0.00625, 0, -1, 3],
    [0, 0, 112, 132, 35, -0.25,     0.00625, 0,  1, 4],

    // Throat: x=132 through x=137
    [0, 0, 132, 137, 17.5, 0,        0,        0, -1, 3],
    [0, 0, 132, 137, 32.5, 0,        0,        0,  1, 4],

    // Divergence: x=137 through x=157
    [0, 0, 137, 157, 17.5, 0,       -0.00625, 0, -1, 3],
    [0, 0, 137, 157, 32.5, 0,        0.00625, 0,  1, 4],

    // Exit: x=157 through x=167
    [0, 0, 157, 167, 15,  0,        0,        0, -1, 3],
    [0, 0, 157, 167, 35,  0,        0,        0,  1, 4]
);

// Required: tells ForceDynamicsBase to load particles from bin_file.
pdata_from_file 		= true;

// Required: enables or disables study/batch generation mode.
study					= false;

// Required when study is true; otherwise kept at zero.
num_studies 			= 0;

