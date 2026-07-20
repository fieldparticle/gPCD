import math

from gbase.GenStreaming import GenStreaming
from gbase.GenericGenData import GenericGenData


class GenLightingData(GenStreaming):
    """Generate explicit lighting/demo particles with scheduled release frames."""

    @staticmethod
    def _vector3_from_config(raw_value, default):
        if raw_value is None:
            return tuple(default)
        values = [float(raw_value[index]) for index in range(min(3, len(raw_value)))]
        while len(values) < 3:
            values.append(0.0)
        return tuple(values)

    @staticmethod
    def _normalize3(vector):
        length = math.sqrt(sum(component * component for component in vector))
        if length <= 1.0e-12:
            return None
        return tuple(component / length for component in vector)

    @staticmethod
    def _lighting_eye_position3(run_configuration):
        return GenLightingData._vector3_from_config(
            run_configuration.get("lighting_eye_position"),
            (0.0, 0.0, 0.0),
        )

    @staticmethod
    def _lighting_eye_direction3(run_configuration):
        eye_position = GenLightingData._lighting_eye_position3(run_configuration)
        target = run_configuration.get("lighting_eye_target")
        if target is not None:
            target_position = GenLightingData._vector3_from_config(
                target,
                (0.0, 0.0, 0.0),
            )
            direction = tuple(
                target_position[index] - eye_position[index]
                for index in range(3)
            )
            normalized = GenLightingData._normalize3(direction)
            if normalized is not None:
                return normalized

        raw_direction = run_configuration.get("lighting_eye_direction")
        if raw_direction is not None:
            normalized = GenLightingData._normalize3(
                GenLightingData._vector3_from_config(raw_direction, (1.0, 0.0, 0.0))
            )
            if normalized is not None:
                return normalized

        eye_angle = math.radians(
            float(run_configuration.get("lighting_eye_angle_degrees", 0.0))
        )
        return math.cos(eye_angle), math.sin(eye_angle), 0.0

    @staticmethod
    def _ray_endpoint_from_direction(origin_x, origin_y, dir_x, dir_y, view_box):
        x_min, x_max, y_min, y_max = view_box
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
    def _ray_endpoint(origin_x, origin_y, angle_radians, view_box):
        return GenLightingData._ray_endpoint_from_direction(
            origin_x,
            origin_y,
            math.cos(angle_radians),
            math.sin(angle_radians),
            view_box,
        )

    @staticmethod
    def SpecificDraw(screen, run_configuration, dynamics, view_box, draw_helpers):
        """Draw lighting-specific eye/FOV diagnostics in the Python viewer."""
        del dynamics
        import pygame

        eye_x, eye_y, _eye_z = GenLightingData._lighting_eye_position3(
            run_configuration
        )
        eye_direction = GenLightingData._lighting_eye_direction3(run_configuration)
        eye_direction_xy_length = math.hypot(eye_direction[0], eye_direction[1])
        if eye_direction_xy_length <= 1.0e-12:
            return
        eye_dir_x = eye_direction[0] / eye_direction_xy_length
        eye_dir_y = eye_direction[1] / eye_direction_xy_length
        eye_angle = math.atan2(eye_dir_y, eye_dir_x)
        fov = math.radians(float(run_configuration.get("lighting_eye_fov_degrees", 90.0)))
        half_fov = fov * 0.5

        eye_screen = draw_helpers.to_screen(eye_x, eye_y)
        look_end = GenLightingData._ray_endpoint_from_direction(
            eye_x,
            eye_y,
            eye_dir_x,
            eye_dir_y,
            view_box,
        )
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

    def report_collision_feasibility(self):
        return GenericGenData.report_collision_feasibility(self)

    def report_cell_occupancy_capacity(self):
        return GenericGenData.report_cell_occupancy_capacity(self)

    def runner(self):
        return GenericGenData.runner(self)
