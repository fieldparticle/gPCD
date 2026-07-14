// ============================================================================
// BoundaryParticleReservoirHorizontal: reduced Python profile
// ============================================================================

// --------------------------------------------------------------------------
// Shared preview and Python game-camera bounds
// --------------------------------------------------------------------------
// PlotParticles uses all three axis ranges. SimulationRunner uses the x and y
// ranges first and falls back to legacy Wall* values only when these are absent.
// SimulationRunner then applies zoom around each axis-range center.
x_axis_lims 					= [-2.0,20.0];
y_axis_lims 					= [0.0,10.0];
z_axis_lims 					= [0.0,3.0];

//  Distance between particle perimiters
particle_separation_distance 	= 0.005;
// Required: explicit cell counts for the cell-array domain.
cell_array_width 				= 33;
cell_array_height 				= 13;
cell_array_depth 				= 5;

view_center 					= [ 15,4,2];

// Frame when the piston begins moving.
piston_start_frame 				= 20;

// Offset the piston upstream of the packed reservoir start.
piston_start_offset 			= 0.02;


//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];
// Required: cell occupancy list capacity written to the .tst file.
cell_occupancy_list_size		= 64;

death_bounds 					= [1, 30,1, 9,0, 4];

initial_particle_velocity 		= [ 0.0, 0.0, 0.0 ];
piston_velocity 				= [ 0.005, 0.0, 0.0 ];

// 2D packing curves derive x/y packing bounds. Particles live on one Z cell center.
particle_plane_z 				= 1.5;
// Function wall format:
// boundary particles are cell-locality sentinels; they are not wall geometry.
curve_wall_segments = {
    wall3 = {
        boundary_kind = "reservoir";
        function = "y_of_x";
        u_start = 2;
        u_end = 2.23;
        f_start = 2;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = -1;
        wall_flag = 3;
    };
    wall4 = {
        boundary_kind = "reservoir";
        function = "y_of_x";
        u_start = 2.23;
        u_end = 2;
        f_start = 8;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 4;
    };
    wall2 = {
        boundary_kind = "regular";
        function = "x_of_y";
        u_start = 2;
        u_end = 8;
        f_start = 2.23;
        a1 = 0;
        a2 = 0;
        a3 = 0;
        normal_sign = 1;
        wall_flag = 2;
    };
};


// --------------------------------------------------------------------------
// Particle geometry and integration
// --------------------------------------------------------------------------
radius 					= 0.05;

// Simulation timestep used by both dynamics integration and wave-frame spacing.
dt 						= 0.045;

// --------------------------------------------------------------------------
// Front-end study and output selection
// --------------------------------------------------------------------------
// Normal single-run mode. When study is true, TabFormGenData iterates
// num_studies and creates a separate inline study run for each index.
study 					= false;
num_studies 			= 0;

output_file_prefix 		= "TestCompressorPy";
