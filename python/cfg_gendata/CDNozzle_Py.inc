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
    // Reservoir/chamber packing walls, x=2 through x=30.
    // The reservoir connects directly to the converging curve; there is no
    // separate constant-radius inlet pipe ahead of the nozzle.
    [1, 0, 2, 30, 15, 0, 0, 0, -1, 3],
    [1, 0, 2, 30, 35, 0, 0, 0,  1, 4],

    // Quadratic convergence, x=30 through x=50.
    [0, 0, 30, 50, 15,  0.25, -0.00625, 0, -1, 3],
    [0, 0, 30, 50, 35, -0.25,  0.00625, 0,  1, 4],

    // Constant-radius throat, x=50 through x=55.
    [0, 0, 50, 55, 17.5, 0, 0, 0, -1, 3],
    [0, 0, 50, 55, 32.5, 0, 0, 0,  1, 4],

    // Quadratic divergence, x=55 through x=75.
    [0, 0, 55, 75, 17.5, 0, -0.00625, 0, -1, 3],
    [0, 0, 55, 75, 32.5, 0,  0.00625, 0,  1, 4],

    // Constant-radius exit, x=75 through x=85.
    [0, 0, 75, 85, 15, 0, 0, 0, -1, 3],
    [0, 0, 75, 85, 35, 0, 0, 0,  1, 4]
);

// Required: tells ForceDynamicsBase to load particles from bin_file.
pdata_from_file = true;

// Required: enables or disables study/batch generation mode.
study=false;

// Required when study is true; otherwise kept at zero.
num_studies = 0;

