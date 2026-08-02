// ============================================================================
// LightingBall: Cathedral Lighting
// ============================================================================

scene_model = {
  objects = (
    {
      name 				= "lighting_sphere";
      enabled 			= true;
      type 				= "sphere";
      center 			= [20.0, 20.0, 20.0];
      radius 			= 4.0;
      material_id 		= 1;
      surface_id 		= 1000;
      initial_surface_color = [0.0, 0.0, 0.0, 1.0];
      sphere_lat_segments = 64;
      sphere_lon_segments = 128;
      roles 			= ["collision", "boundary_markers", "lighting_surface"];
	  obj_file = "C:/_DJ/gPCD/vulkan/sim/LightingBall/UFBall.obj";
	  mesh_file = "C:/_DJ/gPCD/vulkan/sim/LightingBall/UFBall.mesh.cfg";
      obj_regions = (
        {
          obj_name = "UF_F";
          material_id = 7;
        },
        {
          obj_name = "UF_U";
          material_id = 7;
        }
      );
    },
    {
      name 					= "shadow_wall";
      enabled 				= true;
      type 					= "rectangle";
      origin 				= [27.0, 14.0, 14.0];
      u_axis 				= "y";
      u_length 				= 14.0;
      v_axis 				= "z";
      v_length 				= 14.0;
      normal 				= [-1.0, 0.0, 0.0];
      material_id 			= 2;
      surface_id 			= 2000;
      initial_surface_color 	= [0.0, 0.0, 0.0, 1.0];
      deposit_radius 		= 0.65;
      roles 				= ["collision", "boundary_markers", "lighting_surface"];
      rectangle_u_segments 	= 80;
      rectangle_v_segments 	= 80;
    },
    {
      name 					= "reflecting_wall";
      enabled 				= true;
      type 					= "rectangle";
      origin 				= [13.0, 14.0, 5.0];
      u_axis 				= "x";
      u_length 				= 14.0;
      v_axis 				= "y";
      v_length 				= 14.0;
      normal 				= [0.0, 0.0, 1.0];
      material_id 			= 3;
      surface_id 			= 3000;
      initial_surface_color = [0.0, 0.0, 0.0, 1.0];
	  deposit_radius 		= 0.5;
      roles 				= ["collision", "boundary_markers", "lighting_surface"];
      rectangle_u_segments 	= 10;
      rectangle_v_segments 	= 10;
    }
  );

};

reflecting_wall_light_map = {
  enabled = true;
  surface_id = 3000;
  width = 64;
  height = 64;
};

sphere_decal_bucket_search_radius = 2;

// --------------------------------------------------------------------------
// Domain and view
// --------------------------------------------------------------------------
x_axis_lims 				= [0.0, 40.0];
y_axis_lims 				= [0.0, 40.0];
z_axis_lims 				= [0.0, 42.0];

cell_array_width 			= 40;
cell_array_height 			= 40;
cell_array_depth 			= 40;
// Mobile particles die/recycle before they can drift outside the legal scene.
death_bounds 				= [1, 38, 1, 38, 1, 38];
// Must be large enough for dense photons plus boundary markers in one cell.
cell_occupancy_list_size 	= 404;

// Debug particle point size only. Does not affect surface-light deposit size.
gl_point_size 				= 1.5;

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

    // Dense x-directed beam matched to the shadow_wall y/z face.
    // Vulkan profile is dense: 80 x 80 = 6400 photons per wave.
    initial_particle_velocity 		= [0.5, 0.0, 0.0];
	

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 25600;
    spacing_factor 					= 1.05;

    inlet_axis 						= "x";
    inlet_value 					= 15.0;

    span_u_axis 					= "y";
    span_u_min 						= 14.0;
    span_u_max 						= 28.0;
    span_u_count 					= 160;

    span_v_axis 					= "z";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 160;
  },
  {
    name 							= "diffuse_beam_sphere";
    enabled 						= true;
    material_id 					= 6;
    radius 							= 0.015;
    particle_separation_distance 	= 0.005;
	relative_mass 					= 0.025;
    // Dense x-directed beam matched to the shadow_wall y/z face.
    // Vulkan profile is dense: 80 x 80 = 6400 photons per wave.
    initial_particle_velocity 		= [-0.5, 0.0, 0.0];

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 8100;
    spacing_factor 					= 1.05;

    inlet_axis 						= "x";
    inlet_value 					= 24.0;

    span_u_axis 					= "y";
    span_u_min 						= 14.0;
    span_u_max 						= 28.0;
    span_u_count 					= 90;

    span_v_axis 					= "z";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 90;
  },
  {
    name 							= "diffuse_beam_wall";
    enabled 						= true;
    material_id 					= 4;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;
	relative_mass 					= 0.25;
    // Dense x-directed beam matched to the shadow_wall y/z face.
    // Vulkan profile is dense: 80 x 80 = 6400 photons per wave.
    initial_particle_velocity 		= [0.5, 0.0, 0.0];

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 8100;
    spacing_factor 					= 1.05;

    inlet_axis 						= "x";
    inlet_value 					= 26.0;

    span_u_axis 					= "y";
    span_u_min 						= 14.0;
    span_u_max 						= 28.0;
    span_u_count 					= 90;

    span_v_axis 					= "z";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 90;
  },
  {
    name 							= "reflection_beam";
    enabled 						= true;
    material_id 					= 5;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;
	relative_mass 					= 1.0;

    // Reflection test beam starts just above the reflecting_wall and moves
    // toward the sphere. Later it will carry sphere color back to the wall.
    initial_particle_velocity 		= [0.0, 0.0, 0.5];

    release_start_frame 			= 10;
    release_columns 				= 1;
    particles_per_wave 				= 25600;
    spacing_factor 					= 1.05;

    inlet_axis 						= "z";
    inlet_value 					= 6.0;

    span_u_axis 					= "x";
    span_u_min 						= 13.0;
    span_u_max 						= 27.0;
    span_u_count 					= 160;

    span_v_axis 					= "y";
    span_v_min 						= 14.0;
    span_v_max 						= 28.0;
    span_v_count 					= 160;
  },
  {
    name 							= "diffuse_environment";
    enabled 						= false;
    material_id 					= 4;
    radius 							= 0.025;
    particle_separation_distance 	= 0.005;
    relative_mass 					= 0.05;

    // Environment-sphere emitters use the magnitude of this velocity. The
    // per-particle direction is generated from the emitter direction mode.
    initial_particle_velocity 		= [0.5, 0.0, 0.0];

    release_start_frame 			= 16;
    release_columns 				= 1;
    particles_per_wave 				= 6400;
    spacing_factor 					= 1.05;

    emitter = {
      type 							= "environment_sphere";
      bounds 						= "death_bounds";
      radius_mode 					= "inscribed";
      bounds_margin 				= 1.0;
      point_count 					= 6400;
      direction_mode 				= "diffuse_toward_point";
      target 						= [20.0, 20.0, 20.0];
      angular_jitter_degrees 		= 10.0;
    };
  }
);

// --------------------------------------------------------------------------
// Integration
// --------------------------------------------------------------------------
dt 								= 0.05;

// --------------------------------------------------------------------------
// Output
// --------------------------------------------------------------------------
study 				= false;
num_studies 		= 0;
output_file_prefix 	= "LightingBall_Vk";
