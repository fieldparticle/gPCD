#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float BOUNDARY_XMIN = 0.50;
const float BOUNDARY_XMAX  = 19.50;
const float BOUNDARY_YMIN  = 37.00;
const float BOUNDARY_YMAX  = 62.50;
const float wall_contact_offset = 0.20;
#define WALL_FUNC horizontal_wall
#define PERIODIC_DIRECTION horizontal
#define BOUNDARY_GUARD cell_guard
#define WALL_MODEL_BOUNDARY_PARTICLE
#endif
