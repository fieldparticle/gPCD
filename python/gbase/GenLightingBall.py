import math

from gbase.BoundaryLighting import BOUNDARY_LIGHT_SURFACE_SPHERE
from gbase.GenStreaming import GenStreaming


class GenLightingBall(GenStreaming):
    """Generate the sphere lighting scenario."""

    def parse_lighting_ball(self):
        values = self.itemcfg.get("Lighting_ball")
        if values is None:
            return None
        if hasattr(values, "get"):
            center = (
                float(values.get("x")),
                float(values.get("y")),
                float(values.get("z")),
            )
            ball_radius = float(values.get("radius"))
            material_id = int(values.get("material_id", 0))
        else:
            if len(values) not in (4, 5):
                raise ValueError(
                    "Lighting_ball must be [x_center, y_center, z_center, radius]"
                    " or [x_center, y_center, z_center, radius, material_id]"
                )
            center = tuple(float(values[index]) for index in range(3))
            ball_radius = float(values[3])
            material_id = int(values[4]) if len(values) == 5 else 0

        if ball_radius <= 0.0:
            raise ValueError("Lighting_ball radius must be greater than zero")
        if material_id not in self.material_properties_by_id:
            raise ValueError(f"Lighting_ball material_id {material_id} is not defined")
        return center, ball_radius, material_id

    def add_lighting_ball_boundary_particles(self):
        lighting_ball = self.parse_lighting_ball()
        if lighting_ball is None:
            return 0

        center, ball_radius, material_id = lighting_ball
        raw_lighting_ball = self.itemcfg.get("Lighting_ball")
        wall_flag = int(
            raw_lighting_ball.get("wall_flag", 1000)
            if hasattr(raw_lighting_ball, "get")
            else self.itemcfg.get("lighting_ball_wall_flag", 1000)
        )
        surface_spacing = 1.0
        theta_count = max(4, int(math.ceil(math.pi * ball_radius / surface_spacing)))
        marker_cells = set()
        added_count = 0

        for theta_index in range(theta_count + 1):
            theta = math.pi * theta_index / theta_count
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            ring_radius = ball_radius * sin_theta
            ring_count = max(
                1,
                int(math.ceil((2.0 * math.pi * ring_radius) / surface_spacing)),
            )

            for phi_index in range(ring_count):
                phi = 0.0 if ring_count == 1 else 2.0 * math.pi * phi_index / ring_count
                normal = (
                    sin_theta * math.cos(phi),
                    sin_theta * math.sin(phi),
                    cos_theta,
                )
                surface_position = (
                    center[0] + ball_radius * normal[0],
                    center[1] + ball_radius * normal[1],
                    center[2] + ball_radius * normal[2],
                )
                cell_position = tuple(round(value) for value in surface_position)
                if cell_position in marker_cells:
                    continue
                marker_cells.add(cell_position)

                normal_x = cell_position[0] - center[0]
                normal_y = cell_position[1] - center[1]
                normal_z = cell_position[2] - center[2]
                normal_length = math.sqrt(
                    normal_x * normal_x
                    + normal_y * normal_y
                    + normal_z * normal_z
                )
                if normal_length <= 0.0:
                    continue

                particle = self.add_boundary_particle(
                    (
                        float(cell_position[0]),
                        float(cell_position[1]),
                        float(cell_position[2]),
                    ),
                    material_id=material_id,
                )
                particle.vx = normal_x / normal_length
                particle.vy = normal_y / normal_length
                particle.vz = normal_z / normal_length
                self.register_boundary_light_source(
                    particle.pnum,
                    BOUNDARY_LIGHT_SURFACE_SPHERE,
                    wall_flag,
                    material_id,
                    (particle.vx, particle.vy, particle.vz),
                )
                added_count += 1

        report_text = (
            "Lighting ball boundary report:\n"
            f"  center: {center}\n"
            f"  ball radius: {ball_radius:g}\n"
            f"  material_id: {material_id}\n"
            f"  surface spacing: {surface_spacing:g}\n"
            f"  unique boundary markers: {added_count}\n"
            "  marker position: integer cell center\n"
            "  normal storage: vx/vy/vz"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return added_count

    def add_configured_wall_markers(self):
        super().add_configured_wall_markers()
        self.add_lighting_ball_boundary_particles()
        return self.number_boundary_particles
