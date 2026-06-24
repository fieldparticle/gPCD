#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float BOUNDARY_XMIN = 3.50;
const float BOUNDARY_XMAX  = 29.00;
const float BOUNDARY_YMIN  = 0.50;
const float BOUNDARY_YMAX  = 32.00;
const float wall_contact_offset = 0.20;
#define WALL_FUNC vertical_wall
#define PERIODIC_DIRECTION vertical
#define BOUNDARY_GUARD cell_guard
#define WALL_MODEL_BOUNDARY_PARTICLE
#endif
