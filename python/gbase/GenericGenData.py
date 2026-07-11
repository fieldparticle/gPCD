import os

from gbase.FunctionWall import bounds as wall_bounds
from gbase.FunctionWall import sample_points
from gbase.pdata import PTYPE_MOBILE, PTYPE_NULL, pdata
import math


class GenericGenData:
    """Generate particle data from declarative particle and wall configuration."""

    BOUNDARY_PARTICLE_PTYPE = 1.0

    def __init__(self):
        self.parent = None
        self.bobj = None
        self.cfg = None
        self.log = None
        self.itemcfg = None
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0

    def create(self, parent, itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg

    def openSelectionsFile(self):
        """This generator does not use a selections file."""

    def clear_selections(self):
        """This generator does not use selection records."""

    def clear_files(self):
        """Output replacement occurs only after configuration verification."""

    def do_all_files_dbg(self):
        return self.runner()

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

        try:
            target_penetration_fraction = float(
                self.itemcfg.get(
                    "target_penetration_fraction",
                    self.itemcfg.get("max_penetration_fraction", 0.5),
                )
            )
        except (TypeError, ValueError):
            errors.append("target_penetration_fraction must be numeric")
            target_penetration_fraction = None

        try:
            hard_penetration_fraction = float(
                self.itemcfg.get("hard_penetration_fraction", 0.75)
            )
        except (TypeError, ValueError):
            errors.append("hard_penetration_fraction must be numeric")
            hard_penetration_fraction = None

        if target_penetration_fraction is not None:
            if not math.isfinite(target_penetration_fraction):
                errors.append("target_penetration_fraction must be finite")
            elif not 0.0 < target_penetration_fraction < 1.0:
                errors.append("target_penetration_fraction must be between 0 and 1")

        if hard_penetration_fraction is not None:
            if not math.isfinite(hard_penetration_fraction):
                errors.append("hard_penetration_fraction must be finite")
            elif not 0.0 < hard_penetration_fraction < 1.0:
                errors.append("hard_penetration_fraction must be between 0 and 1")

        if (
            target_penetration_fraction is not None
            and hard_penetration_fraction is not None
            and math.isfinite(target_penetration_fraction)
            and math.isfinite(hard_penetration_fraction)
            and hard_penetration_fraction <= target_penetration_fraction
        ):
            errors.append(
                "hard_penetration_fraction must be greater than "
                "target_penetration_fraction"
            )

        death_bounds = required_values("death_bounds", 6)
        if death_bounds:
            for axis, minimum, maximum in (
                ("x", death_bounds[0], death_bounds[1]),
                ("y", death_bounds[2], death_bounds[3]),
                ("z", death_bounds[4], death_bounds[5]),
            ):
                if minimum >= maximum:
                    errors.append(
                        f"death_bounds {axis}_min must be less than {axis}_max"
                    )

        raw_segments = self.itemcfg.get("curve_wall_segments")
        curve_segments = []
        if not raw_segments:
            errors.append("curve_wall_segments is required and must not be empty")
        else:
            for index, raw_segment in enumerate(raw_segments):
                if len(raw_segment) != 10:
                    errors.append(
                        f"curve_wall_segments[{index}] must contain 10 values"
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
                (
                    boundary_kind,
                    independent_axis,
                    u_start,
                    u_end,
                    _f_start,
                    _a1,
                    _a2,
                    _a3,
                    normal_sign,
                    wall_flag,
                ) = segment
                if (
                    not boundary_kind.is_integer()
                    or int(boundary_kind) not in (0, 1)
                ):
                    errors.append(
                        f"curve_wall_segments[{index}] boundary_kind must be 0 or 1"
                    )
                if (
                    not independent_axis.is_integer()
                    or int(independent_axis) not in (0, 1)
                ):
                    errors.append(
                        f"curve_wall_segments[{index}] independent_axis must be 0 or 1"
                    )
                if not wall_flag.is_integer() or int(wall_flag) <= 0:
                    errors.append(
                        f"curve_wall_segments[{index}] wall_flag must be a positive integer"
                    )
                if abs(u_end - u_start) <= 1.0e-12:
                    errors.append(f"curve_wall_segments[{index}] has zero length")
                if normal_sign == 0.0:
                    errors.append(
                        f"curve_wall_segments[{index}] normal_sign must not be zero"
                    )
                curve_segments.append(segment)

        particle_data = self.itemcfg.get("PARTICLE_DATA")
        particles = []
        if not particle_data:
            errors.append("PARTICLE_DATA is required and must not be empty")
        else:
            for index in range(len(particle_data)):
                name = f"p{index + 1}"
                particle = particle_data.get(name)
                if particle is None:
                    errors.append(f"PARTICLE_DATA.{name} is required")
                    continue
                try:
                    values = {
                        "name": name,
                        "x": float(particle.location.x1),
                        "y": float(particle.location.y1),
                        "z": float(particle.location.z1),
                        "vx": float(particle.vx),
                        "vy": float(particle.vy),
                        "vz": float(particle.get("vz", 0.0)),
                        "mass": float(particle.mass),
                        "radius": float(particle.radius),
                        "collision_stiffness_q": float(
                            particle.get(
                                "collision_stiffness_q",
                                self.itemcfg.get("collision_stiffness_q", 0.0),
                            )
                        ),
                    }
                except (AttributeError, TypeError, ValueError) as error:
                    errors.append(f"PARTICLE_DATA.{name} is invalid: {error}")
                    continue
                numeric_values = (
                    value for key, value in values.items() if key != "name"
                )
                if not all(math.isfinite(value) for value in numeric_values):
                    errors.append(f"PARTICLE_DATA.{name} values must be finite")
                if values["radius"] <= 0.0:
                    errors.append(f"PARTICLE_DATA.{name}.radius must be positive")
                if values["mass"] <= 0.0:
                    errors.append(f"PARTICLE_DATA.{name}.mass must be positive")
                if values["collision_stiffness_q"] < 0.0:
                    errors.append(
                        f"PARTICLE_DATA.{name}.collision_stiffness_q must not be negative"
                    )
                particles.append(values)

        if len(dimensions) == 3:
            width, height, depth = dimensions
            if death_bounds and (
                death_bounds[0] < 0.0
                or death_bounds[1] > width
                or death_bounds[2] < 0.0
                or death_bounds[3] > height
                or death_bounds[4] < 0.0
                or death_bounds[5] > depth
            ):
                errors.append("death_bounds must fit inside the cell array")
            for index, segment in enumerate(curve_segments):
                x_min, x_max, y_min, y_max = wall_bounds(segment)
                if x_min < 0.0 or x_max > width:
                    errors.append(
                        f"curve_wall_segments[{index}] x extent is outside the cell array"
                    )
                if y_min < 0.0 or y_max > height:
                    errors.append(
                        f"curve_wall_segments[{index}] y extent is outside the cell array"
                    )
            for index, particle in enumerate(particles, start=1):
                if not (
                    0.0 <= particle["x"] <= width
                    and 0.0 <= particle["y"] <= height
                    and 0.0 <= particle["z"] <= depth
                ):
                    errors.append(
                        f"PARTICLE_DATA.p{index} position is outside the cell array"
                    )

        if errors:
            raise ValueError(
                "GenericGenData configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )

        self.cell_array_width, self.cell_array_height, self.cell_array_depth = dimensions
        self.death_bounds = death_bounds
        self.curve_wall_segments = curve_segments
        self.explicit_particles = particles
        self.number_configured_particles = len(particles)
        self.particle_plane_z = particles[0]["z"]
        self.radius = float(self.itemcfg.radius)
        self.wall_contact_offset = float(self.itemcfg.wall_contact_offset)
        self.dt = float(self.itemcfg.dt)
        self.cell_occupancy_list_size = int(self.itemcfg.cell_occupancy_list_size)
        return True

    def report_collision_feasibility(self):
        """Print a kinematic collision timing estimate for configured particles."""
        if len(self.explicit_particles) < 2:
            report_text = "Collision Feasibility: fewer than two mobile particles"
            print(report_text)
            self.write_validation_log(report_text)
            return []

        dt = float(self.dt)
        target_penetration_fraction = float(
            self.itemcfg.get(
                "target_penetration_fraction",
                self.itemcfg.get("max_penetration_fraction", 0.5),
            )
        )
        hard_penetration_fraction = float(
            self.itemcfg.get("hard_penetration_fraction", 0.75)
        )
        min_compression_frames = float(
            self.itemcfg.get("min_compression_frames", 3.0)
        )
        compression_stiffness_gain = max(
            0.0,
            float(self.itemcfg.get("compression_stiffness_gain", 0.0)),
        )
        compression_stiffness_power = max(
            0.0,
            float(self.itemcfg.get("compression_stiffness_power", 2.0)),
        )
        reports = []

        lines = [
            "Collision Feasibility:",
            f"  minimum compression frames: {min_compression_frames:.3f}",
        ]
        for source_index, source in enumerate(self.explicit_particles):
            for target in self.explicit_particles[source_index + 1 :]:
                dx = target["x"] - source["x"]
                dy = target["y"] - source["y"]
                dz = target["z"] - source["z"]
                center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if center_distance <= 1.0e-12:
                    normal_x, normal_y, normal_z = 1.0, 0.0, 0.0
                else:
                    normal_x = dx / center_distance
                    normal_y = dy / center_distance
                    normal_z = dz / center_distance

                relative_velocity_x = source["vx"] - target["vx"]
                relative_velocity_y = source["vy"] - target["vy"]
                relative_velocity_z = source["vz"] - target["vz"]
                relative_normal_speed = (
                    relative_velocity_x * normal_x
                    + relative_velocity_y * normal_y
                    + relative_velocity_z * normal_z
                )

                contact_distance = source["radius"] + target["radius"]
                initial_gap = center_distance - contact_distance
                per_frame_closing_distance = max(0.0, relative_normal_speed) * dt
                target_penetration_depth = (
                    target_penetration_fraction * source["radius"]
                )
                hard_penetration_depth = (
                    hard_penetration_fraction * source["radius"]
                )
                if target_penetration_depth > 0.0:
                    target_depth_step_fraction = (
                        per_frame_closing_distance / target_penetration_depth
                    )
                else:
                    target_depth_step_fraction = math.inf
                if hard_penetration_depth > 0.0:
                    hard_depth_step_fraction = (
                        per_frame_closing_distance / hard_penetration_depth
                    )
                else:
                    hard_depth_step_fraction = math.inf

                if initial_gap <= 0.0:
                    frames_to_first_contact = 0.0
                elif per_frame_closing_distance > 0.0:
                    frames_to_first_contact = initial_gap / per_frame_closing_distance
                else:
                    frames_to_first_contact = math.inf

                if per_frame_closing_distance > 0.0:
                    frames_to_target_depth = (
                        target_penetration_depth / per_frame_closing_distance
                    )
                    frames_to_hard_depth = (
                        hard_penetration_depth / per_frame_closing_distance
                    )
                else:
                    frames_to_target_depth = math.inf
                    frames_to_hard_depth = math.inf
                time_to_first_contact = frames_to_first_contact * dt
                time_to_target_depth = frames_to_target_depth * dt
                time_to_hard_depth = frames_to_hard_depth * dt

                stiffness_at_contact = min(
                    source["collision_stiffness_q"],
                    target["collision_stiffness_q"],
                )
                if (
                    compression_stiffness_gain > 0.0
                    and hard_penetration_depth > 0.0
                ):
                    target_compression_fraction = max(
                        0.0,
                        min(1.0, target_penetration_depth / hard_penetration_depth),
                    )
                    hard_compression_fraction = 1.0
                    effective_stiffness_at_target = stiffness_at_contact * (
                        1.0
                        + compression_stiffness_gain
                        * (target_compression_fraction ** compression_stiffness_power)
                    )
                    effective_stiffness_at_hard = stiffness_at_contact * (
                        1.0
                        + compression_stiffness_gain
                        * (hard_compression_fraction ** compression_stiffness_power)
                    )
                else:
                    effective_stiffness_at_target = stiffness_at_contact
                    effective_stiffness_at_hard = stiffness_at_contact
                force_at_target_depth = (
                    effective_stiffness_at_target * target_penetration_depth
                )
                source_dv_per_frame_at_max = (
                    force_at_target_depth / source["mass"]
                ) * dt
                target_dv_per_frame_at_max = (
                    force_at_target_depth / target["mass"]
                ) * dt
                relative_dv_per_frame_at_max = (
                    source_dv_per_frame_at_max + target_dv_per_frame_at_max
                )
                response_mass_factor = (1.0 / source["mass"]) + (
                    1.0 / target["mass"]
                )
                if (
                    relative_normal_speed > 0.0
                    and frames_to_target_depth > 0.0
                    and math.isfinite(frames_to_target_depth)
                    and target_penetration_depth > 0.0
                    and dt > 0.0
                    and response_mass_factor > 0.0
                ):
                    required_stiffness_for_max_depth = relative_normal_speed / (
                        frames_to_target_depth
                        * target_penetration_depth
                        * dt
                        * response_mass_factor
                    )
                else:
                    required_stiffness_for_max_depth = 0.0
                if relative_normal_speed <= 0.0:
                    frames_to_cancel_relative_speed = 0.0
                elif relative_dv_per_frame_at_max > 0.0:
                    frames_to_cancel_relative_speed = (
                        relative_normal_speed / relative_dv_per_frame_at_max
                    )
                else:
                    frames_to_cancel_relative_speed = math.inf
                time_to_cancel_relative_speed = (
                    frames_to_cancel_relative_speed * dt
                )

                if relative_normal_speed <= 0.0:
                    status = "OPENING"
                elif frames_to_hard_depth < 1.0:
                    status = "ERROR"
                elif frames_to_target_depth < min_compression_frames:
                    status = "WARNING"
                elif frames_to_cancel_relative_speed > frames_to_target_depth:
                    status = "WARNING_STIFFNESS"
                else:
                    status = "OK"

                lines.extend(
                    [
                        f"  source pair: {source['name']} -> {target['name']}",
                        f"  initial gap: {initial_gap:.6f}",
                        "  relative normal speed: "
                        f"{max(0.0, relative_normal_speed):.6f}",
                        "  per-frame closing distance: "
                        f"{per_frame_closing_distance:.6f}",
                        "  frames to first contact: "
                        f"{frames_to_first_contact:.3f}",
                        "  time to first contact: "
                        f"{time_to_first_contact:.6f}",
                        "  target penetration depth: "
                        f"{target_penetration_depth:.6f}",
                        "  hard penetration depth: "
                        f"{hard_penetration_depth:.6f}",
                        "  target-depth step fraction: "
                        f"{target_depth_step_fraction:.6f}",
                        "  hard-depth step fraction: "
                        f"{hard_depth_step_fraction:.6f}",
                        "  frames from contact to target depth: "
                        f"{frames_to_target_depth:.3f}",
                        "  time from contact to target depth: "
                        f"{time_to_target_depth:.6f}",
                        "  frames from contact to hard depth: "
                        f"{frames_to_hard_depth:.3f}",
                        "  time from contact to hard depth: "
                        f"{time_to_hard_depth:.6f}",
                        "  stiffness at contact: "
                        f"{stiffness_at_contact:.6f}",
                        "  compression stiffness gain: "
                        f"{compression_stiffness_gain:.6f}",
                        "  compression stiffness power: "
                        f"{compression_stiffness_power:.6f}",
                        "  effective stiffness at target depth: "
                        f"{effective_stiffness_at_target:.6f}",
                        "  effective stiffness at hard depth: "
                        f"{effective_stiffness_at_hard:.6f}",
                        "  force at target depth: "
                        f"{force_at_target_depth:.6f}",
                        "  source dv/frame at max: "
                        f"{source_dv_per_frame_at_max:.6f}",
                        "  target dv/frame at max: "
                        f"{target_dv_per_frame_at_max:.6f}",
                        "  relative dv/frame at max: "
                        f"{relative_dv_per_frame_at_max:.6f}",
                        "  frames to cancel relative speed: "
                        f"{frames_to_cancel_relative_speed:.3f}",
                        "  time to cancel relative speed: "
                        f"{time_to_cancel_relative_speed:.6f}",
                        "  required stiffness for max-depth response: "
                        f"{required_stiffness_for_max_depth:.6f}",
                        f"  status: {status}",
                    ]
                )

                reports.append(
                    {
                        "source": source["name"],
                        "target": target["name"],
                        "initial_gap": initial_gap,
                        "relative_normal_speed": relative_normal_speed,
                        "per_frame_closing_distance": per_frame_closing_distance,
                        "frames_to_first_contact": frames_to_first_contact,
                        "time_to_first_contact": time_to_first_contact,
                        "target_penetration_depth": target_penetration_depth,
                        "hard_penetration_depth": hard_penetration_depth,
                        "target_depth_step_fraction": target_depth_step_fraction,
                        "hard_depth_step_fraction": hard_depth_step_fraction,
                        "frames_to_target_depth": frames_to_target_depth,
                        "time_to_target_depth": time_to_target_depth,
                        "frames_to_hard_depth": frames_to_hard_depth,
                        "time_to_hard_depth": time_to_hard_depth,
                        "stiffness_at_contact": stiffness_at_contact,
                        "compression_stiffness_gain": compression_stiffness_gain,
                        "compression_stiffness_power": compression_stiffness_power,
                        "effective_stiffness_at_target": effective_stiffness_at_target,
                        "effective_stiffness_at_hard": effective_stiffness_at_hard,
                        "force_at_target_depth": force_at_target_depth,
                        "source_dv_per_frame_at_max": source_dv_per_frame_at_max,
                        "target_dv_per_frame_at_max": target_dv_per_frame_at_max,
                        "relative_dv_per_frame_at_max": relative_dv_per_frame_at_max,
                        "frames_to_cancel_relative_speed": frames_to_cancel_relative_speed,
                        "time_to_cancel_relative_speed": time_to_cancel_relative_speed,
                        "required_stiffness_for_max_depth": required_stiffness_for_max_depth,
                        "status": status,
                    }
                )

        report_text = "\n".join(lines)
        print(report_text)
        self.write_validation_log(report_text)
        return reports

    def initialize_generation(self):
        self.p_list = []
        self.bin_file = None
        self.count = 0
        self.number_particles = 0
        self.number_active_particles = 0
        self.number_boundary_particles = 0

        output_prefix = str(
            self.itemcfg.get("output_file_prefix", self.itemcfg.STUDY_NAME)
        )
        output_directory = str(self.itemcfg.data_dir)
        os.makedirs(output_directory, exist_ok=True)
        self.test_bin_name = os.path.join(output_directory, f"{output_prefix}.bin")
        self.test_file_name = os.path.join(output_directory, f"{output_prefix}.tst")
        self.report_file = os.path.join(output_directory, f"{output_prefix}.rpt")
        self.validation_log_name = os.path.join(output_directory, f"{output_prefix}.log")
        with open(self.validation_log_name, "w", encoding="ascii", newline="\n") as output:
            output.write(
                "Function-wall particle validation log\n"
                f"  output prefix: {output_prefix}\n"
            )
        configured_obj_file = self.itemcfg.get("obj_file_name")
        if configured_obj_file:
            self.obj_file_name = os.path.normpath(str(configured_obj_file))
        else:
            self.obj_file_name = os.path.join(
                output_directory,
                f"{output_prefix}.obj",
            )

    def write_validation_log(self, text):
        with open(self.validation_log_name, "a", encoding="ascii", newline="\n") as output:
            output.write(text.rstrip())
            output.write("\n")

    def add_null_particle(self):
        particle = pdata()
        particle.pnum = 0
        particle.ptype = PTYPE_NULL
        self.p_list.append(particle)
        return particle

    def add_mobile_particle(
        self,
        position,
        velocity,
        radius=None,
        mass=1.0,
        collision_stiffness_q=None,
    ):
        particle = pdata()
        self.number_particles += 1
        self.number_active_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = PTYPE_MOBILE
        particle.rx, particle.ry, particle.rz = position
        particle.vx, particle.vy, particle.vz = velocity
        particle.radius = self.radius if radius is None else radius
        particle.molar_mass = mass
        particle.state_flg = 0.0
        particle.collision_stiffness_q = (
            float(self.itemcfg.get("collision_stiffness_q", 0.0))
            if collision_stiffness_q is None
            else collision_stiffness_q
        )
        self.p_list.append(particle)
        return particle

    def add_explicit_mobile_particles(self):
        """Create the mobile particles declared by PARTICLE_DATA."""
        for configured in self.explicit_particles:
            self.add_mobile_particle(
                (configured["x"], configured["y"], configured["z"]),
                (configured["vx"], configured["vy"], configured["vz"]),
                radius=configured["radius"],
                mass=configured["mass"],
                collision_stiffness_q=configured["collision_stiffness_q"],
            )

        if self.number_active_particles != self.number_configured_particles:
            raise RuntimeError(
                "generated mobile-particle count does not match PARTICLE_DATA"
            )
        return self.number_active_particles

    def add_boundary_particle(self, position):
        particle = pdata()
        self.number_particles += 1
        self.number_boundary_particles += 1
        particle.pnum = self.number_particles
        particle.ptype = self.BOUNDARY_PARTICLE_PTYPE
        particle.rx, particle.ry, particle.rz = position
        particle.vx = 0.0
        particle.vy = 0.0
        particle.vz = 0.0
        particle.radius = self.radius
        particle.molar_mass = 1.0
        particle.state_flg = 0.0
        particle.collision_stiffness_q = 0.0
        self.p_list.append(particle)
        return particle

    def curve_marker_points(self, segment, maximum_spacing=1.0):
        """Return sampled points used only for boundary-sentinel placement."""
        return sample_points(segment, maximum_spacing)

    def add_function_wall_markers(self):
        """Create deduplicated boundary-sentinel markers along wall segments."""
        marker_cells = set()
        segment_marker_counts = []

        for segment in self.curve_wall_segments:
            wall_flag = int(round(segment[9]))
            points = self.curve_marker_points(segment)
            added_for_segment = 0
            for marker_x, marker_y in points:
                cell_x = round(marker_x)
                cell_y = round(marker_y)
                cell_z = round(self.particle_plane_z)
                marker_cell_key = (
                    cell_x,
                    cell_y,
                    cell_z,
                    wall_flag,
                )
                if marker_cell_key in marker_cells:
                    continue
                marker_cells.add(marker_cell_key)
                self.add_boundary_particle(
                    (float(cell_x), float(cell_y), float(cell_z))
                )
                added_for_segment += 1
            segment_marker_counts.append(added_for_segment)

        report_text = (
            "Function wall-marker report:\n"
            f"  curve segments: {len(self.curve_wall_segments)}\n"
            f"  unique boundary markers: {self.number_boundary_particles}\n"
            f"  boundary ptype: {self.BOUNDARY_PARTICLE_PTYPE:g}\n"
            f"  markers added per segment: {segment_marker_counts}\n"
            "  occupancy rule: boundary markers are cell-locality sentinels\n"
            "  marker position: integer cell center\n"
            "  maximum sampled function interval: 1 cell"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_boundary_particles

    def write_function_wall_obj(self):
        """Write triangle ribbons sampled from function-wall paths."""
        half_thickness = 0.25
        vertices = []
        faces = []

        for segment in self.curve_wall_segments:
            points = self.curve_marker_points(segment)
            segment_vertices = []

            for point_index, (point_x, point_y) in enumerate(points):
                if len(points) == 1:
                    tangent_x, tangent_y = 1.0, 0.0
                elif point_index == 0:
                    next_x, next_y = points[point_index + 1]
                    tangent_x = next_x - point_x
                    tangent_y = next_y - point_y
                else:
                    previous_x, previous_y = points[point_index - 1]
                    tangent_x = point_x - previous_x
                    tangent_y = point_y - previous_y
                tangent_length = math.hypot(tangent_x, tangent_y)
                if tangent_length <= 1.0e-12:
                    raise RuntimeError(
                        "cannot generate OBJ ribbon from a zero-length wall sample"
                    )

                normal_x = -tangent_y / tangent_length
                normal_y = tangent_x / tangent_length
                first_index = len(vertices) + 1
                vertices.append(
                    (
                        point_x + half_thickness * normal_x,
                        point_y + half_thickness * normal_y,
                        self.particle_plane_z,
                    )
                )
                vertices.append(
                    (
                        point_x - half_thickness * normal_x,
                        point_y - half_thickness * normal_y,
                        self.particle_plane_z,
                    )
                )
                segment_vertices.append((first_index, first_index + 1))

            for index in range(len(segment_vertices) - 1):
                outer_a, inner_a = segment_vertices[index]
                outer_b, inner_b = segment_vertices[index + 1]
                faces.append((outer_a, outer_b, inner_b))
                faces.append((outer_a, inner_b, inner_a))

        os.makedirs(os.path.dirname(self.obj_file_name), exist_ok=True)
        with open(self.obj_file_name, "w", encoding="ascii", newline="\n") as output:
            output.write("# Generated from function-wall curve_wall_segments.\n")
            output.write("# Dynamics use boundary particles; this mesh is visual only.\n")
            output.write("o GeneratedFunctionWalls\n")
            for vertex_x, vertex_y, vertex_z in vertices:
                output.write(
                    f"v {vertex_x:.9f} {vertex_y:.9f} {vertex_z:.9f}\n"
                )
            for _ in vertices:
                output.write("vt 0.0 0.0\n")
            output.write("vn 0.0 0.0 1.0\n")
            output.write("vn 0.0 0.0 -1.0\n")
            for first, second, third in faces:
                output.write(
                    f"f {first}/{first}/1 {second}/{second}/1 {third}/{third}/1\n"
                )
                output.write(
                    f"f {third}/{third}/2 {second}/{second}/2 {first}/{first}/2\n"
                )

        report_text = (
            "Function wall OBJ report:\n"
            f"  file: {self.obj_file_name}\n"
            f"  vertices: {len(vertices)}\n"
            f"  triangles: {2 * len(faces)}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.obj_file_name

    def report_generated_bounds(self):
        """Report generated mobile-particle center and perimeter bounds."""
        mobile_particles = [
            particle
            for particle in self.p_list
            if int(round(float(particle.ptype))) == int(PTYPE_MOBILE)
            and int(round(float(particle.pnum))) != 0
        ]
        if not mobile_particles:
            report_text = "Generic particle generated bounds: no mobile particles"
            print(report_text)
            self.write_validation_log(report_text)
            return None

        center_bounds = (
            min(particle.rx for particle in mobile_particles),
            max(particle.rx for particle in mobile_particles),
            min(particle.ry for particle in mobile_particles),
            max(particle.ry for particle in mobile_particles),
            min(particle.rz for particle in mobile_particles),
            max(particle.rz for particle in mobile_particles),
        )
        perimeter_bounds = (
            min(particle.rx - particle.radius for particle in mobile_particles),
            max(particle.rx + particle.radius for particle in mobile_particles),
            min(particle.ry - particle.radius for particle in mobile_particles),
            max(particle.ry + particle.radius for particle in mobile_particles),
            min(particle.rz - particle.radius for particle in mobile_particles),
            max(particle.rz + particle.radius for particle in mobile_particles),
        )
        report_text = (
            "Generic particle generated bounds:\n"
            f"  center x: [{center_bounds[0]:g}, {center_bounds[1]:g}]\n"
            f"  center y: [{center_bounds[2]:g}, {center_bounds[3]:g}]\n"
            f"  center z: [{center_bounds[4]:g}, {center_bounds[5]:g}]\n"
            f"  perimeter x: [{perimeter_bounds[0]:g}, "
            f"{perimeter_bounds[1]:g}]\n"
            f"  perimeter y: [{perimeter_bounds[2]:g}, "
            f"{perimeter_bounds[3]:g}]\n"
            f"  perimeter z: [{perimeter_bounds[4]:g}, "
            f"{perimeter_bounds[5]:g}]"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return center_bounds, perimeter_bounds

    @staticmethod
    def next_power_of_two(value):
        value = int(math.ceil(float(value)))
        if value <= 1:
            return 1
        return 1 << (value - 1).bit_length()

    def cell_location_from_indices(self, cell_x, cell_y, cell_z):
        return (
            cell_x
            + self.cell_array_width
            * (cell_y + self.cell_array_height * cell_z)
        )

    def particle_cell_indices(self, particle):
        return (
            int(math.floor(float(particle.rx))),
            int(math.floor(float(particle.ry))),
            int(math.floor(float(particle.rz))),
        )

    def particle_corner_cell_indices(self, particle):
        radius = float(particle.radius)
        x_values = {
            int(math.floor(float(particle.rx) - radius)),
            int(math.floor(float(particle.rx) + radius)),
        }
        y_values = {
            int(math.floor(float(particle.ry) - radius)),
            int(math.floor(float(particle.ry) + radius)),
        }
        z_values = {
            int(math.floor(float(particle.rz) - radius)),
            int(math.floor(float(particle.rz) + radius)),
        }
        cells = set()
        for cell_x in x_values:
            for cell_y in y_values:
                for cell_z in z_values:
                    cells.add((cell_x, cell_y, cell_z))
        return cells

    def is_valid_cell_index(self, cell_x, cell_y, cell_z):
        return (
            0 <= cell_x < self.cell_array_width
            and 0 <= cell_y < self.cell_array_height
            and 0 <= cell_z < self.cell_array_depth
        )

    def report_cell_occupancy_capacity(self):
        """Report initial occupancy against configured Vulkan cell-list capacity."""
        center_occupancy = {}
        corner_occupancy = {}
        out_of_bounds = []

        for particle in self.p_list:
            if int(round(float(particle.pnum))) == 0:
                continue

            center_cell = self.particle_cell_indices(particle)
            if self.is_valid_cell_index(*center_cell):
                center_loc = self.cell_location_from_indices(*center_cell)
                center_occupancy.setdefault(center_loc, []).append(particle.pnum)
            else:
                out_of_bounds.append((particle.pnum, center_cell))

            for corner_cell in self.particle_corner_cell_indices(particle):
                if not self.is_valid_cell_index(*corner_cell):
                    out_of_bounds.append((particle.pnum, corner_cell))
                    continue
                corner_loc = self.cell_location_from_indices(*corner_cell)
                corner_occupancy.setdefault(corner_loc, set()).add(particle.pnum)

        def max_entry(occupancy):
            if not occupancy:
                return 0, None
            location, particles = max(
                occupancy.items(),
                key=lambda item: len(item[1]),
            )
            return len(particles), location

        max_center_count, max_center_location = max_entry(center_occupancy)
        max_corner_count, max_corner_location = max_entry(corner_occupancy)
        headroom_factor = float(
            self.itemcfg.get("cell_occupancy_runtime_headroom_factor", 1.25)
        )
        recommended_size = self.next_power_of_two(
            max_corner_count * max(1.0, headroom_factor)
        )
        configured_size = int(self.cell_occupancy_list_size)
        runtime_headroom = configured_size - max_corner_count

        if configured_size < max_corner_count:
            status = "ERROR"
        elif configured_size < recommended_size:
            status = "WARNING_HEADROOM"
        else:
            status = "OK"

        report_text = (
            "Cell occupancy capacity report:\n"
            f"  configured cell_occupancy_list_size: {configured_size}\n"
            f"  initial max center occupancy: {max_center_count}"
            f" at loc {max_center_location}\n"
            f"  initial max corner occupancy: {max_corner_count}"
            f" at loc {max_corner_location}\n"
            f"  runtime headroom factor: {headroom_factor:g}\n"
            f"  runtime headroom slots: {runtime_headroom}\n"
            f"  recommended cell_occupancy_list_size: {recommended_size}\n"
            f"  out-of-bounds cell references: {len(out_of_bounds)}\n"
            f"  status: {status}"
        )
        print(report_text)
        self.write_validation_log(report_text)

        if out_of_bounds:
            sample = ", ".join(
                f"p{int(pnum)}->{cell}" for pnum, cell in out_of_bounds[:8]
            )
            raise RuntimeError(
                "generated particle occupancy references cells outside the "
                f"cell array: {sample}"
            )
        if configured_size < max_corner_count:
            raise RuntimeError(
                "cell_occupancy_list_size is too small for the generated "
                f"initial state: configured {configured_size}, initial "
                f"corner occupancy {max_corner_count}"
            )
        return {
            "configured_size": configured_size,
            "max_center_count": max_center_count,
            "max_center_location": max_center_location,
            "max_corner_count": max_corner_count,
            "max_corner_location": max_corner_location,
            "recommended_size": recommended_size,
            "status": status,
        }

    def create_bin_file(self):
        os.makedirs(str(self.itemcfg.data_dir), exist_ok=True)
        self.bin_file = open(self.test_bin_name, "wb")
        self.count = 0

    def write_bin_file(self):
        if self.bin_file is None:
            raise RuntimeError("binary output file is not open")
        for particle in self.p_list:
            self.bin_file.write(particle)
            self.count += 1

    def close_bin_file(self):
        if self.bin_file is None:
            return
        self.bin_file.flush()
        self.bin_file.close()
        self.bin_file = None

    def write_particle_bin(self):
        self.create_bin_file()
        try:
            self.write_bin_file()
        finally:
            self.close_bin_file()
        return self.test_bin_name

    def write_test_file(self):
        """Write Vulkan metadata for the function-wall particle simulation."""
        particle_data_bin_file = self.test_bin_name.replace(os.sep, "/")
        report_file = self.report_file.replace(os.sep, "/")
        view_center = self.itemcfg.get(
            "view_center",
            (
                0.5 * self.cell_array_width,
                0.5 * self.cell_array_height,
                0.5 * self.cell_array_depth,
            ),
        )
        (
            death_x_min,
            death_x_max,
            death_y_min,
            death_y_max,
            death_z_min,
            death_z_max,
        ) = self.death_bounds

        try:
            output = open(self.test_file_name, "w", encoding="ascii")
        except OSError as error:
            raise OSError(
                f"Could not create test file {self.test_file_name}: {error}"
            ) from error

        with output:
            output.write("index = 0;\n")
            output.write(f"CellAryW = {self.cell_array_width};\n")
            output.write(f"CellAryH = {self.cell_array_height};\n")
            output.write(f"CellAryL = {self.cell_array_depth};\n")
            output.write(
                "view_center = ["
                f"{float(view_center[0]):.9f}, "
                f"{float(view_center[1]):.9f}, "
                f"{float(view_center[2]):.9f}];\n"
            )
            output.write(f"radius = {self.radius:.9f};\n")
            output.write(f"num_particles = {self.number_particles};\n")
            output.write("particles_per_cell = 0;\n")
            output.write("num_particle_colliding = 0;\n")
            output.write("exp_collisions_per_cell = 0;\n")
            output.write("act_collisions_per_cell = 0;\n")
            output.write("particles_in_row = 0;\n")
            output.write("collsion_density = 0.0;\n")
            output.write("pdensity = 0.0;\n")
            output.write(
                f'particle_data_bin_file = "{particle_data_bin_file}";\n'
            )
            output.write(f'report_file = "{report_file}";\n')
            output.write(f"dispatchx = {self.number_active_particles + 1};\n")
            output.write(f"dispatchy = {int(self.itemcfg.dispatchy)};\n")
            output.write(f"dispatchz = {int(self.itemcfg.dispatchz)};\n")
            output.write(f"workGroupsx = {int(self.itemcfg.workGroupsx)};\n")
            output.write(f"workGroupsy = {int(self.itemcfg.workGroupsy)};\n")
            output.write(f"workGroupsz = {int(self.itemcfg.workGroupsz)};\n")
            output.write(
                "cell_occupancy_list_size = "
                f"{self.cell_occupancy_list_size};\n"
            )

            output.write(f"death_x_min = {death_x_min:.9f};\n")
            output.write(f"death_x_max = {death_x_max:.9f};\n")
            output.write(f"death_y_min = {death_y_min:.9f};\n")
            output.write(f"death_y_max = {death_y_max:.9f};\n")
            output.write(f"death_z_min = {death_z_min:.9f};\n")
            output.write(f"death_z_max = {death_z_max:.9f};\n")

            output.write("curve_wall_segments = (\n")
            for segment_index, segment in enumerate(self.curve_wall_segments):
                separator = (
                    "," if segment_index + 1 < len(self.curve_wall_segments) else ""
                )
                values = ", ".join(f"{float(value):.9f}" for value in segment)
                output.write(f"    [{values}]{separator}\n")
            output.write(");\n")

            output.write(f"wall_contact_offset = {self.wall_contact_offset:.9f};\n")
            output.write(
                "compression_stiffness_gain = "
                f"{float(self.itemcfg.get('compression_stiffness_gain', 0.0)):.9f};\n"
            )
            output.write(
                "compression_stiffness_power = "
                f"{float(self.itemcfg.get('compression_stiffness_power', 2.0)):.9f};\n"
            )
            output.write(f"DT = {self.dt:.9f};\n")
            output.write(
                "contact_force_measure = "
                f'"{self.itemcfg.get("contact_force_measure", "depth")}";\n'
            )
            output.write(
                f"hsv_color = {1 if self.itemcfg.get('hsv_color', False) else 0};\n"
            )
            output.write(f"hsv_sat = {float(self.itemcfg.hsv_sat):.9f};\n")
            output.write(f"hsv_val = {float(self.itemcfg.hsv_val):.9f};\n")
            output.write(
                f"as_points = {1 if self.itemcfg.get('as_points', False) else 0};\n"
            )
            output.write(
                "presentation_quality = "
                f"{1 if self.itemcfg.get('presentation_quality', False) else 0};\n"
            )
            output.write(
                "dynamics_diagnostics = "
                f"{1 if self.itemcfg.get('dynamics_diagnostics', True) else 0};\n"
            )
            output.write(
                f"grid_on = {1 if self.itemcfg.get('grid_on', False) else 0};\n"
            )

        report_text = (
            "Function-wall particle test-file report:\n"
            f"  file: {self.test_file_name}\n"
            f"  particle records excluding null: {self.number_particles}\n"
            f"  mobile compute records including null: "
            f"{self.number_active_particles + 1}\n"
            f"  curve segments: {len(self.curve_wall_segments)}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.test_file_name

    def runner(self):
        try:
            self.validate_simulation_configuration()
        except (AttributeError, TypeError, ValueError) as error:
            print(
                "Function-wall particle configuration validation stopped:\n"
                f"{error}"
            )
            return False

        self.initialize_generation()
        try:
            self.report_collision_feasibility()
            self.add_null_particle()
            self.add_explicit_mobile_particles()
            self.add_function_wall_markers()
            self.report_cell_occupancy_capacity()
            self.write_particle_bin()
            self.write_test_file()
            self.report_generated_bounds()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.close_bin_file()
            print(
                "Generic particle generation stopped:\n"
                f"{type(error).__name__}: {error}"
            )
            return False

        report_text = (
            "Generic particle generation complete:\n"
            f"  binary file: {self.test_bin_name}\n"
            f"  records: {self.count}\n"
            f"  mobile particles: {self.number_active_particles}\n"
            f"  boundary markers: {self.number_boundary_particles}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return True
