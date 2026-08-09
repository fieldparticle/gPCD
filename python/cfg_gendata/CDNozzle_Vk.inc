// ============================================================================
// CDNozzle_Vk.inc
// ============================================================================
//
// Reference Vulkan data-generation include for the converging-diverging nozzle.
//
// This file is meant to be a readable baseline for the Vulkan nozzle geometry,
// particle packing, and wall-contact parameters. The generated data path uses
// this include to create:
//
//   - C:/_DJ/gPCDData/examples/CDNozzle_Vk.bin
//       Binary particle data consumed by the Vulkan app.
//
//   - C:/_DJ/gPCDData/examples/CDNozzle_Vk.tst
//       Runtime configuration consumed by the Vulkan app.
//
//   - C:/_DJ/gPCD/vulkan/sim/CDNozzle/CDNozzle_Vk.obj
//       Visual wall/boundary geometry.
//
// Function walls are the physical wall model. Boundary particles generated
// from those walls are only cell-locality sentinels. A nearby boundary marker
// tells the shader that a wall may be near; the analytic wall curve itself
// supplies the contact point, penetration depth, and normal.
//
// Nozzle station summary, in cell units:
//
//   Lower/upper reservoir walls: x = 2..402
//   Flat transition spacer:      x = 402..404
//   Converging section:          x = 404..424
//   Throat:                      x = 424..429
//   Diverging section:           x = 429..449
//   Exit straight:               x = 449..459
//
// Channel heights:
//
//   Reservoir/exit height:       y = 15..35, height 20
//   Throat height:               y = 20..30, height 10
//
// Polynomial segment convention:
//
//   function = "y_of_x"
//   u is x
//   f(u) = f_start + a1*s + a2*s^2 + a3*s^3
//   s = u - u_start
//
// A later segment inherits u_start and f_start from the end of the previous
// segment. Only length and coefficients are needed after the first segment.
//
// Historical note:
//
//   reservoir_starting_vx was raised to 0.05 from 0.005 for this Vulkan
//   reference case.
//
// ============================================================================

// Simulation timestep used by the generated .tst as DT.
//
// A smaller dt reduces per-frame penetration and makes wall/particle contact
// less abrupt. A larger dt moves particles farther per frame and makes the
// depth constraint more visible.
dt = 0.01;

// Output stem for generated files. The generator writes CDNozzle_Vk.bin and
// CDNozzle_Vk.tst under data_dir, and the Vulkan app captures frames using
// this same stem.
output_file_prefix = "CDNozzle_Vk";

// Visual wall mesh path. This OBJ is for display/inspection. It is not the
// source of physical wall contact; curve_wall_segments below are.
obj_file_name = "C:/_DJ/gPCD/vulkan/sim/CDNozzle/CDNozzle_Vk.obj";

// Python preview zoom used by the generated plotting/viewing path.
zoom = 5.5;

// ============================================================================
// Preview And Cell Domain
// ============================================================================

// Axis limits for the Python preview plot. These should comfortably contain
// the nozzle, reservoir particles, and the visual boundary.
x_axis_lims = [0.0, 470.0];
y_axis_lims = [10.0, 40.0];
z_axis_lims = [0.75, 1.25];

// Cell-array dimensions. These must contain every active particle and boundary
// sentinel. The death bounds below are deliberately inside this cell array.
cell_array_width = 500;
cell_array_height = 40;
cell_array_depth = 5;

// Initial camera center used by the Vulkan/Python viewers.
view_center = [450, 25, 2];

// Frame when the visual piston begins moving. This is display/control metadata
// for the generated test case.
piston_start_frame = 20;

// Death bounds are the active simulation window. Mobile particles outside
// these limits are marked dead. Keep these inside the cell-array bounds so
// particles die before indexing outside valid cells.
//
// Format:
//
//   [x_min, x_max,
//    y_min, y_max,
//    z_min, z_max]
death_bounds = [
    1, 498,
    12, 38,
    0, 4
];

// ============================================================================
// Particle Stream
// ============================================================================

