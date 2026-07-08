import math

from gbase.GenericGenData import GenericGenData
from gbase.ParametricCurve import bounds as curve_bounds


class GenReservoir(GenericGenData):
    """Generate a packed reservoir using the GenericGenData output contract."""

    def validate_simulation_configuration(self):
        errors = []

        def required_values(name, count):
            values = self.itemcfg.get(name)
            if values is None:
                errors.append(f"{name} is required")
                return ()
            if len(values) != count:
                errors.append(f"{name} must contain exactly {count} values")
                return ()
            try:
                result = tuple(float(value) for value in values)
            except (TypeError, ValueError):
                errors.append(f"{name} values must be numeric")
                return ()
            if not all(math.isfinite(value) for value in result):
                errors.append(f"{name} values must be finite")
                return ()
            return result

        dimensions = []
        for name in (
            "cell_array_width",
            "cell_array_height",
            "cell_array_depth",
        ):
            value = self.itemcfg.get(name)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{name} must be a positive integer")
            else:
                dimensions.append(value)

        death_bounds = required_values("death_bounds", 6)
        chamber_bounds = required_values("chamber_bounds", 6)
        velocity_key = "reservoir_velocity"
        if self.itemcfg.get(velocity_key) is None:
            velocity_key = "piston_velocity"
        reservoir_velocity = required_values(velocity_key, 3)
        raw_segments = self.itemcfg.get("curve_wall_segments")
        curve_segments = []
        if not raw_segments:
            errors.append("curve_wall_segments is required and must not be empty")
        else:
            for index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) != 9:
                    errors.append(
                        f"curve_wall_segments[{index}] must contain 9 values"
                    )
                    continue
                try:
                    segment = tuple(float(value) for value in raw_segment)
                except (TypeError, ValueError):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be numeric"
                    )
                    continue
                if not all(math.isfinite(value) for value in segment):
                    errors.append(
                        f"curve_wall_segments[{index}] values must be finite"
                    )
                    continue
                wall_flag = segment[8]
                if not wall_flag.is_integer() or int(wall_flag) <= 0:
                    errors.append(
                        f"curve_wall_segments[{index}] wall_flag must be a positive integer"
                    )
                if all(abs(value) <= 1.0e-12 for value in segment[1:4] + segment[5:8]):
                    errors.append(f"curve_wall_segments[{index}] has zero length")
                curve_segments.append(segment)

        separation = self.itemcfg.get("particle_separation_distance")
        try:
            particle_separation_distance = float(separation)
        except (TypeError, ValueError):
            errors.append("particle_separation_distance is required and numeric")
            particle_separation_distance = None

        piston_start_frame = self.itemcfg.get("piston_start_frame", 0)
        try:
            piston_start_frame_value = float(piston_start_frame)
        except (TypeError, ValueError):
            errors.append("piston_start_frame must be numeric")
            piston_start_frame_value = None

        if particle_separation_distance is not None:
            if not math.isfinite(particle_separation_distance):
                errors.append("particle_separation_distance must be finite")
            elif particle_separation_distance < 0.0:
                errors.append("particle_separation_distance must not be negative")

        if piston_start_frame_value is not None:
            if not math.isfinite(piston_start_frame_value):
                errors.append("piston_start_frame must be finite")
            elif piston_start_frame_value < 0.0:
                errors.append("piston_start_frame must not be negative")
            elif not piston_start_frame_value.is_integer():
                errors.append("piston_start_frame must be an integer")

        if chamber_bounds and len(dimensions) == 3:
            x_start, x_end, y_bottom, y_top, z_front, z_back = chamber_bounds
            if x_start >= x_end:
                errors.append("chamber_bounds: x_start must be less than x_end")
            if y_bottom >= y_top:
                errors.append("chamber_bounds: y_bottom must be less than y_top")
            if z_front >= z_back:
                errors.append("chamber_bounds: z_front must be less than z_back")
            if (
                x_start < 0.0
                or x_end > dimensions[0]
                or y_bottom < 0.0
                or y_top > dimensions[1]
                or z_front < 0.0
                or z_back > dimensions[2]
            ):
                errors.append("chamber_bounds must fit inside the cell array")
            if (
                death_bounds
                and (
                    x_start < death_bounds[0]
                    or x_end > death_bounds[1]
                    or y_bottom < death_bounds[2]
                    or y_top > death_bounds[3]
                    or z_front < death_bounds[4]
                    or z_back > death_bounds[5]
                )
            ):
                errors.append("chamber_bounds must fit inside death_bounds")

        if death_bounds and len(dimensions) == 3:
            width, height, depth = dimensions
            for axis, minimum, maximum, domain_maximum in (
                ("x", death_bounds[0], death_bounds[1], width),
                ("y", death_bounds[2], death_bounds[3], height),
                ("z", death_bounds[4], death_bounds[5], depth),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis}_min must be less than {axis}_max"
                    )
                if minimum < 0.0 or maximum > domain_maximum:
                    errors.append(
                        f"death_bounds {axis} range must fit inside the cell array"
                    )

            for index, segment in enumerate(curve_segments):
                x_min, x_max, y_min, y_max = curve_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside the cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside the cell array"
                    )

        if errors:
            raise ValueError(
                "Reservoir configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.chamber_bounds = chamber_bounds
        self.reservoir_velocity = reservoir_velocity
        self.reservoir_velocity_key = velocity_key
        self.particle_separation_distance = particle_separation_distance
        self.piston_start_frame = int(piston_start_frame_value)
        self.number_configured_particles = 0
        self.explicit_particles = []
        self.radius = float(self.itemcfg.radius)
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        self.calculate_chamber_packing()
        return True

    def calculate_chamber_packing(self):
        radius = self.radius
        center_spacing = 2.0 * radius + self.particle_separation_distance
        boundary_clearance = radius * (1.0 + self.wall_contact_offset) + 1.0e-9
        x_start, x_end, y_bottom, y_top, z_front, z_back = self.chamber_bounds
        z_center = 0.5 * (z_front + z_back)

        x_center_min = x_start + boundary_clearance
        x_center_max = x_end - boundary_clearance
        y_center_min = y_bottom + boundary_clearance
        y_center_max = y_top - boundary_clearance

        usable_x = x_center_max - x_center_min
        usable_y = y_center_max - y_center_min
        if usable_x < 0.0 or usable_y < 0.0:
            raise ValueError("chamber_bounds are too small for particle clearance")

        x_count = int(math.floor((usable_x / center_spacing) + 1.0e-12)) + 1
        y_count = int(math.floor((usable_y / center_spacing) + 1.0e-12)) + 1
        occupied_x = (x_count - 1) * center_spacing
        occupied_y = (y_count - 1) * center_spacing
        first_x = x_center_min + 0.5 * (usable_x - occupied_x)
        first_y = y_center_min + 0.5 * (usable_y - occupied_y)

        self.packing_x_count = x_count
        self.packing_y_count = y_count
        self.packing_particle_count = x_count * y_count
        self.particle_center_spacing = center_spacing
        self.boundary_particle_clearance = boundary_clearance
        self.particle_plane_z = z_center
        self.packing_first_center = (first_x, first_y, z_center)
        self.packing_last_center = (
            first_x + occupied_x,
            first_y + occupied_y,
            z_center,
        )

        print(
            "Reservoir packing report:\n"
            f"  chamber bounds: {self.chamber_bounds}\n"
            f"  radius: {radius:g}\n"
            f"  surface separation: {self.particle_separation_distance:g}\n"
            f"  center spacing: {center_spacing:g}\n"
            f"  boundary clearance: {boundary_clearance:g}\n"
            f"  grid: {x_count} columns x {y_count} rows\n"
            f"  particle count: {self.packing_particle_count}\n"
            f"  first center: {self.packing_first_center}\n"
            f"  last center: {self.packing_last_center}\n"
            f"  reservoir velocity: {self.reservoir_velocity}"
        )
        return self.packing_particle_count

    def add_reservoir_mobile_particles(self):
        first_x, first_y, particle_z = self.packing_first_center
        velocity = self.reservoir_velocity

        for column in range(self.packing_x_count):
            particle_x = first_x + column * self.particle_center_spacing
            for row in range(self.packing_y_count):
                particle_y = first_y + row * self.particle_center_spacing
                self.add_mobile_particle(
                    (particle_x, particle_y, particle_z),
                    velocity,
                    radius=self.radius,
                    mass=1.0,
                    collision_stiffness_q=float(
                        self.itemcfg.get("collision_stiffness_q", 0.0)
                    ),
                )

        print(
            "Reservoir mobile-particle report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  velocity: {self.reservoir_velocity}\n"
            f"  first particle number: 1\n"
            f"  last particle number: {self.number_active_particles}"
        )
        return self.number_active_particles

    def write_test_file(self):
        test_file_name = super().write_test_file()
        with open(test_file_name, "a", encoding="ascii") as output:
            output.write(f"piston_start_frame = {self.piston_start_frame};\n")
            output.write(f"chamber_x_start = {self.chamber_bounds[0]:.9f};\n")
            output.write(f"chamber_x_end = {self.chamber_bounds[1]:.9f};\n")
            output.write(f"chamber_y_bottom = {self.chamber_bounds[2]:.9f};\n")
            output.write(f"chamber_y_top = {self.chamber_bounds[3]:.9f};\n")
            output.write(f"chamber_z_front = {self.chamber_bounds[4]:.9f};\n")
            output.write(f"chamber_z_back = {self.chamber_bounds[5]:.9f};\n")
            output.write(f"reservoir_velocity_x = {self.reservoir_velocity[0]:.9f};\n")
            output.write(f"reservoir_velocity_y = {self.reservoir_velocity[1]:.9f};\n")
            output.write(f"reservoir_velocity_z = {self.reservoir_velocity[2]:.9f};\n")
            output.write(f"piston_velocity_x = {self.reservoir_velocity[0]:.9f};\n")
            output.write(f"piston_velocity_y = {self.reservoir_velocity[1]:.9f};\n")
            output.write(f"piston_velocity_z = {self.reservoir_velocity[2]:.9f};\n")
        return test_file_name

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Reservoir configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            self.add_null_particle()
            self.add_reservoir_mobile_particles()
            self.add_parametric_wall_markers()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Reservoir generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        print(
            "Reservoir generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        return True
