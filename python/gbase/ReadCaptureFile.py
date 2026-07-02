import csv
import re
from pathlib import Path

import numpy as np


lstr_dtype = np.dtype([
    ("pindex", np.uint32),
    ("ploc", np.uint32),
    ("fill", np.uint32),
])

particle_dtype = np.dtype([
    ("PosLocA", np.float32, 4),
    ("PosLocB", np.float32, 4),
    ("VelRadA", np.float32, 4),
    ("VelRadB", np.float32, 4),
    ("Data", np.float32, 4),
    ("parms", np.float32, 4),
    ("CornerList", lstr_dtype, 8),
    ("contactCount", np.uint32),
    ("colFlg", np.uint32),
    ("ptype", np.float32),
    ("temp_vel", np.float32),
])

input_particle_dtype = np.dtype([
    ("pnum", np.float64),
    ("rx", np.float64),
    ("ry", np.float64),
    ("rz", np.float64),
    ("radius", np.float64),
    ("vx", np.float64),
    ("vy", np.float64),
    ("vz", np.float64),
    ("ptype", np.float64),
    ("state_flg", np.float64),
    ("molar_mass", np.float64),
    ("temp_vel", np.float64),
    ("collision_stiffness_q", np.float64),
])

CSV_FIELDS = [
    "record_type", "source_file", "frame", "particle_count",
    "active_count", "waiting_count", "dead_count", "boundary_count",
    "momentum_x", "momentum_y", "momentum_z", "momentum_magnitude",
    "kinetic_energy", "upstream_count", "max_speed",
    "reverse_momentum_x", "reverse_momentum_y", "reverse_momentum_z",
    "reverse_momentum_magnitude", "reverse_flow_momentum",
    "reverse_kinetic_energy", "reverse_max_speed",
    "reverse_max_particle_momentum", "reverse_max_particle_kinetic_energy",
    "baseline_momentum_x", "baseline_momentum_y", "baseline_momentum_z",
    "baseline_momentum_magnitude", "baseline_kinetic_energy",
    "delta_momentum_x", "delta_momentum_y", "delta_momentum_z",
    "delta_momentum_magnitude", "delta_kinetic_energy",
]