// The stream generator packs particles inside the 2D region enclosed by the
// lower and upper function walls. Particles are generated on particle_plane_z.
//
// Important distinction:
//
//   particle_separation_distance is the intended center-to-center packing
//   clearance used by the generator.
//
//   particle_spacing_x/y are the packing lattice increments used by the stream
//   generator. Small spacing creates dense rows/columns.
//
//   radius is the physical particle radius used by contact detection.
//
// The values below make a dense, small-particle reference case.
particle_streams = (
  {
    name = "reservoir_substance";

    // Material id 3 is normally configured as the flowing substance display
    // material in the parent .cfg/.tst.
    material_id = 3;

    // Physical particle radius.
    radius = 0.1;

    // Generator packing values. With radius 0.1 and spacing 0.05, particles
    // begin deeply interpenetrating by geometric standards; that is intentional
    // for this dense continuum-style setup.
    particle_separation_distance = 0.05;
    particle_spacing_x = 0.05;
    particle_spacing_y = 0.05;

    // Particle-particle collision stiffness. Wall contacts can optionally
    // override this at curve_wall_segments group level; this baseline file does
    // not set wall-specific overrides, so wall contacts fall back to this
    // source-particle stiffness.
    collision_stiffness_q = 16.0;

    // Depth-dependent stiffness multiplier:
    //
    //   effective_q = base_q * (1 + gain * (penetration / hard_depth)^power)
    //
    // This stiffens contacts as penetration approaches hard depth.
    compression_stiffness_gain = 8.0;
    compression_stiffness_power = 2.0;

    // Target/hard penetration depths are fractions of source particle radius.
    //
    // The maximum-depth velocity constraint begins at target depth and prevents
    // motion that would exceed hard depth.
    target_penetration_fraction = 0.5;
    hard_penetration_fraction = 0.75;
    min_compression_frames = 3.0;

    // Initial injected stream velocity. For this nozzle, flow is in +X.
    stream_velocity = [0.05, 0.0, 0.0];

    // Temporary velocity control:
    //
    //   "none"        leaves velocity alone after initialization.
    //   "directional" relaxes velocity toward temp_velocity.xyz.
    //   "magnitude"  biases speed toward temp_velocity magnitude while
    //                preserving direction as much as the force path allows.
    //
    // This reference case uses magnitude control toward speed 0.07 with a very
    // small rate.
    //temp_vel_type = "directional";
    temp_vel_type = "magnitude";
    temp_velocity = [0.07, 0.0, 0.0, 0.0];
    temp_vel_rate = 0.00001;
  }
);

// 2D packing curves derive x/y packing bounds. Particles live on one Z cell
// center so the dynamics are effectively 2D while still using 3D particle
// records.
particle_plane_z = 1.5;

// ============================================================================
// Visual Piston
// ============================================================================

// Visual-only piston symbol written to the generated .tst for Vulkan display.
// It helps orient the upstream side but does not define nozzle wall geometry.
piston_visual = {
    enabled = true;
    y_min = 15.0;
    y_max = 35.0;
    head_length = 10.0;
    rod_length = 10.0;
    rod_height = 4.0;
    z = 1.5;
    head_color = {red = 0.0; green = 0.8; blue = 1.0; alpha = 1.0;};
    rod_color = {red = 0.0; green = 0.45; blue = 0.7; alpha = 1.0;};
};

