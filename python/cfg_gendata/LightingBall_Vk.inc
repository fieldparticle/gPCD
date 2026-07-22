// ============================================================================
// LightingBall: Catherdral Lighting
// ============================================================================
//
Lighting_ball = {
	x = 7.0;
	y = 5.0;
	z = 7.0;
	radius = 2.0;
	material_id = 1;
	wall_flag = 1000;
};
// --------------------------------------------------------------------------
// Shared preview and Python game-camera bounds
// --------------------------------------------------------------------------
// PlotParticles uses all three axis ranges. SimulationRunner uses the x and y
// ranges first and falls back to legacy Wall* values only when these are absent.
// SimulationRunner then applies zoom around each axis-range center.
x_axis_lims 					= [0.0,20.0];
y_axis_lims 					= [0.0,20.0];
z_axis_lims 					= [0.0,22.0];

//  Distance between particle perimiters
particle_separation_distance 	= 0.005;
// Required: explicit cell counts for the cell-array domain.
cell_array_width 				= 20;
cell_array_height 				= 20;
cell_array_depth 				= 22;


view_center 					= [ 10.5,10.5,12.5];
zoom							= .75;
align_with_eye					= true;
eye_view_distance 				= 30.0;
lighting_eye_position 			= [2.5, 7.0, 8.0];
lighting_eye_direction 			= [0.810026, -0.424246, -0.404812];
//lighting_eye_target   		= [5.1259, 5.6247, 4.6877];
//lighting_eye_angle_degrees 	= 45.0;
lighting_eye_fov_degrees 		= 90.0;
lighting_diffuse_strength 		= 0.20;
lighting_specular_strength 		= 1.0;
lighting_specular_shininess 	= 32.0;
lighting_surface_color 			= [1.0, 1.0, 1.0];

//death_bounds = [
//    x_min, x_max,
//    y_min, y_max,
//    z_min, z_max
//];
// Required: cell occupancy list capacity written to the .tst file.
cell_occupancy_list_size		= 512;

death_bounds 					= [1, 19,1, 19, 1, 21];

// Streaming inlet release model.
//
// particle_streams is a list of stream records.  Each record describes one
// material, one timed release schedule, one fixed inlet plane, and a rectangular
// particle lattice on that plane.  GenStreaming/GenLightingData consume this
// structure at data-generation time; the generated .bin/.tst files contain the
// resulting particle positions, velocities, material_id values, and release
// frames.  The stream-shape fields themselves are not runtime GLSL metadata.
//
// Runtime release state:
//   Data.w = release frame for pending/generated particles.
//   frameNum < Data.w  -> particle is pending and not simulated.
//   frameNum >= Data.w -> particle is active.
//   Data.w < 0         -> particle is dead.
//
// Stream record fields:
//   name
//     Human-readable stream name used in diagnostics.  Keep names unique.
//   material_id
//     Base material assigned to every particle from the stream.  During
//     generation, material_properties seeds pdata.ptype so photon behavior is
//     stable even if runtime material_id changes to a hit surface material.
//   initial_particle_velocity
//     Initial vx/vy/vz for every released particle.  For photons, this vector
//     also defines the invariant photon speed used by the Vulkan force path.
//   release_start_frame
//     First frame at which the first generated wave becomes active.
//   release_columns
//     Number of release waves/columns to generate.  Python preview uses 1 here
//     to keep the live runner light; Vulkan uses a larger value.
//   particles_per_wave
//     Particle count per release wave.  For 3D rectangular patch streams this
//     must equal span_u_count * span_v_count.
//   spacing_factor
//     Multiplier on particle diameter used to compute spacing and wave timing.
//   inlet_axis / inlet_value
//     Fixed coordinate plane for the stream, e.g. inlet_axis="x" and
//     inlet_value=2.25 emits from x=2.25.
//   span_u_axis / span_v_axis
//     The two varying axes on the inlet plane.  They must be different from
//     inlet_axis and from each other.
//   span_u_min / span_u_max / span_u_count
//   span_v_min / span_v_max / span_v_count
//     Inclusive lattice ranges and counts on the inlet plane.  Set a span
//     count to 1 with equal min/max for a line-like stream.
particle_streams = (
  {
    name 						= "photon_beam";
    material_id 				= 0;

    // Reflection-law beam aimed for a bright point at [5.1259, 5.6247, 4.6877].
	initial_particle_velocity 	= [ 0.209968, -0.026364, 0.187666 ];

    release_start_frame 		= 10;
    release_columns 			= 10;
    particles_per_wave 			= 800;
    spacing_factor 				= 1.05;

    inlet_axis 					= "x";
    inlet_value 				= 4.0;

    span_u_axis 				= "y";
    span_u_min 					= 3.15;
    span_u_max 					= 7.60;
    span_u_count 				= 40;

    span_v_axis 				= "z";
    span_v_min 					= 1.35;
    span_v_max 					= 7.30;
    span_v_count 				= 20;
  }

);
// Optional: preferred flow angle in degrees.
//   flow_direction = (cos(flow_angle), sin(flow_angle))
flow_angle 		= 90.0;
// Optional: velocity-direction alignment with flow_angle.
// The directed velocity contribution is proportional to flow_alignment; the
// random contribution is proportional to (1 - flow_alignment).
flow_alignment = 1.00;

