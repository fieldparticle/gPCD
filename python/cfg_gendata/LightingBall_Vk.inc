// ============================================================================
// LightingBall: Cathedral Lighting
// ============================================================================

scene_model = {
  objects = (
    {
      name = "lighting_sphere";
      type = "sphere";
      center = [9.0, 8.0, 10.0];
      radius = 4.0;
      material_id = 1;
      surface_id = 1000;
      roles = ["collision", "boundary_markers", "lighting_surface"];
    },
    {
      name = "shadow_wall";
      type = "rectangle";
      origin = [16.0, 2.0, 2.0];
      u_axis = "y";
      u_length = 14.0;
      v_axis = "z";
      v_length = 14.0;
      normal = [-1.0, 0.0, 0.0];
      material_id = 2;
      surface_id = 2000;
      roles = ["collision", "boundary_markers", "lighting_surface"];
      rectangle_u_segments = 80;
      rectangle_v_segments = 80;
    }
  );
};

// Enables persistent boundary-space lighting. Retired boundary_space_patch_*
// keys must not be used; lighting is now cell-owned.
boundary_space_lighting_enabled 	= true;

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

    // Dense x-directed beam matched to the shadow_wall y/z face.
    // Vulkan profile is dense: 80 x 80 = 6400 photons per wave.
    initial_particle_velocity = [0.209968, 0.0, 0.0];

    release_start_frame = 10;
    release_columns = 1;
    particles_per_wave = 6400;
    spacing_factor = 0.5;

    inlet_axis = "x";
    inlet_value = 4.0;

    span_u_axis = "y";
    span_u_min = 2.0;
    span_u_max = 16.0;
    span_u_count = 80;

    span_v_axis = "z";
    span_v_min = 2.0;
    span_v_max = 16.0;
    span_v_count = 80;
  }
);

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