// ============================================================================
// Analytic Function Walls
// ============================================================================
//
// curve_wall_segments defines both the generated visual boundary sentinels and
// the analytic collision surface. The analytic curve is the physical wall.
//
// Common fields:
//
//   function
//       "y_of_x" means x is independent and y is generated by the polynomial.
//
//   normal_sign
//       -1 for the lower wall. The wall normal stored in contact state points
//       outward/downward so the force path applies -F * normal upward.
//
//        1 for the upper wall. The outward normal points upward so -F * normal
//       pushes particles downward.
//
//   wall_flag
//       Identifies one logical wall. The source-owned wall scan keeps the
//       deepest valid contact per wall_flag.
//
//   boundary_kind
//       "reservoir" marks an upstream reservoir wall segment.
//       "regular" marks normal nozzle wall segments.
//
// Optional wall-specific physical fields can be placed at the group level:
//
//   wall_collision_stiffness_q
//   wall_target_penetration_fraction
//   wall_hard_penetration_fraction
//   wall_compression_stiffness_gain
//   wall_compression_stiffness_power
//
// This baseline file intentionally leaves those unset. That makes wall
// contacts inherit the stream particle/global contact behavior, which is useful
// for comparing against older generated cases.
curve_wall_segments = {
    lower_wall = {
        function = "y_of_x";
        normal_sign = -1;
        wall_flag = 3;

        segments = {
            // Lower reservoir wall.
            //
            // x = 2..402, y = 15.
            // This is a long flat upstream feed section.
            wall3 = {
                boundary_kind = "reservoir";
                u_start = 2;
                length = 400;
                f_start = 15;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Lower flat spacer.
            //
            // x = 402..404, y = 15.
            // This creates a short straight transition before the converging
            // curve begins.
            segment03 = {
                boundary_kind = "regular";
                length = 2;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Lower converging wall.
            //
            // x = 404..424.
            // y rises from 15 to 20.
            //
            // f(s) = 15 + 0.01875*s^2 - 0.000625*s^3
            //
            // At s = 0:
            //   y = 15, slope = 0
            //
            // At s = 20:
            //   y = 20, slope = 0
            //
            // This cubic gives a smooth flat-to-flat contraction into the
            // throat.
            segment05 = {
                boundary_kind = "regular";
                length = 20;
                a1 = 0;
                a2 = 0.01875;
                a3 = -0.000625;
            };

            // Lower throat.
            //
            // x = 424..429, y = 20.
            // Constant-area narrow section.
            segment07 = {
                boundary_kind = "regular";
                length = 5;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Lower diverging wall.
            //
            // x = 429..449.
            // y falls from 20 to 15.
            //
            // f(s) = 20 - 0.00625*s^2
            //
            // This is a simple quadratic expansion. It starts flat at the
            // throat and exits with a nonzero downward slope.
            segment09 = {
                boundary_kind = "regular";
                length = 20;
                a1 = 0;
                a2 = -0.00625;
                a3 = 0;
            };

            // Lower exit straight.
            //
            // x = 449..459, y = 15.
            // The nozzle is back at reservoir height.
            segment11 = {
                boundary_kind = "regular";
                length = 10;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };
        };
    };

    upper_wall = {
        function = "y_of_x";
        normal_sign = 1;
        wall_flag = 4;

        segments = {
            // Upper reservoir wall.
            //
            // x = 2..402, y = 35.
            // Pairs with lower wall y = 15 for a reservoir height of 20.
            wall4 = {
                boundary_kind = "reservoir";
                u_start = 2;
                length = 400;
                f_start = 35;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Upper flat spacer.
            //
            // x = 402..404, y = 35.
            segment04 = {
                boundary_kind = "regular";
                length = 2;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Upper converging wall.
            //
            // x = 404..424.
            // y falls from 35 to 30.
            //
            // f(s) = 35 - 0.01875*s^2 + 0.000625*s^3
            //
            // This mirrors the lower converging wall and keeps the centerline
            // at y = 25.
            segment06 = {
                boundary_kind = "regular";
                length = 20;
                a1 = 0;
                a2 = -0.01875;
                a3 = 0.000625;
            };

            // Upper throat.
            //
            // x = 424..429, y = 30.
            // Pairs with lower throat y = 20 for throat height 10.
            segment08 = {
                boundary_kind = "regular";
                length = 5;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };

            // Upper diverging wall.
            //
            // x = 429..449.
            // y rises from 30 to 35.
            //
            // f(s) = 30 + 0.00625*s^2
            //
            // Mirrors the lower diverging wall.
            segment10 = {
                boundary_kind = "regular";
                length = 20;
                a1 = 0;
                a2 = 0.00625;
                a3 = 0;
            };

            // Upper exit straight.
            //
            // x = 449..459, y = 35.
            segment12 = {
                boundary_kind = "regular";
                length = 10;
                a1 = 0;
                a2 = 0;
                a3 = 0;
            };
        };
    };
};

// Required: tells ForceDynamicsBase to load particle records from the generated
// bin file instead of constructing particles directly from the .tst.
pdata_from_file = true;

// Required when study is true. Kept at zero for this single reference case.
num_studies = 0;