// Stream span_u/span_v controls inlet packing, so LightingBall does not need
// reservoir helper walls. particle_plane_z remains for legacy wall-marker placement.
particle_plane_z 				= 3.5;

// 3D photon chamber. Rectangle wall normals point inward, into the valid
// particle region. Boundary particles are cell-locality sentinels; the
// rectangle definitions own the physical wall geometry.
curve_wall_segments = {};
rectangle_wall_segments = {
    x_min = { origin = [3.0, 1.0, 1.0];  u_axis = "Y"; v_axis = "Z"; u_length = 8.0; v_length = 12.0; normal = [ 1.0,  0.0,  0.0]; wall_flag = 1; material_id = 2; };
    x_max = { origin = [11.0, 1.0, 1.0]; u_axis = "Y"; v_axis = "Z"; u_length = 8.0; v_length = 12.0; normal = [-1.0,  0.0,  0.0]; wall_flag = 2; material_id = 2; };
    y_min = { origin = [3.0, 1.0, 1.0];  u_axis = "X"; v_axis = "Z"; u_length = 8.0; v_length = 12.0; normal = [ 0.0,  1.0,  0.0]; wall_flag = 3; material_id = 2; };
    y_max = { origin = [3.0, 9.0, 1.0];  u_axis = "X"; v_axis = "Z"; u_length = 8.0; v_length = 12.0; normal = [ 0.0, -1.0,  0.0]; wall_flag = 4; material_id = 2; };
    z_min = { origin = [3.0, 1.0, 1.0];  u_axis = "X"; v_axis = "Y"; u_length = 8.0; v_length = 8.0;  normal = [ 0.0,  0.0,  1.0]; wall_flag = 5; material_id = 2; };
    z_max = { origin = [3.0, 1.0, 13.0]; u_axis = "X"; v_axis = "Y"; u_length = 8.0; v_length = 8.0;  normal = [ 0.0,  0.0, -1.0]; wall_flag = 6; material_id = 2; };
};



// --------------------------------------------------------------------------
// Particle geometry and integration
// --------------------------------------------------------------------------
radius 					= 0.05;

// Simulation timestep used by both dynamics integration and wave-frame spacing.
dt 							= 0.045;
// --------------------------------------------------------------------------
// Front-end study and output selection
// --------------------------------------------------------------------------
// Normal single-run mode. When study is true, TabFormGenData iterates
// num_studies and creates a separate inline study run for each index.
study 					= false;
num_studies 			= 0;

output_file_prefix 		= "LightingBall_Vk";
