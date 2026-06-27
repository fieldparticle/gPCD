#ifndef BOUNDARY_GLSL
#define BOUNDARY_GLSL
const uint BOUNDARY_ENABLED = 1u;
const float BOUNDARY_XMIN = 1.00;
const float BOUNDARY_XMAX  = 65.00;
const float BOUNDARY_YMIN  = 40.00;
const float BOUNDARY_YMAX  = 60.00;
const float wall_contact_offset = 0.20;
#define WALL_FUNC cd_nozzle_wall
#define PERIODIC_DIRECTION horizontal
#define BOUNDARY_GUARD cell_guard
#define WALL_MODEL_BOUNDARY_PARTICLE
const float CD_NOZZLE_START_X = BOUNDARY_XMIN;
const float CD_NOZZLE_CENTER_Y = 0.5 * (BOUNDARY_YMIN + BOUNDARY_YMAX);
const float CD_NOZZLE_INLET_LENGTH = 10.00;
const float CD_NOZZLE_CONVERGE_LENGTH = 20.00;
const float CD_NOZZLE_THROAT_LENGTH = 5.00;
const float CD_NOZZLE_DIVERGE_LENGTH = 20.00;
const float CD_NOZZLE_EXIT_LENGTH = 10.00;
const float CD_NOZZLE_INLET_RADIUS = 10.00;
const float CD_NOZZLE_THROAT_RADIUS = 7.50;
const float CD_NOZZLE_EXIT_RADIUS = 10.00;
#endif
