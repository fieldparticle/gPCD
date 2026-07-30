// ============================================================================
// LightingBall: Cathedral Lighting
// ============================================================================

scene_model = {
  objects = (
    {
      name			= "lighting_sphere";
      enabled 		= true;
      type 			= "sphere";
      center 		= [20.0, 20.0, 20.0];
      radius 		= 4.0;
      material_id 	= 1;
      surface_id	= 1000;
      initial_surface_color = [1.0, 1.0, 0.0, 1.0];
      roles 		= ["collision", "boundary_markers", "lighting_surface"];
    },
    {
      name 			= "shadow_wall";
      enabled 		= true;
      type 			= "rectangle";
      origin 		= [27.0, 14.0, 14.0];
      u_axis 		= "y";
      u_length 		= 14.0;
      v_axis 		= "z";
      v_length 		= 14.0;
      normal 		= [-1.0, 0.0, 0.0];
      material_id 	= 2;
      surface_id 	= 2000;
      initial_surface_color = [0.0, 0.0, 0.0, 1.0];
      deposit_radius = 0.35;
      roles 		= ["collision", "boundary_markers", "lighting_surface"];
      rectangle_u_segments = 80;
      rectangle_v_segments = 80;
    },
    {
      name 			= "reflecting_wall";
      enabled 		= true;
      type 			= "rectangle";
      origin 		= [13.0, 14.0, 5.0];
      u_axis 		= "x";
      u_length 		= 14.0;
      v_axis 		= "y";
      v_length 		= 14.0;
      normal 		= [0.0, 0.0, 1.0];
      material_id 	= 3;
      surface_id 	= 3000;
      initial_surface_color = [0.0, 0.0, 0.0, 1.0];
      roles 		= ["collision", "boundary_markers", "lighting_surface"];
      rectangle_u_segments = 80;
      rectangle_v_segments = 80;
    }
  );
};

// --------------------------------------------------------------------------
// Domain and view
// --------------------------------------------------------------------------
x_axis_lims 				= [0.0, 20.0];
y_axis_lims 				= [0.0, 20.0];
z_axis_lims 				= [0.0, 22.0];

cell_array_width 			= 40;
cell_array_height 			= 40;
cell_array_depth 			= 40;
// Mobile particles die/recycle before they can drift outside the legal scene.
death_bounds 				= [1, 38, 1, 38, 1, 38];
// Must be large enough for dense photons plus boundary markers in one cell.
cell_occupancy_list_size 	= 256;

// Debug particle point size only. Does not affect surface-light deposit size.
gl_point_size 				= 12.0;

// --------------------------------------------------------------------------
// Photon stream
// --------------------------------------------------------------------------
particle_streams = (
  {
    name 							= "photon_beam";
    enabled 						= true;
    material_id 					= 0;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;

    // Dense x-directed beam centered on the Lighting_ball y/z cross-section.
    // Python profile is intentionally sparse enough to inspect interactively.
    initial_particle_velocity 		= [0.909968, 0.0, 0.0];

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 25;
    spacing_factor 					= 1.00;

    inlet_axis 						= "x";
    inlet_value 					= 15.0;

    span_u_axis 					= "y";
    span_u_min 						= 14.0;
    span_u_max 						= 28.0;
    span_u_count 					= 5;

    span_v_axis 					= "z";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 5;
  },
  {
    name 							= "reflection_beam";
    enabled 						= true;
    material_id 					= 5;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;
    relative_mass 					= 0.25;

    // Reflection test beam starts just above the reflecting_wall and moves
    // toward the sphere. Later it will carry sphere color back to the wall.
    initial_particle_velocity 		= [0.0, 0.0, 0.909968];

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 25;
    spacing_factor 					= 1.00;

    inlet_axis 						= "z";
    inlet_value 					= 6.0;

    span_u_axis 					= "x";
    span_u_min 						= 13.0;
    span_u_max 						= 27.0;
    span_u_count 					= 5;

    span_v_axis 					= "y";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 5;
  },
  {
    name 							= "diffuse_environment";
    enabled 						= true;
    material_id 					= 4;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;
    relative_mass 					= 0.05;

    // Environment-sphere emitters use the magnitude of this velocity. The
    // per-particle direction is generated from the emitter direction mode.
    initial_particle_velocity 		= [0.209968, 0.0, 0.0];

    release_start_frame 			= 16;
    release_columns 				= 1;
    particles_per_wave 				= 10;
    spacing_factor 					= 1.05;

    emitter = {
      type 							= "environment_sphere";
      bounds 						= "death_bounds";
      radius_mode 					= "inscribed";
      bounds_margin 				= 1.0;
      point_count 					= 10;
      direction_mode 				= "diffuse_toward_point";
      target 						= [9.0, 8.0, 14.0];
      angular_jitter_degrees 		= 10.0;
    };
  }
);

// --------------------------------------------------------------------------
// Integration
// --------------------------------------------------------------------------
dt 								= 0.045;

// --------------------------------------------------------------------------
// Output
// --------------------------------------------------------------------------
study 				= false;
num_studies 		= 0;
output_file_prefix 	= "LightingBall_Py";