class ReadCaptureFile:
    def __init__(self):
        self.bin_path = None
        self.capture_path = None
        self.initial_particles = None
        self.capture_particles = None

    @staticmethod
    def _resolve_bin_path(filename):
        path = Path(filename)
        if path.suffix.lower() != ".bin":
            raise ValueError(f"Expected a .bin file, received: {path}")
        return path

    def ReadBinFile(self, filename):
        self.bin_path = self._resolve_bin_path(filename).resolve()
        if not self.bin_path.exists():
            raise FileNotFoundError(self.bin_path)
        self.initial_particles = np.fromfile(self.bin_path, dtype=input_particle_dtype)
        print(f"Initial particle count: {len(self.initial_particles)}")

    @staticmethod
    def FindCaptureFiles(bin_filename):
        bin_path = Path(bin_filename).resolve()
        if bin_path.suffix.lower() != ".bin":
            raise ValueError(f"Expected a .bin file, received: {bin_path}")

        capture_files = list(bin_path.parent.glob(f"{bin_path.stem}_*.cap"))
        return sorted(
            capture_files,
            key=lambda path: (int(ReadCaptureFile._frame_from_name(path) or -1), path.name),
        )

    def ReadCapFile(self, filename):
        self.capture_path = Path(filename).resolve()
        if not self.capture_path.exists():
            raise FileNotFoundError(self.capture_path)
        self.capture_particles = np.fromfile(self.capture_path, dtype=particle_dtype)
        print(f"Captured particle count: {len(self.capture_particles)}")

    @staticmethod
    def _totals(mass, velocity):
        mass = np.asarray(mass, dtype=np.float64)
        velocity = np.asarray(velocity, dtype=np.float64)
        if len(mass) == 0:
            return np.zeros(3, dtype=np.float64), 0.0, 0.0
        momentum = np.sum(mass[:, None] * velocity, axis=0, dtype=np.float64)
        speed_squared = np.sum(velocity * velocity, axis=1, dtype=np.float64)
        kinetic_energy = float(np.sum(0.5 * mass * speed_squared, dtype=np.float64))
        return momentum, kinetic_energy, float(np.sqrt(np.max(speed_squared)))

    @staticmethod
    def _frame_from_name(path):
        matches = re.findall(r"(\d+)", path.stem)
        return matches[-1] if matches else ""

    @staticmethod
    def _put_vector(row, prefix, vector):
        row[f"{prefix}_x"] = float(vector[0])
        row[f"{prefix}_y"] = float(vector[1])
        row[f"{prefix}_z"] = float(vector[2])
        row[f"{prefix}_magnitude"] = float(np.linalg.norm(vector))

    def _initial_row(self):
        particles = self.initial_particles
        mobile = (np.arange(len(particles)) > 0) & (particles["ptype"] <= 0.5)
        velocity = np.column_stack((particles["vx"], particles["vy"], particles["vz"]))
        momentum, kinetic_energy, max_speed = self._totals(
            particles["molar_mass"][mobile], velocity[mobile]
        )
        row = {
            "record_type": "INITIAL",
            "source_file": str(self.bin_path),
            "frame": 0,
            "particle_count": len(particles),
            "active_count": int(np.count_nonzero(mobile)),
            "waiting_count": 0,
            "dead_count": 0,
            "boundary_count": int(np.count_nonzero(particles["ptype"] > 0.5)),
            "kinetic_energy": kinetic_energy,
            "upstream_count": int(np.count_nonzero(mobile & (particles["vx"] < 0.0))),
            "max_speed": max_speed,
        }
        self._put_vector(row, "momentum", momentum)
        return row

    def _flow_direction(self):
        particles = self.initial_particles
        mobile = (np.arange(len(particles)) > 0) & (particles["ptype"] <= 0.5)
        velocity = np.column_stack((particles["vx"], particles["vy"], particles["vz"]))
        momentum, _, _ = self._totals(particles["molar_mass"][mobile], velocity[mobile])
        magnitude = np.linalg.norm(momentum)
        if magnitude <= 1.0e-12:
            raise ValueError("Cannot determine flow direction from zero initial momentum")
        return momentum / magnitude

    def _capture_row(self):
        initial = self.initial_particles
        captured = self.capture_particles
        if len(initial) != len(captured):
            raise ValueError(
                f"Particle count mismatch: initial={len(initial)}, capture={len(captured)}"
            )

        indices = np.arange(len(captured))
        mobile = (indices > 0) & (captured["ptype"] <= 0.5)
        life = captured["Data"][:, 3]
        active = mobile & np.isclose(life, 0.0, atol=1.0e-6)
        waiting = mobile & (life > 1.0e-6)
        dead = mobile & (life < -1.0e-6)
        boundary = captured["ptype"] > 0.5

        use_a = np.isclose(captured["PosLocA"][:, 3], 0.0)
        capture_velocity = np.where(
            use_a[:, None],
            captured["VelRadA"][:, :3],
            captured["VelRadB"][:, :3],
        )
        capture_mass = captured["parms"][:, 0]
        momentum, kinetic_energy, max_speed = self._totals(
            capture_mass[active], capture_velocity[active]
        )

        flow_direction = self._flow_direction()
        flow_velocity = capture_velocity @ flow_direction
        reverse = active & (flow_velocity < 0.0)
        reverse_momentum, reverse_ke, reverse_max_speed = self._totals(
            capture_mass[reverse], capture_velocity[reverse]
        )
        reverse_particle_momentum = (
            capture_mass[reverse] * np.linalg.norm(capture_velocity[reverse], axis=1)
        )
        reverse_particle_ke = (
            0.5 * capture_mass[reverse]
            * np.sum(capture_velocity[reverse] ** 2, axis=1, dtype=np.float64)
        )

        initial_velocity = np.column_stack((initial["vx"], initial["vy"], initial["vz"]))
        baseline_momentum, baseline_ke, _ = self._totals(
            initial["molar_mass"][active], initial_velocity[active]
        )
        delta_momentum = momentum - baseline_momentum

        row = {
            "record_type": "CAPTURE",
            "source_file": str(self.capture_path),
            "frame": self._frame_from_name(self.capture_path),
            "particle_count": len(captured),
            "active_count": int(np.count_nonzero(active)),
            "waiting_count": int(np.count_nonzero(waiting)),
            "dead_count": int(np.count_nonzero(dead)),
            "boundary_count": int(np.count_nonzero(boundary)),
            "kinetic_energy": kinetic_energy,
            "upstream_count": int(np.count_nonzero(reverse)),
            "max_speed": max_speed,
            "reverse_flow_momentum": float(
                np.sum(capture_mass[reverse] * flow_velocity[reverse], dtype=np.float64)
            ),
            "reverse_kinetic_energy": reverse_ke,
            "reverse_max_speed": reverse_max_speed,
            "reverse_max_particle_momentum": (
                float(np.max(reverse_particle_momentum)) if len(reverse_particle_momentum) else 0.0
            ),
            "reverse_max_particle_kinetic_energy": (
                float(np.max(reverse_particle_ke)) if len(reverse_particle_ke) else 0.0
            ),
            "baseline_kinetic_energy": baseline_ke,
            "delta_kinetic_energy": kinetic_energy - baseline_ke,
        }
        self._put_vector(row, "momentum", momentum)
        self._put_vector(row, "reverse_momentum", reverse_momentum)
        self._put_vector(row, "baseline_momentum", baseline_momentum)
        self._put_vector(row, "delta_momentum", delta_momentum)
        return row

    def Report(self):
        if self.initial_particles is None or self.capture_particles is None:
            raise RuntimeError("ReadBinFile and ReadCapFile must be called before Report")

        csv_path = self.bin_path.with_suffix(".csv")
        new_file = not csv_path.exists()
        if not new_file:
            with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
                existing_fields = next(csv.reader(csv_file), [])
            new_file = existing_fields != CSV_FIELDS
        capture_row = self._capture_row()
        mode = "w" if new_file else "a"
        with csv_path.open(mode, newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS, extrasaction="ignore")
            if new_file:
                writer.writeheader()
                writer.writerow(self._initial_row())
            writer.writerow(capture_row)

        print(f"Capture report written to: {csv_path}")
        print(
            f"Active={capture_row['active_count']}, "
            f"momentum=<{capture_row['momentum_x']:.9g}, "
            f"{capture_row['momentum_y']:.9g}, {capture_row['momentum_z']:.9g}>, "
            f"KE={capture_row['kinetic_energy']:.9g}, "
            f"reverse={capture_row['upstream_count']}, "
            f"reverse momentum={capture_row['reverse_flow_momentum']:.9g}, "
            f"reverse KE={capture_row['reverse_kinetic_energy']:.9g}"
        )
        return csv_path
