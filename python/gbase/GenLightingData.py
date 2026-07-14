import math

from gbase.GenStreaming import GenStreaming
from gbase.GenericGenData import GenericGenData


class GenLightingData(GenStreaming):
    """Generate explicit lighting/demo particles with scheduled release frames."""

    @staticmethod
    def _ray_endpoint(origin_x, origin_y, angle_radians, view_box):
        x_min, x_max, y_min, y_max = view_box
        dir_x = math.cos(angle_radians)
        dir_y = math.sin(angle_radians)
        candidates = []
        if abs(dir_x) > 1.0e-12:
            for x_bound in (x_min, x_max):
                scale = (x_bound - origin_x) / dir_x
                y_value = origin_y + scale * dir_y
                if scale > 0.0 and y_min - 1.0e-9 <= y_value <= y_max + 1.0e-9:
                    candidates.append((scale, x_bound, y_value))
        if abs(dir_y) > 1.0e-12:
            for y_bound in (y_min, y_max):
                scale = (y_bound - origin_y) / dir_y
                x_value = origin_x + scale * dir_x
                if scale > 0.0 and x_min - 1.0e-9 <= x_value <= x_max + 1.0e-9:
                    candidates.append((scale, x_value, y_bound))
        if not candidates:
            fallback_scale = max(x_max - x_min, y_max - y_min)
            return (
                origin_x + fallback_scale * dir_x,
                origin_y + fallback_scale * dir_y,
            )
        _scale, end_x, end_y = min(candidates, key=lambda item: item[0])
        return end_x, end_y

    @staticmethod
    def SpecificDraw(screen, run_configuration, dynamics, view_box, draw_helpers):
        """Draw lighting-specific eye/FOV diagnostics in the Python viewer."""
        del dynamics
        import pygame

        eye_position = run_configuration.get("lumens_eye_position", (0.0, 0.0))
        eye_x = float(eye_position[0])
        eye_y = float(eye_position[1])
        eye_angle = math.radians(
            float(run_configuration.get("lumens_eye_angle_degrees", 0.0))
        )
        fov = math.radians(float(run_configuration.get("lumens_eye_fov_degrees", 90.0)))
        half_fov = fov * 0.5

        eye_screen = draw_helpers.to_screen(eye_x, eye_y)
        look_end = GenLightingData._ray_endpoint(eye_x, eye_y, eye_angle, view_box)
        left_end = GenLightingData._ray_endpoint(
            eye_x,
            eye_y,
            eye_angle + half_fov,
            view_box,
        )
        right_end = GenLightingData._ray_endpoint(
            eye_x,
            eye_y,
            eye_angle - half_fov,
            view_box,
        )

        pygame.draw.line(
            screen,
            (255, 240, 120),
            eye_screen,
            draw_helpers.to_screen(*look_end),
            2,
        )
        for end_point in (left_end, right_end):
            pygame.draw.line(
                screen,
                (120, 120, 80),
                eye_screen,
                draw_helpers.to_screen(*end_point),
                1,
            )

        pygame.draw.circle(screen, (255, 240, 120), eye_screen, 4)
        if bool(run_configuration.get("lumens_draw_eye_radius", False)):
            radius = draw_helpers.radius_to_pixels(
                float(run_configuration.get("lumens_eye_radius", 0.0))
            )
            pygame.draw.circle(
                screen,
                (255, 240, 120),
                eye_screen,
                max(1, radius),
                1,
            )

    def validate_simulation_configuration(self):
        GenericGenData.validate_simulation_configuration(self)

        errors = []
        particle_data = self.itemcfg.get("PARTICLE_DATA")
        for index, configured in enumerate(self.explicit_particles):
            particle_name = f"p{index + 1}"
            particle_cfg = particle_data.get(particle_name)
            raw_release_frame = particle_cfg.get(
                "releaseFrame",
                particle_cfg.get("state_flg", 0.0),
            )
            try:
                release_frame = float(raw_release_frame)
            except (TypeError, ValueError):
                errors.append(f"PARTICLE_DATA.{particle_name}.releaseFrame must be numeric")
                continue
            if not math.isfinite(release_frame):
                errors.append(f"PARTICLE_DATA.{particle_name}.releaseFrame must be finite")
            elif release_frame < 0.0:
                errors.append(
                    f"PARTICLE_DATA.{particle_name}.releaseFrame must not be negative"
                )
            configured["release_frame"] = release_frame

        if errors:
            raise ValueError(
                "Lighting configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )
        return True

    def add_explicit_mobile_particles(self):
        for configured in self.explicit_particles:
            particle = self.add_mobile_particle(
                (configured["x"], configured["y"], configured["z"]),
                (configured["vx"], configured["vy"], configured["vz"]),
                radius=configured["radius"],
                mass=configured["mass"],
                material_id=configured.get("material_id", 0),
                collision_stiffness_q=configured["collision_stiffness_q"],
            )
            particle.state_flg = float(configured.get("release_frame", 0.0))

        if self.number_active_particles != self.number_configured_particles:
            raise RuntimeError(
                "generated mobile-particle count does not match PARTICLE_DATA"
            )

        report_text = (
            "Lighting explicit-particle release report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            "  release field: PARTICLE_DATA.pN.releaseFrame -> pdata.state_flg"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_active_particles
