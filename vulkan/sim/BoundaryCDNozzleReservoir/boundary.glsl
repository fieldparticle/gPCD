#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float BOUNDARY_XMIN = 40.00;
const float BOUNDARY_XMAX  = 60.00;
const float BOUNDARY_YMIN  = 40.00;
const float BOUNDARY_YMAX  = 60.00;
const float wall_contact_offset = 0.20;
#define WALL_FUNC horizontal_wall
#define PERIODIC_DIRECTION horizontal
#define BOUNDARY_GUARD cell_guard
#define WALL_MODEL_BOUNDARY_PARTICLE
#endif
