// ============================================================================
// sub_CDNozCharLines Python data-generation configuration
//
// 	Speicifc Chnages:
// reservoir_starting_vx = 0.05; from 0.005 to 0.05
// 
// ============================================================================

// Required: default particle-owned contact stiffness written to Data.y.
collision_stiffness_q = 0.5;

// Required: depth-dependent stiffness shape for current contact dynamics.
compression_stiffness_gain = 8.0;
compression_stiffness_power = 2.0;

// Required: penetration-depth limits for contact compression.
target_penetration_fraction = 0.5;
hard_penetration_fraction = 0.75;

// Required: generation-time compression feasibility threshold.
min_compression_frames = 3.0;

// Required: simulation timestep.
dt= 0.5;

// Required: mobile particle radius used for generation and collision.
radius = 0.25;



// Required: binary particle file consumed by the Python runner.
output_file_prefix = "CDNozzle_Py";

// Temporary upper bound that includes the chamber packing and wall markers.
particle_range = [1,500];

// Required: Python viewer zoom.
zoom= 1.0;

// ============================================================================


// Required for Python plotter: axis limits for the particle preview.
x_axis_lims = [0.0,90.0];
y_axis_lims = [10.0,40.0];
z_axis_lims = [0.75,1.25];

//  Distance between particle perimiters
particle_separation_distance 	= 1.0;

// Required: explicit cell counts for the cell-array domain.
cell_array_width 				= 90;
cell_array_height 				= 40;
cell_array_depth 				= 5;

view_center = [45,25,2];

// Frame when the piston begins moving.
piston_start_frame = 20;


//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];

death_bounds = [
    1, 88,
    12, 38,
    0, 4
];

initial_particle_velocity = [ 0.05, 0.0, 0.0 ];
piston_velocity = [ 0.05, 0.0, 0.0 ];

// 2D packing curves derive x/y packing bounds. Particles live on one Z cell center.
particle_plane_z = 1.5;

// Function wall format:
//   -1 for lower walls where outward is below the conduit
//    1 for upper walls where outward is above the conduit
// Boundary particles are cell-locality sentinels; they are not wall geometry.
curve_wall_segments = {
    wall3 = {
        boundary_kind = "reservoir";
        function = "y_of_x";
        u_start = 2;
        u_end = 30;
        f_start = 15;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4 = {
        boundary_kind = "reservoir";
        function = "y_of_x";
        u_start = 2;
        u_end = 30;
        f_start = 35;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
    wall3_segment03 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 30;
        u_end = 50;
        f_start = 15;
        a1 = 0.25;
        a2 = -0.00625;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4_segment04 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 30;
        u_end = 50;
        f_start = 35;
        a1 = -0.25;
        a2 = 0.00625;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
    wall3_segment05 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 50;
        u_end = 55;
        f_start = 17.5;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4_segment06 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 50;
        u_end = 55;
        f_start = 32.5;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
    wall3_segment07 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 55;
        u_end = 75;
        f_start = 17.5;
        a1 = 0;
        a2 = -0.00625;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4_segment08 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 55;
        u_end = 75;
        f_start = 32.5;
        a1 = 0;
        a2 = 0.00625;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
    wall3_segment09 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 75;
        u_end = 85;
        f_start = 15;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4_segment10 = {
        boundary_kind = "regular";
        function = "y_of_x";
        u_start = 75;
        u_end = 85;
        f_start = 35;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
};

// Required: tells ForceDynamicsBase to load particles from bin_file.
pdata_from_file = true;

// Required: enables or disables study/batch generation mode.
study=false;

// Required when study is true; otherwise kept at zero.
num_studies = 0;

