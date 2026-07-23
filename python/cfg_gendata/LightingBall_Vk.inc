// ============================================================================
// LightingBall: Cathedral Lighting
// ============================================================================

Lighting_ball = {
    x = 7.0;
    y = 5.0;
    z = 7.0;
    radius = 2.0;
    material_id = 1;
    wall_flag = 1000;
};

// --------------------------------------------------------------------------
// Domain and view
// --------------------------------------------------------------------------
x_axis_lims = [0.0, 20.0];
y_axis_lims = [0.0, 20.0];
z_axis_lims = [0.0, 22.0];

cell_array_width = 20;
cell_array_height = 20;
cell_array_depth = 22;
death_bounds = [1, 19, 1, 19, 1, 21];
cell_occupancy_list_size = 256;

view_center = [3.5, 2.5, 2.5];
zoom = 1.25;
gl_point_size = 2.0;

// --------------------------------------------------------------------------
// Photon stream
// --------------------------------------------------------------------------
particle_streams = (
  {
    name = "photon_beam";
    material_id = 0;

    // Dense x-directed beam centered on the Lighting_ball y/z cross-section.
    initial_particle_velocity = [0.209968, 0.0, 0.0];

    release_start_frame = 10;
    release_columns = 1;
    particles_per_wave = 2025;
    spacing_factor = 1.00;

    inlet_axis = "x";
    inlet_value = 4.9;

    span_u_axis = "y";
    span_u_min = 2.8;
    span_u_max = 7.2;
    span_u_count = 45;

    span_v_axis = "z";
    span_v_min = 4.8;
    span_v_max = 9.2;
    span_v_count = 45;
  }
);

// --------------------------------------------------------------------------
// Boundary markers
// --------------------------------------------------------------------------
curve_wall_segments = {};
rectangle_wall_segments = {};

// --------------------------------------------------------------------------
// Particle geometry and integration
// --------------------------------------------------------------------------
particle_separation_distance = 0.005;
radius = 0.05;
dt = 0.045;

// --------------------------------------------------------------------------
// Output
// --------------------------------------------------------------------------
study = false;
num_studies = 0;
output_file_prefix = "LightingBall_Vk";
