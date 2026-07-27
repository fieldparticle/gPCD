// ============================================================================
// LightingBall: Cathedral Lighting
// ============================================================================

Lighting_ball = {
    // Analytic sphere surface. Boundary particles are locality markers only.
    x = 9.0;
    y = 8.0;
    z = 14.0;
    radius = 4.0;
    material_id = 1;
    wall_flag = 1000;
};

// Enables persistent boundary-space lighting. Retired boundary_space_patch_*
// keys must not be used; lighting is now cell-owned.
boundary_space_lighting_enabled 	= true;
// Wall surface mesh density for later per-vertex wall lighting.
// triangles_per_cell = subdivisions_per_cell * subdivisions_per_cell * 2.
boundary_light_wall_subdivisions_per_cell = 1;

// --------------------------------------------------------------------------
// Domain and view
// --------------------------------------------------------------------------
x_axis_lims 				= [0.0, 20.0];
y_axis_lims 				= [0.0, 20.0];
z_axis_lims 				= [0.0, 22.0];

cell_array_width 			= 20;
cell_array_height 			= 20;
cell_array_depth 			= 22;
// Mobile particles die/recycle before they can drift outside the legal scene.
death_bounds 				= [1, 19, 1, 19, 1, 21];
// Must be large enough for dense photons plus boundary markers in one cell.
cell_occupancy_list_size 	= 256;

// Debug particle point size only. Does not affect surface-light deposit size.
gl_point_size 				= 1.5;

// --------------------------------------------------------------------------
// Photon stream
// --------------------------------------------------------------------------
particle_streams = (
  {
    name = "photon_beam";
    material_id = 0;

    // Dense x-directed beam centered on the Lighting_ball y/z cross-section.
    // Vulkan profile is dense: 80 x 80 = 6400 photons per wave.
    initial_particle_velocity = [0.209968, 0.0, 0.0];

    release_start_frame = 10;
    release_columns = 1;
    particles_per_wave = 6400;
    spacing_factor = 0.5;

    inlet_axis = "x";
    inlet_value = 4.0;

    span_u_axis = "y";
    span_u_min = 4.0;
    span_u_max = 12.0;
    span_u_count = 80;

    span_v_axis = "z";
    span_v_min = 10.0;
    span_v_max = 18.0;
    span_v_count = 80;
  }
);

// --------------------------------------------------------------------------
// Boundary markers
// --------------------------------------------------------------------------
// Rectangle walls are active here; empty curve_wall_segments is intentional.
curve_wall_segments = {};
rectangle_wall_segments = {
    wall_xmax = {
        // 14 x 14 rectangle on x=16, spanning y=2..16 and z=2..16.
        origin = [16.0, 2.0, 2.0];
        u_axis = "y";
        u_length = 14.0;
        v_axis = "z";
        v_length = 14.0;
        // Normal points inward, toward the photon stream and sphere.
        normal = [-1.0, 0.0, 0.0];
        wall_flag = 2000;
        // material_id 2 is shadow_wall in LightingBall.cfg.
        material_id = 2;
    };
};

// --------------------------------------------------------------------------
// Particle geometry and integration
// --------------------------------------------------------------------------
particle_separation_distance 	= 0.005;
radius 							= 0.05;
dt 								= 0.045;

// --------------------------------------------------------------------------
// Output
// --------------------------------------------------------------------------
study 				= false;
num_studies 		= 0;
output_file_prefix 	= "LightingBall_Vk";
