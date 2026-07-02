#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float wall_contact_offset = 0.062500000;
#define CONTACT_FORCE_MEASURE  depth
#define WALL_MODEL_BOUNDARY_PARTICLE
const float BOUNDARY_XMIN = 2.000000000;
const float BOUNDARY_XMAX = 20.000000000;
const float BOUNDARY_YMIN = 2.000000000;
const float BOUNDARY_YMAX = 8.000000000;
const float BOUNDARY_ZMIN = 1.000000000;
const float BOUNDARY_ZMAX = 1.000000000;
const float death_x_min = 1.000000000;
const float death_x_max = 30.000000000;
const float death_y_min = 1.000000000;
const float death_y_max = 9.000000000;
const float death_z_min = 0.000000000;
const float death_z_max = 4.000000000;
#endif
